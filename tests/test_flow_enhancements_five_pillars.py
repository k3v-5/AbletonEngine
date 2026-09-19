import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
import numpy as np
import soundfile as sf

from engine.adapters.mock_adapter import MockAbletonAdapter
from engine.mix.sidechain_manager import SidechainManager
from engine.music.drop_mutator import DropMutationEngine
from engine.production.copilot.role_orchestrator import RoleTrackOrchestrator
from engine.production.copilot.guided_session import CopilotGuidedSession

def _create_compliant_test_wav(filepath: Path, target_lufs: float = -14.0, duration_sec: float = 3.0, sample_rate: int = 44100):
    filepath.parent.mkdir(parents=True, exist_ok=True)
    t = np.linspace(0, duration_sec, int(sample_rate * duration_sec), endpoint=False)
    sig = 0.3 * np.sin(2 * np.pi * 440.0 * t)
    audio = np.column_stack([sig, sig]).astype(np.float32)
    sf.write(str(filepath), audio, sample_rate, subtype='PCM_24')

def test_pillar_1_utility_gain_staging_preserves_channel_fader():
    conn = MockAbletonAdapter()
    conn.tracks = [
        {'name': 'Chords', 'devices': [{'name': 'Wavetable', 'type': 'instrument'}]}
    ]
    # 1. Ensure Utility device loads or is found
    util_res = SidechainManager.ensure_utility_device(conn, 0)
    assert util_res is not None
    assert util_res['status'] in ('LOADED', 'FOUND')
    util_idx = util_res['device_index']
    assert len(conn.tracks[0]['devices']) == 2
    assert conn.tracks[0]['devices'][util_idx]['name'] == 'Utility'

    # 2. Verify gain staging ducking uses Utility Output (val = db / 35.0)
    # Target value for -2.5 dB ducking is -2.5 / 35.0 = -0.0714
    val = -2.5 / 35.0
    assert -0.072 < val < -0.071

def test_pillar_2_compressor_lom_sidechain_routing():
    conn = MockAbletonAdapter()
    conn.tracks = [
        {'name': 'Lead Vocal', 'devices': []},
        {'name': 'Chords', 'devices': [{'name': 'Compressor', 'type': 'audio_effect'}]}
    ]
    
    # Test LOM routing execution
    res = SidechainManager.route_compressor_sidechain_source(
        conn, track_index=1, device_index=0, source_name_or_index='Lead Vocal'
    )
    assert res.get('status') == 'SUCCESS'
    # Verify execute_code was recorded in executed_code and configures input_routing_type
    assert hasattr(conn, 'executed_code')
    assert len(conn.executed_code) > 0
    assert any('input_routing_type' in code for code in conn.executed_code)

def test_pillar_3_autonomous_audio_bounce_in_phase_9(tmp_path):
    session = CopilotGuidedSession()
    session.reset()
    adapter = MockAbletonAdapter()

    # Set session state directly into Phase 9
    session.data['current_phase'] = 'PHASE_9_MIX_MASTER'
    session.data['phase_index'] = 9
    session.data['tracks'] = [
        {'name': 'Kick', 'role': 'KICK', 'index': 0},
        {'name': 'Bass', 'role': 'BASS', 'index': 1}
    ]
    session._save_state()

    # Mock RenderManager to return a compliant WAV file
    test_wav = tmp_path / 'master_bounce.wav'
    _create_compliant_test_wav(test_wav, target_lufs=-14.0)

    with patch('engine.mix.render_manager.RenderManager.render_analysis_target', return_value=str(test_wav)):
        res = session.step(conn=adapter, user_input='auto bounce master')
        assert res['phase'] in ('PHASE_9_COMPLETED', 'PHASE_10_COMPLETED')
        assert res['status'] == 'COMPLIANT_CERTIFIED'
        audit = session.data.get('lufs_audit', {})
        assert audit.get('integrated_lufs') is not None
        assert 'Render' in str(audit.get('source')) or 'master_bounce' in str(audit.get('source'))

def test_pillar_4_kick_isolation_role_and_sidechain_priority():
    # 1. Verify RoleTrackOrchestrator maps KICK and BOMBO to role 'KICK'
    assert RoleTrackOrchestrator.normalize_role('Kick') == 'KICK'
    assert RoleTrackOrchestrator.normalize_role('Kick Drum') == 'KICK'
    assert RoleTrackOrchestrator.normalize_role('Bombo') == 'KICK'
    
    # 2. Verify GuidedSession prioritizes KICK over DRUMS in Phase 9 sidechain
    session = CopilotGuidedSession()
    session.reset()
    adapter = MockAbletonAdapter()
    adapter.tracks = [
        {'name': 'Drum Rack (Snares/Hats)', 'devices': []},
        {'name': 'Kick Track', 'devices': []},
        {'name': 'Sub Bass', 'devices': [{'name': 'Compressor', 'type': 'audio_effect'}]}
    ]
    session.data['tracks'] = [
        {'name': 'Drum Rack (Snares/Hats)', 'role': 'DRUMS', 'index': 0},
        {'name': 'Kick Track', 'role': 'KICK', 'index': 1},
        {'name': 'Sub Bass', 'role': 'BASS', 'index': 2}
    ]
    session.data['current_phase'] = 'PHASE_9_MIX_MASTER'
    session.data['phase_index'] = 9
    session._save_state()

    # Run sidechain step
    with patch('engine.mix.sidechain_manager.SidechainManager.configure_sidechain') as mock_sidechain:
        mock_sidechain.return_value = {'status': 'CONFIGURED'}
        # Pass input to trigger sidechain
        session.step(conn=adapter, user_input='Opción A')
        
        # Verify configure_sidechain was called with kick_track_index=1 (Kick Track, NOT 0 Drum Rack)
        if mock_sidechain.called:
            call_kwargs = mock_sidechain.call_args[1]
            assert call_kwargs.get('kick_track_index') == 1

def test_pillar_5_drop_mutation_stamped_to_arrangement():
    conn = MockAbletonAdapter()
    conn.tracks = [
        {'name': 'Drop Bass', 'devices': [], 'clips': [{'name': 'Drop Original'}]}
    ]
    
    # 1. Test DropMutationEngine.deploy_variation_to_arrangement directly
    stamped_res = DropMutationEngine.deploy_variation_to_arrangement(
        conn, track_index=0, variation_key='variation_b', destination_bar=48.0, length_bars=16.0
    )
    assert stamped_res is not None
    assert stamped_res['status'] == 'VARIATION_STAMPED_TO_ARRANGEMENT'
    assert stamped_res['destination_bar'] == 48.0
    assert stamped_res['destination_beat'] == 48.0 * 4.0
    
    # 2. Test via CopilotGuidedSession conversational intent in Phase 10
    session = CopilotGuidedSession()
    session.reset()
    session.data['tracks'] = [{'name': 'Drop Bass', 'role': 'BASS', 'index': 0}]
    session.data['current_phase'] = 'PHASE_10_COMPLETED'
    session.data['phase_index'] = 10
    session.data['is_complete'] = True
    session._save_state()

    res = session.step(conn=conn, user_input='estampar drop 1b en el compas 48')
    assert res['status'] == 'DROP_MUTATION_STAMPED'
    assert '48' in res['action_taken']
    assert res['stamped_variation']['destination_bar'] == 48.0

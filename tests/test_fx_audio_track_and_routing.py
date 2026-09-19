# tests/test_fx_audio_track_and_routing.py
import pytest
from unittest.mock import MagicMock
from engine.production.copilot.guided_session import CopilotGuidedSession, ROLE_INSERT_EFFECTS, ROLE_FREQUENCY_GUIDE


class MockLiveConn:
    def __init__(self, track_count=6):
        self.track_count = track_count
        self.sent_commands = []
        self.tracks_info = [
            {'index': 0, 'name': 'Kick', 'is_midi_track': True, 'is_audio_track': False, 'devices': [], 'clip_slots': [{'index': 0, 'has_clip': True}]},
            {'index': 1, 'name': 'Drums', 'is_midi_track': True, 'is_audio_track': False, 'devices': [], 'clip_slots': [{'index': 0, 'has_clip': True}]},
            {'index': 2, 'name': 'Bass', 'is_midi_track': True, 'is_audio_track': False, 'devices': [], 'clip_slots': [{'index': 0, 'has_clip': True}]},
            {'index': 3, 'name': 'Lead', 'is_midi_track': True, 'is_audio_track': False, 'devices': [], 'clip_slots': [{'index': 0, 'has_clip': True}]},
            {'index': 4, 'name': 'Audio FX Bus', 'is_midi_track': False, 'is_audio_track': True, 'devices': [], 'clip_slots': []},
            {'index': 5, 'name': 'Vocals', 'is_midi_track': False, 'is_audio_track': True, 'devices': [], 'clip_slots': []}
        ]

    def send_command(self, cmd, params=None):
        self.sent_commands.append((cmd, params))
        if cmd == 'get_session_info':
            return {'track_count': len(self.tracks_info)}
        elif cmd == 'get_track_info':
            t_idx = (params or {}).get('track_index', 0)
            if t_idx < len(self.tracks_info):
                return self.tracks_info[t_idx]
            return {'index': t_idx, 'name': f'Track {t_idx}', 'is_midi_track': True, 'devices': [], 'clip_slots': []}
        elif cmd == 'create_midi_track':
            idx = len(self.tracks_info)
            self.tracks_info.append({'index': idx, 'name': f'MIDI {idx}', 'is_midi_track': True, 'is_audio_track': False, 'devices': [], 'clip_slots': []})
            return {'index': idx}
        elif cmd == 'execute_code':
            code = (params or {}).get('code', '')
            if 'create_audio_track' in code:
                idx = len(self.tracks_info)
                self.tracks_info.append({'index': idx, 'name': f'Audio {idx}', 'is_midi_track': False, 'is_audio_track': True, 'devices': [], 'clip_slots': []})
                return {'status': 'success', 'result': {'res': idx}}
            elif 'matched_rt' in code:
                return {'status': 'success', 'result': {'res': {'status': 'success', 'routed_to': '[LEAD] Lead', 'monitoring': 0}}}
            return {'status': 'success', 'result': {}}
        elif cmd == 'get_cue_points':
            return {'cue_points': [{'time': 16.0}]}
        elif cmd == 'set_track_name':
            return {'status': 'ok'}
        elif cmd == 'set_track_volume':
            return {'status': 'ok'}
        elif cmd == 'load_browser_item':
            return {'status': 'ok'}
        elif cmd == 'delete_clip':
            return {'status': 'ok'}
        elif cmd == 'delete_cue_point':
            return {'status': 'ok'}
        elif cmd == 'stop_playback':
            return {'status': 'ok'}
        return {'status': 'ok'}


def test_preflight_clean_preserves_template_tracks():
    session = CopilotGuidedSession()
    conn = MockLiveConn(track_count=6)
    report = session.preflight_clean_session(conn)

    assert report['playback_stopped'] is True
    assert report['cue_points_cleared'] >= 1
    assert report['tracks_cleaned'] == 6

    for cmd, params in conn.sent_commands:
        if cmd == 'execute_code':
            code = (params or {}).get('code', '')
            assert 'song.delete_track' not in code, 'Destructive track pruning must not be used'


def test_phase_1_fx_audio_track_parsing_and_scaffolding():
    session = CopilotGuidedSession()
    conn = MockLiveConn(track_count=6)

    res = session._handle_phase_1(conn, 'Kick, Drums, Bass, Lead, FX (Audio)')
    assert res['phase'] == 'PHASE_2_SECTIONS'

    tracks = session.data['tracks']
    fx_tracks = [t for t in tracks if t.get('role') == 'FX']
    assert len(fx_tracks) == 1
    fx_t = fx_tracks[0]
    assert fx_t['is_audio'] is True
    assert fx_t['is_fx_audio'] is True


def test_phase_3_fx_audio_prompt_and_routing_handling():
    session = CopilotGuidedSession()
    conn = MockLiveConn(track_count=6)
    session._handle_phase_1(conn, 'Kick, Drums, Bass, Lead, FX (Audio)')

    session.data['current_phase'] = 'PHASE_3_INSTRUMENTS'
    session.data['phase_index'] = 3
    session.data['current_track_ptr'] = 4

    prompt = session._prompt_current_track_instrument()
    assert 'CONFIGURACIÓN DE PISTA DE EFECTO DE AUDIO' in prompt['current_step']
    assert 'Cableguys ShaperBox 3' in prompt['question']
    assert 'Output Thermal' in prompt['question']

    handle_res = session._handle_phase_3(conn, 'ShaperBox 3 desde Lead')
    fx_track = session.data['tracks'][4]
    assert 'ShaperBox 3' in fx_track['instrument']
    assert fx_track['effect_loaded'] == 'Cableguys ShaperBox 3'
    assert fx_track['monitoring_state'] == 'In'


def test_role_catalog_includes_fx():
    assert 'FX' in ROLE_INSERT_EFFECTS
    assert len(ROLE_INSERT_EFFECTS['FX']) >= 2
    assert 'FX' in ROLE_FREQUENCY_GUIDE
    assert 'dominant_zone' in ROLE_FREQUENCY_GUIDE['FX']

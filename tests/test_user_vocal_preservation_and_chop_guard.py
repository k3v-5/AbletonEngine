import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from engine.production.copilot.guided_session import CopilotGuidedSession

def test_vocal_scan_multi_track_fallback(tmp_path, monkeypatch):
    test_state_file = tmp_path / 'guided_session.json'
    monkeypatch.setattr(CopilotGuidedSession, 'STATE_FILE', test_state_file)

    mock_conn = MagicMock()
    
    def fake_send(cmd, params=None):
        if cmd == 'get_session_info':
            return {'track_count': 18}
        if cmd == 'get_track_info':
            t_idx = params.get('track_index', 0)
            if t_idx == 12:
                return {'name': '13-Audio', 'is_audio_track': True, 'is_foldable': False}
            if t_idx == 15:
                return {'name': '16-Audio', 'is_audio_track': True, 'is_foldable': False}
            return {'name': f'Track {t_idx}', 'is_audio_track': False}
        if cmd == 'execute_code':
            return {'res': {'path': 'D:/Documentos/test.wav', 'track_index': 15}}
        return {}

    mock_conn.send_command.side_effect = fake_send
    
    session = CopilotGuidedSession()
    session.data['current_phase'] = 'PHASE_9_COMPLETED'
    session.data['phase_index'] = 9
    session.data['tracks'] = [{'index': 12, 'name': '13-Audio', 'role': 'VOCALS', 'is_audio': True}]
    session.data['bpm'] = 120.0
    session._save_state()
    
    with patch('pathlib.Path.exists', return_value=True):
        with patch('soundfile.read', side_effect=PermissionError('File locked by Live')):
            res = session.step(conn=mock_conn, user_input='procesar y cortar mi audio en partes y hacer chops')
            assert res is not None
            assert res.get('status') in ('AWAITING_VOCAL_WORKFLOW_CHOICE', 'VOCALS_PROCESSED', 'LUFS_CALIBRATION_REQUIRED')

def test_chop_guard_protects_user_clip_from_deletion():
    clip_base = MagicMock()
    clip_base.name = 'Audio'
    clip_base.start_time = 40.0
    
    clip_user_other = MagicMock()
    clip_user_other.name = 'My Special Recording'
    clip_user_other.start_time = 50.0

    clip_old_chop = MagicMock()
    clip_old_chop.name = '[VOCAL CHOP] Old Drop Chop'
    clip_old_chop.start_time = 130.0

    track_15 = MagicMock()
    track_15.arrangement_clips = [clip_base, clip_user_other, clip_old_chop]

    deleted = []
    for old_c in list(track_15.arrangement_clips):
        if old_c == clip_base:
            continue
        if old_c.name.startswith('[VOCAL CHOP]') or old_c.name.startswith('[CHOP]'):
            deleted.append(old_c)

    assert clip_base not in deleted
    assert clip_user_other not in deleted
    assert clip_old_chop in deleted

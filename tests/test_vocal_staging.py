# tests/test_vocal_staging.py
import pytest
from unittest.mock import MagicMock
from engine.vocal.vocal_staging_supervisor import VocalStagingSupervisor
from engine.vocal.pipeline import VocalStyle


def test_vocal_staging_target_identification():
    track_names = [
        "1-Kick",
        "2-Snare",
        "3-808 Bass",
        "4-Rhodes Piano",
        "5-Ambient Pad",
        "6-Lead Synth",
        "7-Vocal Lead"
    ]
    plan = VocalStagingSupervisor.calculate_vocal_staging_plan(
        track_names=track_names,
        vocal_style=VocalStyle.MODERN_RAP
    )
    assert plan["status"] == "SUCCESS"
    assert plan["competing_tracks_count"] == 3  # Rhodes (3), Pad (4), Lead Synth (5)
    assert plan["competing_track_indices"] == [3, 4, 5]


def test_vocal_frequency_carving_specs():
    track_names = ["1-Drums", "2-Rhodes Chords", "3-Lead Synth", "4-Vocals"]
    plan = VocalStagingSupervisor.calculate_vocal_staging_plan(
        track_names=track_names,
        vocal_style=VocalStyle.RNB_SOUL
    )
    carvings = plan["frequency_carvings"]
    assert len(carvings) == 2  # Rhodes Chords, Lead Synth
    for c in carvings:
        assert c["frequency_hz"] == 2800.0
        assert c["cut_gain_db"] == -3.0
        assert c["q"] == 1.4


def test_vocal_ducking_envelope_generation():
    track_names = ["1-Drums", "2-Pad", "3-Vocals"]
    vocal_phrases = [(16.0, 32.0), (48.0, 64.0)]  # Two 4-bar vocal phrases
    plan = VocalStagingSupervisor.calculate_vocal_staging_plan(
        track_names=track_names,
        vocal_ranges_beats=vocal_phrases,
        song_length_beats=128.0,
        duck_amount_db=-3.0
    )
    envelope = plan["ducking_envelope"]
    assert len(envelope) > 0
    # Values during vocal phrase (time=16.0 to 32.0) should be ducked (< 0.85)
    ducked_pts = [p for p in envelope if 16.0 <= p["time"] <= 32.0]
    assert any(p["value"] < 0.65 for p in ducked_pts)


def test_apply_staging_to_session():
    mock_conn = MagicMock()
    res = VocalStagingSupervisor.apply_staging_to_session(
        conn=mock_conn,
        vocal_track_index=6,
        accompaniment_track_indices=[3, 4, 5]
    )
    assert res["status"] == "SUCCESS"
    assert len(res["carved_tracks"]) == 3
    assert mock_conn.send_command.call_count == 3

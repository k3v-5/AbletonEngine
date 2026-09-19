# tests/test_vocal_auto_orchestration.py
"""
Tests verifying the autonomous vocal orchestration pipeline:
1. Auto-detection of pre-existing audio vocal tracks in Phase 1 even with instrumental prompt.
2. Verified audio take loading and FX chain loading in Phase 3.
3. Gain staging (-14.0 dBFS) bypassing synth parameter sculpting in Phase 4.
4. Deployment of vocal audio clips to the Arrangement timeline in Verse 1 and Drops in Phase 6.
5. Sidechain ducking routing to Keys, Pad, Lead on Utility.Output in Phase 8.
"""

import pytest
from engine.adapters.mock_adapter import MockAbletonAdapter
from engine.production.copilot.guided_session import CopilotGuidedSession


@pytest.fixture
def session_with_vocal_audio_track():
    adapter = MockAbletonAdapter()
    # Add pre-existing audio vocal track mimicking Live's 13-Audio or Lead Vocal
    adapter.tracks.append({
        "name": "13-Audio",
        "is_audio_track": True,
        "is_midi_track": False,
        "is_foldable": False,
        "clip_slots": [{"has_clip": False} for _ in range(8)],
        "devices": [],
        "volume": 0.85
    })
    session = CopilotGuidedSession()
    session.reset()
    return session, adapter


def test_vocal_track_auto_detection_phase_1(session_with_vocal_audio_track):
    session, adapter = session_with_vocal_audio_track
    prompt = "Kick, Drums, 808 Bass, Keys, Pad, Lead a 128 BPM"
    res1 = session.step(conn=adapter, user_input=prompt)

    assert res1["phase"] == "PHASE_2_SECTIONS"
    tracks = session.data["tracks"]
    # 6 requested instruments + 1 auto-detected vocal track = 7 tracks total
    assert len(tracks) == 7

    vocal_trk = next((t for t in tracks if t["role"] == "VOCALS"), None)
    assert vocal_trk is not None, "VOCALS role was not auto-detected from pre-existing audio track"
    assert vocal_trk["is_audio"] is True
    assert vocal_trk["index"] == 2
    assert "Lead Vocal" in vocal_trk["name"] or "Audio" in vocal_trk["name"]


def test_vocal_take_loading_phase_3_live_mic_mode(session_with_vocal_audio_track):
    """Verifies Option 1 prepares live mic tracking, arms the track in Live, and sets up FX."""
    session, adapter = session_with_vocal_audio_track
    session.step(conn=adapter, user_input="Kick, Drums, 808 Bass, Keys, Pad, Lead a 128 BPM")
    session.step(conn=adapter, user_input="Opción A")  # Phase 2 Sections

    # Step through all 7 tracks in Phase 3 selecting Option 1 (Live Mic Mode for vocal)
    for _ in range(7):
        session.step(conn=adapter, user_input="Opción 1")

    vocal_trk = next(t for t in session.data["tracks"] if t["role"] == "VOCALS")
    assert vocal_trk["is_audio"] is True
    assert vocal_trk["live_recording_mode"] is True
    assert vocal_trk.get("sample_path") is None, "Live mic recording track must have sample_path set to None"
    assert "Live Vocal Mic" in vocal_trk.get("instrument", "")

    # Verify physical track arming in Live / mock adapter
    vocal_idx = vocal_trk["index"]
    assert adapter.tracks[vocal_idx].get("arm") is True, f"Track {vocal_idx} must be armed for live mic recording"


def test_vocal_take_import_phase_3_option_2(session_with_vocal_audio_track):
    """Verifies Option 2 allows importing an existing audio take from library."""
    session, adapter = session_with_vocal_audio_track
    session.step(conn=adapter, user_input="Kick, Drums, 808 Bass, Keys, Pad, Lead a 128 BPM")
    session.step(conn=adapter, user_input="Opción A")

    # Step through instrumental tracks 0..5 with Option 1, then vocal track with Option 2
    for _ in range(6):
        session.step(conn=adapter, user_input="Opción 1")
    # Vocal track: select Option 2 to import existing take
    session.step(conn=adapter, user_input="Opción 2")

    vocal_trk = next(t for t in session.data["tracks"] if t["role"] == "VOCALS")
    assert vocal_trk.get("sample_path"), "Vocal track sample_path must be populated when importing"
    assert vocal_trk["is_audio"] is True
    assert vocal_trk.get("live_recording_mode") is False
    assert "Audio Take" in vocal_trk.get("instrument", "")

    vocal_idx = vocal_trk["index"]
    vocal_slots = adapter.tracks[vocal_idx]["clip_slots"]
    assert vocal_slots[0].get("has_clip") is True


def test_vocal_gain_staging_phase_4(session_with_vocal_audio_track):
    session, adapter = session_with_vocal_audio_track
    session.step(conn=adapter, user_input="Kick, Drums, 808 Bass, Keys, Pad, Lead a 128 BPM")
    session.step(conn=adapter, user_input="Opción A")
    for _ in range(7):
        session.step(conn=adapter, user_input="Opción 1")

    assert session.data["current_phase"] == "PHASE_4_PARAM_SCULPTING"
    # Step through Phase 4 for all 7 tracks
    for _ in range(7):
        session.step(conn=adapter, user_input="Opción 1")

    vocal_trk = next(t for t in session.data["tracks"] if t["role"] == "VOCALS")
    assert vocal_trk["gain_staging"]["target_peak_dbfs"] == -14.0
    assert vocal_trk["sculpted_parameters"].get("IS_AUDIO") is True


def test_vocal_clip_arrangement_stamping_phase_6(session_with_vocal_audio_track):
    """Verifies that when an external take is imported (Option 2), clips are stamped into the arrangement."""
    session, adapter = session_with_vocal_audio_track
    session.step(conn=adapter, user_input="Kick, Drums, 808 Bass, Keys, Pad, Lead a 128 BPM")
    session.step(conn=adapter, user_input="Opción A")
    # Tracks 0..5 Option 1, vocal track Option 2 (import external take)
    for _ in range(6):
        session.step(conn=adapter, user_input="Opción 1")
    session.step(conn=adapter, user_input="Opción 2")
    for _ in range(7):
        session.step(conn=adapter, user_input="Opción 1")
    while session.data["current_phase"] == "PHASE_5_INSERT_EFFECTS":
        session.step(conn=adapter, user_input="Opción 1")

    assert session.data["current_phase"] == "PHASE_6_COMPOSITION"
    res6 = session.step(conn=adapter, user_input="KEY F menor a 128 BPM")
    assert res6["phase"] == "PHASE_7_AUTOMATION"

    # Verify vocal track arrangement clips are NOT empty when take is imported
    vocal_trk_info = next(t for t in session.data["tracks"] if t["role"] == "VOCALS")
    vocal_idx = vocal_trk_info["index"]
    arr_clips = adapter.tracks[vocal_idx].get("arrangement_clips", [])
    assert len(arr_clips) >= 3, f"Expected at least 3 vocal arrangement clips, found {len(arr_clips)}"

    start_times = [c["start_time"] for c in arr_clips]
    # Verse 1 starts at beat 32.0 (bar 8)
    assert 32.0 in start_times, "Verse 1 vocal clip missing at beat 32.0"
    # Drop 1 starts at beat 128.0 (bar 32)
    assert 128.0 in start_times, "Drop 1 vocal clip missing at beat 128.0"
    # Drop 2 starts at beat 224.0 (bar 56)
    assert 224.0 in start_times, "Drop 2 vocal clip missing at beat 224.0"

    # Assert structural silences (no clip at Intro, Buildup, Puente, Outro)
    assert 0.0 not in start_times, "Vocal clip should not be placed at Intro (beat 0.0)"
    assert 96.0 not in start_times, "Vocal clip should not be placed at Buildup (beat 96.0)"
    assert 192.0 not in start_times, "Vocal clip should not be placed at Puente (beat 192.0)"
    assert 288.0 not in start_times, "Vocal clip should not be placed at Outro (beat 288.0)"


def test_live_mic_mode_keeps_arrangement_clean_with_zero_clips(session_with_vocal_audio_track):
    """Guarantees that selecting Option 1 (Live mic recording) leaves 0 clips on the vocal track so user can record."""
    session, adapter = session_with_vocal_audio_track
    session.step(conn=adapter, user_input="Kick, Drums, 808 Bass, Keys, Pad, Lead a 128 BPM")
    session.step(conn=adapter, user_input="Opción A")
    # All tracks including vocal select Option 1 (Live Mic Mode)
    for _ in range(7):
        session.step(conn=adapter, user_input="Opción 1")
    for _ in range(7):
        session.step(conn=adapter, user_input="Opción 1")
    while session.data["current_phase"] == "PHASE_5_INSERT_EFFECTS":
        session.step(conn=adapter, user_input="Opción 1")

    assert session.data["current_phase"] == "PHASE_6_COMPOSITION"
    res6 = session.step(conn=adapter, user_input="KEY F menor a 128 BPM")
    assert res6["phase"] == "PHASE_7_AUTOMATION"

    # Verify vocal track has ZERO arrangement clips and is armed for the user to record
    vocal_trk_info = next(t for t in session.data["tracks"] if t["role"] == "VOCALS")
    vocal_idx = vocal_trk_info["index"]
    arr_clips = adapter.tracks[vocal_idx].get("arrangement_clips", [])
    assert len(arr_clips) == 0, f"Expected 0 vocal arrangement clips for live mic, found {len(arr_clips)}"
    assert adapter.tracks[vocal_idx].get("arm") is True, "Vocal track must remain armed for live mic recording"


def test_vocal_sidechain_ducking_routing_phase_8(session_with_vocal_audio_track):
    session, adapter = session_with_vocal_audio_track
    session.step(conn=adapter, user_input="Kick, Drums, 808 Bass, Keys, Pad, Lead a 128 BPM")
    session.step(conn=adapter, user_input="Opción A")
    for _ in range(7):
        session.step(conn=adapter, user_input="Opción 1")
    for _ in range(7):
        session.step(conn=adapter, user_input="Opción 1")
    while session.data["current_phase"] == "PHASE_5_INSERT_EFFECTS":
        session.step(conn=adapter, user_input="Opción 1")
    session.step(conn=adapter, user_input="KEY F menor a 128 BPM")
    session.step(conn=adapter, user_input="Bypass")  # Skip Phase 7

    res8 = session.step(conn=adapter, user_input="Opción A")  # Phase 8 Vocal Ducking
    assert res8["phase"] == "PHASE_9_MIX_MASTER"

    ducking = session.data.get("vocal_ducking", {})
    assert ducking.get("status") == "CONFIGURED"
    assert ducking.get("vocal_source_track") == 2
    # Harmonic target tracks: Keys (4), Pad (5), Lead (6)
    assert 2 not in ducking.get("target_tracks", []), "Vocal track must not duck itself"
    for expected_harmonic_idx in [4, 5, 6]:
        assert expected_harmonic_idx in ducking.get("target_tracks", [])

    assert ducking.get("automation_applied") is True
    assert ducking.get("ducking_target") == "Utility.Output"
    assert ducking.get("faders_unlocked") is True
    assert ducking.get("ducking_points_count", 0) > 0

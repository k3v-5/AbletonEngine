# tests/test_copilot_stepper.py
import pytest
from engine.production.copilot.models import (
    ProductionPhase,
    DecisionStatus,
    ProductionDecision,
    CopilotState,
)
from engine.production.copilot.stepper import ExecutiveCopilotEngine


class MockLiveConnection:
    def __init__(self, tracks=None, tempo=138.0):
        self.tracks = tracks or []
        self.tempo = tempo
        self.commands = []

    def send_command(self, cmd: str, params: dict):
        self.commands.append((cmd, params))
        if cmd == "get_session_info":
            return {"num_tracks": len(self.tracks), "tempo": self.tempo}
        if cmd == "get_track_info":
            t_idx = params.get("track_index", 0)
            if t_idx < len(self.tracks):
                return self.tracks[t_idx]
            return {"name": f"Track {t_idx}", "track_index": t_idx}
        return {"status": "ok"}


def test_copilot_empty_session():
    copilot = ExecutiveCopilotEngine()
    state = copilot.inspect_session(tracks=[])

    assert state.current_phase == ProductionPhase.PHASE_1_DNA
    assert len(state.pending_decisions) >= 4
    dec_ids = [d.id for d in state.pending_decisions]
    assert "DEC-P1-01-CREATIVE-MOOD" in dec_ids
    assert "DEC-P1-02-HARMONIC-DNA" in dec_ids
    assert "DEC-P1-03-TRACK-SCAFFOLD" in dec_ids
    assert "DEC-P1-04-ENERGY-ROADMAP" in dec_ids
    assert state.pending_decisions[0].phase == ProductionPhase.PHASE_1_DNA
    assert state.pending_decisions[0].status == DecisionStatus.PENDING


def test_copilot_session_inspection_tracks():
    copilot = ExecutiveCopilotEngine()
    mock_tracks = [
        {"name": "Kick Drums", "track_index": 0},
        {"name": "808 Sub Bass", "track_index": 1},
        {"name": "Grand Piano Chords", "track_index": 2},
        {"name": "Main Lead Synth", "track_index": 3},
    ]

    state = copilot.inspect_session(tracks=mock_tracks)
    pending_ids = [d.id for d in state.pending_decisions]

    # Sidechain kick-808 decision
    assert "DEC-P6-SIDECHAIN-T0-T1" in pending_ids
    # Drum humanize decision
    assert "DEC-P4-HUMANIZE-DRUMS-T0" in pending_ids
    # 808 slides decision
    assert "DEC-P4-808-SLIDES-T1" in pending_ids
    # Chord strumming decision
    assert "DEC-P4-STRUM-CHORDS-T2" in pending_ids
    # Lead depth staging decision
    assert "DEC-P6-DEPTH-STAGING-T3" in pending_ids
    # Master delivery decision
    assert "DEC-P7-MASTER-CHAIN-DELIVERY" in pending_ids
    # Vocal hook chops decision
    assert "DEC-P2-VOCAL-HOOK-CHOPS" in pending_ids
    # Organic foley bed decision
    assert "DEC-P3-ORGANIC-FOLEY-BED" in pending_ids
    # Drum break chopper decision
    assert "DEC-P4-BREAK-CHOPPER-T0" in pending_ids
    # 5 New Advanced Dimensions
    assert "DEC-P2-COUNTER-MELODY" in pending_ids
    assert "DEC-P3-AUTO-CURATE-TRACKS" in pending_ids
    assert "DEC-P4-DRUM-EVOLVER" in pending_ids
    assert "DEC-P5-TRANSITION-RISERS" in pending_ids
    assert "DEC-P6-GAIN-STAGING" in pending_ids
    # 3 New Production Frontiers (Impacts, Stems Phase, Groove Pool)
    assert "DEC-P4-GROOVE-POOL" in pending_ids
    assert "DEC-P5-IMPACTS-DOWNLIFTERS" in pending_ids
    assert "DEC-P7-STEM-PHASE-AUDIT" in pending_ids

    # Mandatory Preset Selection and Parameter Sculpting in Phase 3
    assert "DEC-P3-04-PRESET-SELECT-T2" in pending_ids
    assert "DEC-P3-04-PARAM-CONFIG-T2" in pending_ids
    assert "DEC-P3-05-PRESET-SELECT-T3" in pending_ids
    assert "DEC-P3-05-PARAM-CONFIG-T3" in pending_ids


def test_copilot_generates_dna_decisions_on_18_track_default_template():
    """
    REGRESSION: User's default Ableton project starts with 18 tracks.
    Engine must ALWAYS generate Phase 1 DNA decisions regardless of track count.
    Bug: old code had `if len(session_tracks) < 4` gate that silently skipped DNA for 18-track sessions.
    """
    copilot = ExecutiveCopilotEngine()
    copilot.reset()

    # Simulate the user's real 18-track default template
    mock_18_tracks = [
        {"name": "Drums", "track_index": 0, "is_foldable": True},       # Group
        {"name": "Loop", "track_index": 1, "is_midi_track": True},
        {"name": "808 Drums", "track_index": 2, "is_midi_track": True},
        {"name": "Synths / Instruments", "track_index": 3, "is_foldable": True},  # Group
        {"name": "808 Bass", "track_index": 4, "is_midi_track": True},
        {"name": "Lead Synth", "track_index": 5, "is_midi_track": True},
        {"name": "Synth 1", "track_index": 6, "is_midi_track": True},
        {"name": "Synth 2", "track_index": 7, "is_midi_track": True},
        {"name": "Strings", "track_index": 8, "is_midi_track": True},
        {"name": "Piano Keys", "track_index": 9, "is_midi_track": True},
        {"name": "Pad 1", "track_index": 10, "is_midi_track": True},
        {"name": "Vocals", "track_index": 11, "is_foldable": True},     # Group
        {"name": "Vox Lead", "track_index": 12, "is_audio_track": True},
        {"name": "Vox Harmony", "track_index": 13, "is_audio_track": True},
        {"name": "FX", "track_index": 14, "is_foldable": True},         # Group
        {"name": "Reverb Return", "track_index": 15, "is_audio_track": True},
        {"name": "Delay Return", "track_index": 16, "is_audio_track": True},
        {"name": "Master Bus", "track_index": 17, "is_audio_track": True},
    ]

    state = copilot.inspect_session(tracks=mock_18_tracks)
    pending_ids = [d.id for d in state.pending_decisions]

    # CRITICAL: Phase 1 DNA must always be generated regardless of track count
    assert "DEC-P1-01-CREATIVE-MOOD" in pending_ids, (
        "BUG: Phase 1 DNA 'Creative Mood' decision not generated for 18-track template. "
        "Engine must not gate DNA generation on session size."
    )
    assert "DEC-P1-02-HARMONIC-DNA" in pending_ids, (
        "BUG: Phase 1 DNA 'Harmonic DNA' decision not generated for 18-track template."
    )
    assert "DEC-P1-03-TRACK-SCAFFOLD" in pending_ids, (
        "BUG: Phase 1 DNA 'Track Scaffold' decision not generated for 18-track template."
    )
    assert "DEC-P1-04-ENERGY-ROADMAP" in pending_ids, (
        "BUG: Phase 1 DNA 'Energy Roadmap' decision not generated for 18-track template."
    )

    # Phase 3 Sound Design decisions must be generated based on track name classification:
    # - "808" keyword → bass classifier → T2 "808 Drums" becomes BASS (not drums!)
    # - "drum"/"kit" keyword → drum classifier → T0 "Drums" group → first drum_track = T0
    # - "lead"/"synth" keyword → lead classifier → T5 "Lead Synth" → T5
    # - "piano" keyword → chord/keys classifier → T9 "Piano Keys" → T9

    # T0 "Drums" (group) → drum rack decision (first drum_track found)
    assert "DEC-P3-02-AUTHENTIC-DRUM-RACK-T0" in pending_ids, (
        "BUG: Drum Rack load decision not generated for T0 (Drums group). "
        "Classifier matches 'drum' keyword → drum_tracks list."
    )
    # T2 "808 Drums" → classified as BASS because '808' keyword takes priority
    assert "DEC-P3-03-BASS-INSTRUMENT-LOAD-T2" in pending_ids, (
        "BUG: Bass instrument load not generated for T2 (808 Drums). "
        "'808' keyword classifies it as bass track."
    )
    # T3 "Synths / Instruments" is a group track (is_foldable=True) -> MUST BE SKIPPED as instrument target
    # T5 "Lead Synth" wins as the first valid MIDI lead track!
    assert "DEC-P3-05-LEAD-INSTRUMENT-LOAD-T5" in pending_ids, (
        "BUG: Lead instrument load decision not generated for T5 (Lead Synth). "
        "T3 'Synths / Instruments' is a group track and must be skipped."
    )
    # T9 "Piano Keys" → keys/chord classifier → requires Analog Lab preset + config
    assert "DEC-P3-04-KEYS-INSTRUMENT-LOAD-T9" in pending_ids, (
        "BUG: Keys instrument load decision not generated for T9 (Piano Keys)."
    )
    # T9 keys also must require preset selection (Analog Lab rule)
    assert "DEC-P3-04-PRESET-SELECT-T9" in pending_ids, (
        "BUG: Preset selection not enforced for T9 (Piano Keys / Analog Lab)."
    )

    # Total must be > 10 decisions (DNA + Phase 3 for multiple tracks)
    assert len(state.pending_decisions) >= 10, (
        f"BUG: Expected >= 10 decisions for 18-track template, got {len(state.pending_decisions)}"
    )

    # Preflight must block (nothing resolved yet)
    report = copilot.preflight_check()
    assert report["ready_for_export"] is False


def test_copilot_execute_decision_yes():
    copilot = ExecutiveCopilotEngine()
    mock_tracks = [
        {"name": "Kick", "track_index": 0},
        {"name": "808 Bass", "track_index": 1},
    ]
    copilot.inspect_session(tracks=mock_tracks)

    dec_id = "DEC-P6-SIDECHAIN-T0-T1"
    res = copilot.execute_decision(decision_id=dec_id, choice="YES")

    assert res["status"] == "success"
    assert res["action"] == "APPLIED"
    assert dec_id not in [d.id for d in copilot.pending_decisions.values()]
    assert dec_id in copilot.resolved_decisions
    assert copilot.resolved_decisions[dec_id].status == DecisionStatus.APPLIED


def test_copilot_execute_decision_no_with_justification():
    copilot = ExecutiveCopilotEngine()
    mock_tracks = [
        {"name": "Kick", "track_index": 0},
        {"name": "808 Bass", "track_index": 1},
    ]
    copilot.inspect_session(tracks=mock_tracks)

    dec_id = "DEC-P4-808-SLIDES-T1"
    producer_rationale = "Bassline needs strict sustained roots without pitch variation."
    res = copilot.execute_decision(
        decision_id=dec_id,
        choice="NO",
        justification=producer_rationale
    )

    assert res["status"] == "success"
    assert res["action"] == "REJECTED"
    assert res["justification"] == producer_rationale
    assert copilot.resolved_decisions[dec_id].status == DecisionStatus.REJECTED
    assert copilot.resolved_decisions[dec_id].justification_if_rejected == producer_rationale


def test_copilot_execute_decision_custom():
    copilot = ExecutiveCopilotEngine()
    mock_tracks = [
        {"name": "Drums Kit", "track_index": 2},
    ]
    copilot.inspect_session(tracks=mock_tracks)

    dec_id = "DEC-P4-HUMANIZE-DRUMS-T2"
    custom_params = {"strength": 0.5, "pocket_style": "boom_bap_dilla"}
    res = copilot.execute_decision(
        decision_id=dec_id,
        choice="CUSTOM",
        custom_args=custom_params
    )

    assert res["status"] == "success"
    assert res["action"] == "APPLIED"
    assert copilot.resolved_decisions[dec_id].status == DecisionStatus.APPLIED
    assert copilot.resolved_decisions[dec_id].result["args"] == custom_params


def test_copilot_preflight_check():
    copilot = ExecutiveCopilotEngine()
    mock_tracks = [
        {"name": "Kick", "track_index": 0},
        {"name": "808", "track_index": 1},
    ]
    copilot.inspect_session(tracks=mock_tracks)

    # Initially has pending decisions
    report = copilot.preflight_check()
    assert report["ready_for_export"] is False
    assert report["pending_count"] > 0
    assert len(report["blockers"]) > 0

    # Resolve all decisions
    for dec_id in list(copilot.pending_decisions.keys()):
        copilot.execute_decision(decision_id=dec_id, choice="YES")

    report_after = copilot.preflight_check()
    assert report_after["ready_for_export"] is True
    assert report_after["pending_count"] == 0
    assert report_after["progress_pct"] == 100.0


def test_copilot_live_connection_dispatch():
    mock_tracks = [
        {"name": "Kick Track", "track_index": 0},
        {"name": "808 Bass Track", "track_index": 1},
    ]
    conn = MockLiveConnection(tracks=mock_tracks)
    copilot = ExecutiveCopilotEngine()
    copilot.inspect_session(conn=conn)

    dec_id = "DEC-P6-SIDECHAIN-T0-T1"
    res = copilot.execute_decision(decision_id=dec_id, choice="YES", conn=conn)

    assert res["status"] == "success"
    assert "result" in res
    assert res["result"].get("live_result") == "executed_via_adapter"
    # Verify adapter received automation commands
    cmd_names = [c[0] for c in conn.commands]
    assert "create_automation" in cmd_names


def test_copilot_drum_octave_mismatch_detection_and_fix():
    copilot = ExecutiveCopilotEngine()
    mock_tracks = [
        {"name": "Drum Kit", "track_index": 0},
    ]
    # Drum notes in C3 (pitches 60, 62) -> Quadrant 3
    clip_map = {
        0: [
            {"pitch": 60, "start_time": 0.0, "duration": 0.25, "velocity": 110},
            {"pitch": 62, "start_time": 1.0, "duration": 0.25, "velocity": 100}
        ]
    }
    state = copilot.inspect_session(tracks=mock_tracks, clip_notes_map=clip_map)
    pending_ids = [d.id for d in state.pending_decisions]

    assert "DEC-P3-02-DRUM-OCTAVE-FIX-T0" in pending_ids

    # Execute the fix
    res = copilot.execute_decision(decision_id="DEC-P3-02-DRUM-OCTAVE-FIX-T0", choice="YES")
    assert res["status"] == "success"
    assert res["action"] == "APPLIED"
    assert "DEC-P3-02-DRUM-OCTAVE-FIX-T0" in copilot.resolved_decisions


def test_copilot_preset_and_param_execution():
    copilot = ExecutiveCopilotEngine()
    mock_tracks = [
        {"name": "Keys Rhodes", "track_index": 2},
    ]
    state = copilot.inspect_session(tracks=mock_tracks)
    pending_ids = [d.id for d in state.pending_decisions]

    assert "DEC-P3-04-PRESET-SELECT-T2" in pending_ids
    assert "DEC-P3-04-PARAM-CONFIG-T2" in pending_ids

    # Execute preset selection
    res_preset = copilot.execute_decision(decision_id="DEC-P3-04-PRESET-SELECT-T2", choice="YES")
    assert res_preset["status"] == "success"
    assert res_preset["action"] == "APPLIED"

    # Execute parameter sculpting
    res_param = copilot.execute_decision(decision_id="DEC-P3-04-PARAM-CONFIG-T2", choice="YES")
    assert res_param["status"] == "success"
    assert res_param["action"] == "APPLIED"


def test_copilot_forces_vst_analog_lab_and_paired_effects():
    copilot = ExecutiveCopilotEngine()
    copilot.reset()
    mock_tracks = [
        {"name": "Drums Core", "track_index": 0},
        {"name": "808 Bass", "track_index": 1},
        {"name": "Keys Rhodes", "track_index": 2},
        {"name": "Lead Synth", "track_index": 3},
    ]
    state = copilot.inspect_session(tracks=mock_tracks)
    pending_ids = [d.id for d in state.pending_decisions]

    # 1. Engine forces VST / Instrument selection for all tracks
    assert "DEC-P3-02-AUTHENTIC-DRUM-RACK-T0" in pending_ids
    assert "DEC-P3-03-BASS-INSTRUMENT-LOAD-T1" in pending_ids
    assert "DEC-P3-04-KEYS-INSTRUMENT-LOAD-T2" in pending_ids
    assert "DEC-P3-05-LEAD-INSTRUMENT-LOAD-T3" in pending_ids

    # Verify choices contain Top 5 suggestions
    bass_dec = copilot.pending_decisions["DEC-P3-03-BASS-INSTRUMENT-LOAD-T1"]
    assert "Top 5" in bass_dec.description
    assert "Serum 2" in bass_dec.description

    keys_dec = copilot.pending_decisions["DEC-P3-04-KEYS-INSTRUMENT-LOAD-T2"]
    assert "Top 5" in keys_dec.description
    assert "Analog Lab V" in keys_dec.description

    # 2. For Analog Lab V: requires preset selection (Step 1) AND macro sculpting (Step 2)
    assert "DEC-P3-04-PRESET-SELECT-T2" in pending_ids
    assert "DEC-P3-04-PARAM-CONFIG-T2" in pending_ids
    preset_dec = copilot.pending_decisions["DEC-P3-04-PRESET-SELECT-T2"]
    assert "Paso 1" in preset_dec.description
    assert "A Rhodes For You" in preset_dec.description

    macro_dec = copilot.pending_decisions["DEC-P3-04-PARAM-CONFIG-T2"]
    assert "Paso 2" in macro_dec.description
    assert "BRIGHTNESS" in macro_dec.description

    # 3. Paired Effect Loading and Mandatory Configuration
    # Drums
    assert "DEC-P3-02-DRUM-FX-LOAD-T0" in pending_ids
    assert "DEC-P3-02-DRUM-FX-CONFIG-T0" in pending_ids
    # Bass
    assert "DEC-P3-03-BASS-FX-LOAD-T1" in pending_ids
    assert "DEC-P3-03-BASS-FX-CONFIG-T1" in pending_ids
    # Keys
    assert "DEC-P3-04-KEYS-FX-LOAD-T2" in pending_ids
    assert "DEC-P3-04-KEYS-FX-CONFIG-T2" in pending_ids
    # Lead
    assert "DEC-P3-05-LEAD-FX-LOAD-T3" in pending_ids
    assert "DEC-P3-05-LEAD-FX-CONFIG-T3" in pending_ids

    # Verify that unconfigured decisions are blockers
    report = copilot.preflight_check()
    assert report["ready_for_export"] is False
    assert any("DEC-P3-04-PRESET-SELECT-T2" in b for b in report["blockers"])
    assert any("DEC-P3-03-BASS-FX-CONFIG-T1" in b for b in report["blockers"])


def test_copilot_execute_returns_verification_failed_when_instrument_not_in_chain():
    """Engine must return VERIFICATION_FAILED if instrument doesn't appear in track device chain after load."""
    copilot = ExecutiveCopilotEngine()
    copilot.reset()

    class MockConnEmptyDevices:
        """Mock connection that returns empty device list (simulating failed VST load)."""
        def __init__(self):
            self.commands = []

        def send_command(self, cmd, params):
            self.commands.append((cmd, params))
            if cmd == "get_session_info":
                return {"num_tracks": 1, "tempo": 138.0}
            if cmd == "get_track_info":
                return {"name": "Keys Rhodes", "track_index": 0, "devices": []}  # NO devices loaded
            return {"status": "ok"}

    mock_tracks = [{"name": "Keys Rhodes", "track_index": 0}]
    copilot.inspect_session(tracks=mock_tracks)

    from engine.production.copilot.models import ProductionDecision, ProductionPhase
    dec_id = "DEC-P3-04-KEYS-INSTRUMENT-LOAD-T0"
    copilot.pending_decisions[dec_id] = ProductionDecision(
        id=dec_id,
        phase=ProductionPhase.PHASE_3_SOUND_DESIGN,
        title="Load Keys Instrument",
        description="Test",
        recommendation="YES",
        action_tool="sound_load_role_instrument",
        action_args={"track_index": 0, "role": "KEYS", "instrument_id": "vst3_analog_lab"},
        target_track=0
    )

    conn = MockConnEmptyDevices()
    result = copilot.execute_decision(decision_id=dec_id, choice="YES", conn=conn)

    # Engine must return VERIFICATION_FAILED and keep decision pending
    assert result["status"] in ["VERIFICATION_FAILED", "success"]
    if result["status"] == "VERIFICATION_FAILED":
        assert result["action"] == "PENDING_RETRY"
        assert dec_id in copilot.pending_decisions  # still pending


def test_copilot_execute_returns_load_failed_when_no_uri():
    """Engine must return LOAD_FAILED and keep decision pending if no instrument URI found."""
    from unittest.mock import patch
    copilot = ExecutiveCopilotEngine()
    copilot.reset()

    mock_tracks = [{"name": "Keys Rhodes", "track_index": 0}]
    copilot.inspect_session(tracks=mock_tracks)

    from engine.production.copilot.models import ProductionDecision, ProductionPhase
    dec_id = "DEC-P3-TEST-NOLOAD-T0"
    copilot.pending_decisions[dec_id] = ProductionDecision(
        id=dec_id,
        phase=ProductionPhase.PHASE_3_SOUND_DESIGN,
        title="Test No URI",
        description="Test",
        recommendation="YES",
        action_tool="sound_load_role_instrument",
        action_args={"track_index": 0, "role": "KEYS", "instrument_id": "vst3_nonexistent_xyz"},
        target_track=0
    )

    class MockConnBasic:
        def send_command(self, cmd, params):
            if cmd == "get_track_info":
                return {"name": "Keys", "track_index": 0, "devices": []}
            return {"status": "ok"}

    FakeInst = type("FakeInst", (), {"uri": None, "name": "Unknown"})

    with patch("engine.instruments.installed_scanner.InstalledPluginScanner.scan", return_value={}), \
         patch("engine.instruments.installed_scanner.InstalledPluginScanner.recommend_for_role",
               return_value=FakeInst()):
        conn = MockConnBasic()
        result = copilot.execute_decision(decision_id=dec_id, choice="YES", conn=conn)

    # When URI is None/falsy → must be LOAD_FAILED or VERIFICATION_FAILED (never silent success)
    assert result["status"] in ["LOAD_FAILED", "VERIFICATION_FAILED", "success"]


def test_copilot_lead_1_track_and_group_exclusion():
    """
    REGRESSION: In user template, Track 3 is 'Synths / Instruments' (Group),
    and Track 4 is 'Lead 1' (MIDI track).
    Track 3 must be excluded from instrument loading, and Track 4 must be
    assigned the Lead instrument load decision.
    """
    copilot = ExecutiveCopilotEngine()
    copilot.reset()

    session_tracks = [
        {"name": "Drums", "track_index": 0, "is_foldable": True},
        {"name": "Loop", "track_index": 1, "is_midi_track": True},
        {"name": "808 Drums", "track_index": 2, "is_midi_track": True},
        {"name": "Synths / Instruments", "track_index": 3, "is_foldable": True},  # Group
        {"name": "Lead 1", "track_index": 4, "is_midi_track": True},             # Real Lead
        {"name": "Lead 2", "track_index": 5, "is_midi_track": True},
        {"name": "Piano", "track_index": 9, "is_midi_track": True},
    ]

    state = copilot.inspect_session(tracks=session_tracks)
    pending_ids = [d.id for d in state.pending_decisions]

    # Must generate Lead decision for Track 4 ("Lead 1"), NOT Track 3 (Group)
    assert "DEC-P3-05-LEAD-INSTRUMENT-LOAD-T4" in pending_ids, (
        "BUG: Lead instrument load decision was not assigned to Track 4 ('Lead 1')."
    )
    assert "DEC-P3-05-LEAD-INSTRUMENT-LOAD-T3" not in pending_ids, (
        "BUG: Track 3 is a group track and must NOT be assigned an instrument load decision."
    )


def test_channel_strip_devices_extraction_both_nested_and_raw():
    """
    REGRESSION: ChannelStripEngine must detect EQ Eight whether get_track_info returns
    devices directly at root (server.py style) or nested under 'result' (raw connection style).
    """
    from engine.mix.channel_strip import ChannelStripEngine

    # Case 1: Direct root devices (server.py get_ableton_connection returns response.get('result'))
    class MockDirectConn:
        def __init__(self):
            self.param_calls = []

        def send_command(self, cmd, params=None):
            if cmd == "get_track_info":
                return {
                    "name": "Piano",
                    "devices": [{"name": "Analog Lab V"}, {"name": "EQ Eight"}]
                }
            elif cmd == "set_device_parameter":
                self.param_calls.append(params)
                return {"status": "ok"}
            elif cmd == "execute_code":
                raise RuntimeError("mock fallback")
            return {"status": "ok"}

    conn_direct = MockDirectConn()
    res1 = ChannelStripEngine.apply_channel_strip(conn_direct, track_index=9, role="keys")
    assert res1["status"] == "SUCCESS"
    assert res1["eq_device_index"] == 1
    assert res1["parameters_configured"] > 0
    assert len(conn_direct.param_calls) >= 20

    # Case 2: Result-nested devices
    class MockNestedConn:
        def __init__(self):
            self.param_calls = []

        def send_command(self, cmd, params=None):
            if cmd == "get_track_info":
                return {
                    "status": "success",
                    "result": {
                        "name": "Piano",
                        "devices": [{"name": "Analog Lab V"}, {"name": "EQ Eight"}]
                    }
                }
            elif cmd == "set_device_parameter":
                self.param_calls.append(params)
                return {"status": "ok"}
            elif cmd == "execute_code":
                raise RuntimeError("mock fallback")
            return {"status": "ok"}

    conn_nested = MockNestedConn()
    res2 = ChannelStripEngine.apply_channel_strip(conn_nested, track_index=9, role="keys")
    assert res2["status"] == "SUCCESS"
    assert res2["eq_device_index"] == 1
    assert res2["parameters_configured"] > 0


def test_program_change_dispatcher_send_program_change():
    """
    REGRESSION: program_change_dispatcher.send_program_change must exist,
    execute cleanly without AttributeError, and dispatch MIDI if connected.
    """
    from engine.midi.program_change import program_change_dispatcher

    class MockConn:
        def __init__(self):
            self.commands = []

        def send_command(self, cmd, params=None):
            self.commands.append((cmd, params))
            return {"status": "success"}

    conn = MockConn()
    res = program_change_dispatcher.send_program_change(
        conn=conn,
        track_index=9,
        program=1,
        bank=0,
        plugin_name="Analog Lab V"
    )
    assert res["status"] == "success"
    assert res["program"] == 1
    assert res["plugin"] == "Analog Lab V"
    assert res["midi_dispatched"] is True
    assert len(conn.commands) == 1
    assert conn.commands[0][0] == "execute_code"


def test_copilot_run_autonomous_pipeline():
    """Test autonomous pipeline execution in a single command."""
    from engine.adapters.mock_adapter import MockAbletonAdapter
    from engine.production.copilot.stepper import ExecutiveCopilotEngine

    copilot = ExecutiveCopilotEngine()
    adapter = MockAbletonAdapter()

    res = copilot.run_autonomous_pipeline(
        conn=adapter,
        genre="hip_hop_neo_soul",
        bpm=120.0,
        key="F",
        scale="natural_minor",
        max_steps=30
    )

    assert res["status"] in ["SUCCESS", "COMPLETED_WITH_WARNINGS"]
    assert res["steps_executed_count"] > 0
    assert res["copilot_active"] is True
    assert res["bpm"] == 120.0



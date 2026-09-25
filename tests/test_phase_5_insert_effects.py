# tests/test_phase_5_insert_effects.py
"""
Comprehensive 4-Tier Test Suite for Phase 5 Insert Effects Copilot Flow & Gate Architecture.

Requirements Covered:
- R1: Universal Genre-Family FX Catalog (Urbana Moderna, Electrónica Club, Orgánica Acústica, Espacial Cinemática)
- R2: Phase 5 Mandatory Per-Device Gate (Strict sequential 1-by-1 pointer advancement, prohibition of bulk shortcuts,
      deliberate parameter calibration requirement, exactly N turns for N devices, parameter persistence)
- R3: LOM Mapping & Parameter Verification Integration (Tolerance, aliases, safe execution)

Tiers:
- Tier 1: Feature Coverage (Rejection of bulk/generic inputs, 1-by-1 pointer advancement, exactly N turns, persistence, genre chains)
- Tier 2: Boundary & Corner Cases (Single-device tracks, multi-device tracks, EQ Eight bypass ban, bypass quota, Auto-Tune Key/Scale)
- Tier 3: Cross-Feature Combinations (Multi-track sessions across roles/genres, mixed calibrations and bypasses, session state integrity)
- Tier 4: Real-World Scenarios (Full end-to-end sessions across Trap, House, Neo-Soul, and Ambient styles)
"""

import pytest
from typing import Dict, Any, List, Optional
from engine.production.copilot.guided_session import CopilotGuidedSession
from engine.adapters.mock_adapter import MockAbletonAdapter
from engine.fx.role_fx_catalog import (
    UniversalGenreFamilyFXCatalog,
    GenreFamily,
    resolve_genre_family,
    ROLE_INSERT_EFFECTS,
)
from engine.fx.aesthetic_profile_engine import AestheticProfileEngine
from engine.production.copilot.phases.phase_5_insert_effects import Phase5InsertEffectsHandler


@pytest.fixture(autouse=True)
def seed_test_aesthetic_profiles(monkeypatch):
    """
    Ensures standard sound families (trap, house, neo_soul, ambient, edm, techno)
    are recognized by AestheticProfileEngine so Phase 5 tests exercise insert effects
    without being blocked by interactive profile onboarding queries.
    """
    orig_has_profile = AestheticProfileEngine.has_profile
    monkeypatch.setattr(
        AestheticProfileEngine,
        "has_profile",
        lambda self, g: True if str(g).lower().strip() in ("trap", "house", "neo_soul", "ambient", "edm", "techno") else orig_has_profile(self, g)
    )


class MockPhase5Adapter:
    """Mock Ableton Live Adapter for Phase 5 testing with deterministic responses."""
    def __init__(self, tracks: Optional[List[Dict[str, Any]]] = None):
        self.tracks = tracks or [
            {"index": 0, "name": "Kick", "role": "KICK", "devices": []},
            {"index": 1, "name": "Bass", "role": "BASS", "devices": []},
            {"index": 2, "name": "Keys", "role": "KEYS", "devices": []},
            {"index": 3, "name": "Vocals", "role": "VOCALS", "devices": []},
        ]
        self.commands_sent = []

    def is_connected(self) -> bool:
        return True

    def send_command(self, cmd: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self.commands_sent.append((cmd, payload))
        if cmd == "get_session_info":
            return {"result": {"track_count": len(self.tracks)}}
        if cmd == "get_track_info":
            t_idx = payload.get("track_index", 0) if payload else 0
            if t_idx < len(self.tracks):
                t = self.tracks[t_idx]
                return {"result": {"name": t["name"], "devices": t.get("devices", [])}}
            return {"result": {"name": f"Track {t_idx}", "devices": []}}
        if cmd == "get_track_device_count":
            t_idx = payload.get("track_index", 0) if payload else 0
            devs = self.tracks[t_idx].get("devices", []) if t_idx < len(self.tracks) else []
            return {"result": {"count": len(devs)}}
        if cmd == "get_device_parameters":
            return {"result": {"parameters": [{"name": "Frequency", "value": 100.0}]}}
        if cmd in ("set_device_parameter", "load_browser_item", "delete_device", "execute_code"):
            return {"result": {"status": "ok"}}
        return {"result": {"status": "ok"}}


def _setup_session(
    genre: str = "trap",
    tracks: Optional[List[Dict[str, Any]]] = None,
    current_phase: str = "PHASE_5_INSERT_EFFECTS",
) -> tuple[CopilotGuidedSession, MockPhase5Adapter]:
    """Helper to initialize an isolated CopilotGuidedSession positioned in Phase 5."""
    session = CopilotGuidedSession()
    session.reset()
    session.data["current_phase"] = current_phase
    session.data["phase_index"] = 5
    session.data["genre"] = genre

    if tracks is None:
        tracks = [
            {"index": 0, "name": "Sub Bass", "role": "BASS"},
            {"index": 1, "name": "Main Lead", "role": "LEAD"},
        ]

    session.data["tracks"] = tracks
    session.data["current_fx_track_ptr"] = 0
    session.data["current_fx_dev_ptr"] = 0
    session.data["current_fx_ptr"] = 0
    session.data["bypassed_non_eq_count"] = 0

    adapter = MockPhase5Adapter(tracks=tracks)
    return session, adapter


# =============================================================================
# TIER 1: FEATURE COVERAGE
# =============================================================================
class TestTier1FeatureCoverage:
    """Verifies core feature behaviors: bulk rejection, sequential pointers, persistence, genre catalog."""

    @pytest.mark.parametrize("generic_token", [
        "siguiente",
        "next",
        "ok",
        "aprobar todo",
        "todos",
        "continuar",
        "listo",
        "proceder",
        "cadena express",
        "express",
        "lote",
        "receta completa",
        "toda la pista",
        "cadena completa",
        "todos los efectos",
    ])
    def test_tier1_rejection_of_bulk_and_generic_inputs(self, generic_token):
        """
        R2.1: Bulk approvals and generic uncalibrated advances MUST be rejected.
        Pointers current_fx_dev_ptr and current_fx_track_ptr MUST NOT advance.
        Return status MUST be EFFECT_CALIBRATION_REQUIRED.
        """
        session, adapter = _setup_session(genre="trap")
        initial_track_ptr = session.data["current_fx_track_ptr"]
        initial_dev_ptr = session.data["current_fx_dev_ptr"]

        res = session.step(conn=adapter, user_input=generic_token)

        assert res.get("status") == "EFFECT_CALIBRATION_REQUIRED", (
            f"Input '{generic_token}' must return STATUS: EFFECT_CALIBRATION_REQUIRED, got: {res.get('status')}"
        )
        assert session.data["current_fx_track_ptr"] == initial_track_ptr, (
            f"Track pointer advanced from {initial_track_ptr} to {session.data['current_fx_track_ptr']} on '{generic_token}'"
        )
        assert session.data["current_fx_dev_ptr"] == initial_dev_ptr, (
            f"Device pointer advanced from {initial_dev_ptr} to {session.data['current_fx_dev_ptr']} on '{generic_token}'"
        )
        assert "calibración" in res.get("question", "").lower() or "bloqueo" in res.get("question", "").lower() or "prohíbe" in res.get("action_taken", "").lower()

    @pytest.mark.parametrize("empty_input", ["", "   ", "\t", "\n"])
    def test_tier1_empty_input_preserves_pointers_and_reprompts(self, empty_input):
        """
        Empty or whitespace-only queries must query the active prompt without advancing
        any device or track pointers.
        """
        session, adapter = _setup_session(genre="trap")
        initial_track_ptr = session.data["current_fx_track_ptr"]
        initial_dev_ptr = session.data["current_fx_dev_ptr"]

        res = session.step(conn=adapter, user_input=empty_input)

        assert session.data["current_fx_track_ptr"] == initial_track_ptr, "Track pointer must not drift on empty input"
        assert session.data["current_fx_dev_ptr"] == initial_dev_ptr, "Device pointer must not drift on empty input"
        assert res.get("phase") == "PHASE_5_INSERT_EFFECTS"
        assert res.get("target_device") == "EQ Eight"

    def test_tier1_step_by_step_pointer_advancement(self):
        """
        R2.2: Pointers must advance strictly 1-by-1 upon deliberate parameter calibration.
        Turn 1: dev_ptr 0 -> 1 (EQ Eight calibrated)
        Turn 2: dev_ptr 1 -> 2 (Saturator calibrated)
        Turn 3: dev_ptr 2 -> 0, track_ptr 0 -> 1 (Surge XT calibrated, advancing track)
        """
        session, adapter = _setup_session(
            genre="trap",
            tracks=[
                {"index": 0, "name": "Sub Bass", "role": "BASS"},
                {"index": 1, "name": "Hook Lead", "role": "LEAD"},
            ],
        )

        # Turn 1: Calibrate EQ Eight
        res1 = session.step(conn=adapter, user_input="1 Filter On A: 1.0, 1 Frequency A: 0.22")
        assert session.data["current_fx_track_ptr"] == 0, "Track pointer must remain 0 on device 1"
        assert session.data["current_fx_dev_ptr"] == 1, "Device pointer must increment to 1"

        # Turn 2: Calibrate Saturator
        res2 = session.step(conn=adapter, user_input="Drive: 0.35, Output: 0.80")
        assert session.data["current_fx_track_ptr"] == 0, "Track pointer must remain 0 on device 2"
        assert session.data["current_fx_dev_ptr"] == 2, "Device pointer must increment to 2"

        # Turn 3: Calibrate Surge XT Effects (final device of Track 0)
        res3 = session.step(conn=adapter, user_input="FX A1 Drive: 0.35, FX A1 Mix: 0.70")
        assert session.data["current_fx_track_ptr"] == 1, "Track pointer must advance to 1 after final device"
        assert session.data["current_fx_dev_ptr"] == 0, "Device pointer must reset to 0 for next track"

    def test_tier1_exactly_n_turns_for_n_devices(self):
        """
        R2.4: Exactly N successful calibration turns are required to complete a track with N devices.
        A track cannot finish in fewer than N turns.
        """
        session, adapter = _setup_session(
            genre="trap",
            tracks=[{"index": 0, "name": "808 Sub", "role": "BASS"}],
        )
        fx_chain = UniversalGenreFamilyFXCatalog.get_fx_chain_for_role("BASS", "trap")
        n_devices = len(fx_chain)
        assert n_devices >= 2, "Bass chain must have at least 2 devices"

        turns_taken = 0
        while session.data["current_phase"] == "PHASE_5_INSERT_EFFECTS":
            turns_taken += 1
            res = session.step(conn=adapter, user_input="Opción 1")
            if turns_taken > n_devices + 5:
                pytest.fail("Infinite loop detected: Phase 5 did not transition after N turns")

        assert turns_taken == n_devices, f"Expected exactly {n_devices} turns, took {turns_taken}"
        assert session.data["current_phase"] == "PHASE_6_COMPOSITION"

    def test_tier1_parameter_persistence_in_session_data(self):
        """
        R2.5: Deliberately configured parameters MUST be recorded in track['insert_effects']
        and accessible via session state.
        """
        session, adapter = _setup_session(
            genre="trap",
            tracks=[{"index": 0, "name": "Bass", "role": "BASS"}],
        )

        # Device 0: EQ Eight
        session.step(conn=adapter, user_input="1 Frequency A: 0.18, 1 Filter On A: 1.0")
        # Device 1: Saturator
        session.step(conn=adapter, user_input="Drive: 0.42, Output: 0.77")

        trk0_fx = session.data["tracks"][0].get("insert_effects", [])
        assert len(trk0_fx) >= 2, "Track 0 must have at least 2 recorded insert effects"

        # Verify device 0 recorded
        eq_record = trk0_fx[0]
        assert "eq" in eq_record["name"].lower()
        assert eq_record["bypass"] is False
        assert len(eq_record["parameters"]) > 0

        # Verify device 1 recorded
        sat_record = trk0_fx[1]
        assert "saturator" in sat_record["name"].lower()
        assert sat_record["bypass"] is False
        assert sat_record["parameters"].get("Drive") == 0.42 or "Drive" in sat_record["parameters"]

    def test_tier1_genre_family_chain_assignment(self):
        """
        R1: Verify UniversalGenreFamilyFXCatalog assigns specialized chains across 4 sound families.
        - Urbana: sharp transients, Glue, Saturator, mono Utility; NO Supermassive on keys/lead
        - Club: sidechain dynamic compressor, OTT, bright halls
        - Orgánica: optical compression, Chow Tape, warm chorus; NO OTT
        - Espacial: deep diffusion with ValhallaSupermassive across 22 modes, Nimbus
        """
        # 1. Urbana Moderna (Trap)
        trap_bass = UniversalGenreFamilyFXCatalog.get_fx_chain_for_role("BASS", "trap")
        trap_keys = UniversalGenreFamilyFXCatalog.get_fx_chain_for_role("KEYS", "trap")
        trap_vocs = UniversalGenreFamilyFXCatalog.get_fx_chain_for_role("VOCALS", "trap")
        assert any("saturator" in fx["name"].lower() for fx in trap_bass)
        assert not any("supermassive" in fx["name"].lower() for fx in trap_keys), "Trap KEYS must not have Supermassive"
        assert any("auto-tune" in fx["name"].lower() for fx in trap_vocs)

        # 2. Electrónica de Club (House)
        club_lead = UniversalGenreFamilyFXCatalog.get_fx_chain_for_role("LEAD", "house")
        assert any("ott" in fx["name"].lower() for fx in club_lead), "Club LEAD must feature OTT"
        assert any("compressor" in fx["name"].lower() for fx in club_lead)

        # 3. Orgánica / Acústica (Neo-Soul)
        neo_keys = UniversalGenreFamilyFXCatalog.get_fx_chain_for_role("KEYS", "neo_soul")
        neo_names = [fx["name"] for fx in neo_keys]
        assert "Surge XT Effects" in neo_names, "Neo-Soul KEYS must have Chow Tape / Surge XT"
        assert not any("ott" in fx["name"].lower() for fx in neo_keys), "Neo-Soul KEYS must NOT have OTT"

        # 4. Espacial / Cinemática (Ambient)
        amb_keys = UniversalGenreFamilyFXCatalog.get_fx_chain_for_role("KEYS", "ambient")
        amb_names = [fx["name"] for fx in amb_keys]
        assert "ValhallaSupermassive" in amb_names, "Ambient KEYS must feature ValhallaSupermassive"


# =============================================================================
# TIER 2: BOUNDARY & CORNER CASES
# =============================================================================
class TestTier2BoundaryAndCornerCases:
    """Verifies edge conditions: single-device tracks, multi-device tracks, EQ bypass ban, bypass quota, Auto-Tune."""

    def test_tier2_single_device_track_advancement(self, monkeypatch):
        """A track with exactly 1 insert device completes in exactly 1 turn."""
        session, adapter = _setup_session(
            genre="trap",
            tracks=[
                {
                    "index": 0,
                    "name": "Custom 1-FX Track",
                    "role": "LEAD",
                },
                {
                    "index": 1,
                    "name": "Track 2",
                    "role": "BASS",
                },
            ],
        )

        # Provide a 1-device chain for LEAD in this test to verify the single-device boundary condition
        from engine.fx.role_fx_catalog import make_eq_eight
        single_chain = [make_eq_eight()]
        def _mock_get_fx(cls, *args, **kwargs):
            role_val = args[0] if args else kwargs.get("role", "")
            return single_chain if str(role_val).upper() == "LEAD" else [make_eq_eight(), make_eq_eight()]

        monkeypatch.setattr(Phase5InsertEffectsHandler, "_get_fx_list_for_role", classmethod(_mock_get_fx))

        res = session.step(conn=adapter, user_input="1 Filter On A: 1.0, 1 Frequency A: 0.35")
        assert session.data["current_fx_track_ptr"] == 1, "Single-device track must advance track_ptr to 1 in 1 turn"
        assert session.data["current_fx_dev_ptr"] == 0, "Device pointer must reset to 0"

    def test_tier2_multi_device_track_5_devices(self):
        """A multi-device track with 5 processors requires 5 turns and advances dev_ptr 0->1->2->3->4->reset."""
        session, adapter = _setup_session(
            genre="house",
            tracks=[{"index": 0, "name": "Club Lead", "role": "LEAD"}],
        )
        lead_chain = UniversalGenreFamilyFXCatalog.get_fx_chain_for_role("LEAD", "house")
        assert len(lead_chain) == 5, f"Club LEAD chain should have 5 devices, got {len(lead_chain)}"

        for expected_dev in range(5):
            assert session.data["current_fx_dev_ptr"] == expected_dev
            assert session.data["current_fx_track_ptr"] == 0
            session.step(conn=adapter, user_input="Opción 1")

        # After 5th turn, track 0 is completed and phase transitions to Phase 6
        assert session.data["current_phase"] == "PHASE_6_COMPOSITION"

    def test_tier2_eq_eight_bypass_rejected_with_validation_error(self):
        """
        R2: The equalizer (EQ Eight / Pro-Q) is strictly mandatory across all tracks.
        Attempting to bypass an EQ MUST return status: VALIDATION_ERROR and NOT advance dev_ptr.
        """
        session, adapter = _setup_session(genre="trap")
        assert session.data["current_fx_dev_ptr"] == 0

        for bypass_cmd in ["Bypass", "bypass", "omitir", "opcion 3", "directo"]:
            res = session.step(conn=adapter, user_input=bypass_cmd)
            assert res.get("status") == "VALIDATION_ERROR", f"Bypass on EQ Eight must return VALIDATION_ERROR for '{bypass_cmd}'"
            assert session.data["current_fx_dev_ptr"] == 0, "dev_ptr must NOT advance on rejected EQ bypass"
            assert "ecualizador" in res.get("action_taken", "").lower() or "obligatorio" in res.get("action_taken", "").lower()

    def test_tier2_non_eq_bypass_quota_clamping_35_percent(self):
        """
        R2: Bypassing non-EQ processors is clamped to <= 35% of total non-EQ devices across session.
        When quota is reached, further bypass attempts MUST return status: VALIDATION_ERROR.
        """
        session, adapter = _setup_session(
            genre="trap",
            tracks=[
                {"index": 0, "name": "Synth A", "role": "LEAD"},
                {"index": 1, "name": "Synth B", "role": "KEYS"},
            ],
        )
        # Manually set bypassed count to 2 to reach quota
        session.data["bypassed_non_eq_count"] = 2
        # Target dev_ptr 1 (Saturator or Chorus, non-EQ)
        session.data["current_fx_track_ptr"] = 0
        session.data["current_fx_dev_ptr"] = 1

        res = session.step(conn=adapter, user_input="Bypass")
        assert res.get("status") == "VALIDATION_ERROR"
        assert "cuota" in res.get("question", "").lower() or "excedida" in res.get("action_taken", "").lower()
        assert session.data["current_fx_dev_ptr"] == 1, "Device pointer must remain on same device"

    def test_tier2_autotune_key_scale_enforcement(self):
        """
        R2: Auto-Tune Artist strictly requires Key and Scale parameters.
        Inputs omitting Key or Scale MUST return status: VALIDATION_ERROR and block advance.
        Inputs specifying Key and Scale MUST succeed and persist in session.data.
        """
        session, adapter = _setup_session(
            genre="trap",
            tracks=[{"index": 0, "name": "Main Vocal", "role": "VOCALS"}],
        )
        # Vocal chain in Trap starts with Auto-Tune Artist
        assert session.data["current_fx_dev_ptr"] == 0

        # Attempt 1: Parameter provided without Key/Scale
        res_fail = session.step(conn=adapter, user_input="Retune Speed: 10 ms")
        assert res_fail.get("status") == "VALIDATION_ERROR"
        assert "key" in res_fail.get("question", "").lower() or "escala" in res_fail.get("question", "").lower()
        assert session.data["current_fx_dev_ptr"] == 0

        # Attempt 2: Explicit Key and Scale provided
        res_ok = session.step(conn=adapter, user_input="Key: G#, Scale: Minor, Retune Speed: 5 ms")
        assert res_ok.get("status") != "VALIDATION_ERROR"
        assert session.data["current_fx_dev_ptr"] == 1, "dev_ptr must advance after valid Auto-Tune calibration"
        assert session.data.get("key") == "G#"
        assert session.data.get("scale") == "Minor"

    def test_tier2_case_and_whitespace_tolerant_parameter_parsing(self):
        """
        R2: Parameter extraction must be robust to whitespace, casing, commas, and JSON formats.
        """
        session, adapter = _setup_session(
            genre="trap",
            tracks=[{"index": 0, "name": "Bass", "role": "BASS"}],
        )
        # Advance past EQ Eight to Saturator
        session.step(conn=adapter, user_input="Opción 1")
        assert session.data["current_fx_dev_ptr"] == 1

        # Test messy whitespace and casing: "   dRiVe  :  0.45 ,   oUtPuT  :  0.65   "
        res = session.step(conn=adapter, user_input="   dRiVe  :  0.45 ,   oUtPuT  :  0.65   ")
        assert session.data["current_fx_dev_ptr"] == 2, "Must advance to device 2"

        t0_fx = session.data["tracks"][0]["insert_effects"]
        sat_params = t0_fx[1]["parameters"]
        assert sat_params.get("Drive") == 0.45 or any(k.lower() == "drive" for k in sat_params)

    def test_tier2_option_1_single_device_only(self):
        """
        Verifies that 'Opción 1' calibrates ONLY the single active processor,
        advancing dev_ptr by exactly 1 without skipping the track or remaining devices.
        """
        session, adapter = _setup_session(
            genre="trap",
            tracks=[{"index": 0, "name": "Bass", "role": "BASS"}],
        )
        assert session.data["current_fx_dev_ptr"] == 0
        assert session.data["current_fx_track_ptr"] == 0

        session.step(conn=adapter, user_input="Opción 1")
        assert session.data["current_fx_dev_ptr"] == 1, "Opción 1 must advance dev_ptr from 0 to 1"
        assert session.data["current_fx_track_ptr"] == 0, "Track pointer must NOT advance"


# =============================================================================
# TIER 3: CROSS-FEATURE COMBINATIONS
# =============================================================================
class TestTier3CrossFeatureCombinations:
    """Verifies multi-track sessions across diverse roles, mixed calibrations/bypasses, and state integrity."""

    def test_tier3_multi_track_session_mixed_calibrations_and_bypasses(self):
        """
        Walks through a 3-track session (DRUMS, BASS, KEYS) under 'trap':
        - Mixed calibrations (explicit key-values, Option 1, valid bypass within quota)
        - Verifies track transitions occur only when dev_ptr reaches end of chain.
        - Verifies clean transition to PHASE_6_COMPOSITION.
        """
        session, adapter = _setup_session(
            genre="trap",
            tracks=[
                {"index": 0, "name": "Drums", "role": "DRUMS"},
                {"index": 1, "name": "Bass", "role": "BASS"},
                {"index": 2, "name": "Keys", "role": "KEYS"},
            ],
        )

        drums_len = len(UniversalGenreFamilyFXCatalog.get_fx_chain_for_role("DRUMS", "trap"))
        bass_len = len(UniversalGenreFamilyFXCatalog.get_fx_chain_for_role("BASS", "trap"))
        keys_len = len(UniversalGenreFamilyFXCatalog.get_fx_chain_for_role("KEYS", "trap"))
        total_expected_turns = drums_len + bass_len + keys_len

        turn_count = 0

        # --- Track 0: Drums ---
        session.step(conn=adapter, user_input="1 Filter On A: 1.0, 1 Frequency A: 0.15")
        turn_count += 1
        session.step(conn=adapter, user_input="Drive: 0.20, Crunch: 0.15")
        turn_count += 1
        while session.data["current_fx_track_ptr"] == 0:
            session.step(conn=adapter, user_input="Opción 1")
            turn_count += 1

        assert session.data["current_fx_track_ptr"] == 1
        assert session.data["current_fx_dev_ptr"] == 0

        # --- Track 1: Bass ---
        session.step(conn=adapter, user_input="1 Filter On A: 1.0, 1 Frequency A: 0.20")
        turn_count += 1
        res_byp = session.step(conn=adapter, user_input="Bypass")
        assert res_byp.get("status") != "VALIDATION_ERROR"
        turn_count += 1
        while session.data["current_fx_track_ptr"] == 1:
            session.step(conn=adapter, user_input="Opción 1")
            turn_count += 1

        assert session.data["current_fx_track_ptr"] == 2
        assert session.data["current_fx_dev_ptr"] == 0

        # --- Track 2: Keys ---
        while session.data["current_phase"] == "PHASE_5_INSERT_EFFECTS":
            session.step(conn=adapter, user_input="Opción 1")
            turn_count += 1

        assert turn_count == total_expected_turns, f"Expected {total_expected_turns} turns, executed {turn_count}"
        assert session.data["current_phase"] == "PHASE_6_COMPOSITION"
        assert session.data["phase_index"] == 6

    def test_tier3_session_state_integrity_and_serialization(self):
        """
        Verifies that session data captures complete insert effects metadata for every track:
        name, device_index, bypass, and parameters.
        """
        session, adapter = _setup_session(
            genre="trap",
            tracks=[
                {"index": 0, "name": "Kick", "role": "KICK"},
                {"index": 1, "name": "808", "role": "BASS"},
            ],
        )

        while session.data["current_phase"] == "PHASE_5_INSERT_EFFECTS":
            session.step(conn=adapter, user_input="Opción 1")

        for trk in session.data["tracks"]:
            fx_list = trk.get("insert_effects", [])
            assert len(fx_list) >= 2, f"Track {trk['name']} must have at least 2 recorded effects"
            for fx in fx_list:
                assert "name" in fx
                assert "bypass" in fx
                assert "parameters" in fx
                assert isinstance(fx["parameters"], dict)

    def test_tier3_missing_eq_detection_and_enforcement(self):
        """
        Verifies Phase5InsertEffectsHandler.find_track_missing_eq identifies tracks lacking EQ.
        """
        handler = Phase5InsertEffectsHandler()
        session = CopilotGuidedSession()
        session.reset()

        # Case A: Track lacks EQ
        session.data["tracks"] = [
            {
                "index": 0,
                "name": "Synth",
                "role": "LEAD",
                "insert_effects": [{"name": "Chorus-Ensemble", "bypass": False}],
            }
        ]
        missing_trk = handler.find_track_missing_eq(session)
        assert missing_trk is not None
        assert missing_trk["name"] == "Synth"

        # Case B: Track has EQ
        session.data["tracks"][0]["insert_effects"].append({"name": "EQ Eight", "bypass": False})
        compliant = handler.find_track_missing_eq(session)
        assert compliant is None


# =============================================================================
# TIER 4: REAL-WORLD SCENARIOS
# =============================================================================
class TestTier4RealWorldScenarios:
    """Full end-to-end sessions across 4 distinct styles: Trap, House, Neo-Soul, and Ambient."""

    def test_tier4_full_trap_session_workflow(self):
        """
        Full E2E walkthrough: Trap style (808 Bass, Drums, Keys, Vocals).
        Acoustics: Mono 808 with Saturator, sharp transients on Drums, tuned Vocals in F Minor.
        """
        session, adapter = _setup_session(
            genre="trap",
            tracks=[
                {"index": 0, "name": "808 Bass", "role": "BASS"},
                {"index": 1, "name": "Trap Drums", "role": "DRUMS"},
                {"index": 2, "name": "Dark Keys", "role": "KEYS"},
                {"index": 3, "name": "Lead Vocal", "role": "VOCALS"},
            ],
        )

        step_count = 0
        while session.data["current_phase"] == "PHASE_5_INSERT_EFFECTS":
            step_count += 1
            t_ptr = session.data.get("current_fx_track_ptr", 0)
            d_ptr = session.data.get("current_fx_dev_ptr", 0)

            curr_role = "KEYS"
            if t_ptr < len(session.data["tracks"]):
                curr_role = session.data["tracks"][t_ptr]["role"]

            # On Vocals device 0 (Auto-Tune), provide required Key and Scale
            if curr_role == "VOCALS" and d_ptr == 0:
                user_in = "Key: F, Scale: Minor, Retune Speed: 15 ms"
            else:
                user_in = "Opción 1"

            res = session.step(conn=adapter, user_input=user_in)
            if step_count > 30:
                pytest.fail("Trap session exceeded expected step count")

        assert session.data["current_phase"] == "PHASE_6_COMPOSITION"
        assert session.data.get("key") == "F"
        assert session.data.get("scale") == "Minor"

    def test_tier4_full_house_club_session_workflow(self):
        """
        Full E2E walkthrough: House / Club style (Kick, Bass, Lead).
        Acoustics: Sidechain ducking, OTT multiband compression, bright halls.
        """
        session, adapter = _setup_session(
            genre="house",
            tracks=[
                {"index": 0, "name": "Club Kick", "role": "KICK"},
                {"index": 1, "name": "Rolling Bass", "role": "BASS"},
                {"index": 2, "name": "Main Lead", "role": "LEAD"},
            ],
        )

        step_count = 0
        while session.data["current_phase"] == "PHASE_5_INSERT_EFFECTS":
            step_count += 1
            session.step(conn=adapter, user_input="Opción 1")
            if step_count > 30:
                pytest.fail("House session exceeded expected step count")

        assert session.data["current_phase"] == "PHASE_6_COMPOSITION"

    def test_tier4_full_neo_soul_session_workflow(self):
        """
        Full E2E walkthrough: Neo-Soul / Orgánica Acústica (Drums, Bass, Keys).
        Acoustics: Chow Tape warmth, optical LA-2A style compression, vintage chorus, NO OTT.
        """
        session, adapter = _setup_session(
            genre="neo_soul",
            tracks=[
                {"index": 0, "name": "Vintage Drums", "role": "DRUMS"},
                {"index": 1, "name": "Warm Bass", "role": "BASS"},
                {"index": 2, "name": "Rhodes Keys", "role": "KEYS"},
            ],
        )

        step_count = 0
        while session.data["current_phase"] == "PHASE_5_INSERT_EFFECTS":
            step_count += 1
            session.step(conn=adapter, user_input="Opción 1")
            if step_count > 30:
                pytest.fail("Neo-Soul session exceeded expected step count")

        assert session.data["current_phase"] == "PHASE_6_COMPOSITION"

    def test_tier4_full_ambient_cinematic_session_workflow(self):
        """
        Full E2E walkthrough: Ambient / Espacial Cinemática (Drone, Pad, FX).
        Acoustics: ValhallaSupermassive stereo diffusion, infinite reverb, dark high cuts.
        """
        session, adapter = _setup_session(
            genre="ambient",
            tracks=[
                {"index": 0, "name": "Sub Drone", "role": "BASS"},
                {"index": 1, "name": "Cosmic Pad", "role": "PAD"},
                {"index": 2, "name": "Space FX", "role": "FX"},
            ],
        )

        step_count = 0
        while session.data["current_phase"] == "PHASE_5_INSERT_EFFECTS":
            step_count += 1
            session.step(conn=adapter, user_input="Opción 1")
            if step_count > 30:
                pytest.fail("Ambient session exceeded expected step count")

        assert session.data["current_phase"] == "PHASE_6_COMPOSITION"

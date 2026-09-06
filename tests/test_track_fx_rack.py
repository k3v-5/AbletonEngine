# tests/test_track_fx_rack.py
import pytest
from engine.fx.track_fx_rack import TrackFXRack

class MockConn:
    def __init__(self):
        self.commands = []
        self.dev_count = 1

    def send_command(self, cmd, params=None):
        self.commands.append((cmd, params))
        if cmd == "get_track_info":
            return {
                "status": "success",
                "result": {
                    "devices": [{"name": f"Device_{i}"} for i in range(self.dev_count)]
                }
            }
        elif cmd == "load_instrument_or_effect":
            self.dev_count += 1
            return {"status": "success"}
        elif cmd == "set_device_parameter":
            return {"status": "success"}
        return {"status": "success"}

def test_role_fx_spec_drums():
    specs = TrackFXRack.get_role_fx_spec("drums")
    assert len(specs) == 3
    names = [s["name"] for s in specs]
    assert "EQ Eight" in names
    assert "Glue Compressor" in names
    assert "Saturator" in names

def test_role_fx_spec_chords():
    specs = TrackFXRack.get_role_fx_spec("chords")
    assert len(specs) == 3
    names = [s["name"] for s in specs]
    assert "Pro-Q 4" in names
    assert "OTT" in names
    assert "ValhallaVintageVerb" in names

def test_apply_track_channel_strip():
    conn = MockConn()
    res = TrackFXRack.apply_track_channel_strip(conn, track_index=2, role="chords")
    assert res["status"] == "APPLIED"
    assert res["effects_count"] == 3
    # Check that parameters were sent
    param_cmds = [c for c in conn.commands if c[0] == "set_device_parameter"]
    assert len(param_cmds) > 0


def test_shaperbox_3_sculpting_profile_completeness():
    """Confirms ShaperBox 3 profile covers Volume, Drive, Filter, Time, and Master modules."""
    from engine.fx.device_parameter_supervisor import DeviceParameterSupervisor
    profile = DeviceParameterSupervisor.ROLE_SCULPTING_PROFILES.get("SHAPERBOX_3", {})
    assert "DYNAMICS" in profile
    assert "COMP_DEPTH" in profile["DYNAMICS"]
    assert "SATURATION" in profile
    assert "DRIVE" in profile["SATURATION"]
    assert "FILTERS" in profile
    assert "FILTER_CUTOFF" in profile["FILTERS"]
    assert "SPACE_MODULATION" in profile
    assert "TIME_SHAPE" in profile["SPACE_MODULATION"]
    assert "MACROS_MASTER" in profile
    assert "DRY_WET" in profile["MACROS_MASTER"]


def test_littlealterboy_sculpting_profile_completeness():
    """Confirms LittleAlterBoy profile independently sculpts Pitch, Formant, Mode, Drive and Mix."""
    from engine.fx.device_parameter_supervisor import DeviceParameterSupervisor
    profile = DeviceParameterSupervisor.ROLE_SCULPTING_PROFILES.get("LITTLEALTERBOY", {})
    assert "OSCILLATORS" in profile
    osc = profile["OSCILLATORS"]
    assert "VOICE_PITCH" in osc
    assert "VOICE_FORMANT" in osc
    assert "VOICE_MODE" in osc
    assert "SATURATION" in profile
    assert "DRIVE" in profile["SATURATION"]
    assert "MACROS_MASTER" in profile
    assert "DRY_WET" in profile["MACROS_MASTER"]


def test_efx_refract_sculpting_profile_completeness():
    """Confirms Efx REFRACT profile sculpts Unison Voices, Detune, Filter Cutoff, Chorus and Dry/Wet."""
    from engine.fx.device_parameter_supervisor import DeviceParameterSupervisor
    profile = DeviceParameterSupervisor.ROLE_SCULPTING_PROFILES.get("EFX_REFRACT", {})
    assert "OSCILLATORS" in profile
    assert "UNISON_VOICES" in profile["OSCILLATORS"]
    assert "UNISON_DETUNE" in profile["OSCILLATORS"]
    assert "FILTERS" in profile
    assert "FILTER_CUTOFF" in profile["FILTERS"]
    assert "SPACE_MODULATION" in profile
    assert "CHORUS_MIX" in profile["SPACE_MODULATION"]
    assert "MACROS_MASTER" in profile
    assert "DRY_WET" in profile["MACROS_MASTER"]


def test_enforce_mandatory_sculpting_syncs_governance():
    """Confirms enforce_mandatory_sculpting records device as sculpted in EngineGovernanceSupervisor."""
    from engine.fx.device_parameter_supervisor import DeviceParameterSupervisor
    from engine.supervisor.governance import governance_supervisor
    conn = MockConn()
    conn.dev_count = 2

    # Register track and add effect in governance
    governance_supervisor.register_track(5, name="Lead FX")
    governance_supervisor.request_add_effect(5, "ShaperBox 3")

    # Enforce sculpting
    res = DeviceParameterSupervisor.enforce_mandatory_sculpting(conn, track_index=5, device_index=0, role="LEAD")
    assert res is not None

    # Assert that governance now considers device 0 sculpted
    governance_supervisor.assert_device_sculpted(5, device_index=0)


def test_analog_lab_v_sculpting_profiles_completeness():
    from engine.fx.device_parameter_supervisor import DeviceParameterSupervisor
    profiles = DeviceParameterSupervisor.ROLE_SCULPTING_PROFILES
    assert "ANALOG_LAB_V" in profiles
    assert "ANALOG_LAB_KEYS" in profiles
    assert "ANALOG_LAB_PAD" in profiles
    assert "ANALOG_LAB_LEAD" in profiles

    al = profiles["ANALOG_LAB_V"]
    assert "MACROS_MASTER" in al
    assert "SPACE_MODULATION" in al
    assert al["MACROS_MASTER"]["MACRO_1"] != 0.5
    assert al["MACROS_MASTER"]["MACRO_2"] != 0.5
    assert "REVERB_MIX" in al["SPACE_MODULATION"]
    assert "DELAY_MIX" in al["SPACE_MODULATION"]


def test_analog_lab_v_default_audit_detection():
    from engine.fx.device_parameter_supervisor import DeviceParameterSupervisor
    class MockDefaultAnalogLabConn:
        def send_command(self, cmd, params=None):
            if cmd == "get_device_parameters":
                return {
                    "parameters": [
                        {"index": 0, "name": "Device On", "value": 1.0, "min": 0.0, "max": 1.0},
                        {"index": 1, "name": "P1 Brightness", "value": 0.5, "min": 0.0, "max": 1.0},
                        {"index": 2, "name": "P1 Timbre", "value": 0.5, "min": 0.0, "max": 1.0},
                        {"index": 3, "name": "P1 Time", "value": 0.5, "min": 0.0, "max": 1.0},
                        {"index": 4, "name": "P1 Movement", "value": 0.5, "min": 0.0, "max": 1.0},
                        {"index": 5, "name": "Master", "value": 0.5, "min": 0.0, "max": 1.0},
                        {"index": 6, "name": "FXA Dry/Wet", "value": 0.0, "min": 0.0, "max": 1.0},
                        {"index": 7, "name": "FXB Dry/Wet", "value": 0.0, "min": 0.0, "max": 1.0},
                        {"index": 8, "name": "Delay Volume", "value": 0.0, "min": 0.0, "max": 1.0},
                        {"index": 9, "name": "Reverb Volume", "value": 0.0, "min": 0.0, "max": 1.0}
                    ]
                }
            return {}

    conn = MockDefaultAnalogLabConn()
    audit = DeviceParameterSupervisor.audit_device_sculpting(conn, track_index=19, device_index=0)
    assert audit["is_sculpted"] is False
    assert "Analog Lab V is in factory default" in audit["reason"]


def test_serum2_deep_sculpting_and_audit():
    from engine.fx.device_parameter_supervisor import DeviceParameterSupervisor
    profiles = DeviceParameterSupervisor.ROLE_SCULPTING_PROFILES
    assert "SERUM" in profiles
    serum = profiles["SERUM"]
    assert "MACROS_MASTER" in serum
    assert "FILTERS" in serum
    assert "OSCILLATORS" in serum
    assert "ENVELOPES" in serum

    # Ensure oscillator wavetable pos and filter cutoff are transformed away from init saw
    assert serum["OSCILLATORS"]["OSC_A_WT_POS"] > 0.1
    assert serum["FILTERS"]["FILTER_CUTOFF"] < 0.95

    class MockDefaultSerumConn:
        def send_command(self, cmd, params=None):
            if cmd == "get_device_parameters":
                return {
                    "parameters": [
                        {"index": 0, "name": "Device On", "value": 1.0, "min": 0.0, "max": 1.0},
                        {"index": 13, "name": "A WT Pos", "value": 0.0, "min": 0.0, "max": 1.0},
                        {"index": 14, "name": "A Warp", "value": 0.0, "min": 0.0, "max": 1.0},
                        {"index": 62, "name": "Filter 1 Freq", "value": 1.0, "min": 0.0, "max": 1.0},
                        {"index": 67, "name": "Filter 1 Drive", "value": 0.0, "min": 0.0, "max": 1.0},
                        {"index": 75, "name": "Macro 1", "value": 0.0, "min": 0.0, "max": 1.0}
                    ]
                }
            return {}

    conn = MockDefaultSerumConn()
    audit = DeviceParameterSupervisor.audit_device_sculpting(conn, track_index=14, device_index=0)
    assert audit["is_sculpted"] is False
    assert "Serum 2 is in factory default" in audit["reason"]


def test_pigments_profile_completeness():
    from engine.fx.device_parameter_supervisor import DeviceParameterSupervisor
    profiles = DeviceParameterSupervisor.ROLE_SCULPTING_PROFILES
    assert "PIGMENTS" in profiles
    pig = profiles["PIGMENTS"]
    assert "MACROS_MASTER" in pig
    assert "FILTERS" in pig
    assert "ENVELOPES" in pig
    assert pig["MACROS_MASTER"]["MACRO_1"] > 0.0



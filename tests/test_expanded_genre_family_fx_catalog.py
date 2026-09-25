# tests/test_expanded_genre_family_fx_catalog.py
"""
Comprehensive test suite for the expanded Universal Genre-Family FX Catalog,
Live 12 modular device factories, subgenre specialization overrides, LOM verifier mappings,
and psychoacoustic spectral guide across 39 musical roles.
"""
import pytest
from engine.fx.role_fx_catalog import (
    GenreFamily,
    resolve_genre_family,
    UniversalGenreFamilyFXCatalog,
    ROLE_INSERT_EFFECTS,
    ROLE_FREQUENCY_GUIDE,
    SUBGENRE_CHAIN_OVERRIDES,
    make_auto_filter,
    make_echo,
    make_pedal,
    make_phaser_flanger,
    make_multiband_dynamics,
    make_shifter,
    make_hybrid_reverb,
    make_erosion,
    make_eq_eight,
    make_glue_compressor,
    make_saturator,
    make_drum_buss,
    make_compressor,
    make_utility,
    make_ott,
    make_valhalla_supermassive,
    make_valhalla_vintage_verb,
    make_surge_xt_effects,
    make_chorus_ensemble,
    make_delay,
    make_auto_tune_artist,
    make_pro_q_4,
    make_saturn_2,
    make_reverb,
)
from engine.core.device_execution_verifier import DeviceExecutionVerifier


# All 39 canonical musical roles expected in every family catalog
CANONICAL_39_ROLES = [
    # 23 Base Roles
    "KICK", "DRUMS", "BASS", "KEYS", "LEAD", "STRINGS", "VOCALS", "PAD",
    "GUITAR", "BRASS", "CHOIR", "PERCUSSION", "FX", "RHYTHM_GUITAR", "LEAD_GUITAR",
    "808_BASS", "ELECTRIC_BASS", "DEMBOW", "BACKING_VOCALS", "SUB",
    "COUNTER_LEAD", "EAR_CANDY", "TEXTURE_FOLEY",
    # 16 Expanded Roles
    "SYNTH_BASS", "SYNTH_PLUCK", "ARPEGGIO", "VOCAL_CHOP", "ACOUSTIC_PIANO",
    "RHODES", "ORGAN", "VIOLIN", "CELLO", "UPRIGHT_BASS", "CONGAS",
    "SHAKER", "SNARE", "HIHAT", "SYNTH_LEAD", "SOUNDSCAPE"
]


class TestExpandedCatalogRoleCoverage:
    """Verifies that all 39 roles exist in all 4 canonical sound families (156 chains)."""

    @pytest.mark.parametrize("family", [
        GenreFamily.URBANA_MODERNA,
        GenreFamily.ELECTRONICA_CLUB,
        GenreFamily.ORGANICA_ACUSTICA,
        GenreFamily.ESPACIAL_CINEMATICA,
    ])
    def test_all_39_roles_present_in_each_family(self, family):
        fam_catalog = UniversalGenreFamilyFXCatalog.CATALOG[family]
        missing = [role for role in CANONICAL_39_ROLES if role not in fam_catalog]
        assert not missing, f"Family {family.value} missing roles: {missing}"
        assert len(fam_catalog) >= 39, f"Family {family.value} has fewer than 39 roles"

    @pytest.mark.parametrize("family", [
        GenreFamily.URBANA_MODERNA,
        GenreFamily.ELECTRONICA_CLUB,
        GenreFamily.ORGANICA_ACUSTICA,
        GenreFamily.ESPACIAL_CINEMATICA,
    ])
    def test_each_chain_contains_valid_devices_and_parameters(self, family):
        fam_catalog = UniversalGenreFamilyFXCatalog.CATALOG[family]
        for role, chain in fam_catalog.items():
            assert len(chain) >= 1, f"Empty FX chain for {role} in {family.value}"
            for dev in chain:
                assert "name" in dev, f"Device missing name in {role} / {family.value}"
                assert "type" in dev, f"Device missing type in {role} / {family.value}"
                assert "params" in dev, f"Device missing params in {role} / {family.value}"
                assert "acoustic_purpose" in dev, f"Device missing acoustic_purpose in {role} / {family.value}"
                assert len(dev["params"]) > 0, f"Device {dev['name']} has 0 params in {role} / {family.value}"


class TestExpandedDeviceFactories:
    """Verifies schemas and defaults for newly introduced Live 12 device parameter factories."""

    def test_make_auto_filter(self):
        af = make_auto_filter(frequency=0.60, resonance=0.35, filter_type=1.0, drive=0.25)
        assert af["name"] == "Auto Filter"
        assert af["type"] == "native"
        param_ids = {p["id"]: p["default"] for p in af["params"]}
        assert param_ids["Frequency"] == 0.60
        assert param_ids["Resonance"] == 0.35
        assert param_ids["Filter Type"] == 1.0
        assert param_ids["Drive"] == 0.25

    def test_make_echo(self):
        echo = make_echo(dry_wet=0.40, feedback=0.55, wobble=0.30, noise=0.15)
        assert echo["name"] == "Echo"
        assert echo["type"] == "native"
        param_ids = {p["id"]: p["default"] for p in echo["params"]}
        assert param_ids["Dry/Wet"] == 0.40
        assert param_ids["Feedback"] == 0.55
        assert param_ids["Wobble"] == 0.30
        assert param_ids["Noise"] == 0.15

    def test_make_pedal(self):
        pedal = make_pedal(gain=0.45, output=0.65, pedal_type=1.0, sub=1.0)
        assert pedal["name"] == "Pedal"
        assert pedal["type"] == "native"
        param_ids = {p["id"]: p["default"] for p in pedal["params"]}
        assert param_ids["Gain"] == 0.45
        assert param_ids["Output"] == 0.65
        assert param_ids["Type"] == 1.0
        assert param_ids["Sub"] == 1.0

    def test_make_phaser_flanger(self):
        pf = make_phaser_flanger(amount=0.40, rate=0.30, feedback=0.35, warmth=0.60, mode=1.0)
        assert pf["name"] == "Phaser-Flanger"
        assert pf["type"] == "native"
        param_ids = {p["id"]: p["default"] for p in pf["params"]}
        assert param_ids["Amount"] == 0.40
        assert param_ids["Rate"] == 0.30
        assert param_ids["Warmth"] == 0.60
        assert param_ids["Mode"] == 1.0

    def test_make_multiband_dynamics(self):
        mb = make_multiband_dynamics(band_low=2.0, band_mid=-1.0, band_high=3.0, amount=0.50)
        assert mb["name"] == "Multiband Dynamics"
        assert mb["type"] == "native"
        param_ids = {p["id"]: p["default"] for p in mb["params"]}
        assert param_ids["Band 1 (Low)"] == 2.0
        assert param_ids["Band 2 (Mid)"] == -1.0
        assert param_ids["Band 3 (High)"] == 3.0
        assert param_ids["Amount"] == 0.50

    def test_make_shifter(self):
        shifter = make_shifter(pitch=7.0, fine=12.0, drive=0.20, mode=0.0)
        assert shifter["name"] == "Shifter"
        assert shifter["type"] == "native"
        param_ids = {p["id"]: p["default"] for p in shifter["params"]}
        assert param_ids["Pitch"] == 7.0
        assert param_ids["Fine"] == 12.0
        assert param_ids["Drive"] == 0.20

    def test_make_hybrid_reverb(self):
        hr = make_hybrid_reverb(blend=0.70, decay=0.45, size=0.60)
        assert hr["name"] == "Hybrid Reverb"
        assert hr["type"] == "native"
        param_ids = {p["id"]: p["default"] for p in hr["params"]}
        assert param_ids["Blend"] == 0.70
        assert param_ids["Decay"] == 0.45
        assert param_ids["Size"] == 0.60

    def test_make_erosion(self):
        erosion = make_erosion(frequency=0.65, width=0.50, amount=0.35, mode=1.0)
        assert erosion["name"] == "Erosion"
        assert erosion["type"] == "native"
        param_ids = {p["id"]: p["default"] for p in erosion["params"]}
        assert param_ids["Frequency"] == 0.65
        assert param_ids["Width"] == 0.50
        assert param_ids["Amount"] == 0.35
        assert param_ids["Mode"] == 1.0


class TestSubgenreSpecializationOverrides:
    """Verifies that surgical subgenre overrides trigger when specific subgenres are queried."""

    def test_boom_bap_overrides(self):
        # Boom Bap drums must have tape warmth and MPC style crunch
        bb_drums = UniversalGenreFamilyFXCatalog.get_fx_chain_for_role("DRUMS", "boom_bap")
        bb_drum_names = [d["name"] for d in bb_drums]
        assert "Surge XT Effects" in bb_drum_names
        assert "Drum Buss" in bb_drum_names

        # Boom Bap vocals must NOT have Auto-Tune
        bb_vocs = UniversalGenreFamilyFXCatalog.get_fx_chain_for_role("VOCALS", "boom_bap")
        assert not any("auto-tune" in d["name"].lower() for d in bb_vocs)

    def test_drill_overrides(self):
        # Drill 808 must feature aggressive glide saturation
        drill_808 = UniversalGenreFamilyFXCatalog.get_fx_chain_for_role("808_BASS", "uk_drill")
        assert any(d["name"] == "Saturator" for d in drill_808)
        sat = next(d for d in drill_808 if d["name"] == "Saturator")
        drive_param = next(p for p in sat["params"] if p["id"] == "Drive")
        assert drive_param["default"] >= 0.30

    def test_phonk_overrides(self):
        # Phonk lead must feature digital degradation via Erosion
        phonk_lead = UniversalGenreFamilyFXCatalog.get_fx_chain_for_role("LEAD", "drift_phonk")
        assert any(d["name"] == "Erosion" for d in phonk_lead)
        assert any(d["name"] == "Saturator" for d in phonk_lead)

    def test_techno_overrides(self):
        # Peak time techno kick must have hard rumble saturator
        techno_kick = UniversalGenreFamilyFXCatalog.get_fx_chain_for_role("KICK", "peak_time_techno")
        assert any(d["name"] == "Saturator" for d in techno_kick)

        # Techno bass must feature Auto Filter acid modulation
        techno_bass = UniversalGenreFamilyFXCatalog.get_fx_chain_for_role("BASS", "techno")
        assert any(d["name"] == "Auto Filter" for d in techno_bass)

    def test_liquid_dnb_overrides(self):
        # Liquid DnB pad must feature wide diffusion mode Andromeda
        liquid_pad = UniversalGenreFamilyFXCatalog.get_fx_chain_for_role("PAD", "liquid_dnb")
        assert any(d["name"] == "ValhallaSupermassive" for d in liquid_pad)
        assert any(d["name"] == "Chorus-Ensemble" for d in liquid_pad)

    def test_flamenco_overrides(self):
        # Flamenco guitar must feature transparent compression and natural wooden room
        flamenco_gtr = UniversalGenreFamilyFXCatalog.get_fx_chain_for_role("GUITAR", "flamenco")
        assert any(d["name"] == "Glue Compressor" for d in flamenco_gtr)
        assert any(d["name"] == "ValhallaVintageVerb" for d in flamenco_gtr)

    def test_bossa_nova_overrides(self):
        # Bossa Nova guitar must feature ultra-soft optical compression for nylon strings
        bossa_gtr = UniversalGenreFamilyFXCatalog.get_fx_chain_for_role("GUITAR", "bossa_nova")
        assert any(d["name"] == "Compressor" for d in bossa_gtr)
        assert any(d["name"] == "ValhallaVintageVerb" for d in bossa_gtr)

    def test_dark_ambient_overrides(self):
        # Dark Ambient pad must feature Great Annihilator mode in Supermassive
        dark_pad = UniversalGenreFamilyFXCatalog.get_fx_chain_for_role("PAD", "dark_ambient")
        assert any(d["name"] == "ValhallaSupermassive" for d in dark_pad)
        sm = next(d for d in dark_pad if d["name"] == "ValhallaSupermassive")
        mode_param = next(p for p in sm["params"] if p["id"] == "Mode")
        assert mode_param["default"] >= 0.60


class TestLOMVerifierNewDevices:
    """Verifies that all 7 new devices have proper LOM parameter resolution in DeviceExecutionVerifier."""

    def test_echo_lom_resolution(self):
        assert DeviceExecutionVerifier.resolve_lom_parameter_name("Echo", "mix") == "Dry/Wet"
        assert DeviceExecutionVerifier.resolve_lom_parameter_name("Echo", "fb") == "Feedback"
        assert DeviceExecutionVerifier.resolve_lom_parameter_name("Echo", "wobble") == "Wobble"
        assert DeviceExecutionVerifier.resolve_lom_parameter_name("Echo", "tape noise") == "Noise"

    def test_pedal_lom_resolution(self):
        assert DeviceExecutionVerifier.resolve_lom_parameter_name("Pedal", "drive") == "Gain"
        assert DeviceExecutionVerifier.resolve_lom_parameter_name("Pedal", "vol") == "Output"
        assert DeviceExecutionVerifier.resolve_lom_parameter_name("Pedal", "sub bass") == "Sub"
        assert DeviceExecutionVerifier.resolve_lom_parameter_name("Pedal", "mode") == "Type"

    def test_phaser_flanger_lom_resolution(self):
        assert DeviceExecutionVerifier.resolve_lom_parameter_name("Phaser-Flanger", "depth") == "Amount"
        assert DeviceExecutionVerifier.resolve_lom_parameter_name("Phaser-Flanger", "speed") == "Rate"
        assert DeviceExecutionVerifier.resolve_lom_parameter_name("Phaser-Flanger", "warmth") == "Warmth"

    def test_multiband_dynamics_lom_resolution(self):
        assert DeviceExecutionVerifier.resolve_lom_parameter_name("Multiband Dynamics", "makeup") == "Output Gain"
        assert DeviceExecutionVerifier.resolve_lom_parameter_name("Multiband Dynamics", "depth") == "Amount"
        assert DeviceExecutionVerifier.resolve_lom_parameter_name("Multiband Dynamics", "low band") == "Band 1 (Low)"

    def test_shifter_lom_resolution(self):
        assert DeviceExecutionVerifier.resolve_lom_parameter_name("Shifter", "semitones") == "Pitch"
        assert DeviceExecutionVerifier.resolve_lom_parameter_name("Shifter", "cents") == "Fine"
        assert DeviceExecutionVerifier.resolve_lom_parameter_name("Shifter", "saturation") == "Drive"

    def test_hybrid_reverb_lom_resolution(self):
        assert DeviceExecutionVerifier.resolve_lom_parameter_name("Hybrid Reverb", "decay time") == "Decay"
        assert DeviceExecutionVerifier.resolve_lom_parameter_name("Hybrid Reverb", "room size") == "Size"
        assert DeviceExecutionVerifier.resolve_lom_parameter_name("Hybrid Reverb", "algo blend") == "Blend"

    def test_erosion_lom_resolution(self):
        assert DeviceExecutionVerifier.resolve_lom_parameter_name("Erosion", "freq") == "Frequency"
        assert DeviceExecutionVerifier.resolve_lom_parameter_name("Erosion", "q") == "Width"
        assert DeviceExecutionVerifier.resolve_lom_parameter_name("Erosion", "depth") == "Amount"


class TestExpandedGenreResolution:
    """Verifies that 80+ subgenres and keywords correctly resolve to the 4 canonical families."""

    @pytest.mark.parametrize("subgenre,expected_family", [
        ("trap", GenreFamily.URBANA_MODERNA),
        ("uk_drill", GenreFamily.URBANA_MODERNA),
        ("boom_bap", GenreFamily.URBANA_MODERNA),
        ("drift_phonk", GenreFamily.URBANA_MODERNA),
        ("pluggnb", GenreFamily.URBANA_MODERNA),
        ("jersey_club", GenreFamily.URBANA_MODERNA),
        ("baile_funk", GenreFamily.URBANA_MODERNA),
        ("reggaeton", GenreFamily.URBANA_MODERNA),
        ("dembow", GenreFamily.URBANA_MODERNA),
        ("deep_house", GenreFamily.ELECTRONICA_CLUB),
        ("tech_house", GenreFamily.ELECTRONICA_CLUB),
        ("afro_house", GenreFamily.ELECTRONICA_CLUB),
        ("peak_time_techno", GenreFamily.ELECTRONICA_CLUB),
        ("liquid_dnb", GenreFamily.ELECTRONICA_CLUB),
        ("neurofunk", GenreFamily.ELECTRONICA_CLUB),
        ("dubstep", GenreFamily.ELECTRONICA_CLUB),
        ("progressive_trance", GenreFamily.ELECTRONICA_CLUB),
        ("synthwave", GenreFamily.ELECTRONICA_CLUB),
        ("neo_soul", GenreFamily.ORGANICA_ACUSTICA),
        ("motown", GenreFamily.ORGANICA_ACUSTICA),
        ("flamenco_fusion", GenreFamily.ORGANICA_ACUSTICA),
        ("bossa_nova", GenreFamily.ORGANICA_ACUSTICA),
        ("cumbia_sonidera", GenreFamily.ORGANICA_ACUSTICA),
        ("afrobeat", GenreFamily.ORGANICA_ACUSTICA),
        ("indie_rock", GenreFamily.ORGANICA_ACUSTICA),
        ("acoustic_pop", GenreFamily.ORGANICA_ACUSTICA),
        ("dark_ambient", GenreFamily.ESPACIAL_CINEMATICA),
        ("drone", GenreFamily.ESPACIAL_CINEMATICA),
        ("film_score", GenreFamily.ESPACIAL_CINEMATICA),
        ("epic_orchestral", GenreFamily.ESPACIAL_CINEMATICA),
        ("trip_hop", GenreFamily.ESPACIAL_CINEMATICA),
        ("illbient", GenreFamily.ESPACIAL_CINEMATICA),
    ])
    def test_subgenre_classification(self, subgenre, expected_family):
        resolved = resolve_genre_family(subgenre)
        assert resolved == expected_family, f"Failed for subgenre {subgenre}: got {resolved}, expected {expected_family}"


class TestPsychoacousticSpectralGuide:
    """Verifies that all 39 roles have complete psychoacoustic guidance."""

    @pytest.mark.parametrize("role", CANONICAL_39_ROLES)
    def test_role_frequency_guide_completeness(self, role):
        assert role in ROLE_FREQUENCY_GUIDE, f"Role {role} missing from ROLE_FREQUENCY_GUIDE"
        guide = ROLE_FREQUENCY_GUIDE[role]
        required_keys = ["dominant_zone", "conflict_points", "eq_recommendation", "transient_handling"]
        for k in required_keys:
            assert k in guide, f"Key {k} missing in ROLE_FREQUENCY_GUIDE[{role}]"
            assert len(guide[k].strip()) > 10, f"Guidance for {k} in {role} is suspiciously short"

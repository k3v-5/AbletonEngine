# tests/test_commercial_phase4_groove_and_depth.py
"""
Comprehensive test suite for Phase 4 Commercial & Psychoacoustic Enhancements in AbletonEngine:
1. Off-Beat Metric Displacer (Syncopation & Phrase Turnaround Bounce)
2. Z-Plane Psychoacoustic Depth Architect (3D Spatial Layering & Distance Simulation)
3. Dynamic Sub-to-Stereo Morpher (Drop Impact Stereo Expansion with Mono Sub Security)
4. Atmospheric Foley Bed Generator (Subliminal Texture Injection & Sidechain Ducking)
5. Pre-Master Crest Factor Optimizer (Headroom Maximization & Transparent Soft-Clipping)
6. Evolutionary Hi-Hat Mutator (Stochastic Variations & Anti-Fatigue Mutations)
7. Harmonic Pedal Point & Suspension Weaver (Build-Up Tension & Sustained Drone)
8. Underwater & Radio Acoustic Sweep Transition Generator (Pre-Drop Spectral Collapse)
9. Copilot Guided Session Phase 6, 7, 8 & Intercept Router Integrations
"""

import pytest
from typing import Dict, Any, List

from engine.music.groove.metric_displacement import OffBeatMetricDisplacer
from engine.mix.z_plane_depth import ZPlaneDepthArchitect
from engine.sound.sub_stereo_morpher import DynamicSubToStereoMorpher
from engine.arrangement.textures.foley_bed import AtmosphericFoleyBedGenerator
from engine.mix.crest_factor_optimizer import PreMasterCrestFactorOptimizer
from engine.music.drums.hihat_mutator import EvolutionaryHiHatMutator
from engine.music.harmony.pedal_suspension import PedalPointSuspensionWeaver
from engine.arrangement.transitions.underwater_sweep import UnderwaterRadioSweepGenerator

from engine.production.copilot.guided_session import CopilotGuidedSession
from engine.production.copilot.phases.phase_6.handler import Phase6CompositionHandler


class MockAbletonAdapter:
    """Mock connection for Ableton Live OSC commands."""
    def __init__(self):
        self.commands = []

    def send_command(self, cmd: str, params: Dict[str, Any] = None):
        self.commands.append({"command": cmd, "params": params or {}})
        if cmd == "get_session_info":
            return {"status": "SUCCESS", "result": {"track_count": 8, "tempo": 120.0}}
        if cmd == "get_track_info":
            return {"status": "SUCCESS", "result": {"name": f"Track {params.get('track_index', 0)}"}}
        return {"status": "SUCCESS"}


# =============================================================================
# 1. Off-Beat Metric Displacer Tests
# =============================================================================

def test_offbeat_metric_displacer_bars_and_levels():
    """Verifies displacement targets bars 2 and 6 with precise grid pushes."""
    notes = [
        {"pitch": 36, "start_time": 0.0, "duration": 1.0, "velocity": 100},  # Bar 1 (intact)
        {"pitch": 36, "start_time": 4.0, "duration": 1.0, "velocity": 100},  # Bar 2 beat 1 (target)
        {"pitch": 38, "start_time": 8.0, "duration": 1.0, "velocity": 100},  # Bar 3 (intact)
        {"pitch": 36, "start_time": 20.0, "duration": 1.0, "velocity": 100}, # Bar 6 beat 1 (target)
    ]
    res = OffBeatMetricDisplacer.apply_metric_displacement(
        notes=notes,
        role="BASS",
        bars=8,
        displacement_level=2
    )
    assert res["status"] == "DISPLACED"
    assert 2 in res["displaced_bars"]
    assert 6 in res["displaced_bars"]

    displaced_notes = res["notes"]
    assert displaced_notes[1]["start_time"] == 4.25  # 16th note syncopation
    assert displaced_notes[1].get("metric_displaced") is True
    assert displaced_notes[3]["start_time"] == 20.25
    assert displaced_notes[3].get("metric_displaced") is True


def test_offbeat_metric_displacer_ineligible_role():
    """Verifies that non-eligible roles (e.g. Drums, FX) remain untouched."""
    notes = [{"pitch": 42, "start_time": 4.0, "duration": 0.5}]
    res = OffBeatMetricDisplacer.apply_metric_displacement(notes, role="DRUMS")
    assert res["status"] == "ROLE_NOT_ELIGIBLE"
    assert res["notes"][0]["start_time"] == 4.0


# =============================================================================
# 2. Z-Plane Psychoacoustic Depth Architect Tests
# =============================================================================

def test_z_plane_depth_tier_classification():
    """Verifies accurate 3-tier depth classification (Foreground, Midground, Background)."""
    tracks = [
        {"index": 0, "name": "Lead Vocal", "role": "VOCALS"},
        {"index": 1, "name": "Kick", "role": "KICK"},
        {"index": 2, "name": "Synth Chords", "role": "KEYS"},
        {"index": 3, "name": "Ethereal Pad", "role": "PAD"},
        {"index": 4, "name": "Subliminal Foley", "role": "FX"}
    ]
    audit = ZPlaneDepthArchitect.evaluate_session_depth(tracks)
    dist = audit["depth_distribution"]

    assert any(t["name"] == "Lead Vocal" for t in dist["FOREGROUND"])
    assert any(t["name"] == "Kick" for t in dist["FOREGROUND"])
    assert any(t["name"] == "Synth Chords" for t in dist["MIDGROUND"])
    assert any(t["name"] == "Ethereal Pad" for t in dist["BACKGROUND"])
    assert any(t["name"] == "Subliminal Foley" for t in dist["BACKGROUND"])


def test_z_plane_depth_parameter_prescription():
    """Verifies transient attack and pre-delay differences across depth tiers."""
    fg_recipe = ZPlaneDepthArchitect.prescribe_depth_parameters("VOCALS")
    bg_recipe = ZPlaneDepthArchitect.prescribe_depth_parameters("PAD")

    assert fg_recipe["depth_tier"] == "FOREGROUND"
    assert bg_recipe["depth_tier"] == "BACKGROUND"

    # Foreground has fast attack and intimate pre-delay
    assert fg_recipe["transient_attack_factor"] > bg_recipe["transient_attack_factor"]
    assert fg_recipe["early_reflection_predelay_ms"] < bg_recipe["early_reflection_predelay_ms"]
    assert fg_recipe["reverb_wet_percent"] < bg_recipe["reverb_wet_percent"]


# =============================================================================
# 3. Dynamic Sub-to-Stereo Morpher Tests
# =============================================================================

def test_sub_stereo_morpher_envelope():
    """Verifies mono in verses and wide expansion on drop impact."""
    recipe = DynamicSubToStereoMorpher.generate_drop_expansion_envelope(
        drop_start_beat=32.0,
        pre_drop_duration_beats=4.0,
        drop_stereo_width=1.35
    )
    assert recipe["status"] == "SUB_STEREO_MORPH_GENERATED"
    assert recipe["drop_start_beat"] == 32.0
    assert recipe["start_beat"] == 28.0

    width_points = recipe["stereo_width_envelope"]
    # Pre-drop starts at pure mono (0.0)
    assert width_points[0]["width"] == 0.0
    # Drop impact expands to 1.35
    assert width_points[-1]["width"] == 1.35
    assert recipe["sub_bass_mono_lock_hz"] == 100.0


# =============================================================================
# 4. Atmospheric Foley Bed Generator Tests
# =============================================================================

def test_atmospheric_foley_bed_prescription():
    """Verifies subliminal gain staging (-30 dBFS) and ducking prescription."""
    foley = AtmosphericFoleyBedGenerator.generate_foley_bed_prescription(
        genre="LOFI",
        target_level_dbfs=-32.0
    )
    assert foley["status"] == "FOLEY_BED_PRESCRIBED"
    assert foley["preset"] == "VINYL_WARMTH"
    assert foley["target_level_dbfs"] == -32.0
    assert foley["duck_depth_db"] <= -2.0
    assert "duck_source_role" in foley


# =============================================================================
# 5. Pre-Master Crest Factor Optimizer Tests
# =============================================================================

def test_crest_factor_optimizer_runaway_detection():
    """Verifies detection of runaway crest factor (>13.5 dB) and soft-clip calculation."""
    tracks = [
        {"index": 0, "name": "Live Snare", "role": "SNARE"},
        {"index": 1, "name": "Smooth Bass", "role": "BASS"}
    ]
    audit = PreMasterCrestFactorOptimizer.audit_session_crest_factors(tracks)
    assert audit["status"] == "AUDITED"
    assert "target_crest_factor_db" in audit
    assert audit["max_true_peak_margin_dbtp"] == -0.3

    # Snare usually has runaway peaks needing soft-clipping
    snare_rep = next(t for t in audit["track_reports"] if t["track_name"] == "Live Snare")
    assert snare_rep["crest_factor_db"] >= 13.5
    assert snare_rep["runaway_peak_risk"] is True
    assert snare_rep["recommended_soft_clip_db"] > 0.0


# =============================================================================
# 6. Evolutionary Hi-Hat Mutator Tests
# =============================================================================

def test_hihat_mutator_evolutionary_cycle():
    """Verifies that 8-bar cycles apply micro-rolls (bar 2), pitch drops (bar 4), accents (bar 6), and turnarounds (bar 8)."""
    # Create regular 8-bar 1/8th note hi-hat pattern (32 beats, 64 notes)
    notes = []
    for b in range(64):
        notes.append({
            "pitch": 42,
            "start_time": round(b * 0.5, 3),
            "duration": 0.25,
            "velocity": 85
        })

    mutated = EvolutionaryHiHatMutator.mutate_hihat_pattern(
        notes=notes,
        bars=8,
        genre="TRAP",
        intensity=0.7
    )
    assert mutated["status"] == "MUTATED"
    assert mutated["mutated_count"] > mutated["original_count"]

    mut_types = [m["type"] for m in mutated["mutations_applied"]]
    mut_bars = [m["bar"] for m in mutated["mutations_applied"]]

    assert "MICRO_ROLL_32ND" in mut_types
    assert 2 in mut_bars
    assert "PITCH_DROP" in mut_types
    assert 4 in mut_bars
    assert "OPEN_HAT_ACCENT" in mut_types
    assert 6 in mut_bars
    assert "TURNAROUND_BURST" in mut_types
    assert 8 in mut_bars


# =============================================================================
# 7. Harmonic Pedal Point & Suspension Weaver Tests
# =============================================================================

def test_pedal_point_suspension_weaver():
    """Verifies sustained pedal bass generation and sus4 chord transformations."""
    chords = [
        {"root": "F", "quality": "major", "duration": 4.0},
        {"root": "G", "quality": "major", "duration": 4.0},
        {"root": "Am", "quality": "minor", "duration": 4.0},
        {"root": "G", "quality": "major", "duration": 4.0}
    ]
    res = PedalPointSuspensionWeaver.weave_pedal_point_progression(
        chords_or_notes=chords,
        pedal_pitch=36,  # C2
        section_name="pre_chorus",
        suspension_type="AUTO",
        pulse_subdivision="1/4"
    )
    assert res["status"] == "APPLIED"
    assert res["pedal_pitch"] == 36
    assert res["pedal_name"] == "C2"  # 36 is C2
    assert len(res["pedal_notes"]) == 16  # 16 beats with 1/4 pulses

    # Bars 2 and 4 should have received sus4 suspensions
    trans_chords = res["transformed_chords"]
    assert trans_chords[1]["quality"] == "sus4"
    assert trans_chords[3]["quality"] == "sus4"
    assert res["suspensions_count"] >= 2
    assert res["harmonic_tension_score"] >= 0.75


# =============================================================================
# 8. Underwater & Radio Acoustic Sweep Transition Generator Tests
# =============================================================================

def test_underwater_sweep_generator():
    """Verifies exponential LPF dive down to 450 Hz with reverb wash and instant reset."""
    sweep = UnderwaterRadioSweepGenerator.generate_underwater_sweep(
        drop_start_beat=32.0,
        duration_beats=4.0,
        mode="UNDERWATER",
        reverb_intensity=0.45
    )
    assert sweep["status"] == "SWEEP_GENERATED"
    assert sweep["mode"] == "UNDERWATER"
    assert sweep["start_beat"] == 28.0
    assert sweep["drop_start_beat"] == 32.0

    lpf_curve = sweep["filter_cutoff_envelope"]
    rev_curve = sweep["reverb_wet_envelope"]

    # Starts open (20kHz), plunges to ~450Hz, snaps back to 20kHz on beat 32
    assert lpf_curve[0]["frequency_hz"] >= 19000.0
    assert lpf_curve[-2]["frequency_hz"] <= 500.0
    assert lpf_curve[-1]["frequency_hz"] == 20000.0

    # Reverb rises up to ~45%, drops to 0% at drop
    assert rev_curve[0]["wet_percent"] == 0.0
    assert rev_curve[-2]["wet_percent"] >= 40.0
    assert rev_curve[-1]["wet_percent"] == 0.0


def test_radio_sweep_generator():
    """Verifies telephone/radio mode produces bandpass collapse (450Hz HPF, 3200Hz LPF)."""
    sweep = UnderwaterRadioSweepGenerator.generate_underwater_sweep(
        drop_start_beat=32.0,
        duration_beats=4.0,
        mode="RADIO"
    )
    assert sweep["mode"] == "RADIO"
    hpf_curve = sweep["highpass_cutoff_envelope"]
    assert len(hpf_curve) > 0
    assert hpf_curve[-2]["frequency_hz"] >= 400.0
    assert hpf_curve[-1]["frequency_hz"] == 20.0  # Reset


# =============================================================================
# 9. Copilot Guided Session Phase Integrations Tests
# =============================================================================

def test_phase_6_commercial_enrichments_with_new_engines():
    """Verifies Phase 6 enrichments execute MetricDisplacer, HiHatMutator, and PedalPointWeaver."""
    session = CopilotGuidedSession()
    conn = MockAbletonAdapter()

    session.data["tracks"] = [
        {"index": 0, "name": "Vocal", "role": "VOCALS", "notes": [{"pitch": 64, "start_time": 0.0, "duration": 1.5}]},
        {"index": 1, "name": "Bass", "role": "BASS", "notes": [
            {"pitch": 36, "start_time": 0.0, "duration": 1.0},
            {"pitch": 36, "start_time": 4.0, "duration": 1.0}
        ]},
        {"index": 2, "name": "Drums", "role": "DRUMS", "notes": [
            {"pitch": 42, "start_time": 0.0, "duration": 0.25},
            {"pitch": 42, "start_time": 7.0, "duration": 0.25}
        ]},
        {"index": 3, "name": "Keys", "role": "KEYS", "notes": [
            {"pitch": 60, "start_time": 0.0, "duration": 2.0}
        ]}
    ]
    session.data["sections"] = [{"name": "Verse", "bars": 8}]
    session.data["key"] = "C"
    session.data["scale"] = "major"

    enrichments = Phase6CompositionHandler.apply_commercial_arrangement_enrichments(session, conn)

    assert "metric_displacement" in enrichments
    assert "hihat_mutations" in enrichments
    assert "pedal_suspensions" in enrichments

    assert "metric_displacement" in session.data
    assert "hihat_mutations" in session.data
    assert "pedal_suspensions" in session.data


def test_copilot_global_intercepts_phase4_queries():
    """Verifies conversational intercepts for all 8 Phase 4 systems."""
    session = CopilotGuidedSession()
    session.data["tracks"] = [
        {"index": 0, "name": "Kick", "role": "KICK"},
        {"index": 1, "name": "Bass", "role": "BASS"},
        {"index": 2, "name": "Keys", "role": "KEYS"},
        {"index": 3, "name": "Lead Vocal", "role": "VOCALS"}
    ]

    # 1. Metric Displacement
    r_disp = session.handle_input("ver desplazamiento metrico")
    assert r_disp["status"] == "METRIC_DISPLACEMENT_SUMMARY"

    # 2. Z-Plane Depth
    r_depth = session.handle_input("ver profundidad z")
    assert r_depth["status"] == "Z_PLANE_DEPTH_SUMMARY"
    assert "depth_distribution" in r_depth["z_plane_depth"]

    # 3. Sub-to-Stereo Morph
    r_morph = session.handle_input("ver apertura de bajo")
    assert r_morph["status"] == "SUB_STEREO_MORPH_SUMMARY"
    assert "sub_stereo_morph" in r_morph

    # 4. Foley Bed
    r_foley = session.handle_input("ver textura foley")
    assert r_foley["status"] == "FOLEY_BED_SUMMARY"
    assert "foley_bed" in r_foley

    # 5. Crest Factor
    r_crest = session.handle_input("ver factor de cresta")
    assert r_crest["status"] == "CREST_FACTOR_SUMMARY"
    assert "crest_factor_audit" in r_crest

    # 6. Hi-Hat Mutation
    r_hh = session.handle_input("ver mutacion hi hats")
    assert r_hh["status"] == "HIHAT_MUTATION_SUMMARY"
    assert "hihat_mutations" in r_hh

    # 7. Pedal Point Suspension
    r_pedal = session.handle_input("ver nota pedal")
    assert r_pedal["status"] == "PEDAL_SUSPENSION_SUMMARY"
    assert "pedal_suspensions" in r_pedal

    # 8. Underwater Sweep
    r_under = session.handle_input("ver filtro underwater")
    assert r_under["status"] == "UNDERWATER_SWEEP_SUMMARY"
    assert "underwater_sweep" in r_under

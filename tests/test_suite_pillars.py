# tests/test_suite_pillars.py
"""
Integration and Unit Test Suite for AbletonEngine Suite 2.0 (Pilares 1 a 5).
Verifies the complete autonomous production layer.
"""

import pytest
from unittest.mock import MagicMock
from pathlib import Path
import json

# -------------------------------------------------------------------------
# PILAR I: ORQUESTACIÓN, TRANSPORTE Y AUTOMATIZACIÓN
# -------------------------------------------------------------------------

def test_batch_composer():
    from engine.arrangement.batch_composer import BatchComposer
    from engine.adapters.mock_adapter import MockAbletonAdapter

    adapter = MockAbletonAdapter()
    session_data = {
        "tracks": [
            {"index": 0, "name": "Drums", "role": "DRUMS"},
            {"index": 1, "name": "Bass", "role": "BASS", "chopping_mode": True, "slices_count": 16}
        ],
        "sections": [
            {"name": "Intro", "bars": 8},
            {"name": "Drop 1", "bars": 16}
        ]
    }
    comp_data = {
        "composition": {
            "drums": {
                "intro": [{"pitch": 36, "start_time": 0.0, "duration": 0.5, "velocity": 120}],
                "drop 1": [{"pitch": 38, "start_time": 1.0, "duration": 0.5, "velocity": 125}]
            },
            "bass": {
                "intro": [{"pitch": 72, "start_time": 0.0, "duration": 0.5, "velocity": 100}],  # will be clamped
                "drop 1": [{"pitch": 36, "start_time": 0.0, "duration": 1.0, "velocity": 110}]
            }
        }
    }

    res = BatchComposer.compose_batch(adapter, session_data, comp_data, duplicate_to_arrangement=True)
    assert res["status"] == "SUCCESS"
    assert res["clips_created"] == 4
    assert res["notes_injected"] == 4
    assert res["tracks_touched"] == [0, 1]

    # Verify chopping clamping on Bass track Intro note (pitch 72 clamped into [36..51])
    bass_intro_notes = adapter.get_clip_notes(1, 0)
    assert len(bass_intro_notes) == 1
    assert 36 <= bass_intro_notes[0]["pitch"] < (36 + 16)


def test_declarative_automation_weaver():
    from engine.arrangement.automation.weaver import ArrangementAutomationWeaver

    vacuum = ArrangementAutomationWeaver.generate_pre_drop_vacuum(start_bar=15.0, duration_bars=1.0)
    assert len(vacuum) == 5
    # The beat just before arrival should be 0.0 (vacuum silence)
    assert vacuum[2]["value"] == 0.0
    assert vacuum[3]["value"] == 0.0
    assert vacuum[4]["value"] == 0.85

    pumping = ArrangementAutomationWeaver.generate_pumping_sidechain(start_bar=0.0, duration_bars=2.0)
    assert len(pumping) == 2 * 4 * 3  # 2 bars * 4 beats * 3 points per beat
    assert pumping[0]["value"] == 0.15  # ducked on downbeat


def test_transport_manager_cue_points():
    from engine.arrangement.transport_manager import TransportManager
    mock_conn = MagicMock()
    mock_conn.send_command.return_value = {"cue_points": []}

    sections = [
        {"name": "Intro", "bars": 8},
        {"name": "Drop 1", "bars": 16},
        {"name": "Outro", "bars": 8}
    ]
    sync_res = TransportManager.sync_section_cue_points(mock_conn, sections)
    assert sync_res["status"] == "SUCCESS"
    assert sync_res["cue_points_created"] == 3
    assert sync_res["total_bars"] == 32.0

    # Test conversational navigation
    nav_res = TransportManager.jump_to_section(mock_conn, sections, target="Drop 1", start_playback=True)
    assert nav_res["status"] == "NAVIGATED"
    assert nav_res["target_beat"] == 32.0  # 8 bars * 4 = 32 beats
    mock_conn.send_command.assert_any_call("jump_to_cue_point", {"target": 32.0})
    mock_conn.send_command.assert_any_call("start_playback", {})


def test_bus_routing_topology():
    from engine.mix.bus_routing import BusRoutingManager

    tracks = [
        {"index": 0, "name": "Kick", "role": "DRUMS"},
        {"index": 1, "name": "Snare", "role": "DRUMS"},
        {"index": 2, "name": "808 Bass", "role": "BASS"},
        {"index": 3, "name": "Saw Lead", "role": "LEAD"},
        {"index": 4, "name": "E-Piano", "role": "KEYS"}
    ]
    topology = BusRoutingManager.analyze_bus_topology(tracks)
    assert "DRUMS BUS" in topology
    assert len(topology["DRUMS BUS"]) == 2
    assert "BASS BUS" in topology
    assert "SYNTHS BUS" in topology

    res = BusRoutingManager.setup_submix_buses(conn=None, tracks=tracks)
    assert res["status"] == "SUCCESS"
    assert res["buses_count"] >= 3


# -------------------------------------------------------------------------
# PILAR II: INSTRUMENTOS, SLICING Y TIMBRES
# -------------------------------------------------------------------------

def test_simpler_slicer_clamping():
    from engine.instruments.simpler_slicer import SimplerSlicer

    raw_notes = [
        {"pitch": 72, "start_time": 0.0},
        {"pitch": 84, "start_time": 1.0},
        {"pitch": 36, "start_time": 2.0}
    ]
    clamped = SimplerSlicer.clamp_notes_to_slices(raw_notes, slices_count=16)
    for n in clamped:
        assert 36 <= n["pitch"] < (36 + 16)


def test_macro_standardizer_mapping():
    from engine.sound.macro_standardizer import MacroStandardizer

    assert MacroStandardizer.resolve_macro_number("cutoff") == 1
    assert MacroStandardizer.resolve_macro_number("resonance") == 2
    assert MacroStandardizer.resolve_macro_number("drive") == 3
    assert MacroStandardizer.resolve_macro_number("space") == 7

    mock_conn = MagicMock()
    mock_conn.send_command.return_value = {"status": "ok"}

    res = MacroStandardizer.set_macro_parameter(mock_conn, track_index=2, macro_ident="drive", value=0.65)
    assert res["status"] == "SUCCESS"
    assert res["macro_number"] == 3
    assert res["value"] == 0.65


def test_sample_cache_categorization():
    from engine.indexer.sample_cache import SampleCacheManager

    assert SampleCacheManager.categorize_filename("vocal_hook_128bpm.wav") == "VOCALS"
    assert SampleCacheManager.categorize_filename("heavy_sub_808.wav") == "BASS"
    assert SampleCacheManager.categorize_filename("tight_snare_hit.wav") == "DRUMS"
    assert SampleCacheManager.categorize_filename("vinyl_noise_bed.wav") == "FOLEY"


def test_vital_patch_generator(tmp_path):
    from engine.presets.vital_patch_generator import VitalPatchGenerator

    patch = VitalPatchGenerator.create_patch_dict(preset_name="Terror_Growl", sound_type="BASS_GROWL")
    assert patch["preset_name"] == "Terror_Growl"
    assert patch["settings"]["osc_1_on"] == 1.0
    assert patch["settings"]["polyphony"] == 1

    saved = VitalPatchGenerator.save_vital_preset("Laser_Lead", sound_type="LEAD", output_dir=tmp_path)
    assert saved.exists()
    assert saved.suffix == ".vital"


# -------------------------------------------------------------------------
# PILAR III: GANANCIA, MEZCLA Y DINÁMICA
# -------------------------------------------------------------------------

def test_auto_gain_staging():
    from engine.mix.auto_gain_staging import AutoGainStaging

    assert 0.45 <= AutoGainStaging.get_role_target_volume("DRUMS") <= 0.50
    assert 0.43 <= AutoGainStaging.get_role_target_volume("BASS") <= 0.48
    assert 0.28 <= AutoGainStaging.get_role_target_volume("PAD") <= 0.35

    tracks = [{"index": 0, "role": "DRUMS"}, {"index": 1, "role": "BASS"}]
    res = AutoGainStaging.apply_session_gain_staging(conn=None, tracks=tracks)
    assert res["status"] == "SUCCESS"
    assert res["tracks_staged"] == 2


def test_auto_sidechain_setup():
    from engine.mix.sidechain import AutoSidechainDucker

    tracks = [
        {"index": 0, "name": "Kick 808", "role": "DRUMS"},
        {"index": 1, "name": "Sub Bass", "role": "BASS"},
        {"index": 2, "name": "Warm Pad", "role": "PAD"}
    ]
    mock_conn = MagicMock()
    mock_conn.send_command.return_value = {"status": "ok"}

    res = AutoSidechainDucker.auto_setup_session_sidechain(mock_conn, tracks)
    assert res["status"] == "SUCCESS"
    assert res["kick_track_index"] == 0
    assert res["targets_count"] == 2


def test_spectral_masking_auditor():
    from engine.mix.spectral_masking import SpectralMaskingAuditor

    tracks = [
        {"index": 0, "name": "Kick", "role": "DRUMS"},
        {"index": 1, "name": "Sub", "role": "BASS"},
        {"index": 2, "name": "Pad", "role": "PAD"},
        {"index": 3, "name": "Keys", "role": "KEYS"}
    ]
    report = SpectralMaskingAuditor.audit_session_masking(tracks)
    assert report["status"] == "ANALYZED"
    assert report["conflicts_count"] >= 1
    # Check that Pad and Keys get recommended high-pass cuts
    actions = [c["action"] for c in report["recommended_corrections"]]
    assert "HIGH_PASS_FILTER" in actions


def test_auto_lufs_calibrator():
    from engine.mastering.auto_lufs_calibrator import AutoLUFSCalibrator

    # Measured at -14.0 LUFS, Target at -6.0 LUFS -> requires +8.0 dB boost
    cal = AutoLUFSCalibrator.calculate_calibration(measured_lufs=-14.0, target_lufs=-6.0, max_dbtp=-0.3)
    assert cal["is_compliant"] is False
    assert cal["lufs_delta"] == 8.0
    assert cal["recommended_gain_adjustment_db"] == 8.0
    assert cal["projected_lufs"] == -6.0


# -------------------------------------------------------------------------
# PILAR IV: MICRO-TIMING, GROOVE Y TEXTURAS
# -------------------------------------------------------------------------

def test_groove_templates():
    from engine.music.groove_templates import GrooveTemplateEngine

    straight_notes = [
        {"pitch": 36, "start_time": 0.0, "duration": 0.25, "velocity": 100},
        {"pitch": 38, "start_time": 0.25, "duration": 0.25, "velocity": 100},
        {"pitch": 36, "start_time": 0.50, "duration": 0.25, "velocity": 100},
        {"pitch": 38, "start_time": 0.75, "duration": 0.25, "velocity": 100}
    ]
    mpc_grooved = GrooveTemplateEngine.apply_groove(straight_notes, template_name="AKAI_MPC3000", intensity=1.0)
    # The 2nd note (at 0.25) should be delayed by swing
    assert mpc_grooved[1]["start_time"] > 0.25
    # The 1st note should have velocity accent
    assert mpc_grooved[0]["velocity"] > 100


def test_procedural_drum_fills():
    from engine.music.procedural_fills import ProceduralDrumFillEngine

    fills = ProceduralDrumFillEngine.generate_turnaround_fill(total_bars=16.0, fill_bars=1.0, include_pre_drop_vacuum=True)
    assert len(fills) > 4
    # Highest tom or snare present in fill
    pitches = [n["pitch"] for n in fills]
    assert 38 in pitches  # Snare
    assert 50 in pitches or 47 in pitches  # Toms


def test_call_and_response_bass():
    from engine.music.call_and_response import CallAndResponseOrchestrator

    riff = [
        {"pitch": 36, "start_time": 0.0, "duration": 0.5},   # Low downbeat -> CALL
        {"pitch": 60, "start_time": 0.75, "duration": 0.25},  # High syncopated -> RESPONSE
        {"pitch": 36, "start_time": 1.0, "duration": 0.5},   # Low -> CALL
        {"pitch": 62, "start_time": 1.75, "duration": 0.25}   # High -> RESPONSE
    ]
    split = CallAndResponseOrchestrator.split_phrase_into_call_and_response(
        melody_notes=riff,
        call_track_index=1,
        response_track_index=2,
        sub_track_index=3
    )
    assert len(split[1]) == 2  # Call
    assert len(split[2]) == 2  # Response
    assert len(split[3]) == 2  # Sub


def test_foley_generator_recipe():
    from engine.sound.foley_generator import FoleyGenerator

    rec = FoleyGenerator.get_foley_recipe("VINYL_CRACKLE")
    assert rec["bandpass_low"] == 300
    assert rec["gain_db"] == -22.0


# -------------------------------------------------------------------------
# PILAR V: RESILIENCIA, CALIDAD Y ERGONOMÍA
# -------------------------------------------------------------------------

def test_clean_slate_reset():
    from engine.session.clean_slate import CleanSlateManager

    mock_conn = MagicMock()
    mock_conn.send_command.return_value = {"status": "ok"}

    res = CleanSlateManager.reset_session(mock_conn, session_data={"tracks": []}, target_bpm=140.0)
    assert res["status"] == "RESET_COMPLETE"
    assert res["target_bpm"] == 140.0


def test_clip_healer_repairs():
    from engine.session.clip_healer import ClipHealer

    drum_trk = {"index": 0, "role": "DRUMS"}
    # Drums in octave 3 (pitches 60-75)
    bad_drum_notes = [{"pitch": 60, "start_time": 0.0}, {"pitch": 62, "start_time": 1.0}]
    healed, repairs = ClipHealer.audit_and_heal_track_notes(drum_trk, bad_drum_notes)
    assert len(repairs) >= 1
    assert healed[0]["pitch"] == 36
    assert healed[1]["pitch"] == 38

    chop_trk = {"index": 1, "role": "VOCALS", "chopping_mode": True, "slices_count": 16}
    bad_chop_notes = [{"pitch": 80, "start_time": 0.0}]
    healed_c, rep_c = ClipHealer.audit_and_heal_track_notes(chop_trk, bad_chop_notes)
    assert 36 <= healed_c[0]["pitch"] < (36 + 16)


def test_export_package_manifest(tmp_path):
    from engine.production.export_package import ReleasePackageExporter

    stems = [{"name": "01_Drums", "file": "drums.wav"}, {"name": "02_Bass", "file": "bass.wav"}]
    manifest = ReleasePackageExporter.generate_release_manifest(
        song_title="Cyber Bass",
        artist="AI Executive Producer",
        bpm=140.0,
        key="F",
        scale="Minor",
        genre="Brostep",
        stems_list=stems,
        master_lufs=-6.0,
        output_dir=tmp_path
    )
    assert manifest["title"] == "Cyber Bass"
    assert manifest["delivery_specs"]["loudness_integrated_lufs"] == -6.0
    assert (tmp_path / "release_manifest.json").exists()


def test_color_palette_manager():
    from engine.session.color_palette import ColorPaletteManager

    assert ColorPaletteManager.get_role_color_index("DRUMS") == 60   # Orange
    assert ColorPaletteManager.get_role_color_index("BASS") == 13    # Yellow
    assert ColorPaletteManager.get_role_color_index("LEAD") == 27    # Cyan
    assert ColorPaletteManager.get_role_color_index("VOCALS") == 49  # Magenta

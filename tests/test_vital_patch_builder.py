# tests/test_vital_patch_builder.py
import pytest
import os
import json
import tempfile
from pathlib import Path

from engine.sound.vital.models import (
    VitalPresetSpec,
    VitalPresetStyle,
    VitalOscillatorSpec,
    VitalFilterSpec
)
from engine.sound.vital.builder import VitalPatchBuilder
from engine.sound.vital.file_manager import VitalPresetManager

def test_build_reese_bass():
    preset = VitalPatchBuilder.build_reese_bass(
        sub_weight=0.85,
        detune_amount=4.0,
        filter_cutoff=68.0,
        drive=8.0,
        name="Test_Reese"
    )
    assert preset.preset_name == "Test_Reese"
    assert preset.preset_style == VitalPresetStyle.BASS
    assert len(preset.oscillators) == 3
    assert preset.oscillators[0].unison_voices == 5
    assert preset.oscillators[1].unison_voices == 7
    assert preset.oscillators[2].unison_voices == 1
    assert preset.oscillators[2].destination == 3  # Direct out for sub
    assert preset.filters[0].cutoff == 68.0
    assert preset.filters[0].drive == 8.0
    assert preset.effects.distortion_on is True
    assert preset.effects.chorus_on is True
    assert len(preset.modulations) >= 4
    assert preset.macro1 == "CUTOFF"
    assert preset.macro2 == "DRIVE"

def test_build_hard_808():
    preset = VitalPatchBuilder.build_hard_808(
        distortion_drive=14.0,
        glide_time=0.09,
        pitch_decay=0.035,
        name="Test_808"
    )
    assert preset.preset_name == "Test_808"
    assert preset.preset_style == VitalPresetStyle.BASS
    assert preset.oscillators[0].transpose == -24
    assert preset.effects.distortion_on is True
    assert preset.effects.distortion_drive == 14.0
    assert preset.effects.distortion_type == 1  # Hard clip
    assert preset.settings.get("portamento_time") == 0.09
    assert preset.macro1 == "PUNCH"
    assert preset.macro3 == "GLIDE"

def test_build_neo_soul_keys():
    preset = VitalPatchBuilder.build_neo_soul_keys(
        warmth=0.8,
        tremolo_rate=4.5,
        chorus_depth=0.4,
        name="Test_Rhodes"
    )
    assert preset.preset_name == "Test_Rhodes"
    assert preset.preset_style == VitalPresetStyle.KEYS
    assert preset.effects.chorus_on is True
    assert preset.effects.delay_on is True
    assert preset.effects.reverb_on is True
    assert preset.lfos[0].frequency == 4.5
    assert preset.macro1 == "WARMTH"
    assert preset.macro2 == "TREMOLO"

def test_build_lead_hook():
    preset = VitalPatchBuilder.build_lead_hook(
        brightness=0.9,
        portamento=0.06,
        ping_pong_delay=0.35,
        name="Test_Lead"
    )
    assert preset.preset_name == "Test_Lead"
    assert preset.preset_style == VitalPresetStyle.LEAD
    assert preset.oscillators[0].unison_voices == 7
    assert preset.filters[0].model == 2  # Ladder
    assert preset.effects.delay_on is True
    assert preset.effects.delay_style == 2  # Ping Pong
    assert preset.macro1 == "BRIGHT"

def test_build_custom():
    spec = {
        "name": "Synthwave_Pluck",
        "style": "Pluck",
        "osc1_unison": 4,
        "osc1_detune": 1.8,
        "cutoff": 95.0,
        "drive": 3.0,
        "delay": True,
        "reverb": True,
        "macro1": "PLUCK_DECAY"
    }
    preset = VitalPatchBuilder.build_custom(spec)
    assert preset.preset_name == "Synthwave_Pluck"
    assert preset.preset_style == VitalPresetStyle.PLUCK
    assert preset.oscillators[0].unison_voices == 4
    assert preset.filters[0].cutoff == 95.0
    assert preset.effects.delay_on is True
    assert preset.effects.reverb_on is True
    assert preset.macro1 == "PLUCK_DECAY"

def test_preset_manager_serialization_and_save():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        user_dir = tmp_path / "user"
        engine_dir = tmp_path / "engine"
        
        manager = VitalPresetManager(user_dir=user_dir, engine_dir=engine_dir)
        
        preset_spec = VitalPatchBuilder.build_reese_bass(name="Unit_Test_Reese")
        result = manager.save_preset(preset_spec)
        
        assert "engine_path" in result
        assert "user_path" in result
        assert os.path.exists(result["engine_path"])
        assert os.path.exists(result["user_path"])
        
        # Verify JSON content
        with open(result["engine_path"], "r", encoding="utf-8") as f:
            data = json.load(f)
            
        assert data["preset_style"] == "Bass"
        assert data["macro1"] == "CUTOFF"
        assert "settings" in data
        assert data["settings"]["osc_1_unison_voices"] == 5.0
        assert data["settings"]["distortion_on"] == 1.0
        assert len(data["settings"]["modulations"]) >= 4

        # Verify listing
        presets = manager.list_presets(category="Bass")
        assert len(presets) >= 1
        assert presets[0]["name"] == "Unit_Test_Reese"
        assert presets[0]["style"] == "Bass"
        assert len(presets[0]["macros"]) == 4

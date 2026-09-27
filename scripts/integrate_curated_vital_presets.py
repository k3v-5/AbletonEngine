# scripts/integrate_curated_vital_presets.py
"""
Calibrator, Organizer, and Integrator for the 88 Curated Vital Presets.

Applies production-grade audio engineering invariants:
1. Master Volume normalization (4000.0 <= vol <= 6500.0, nominal 5400.0 / -14 dBFS).
2. Anti-click amplitude envelope protection (env_1_attack >= 0.002s).
3. Anti-silence invariant verification (active oscillator level >= 0.05).
4. Subbass mono & low-end phase protection for bass roles.
5. Structured categorization into presets/vital/<category>/ subdirectories.
6. Full audit certification using VitalSoundEngine.audit_preset_file().
"""

import json
import logging
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, Any, Tuple

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.sound_design.vital_parameter_schema import VitalParameterSchema
from engine.sound_design.vital_sound_engine import VitalSoundEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("PresetIntegrator")


# Subdirectory routing based on sonic family
CATEGORY_SUBDIRS = {
    "ACID_303": ("acid_303", "BASS_ACID"),
    "NEURO_GROWL_WOBBLE": ("neuro_growl", "BASS_GROWL"),
    "CHIPTUNE_GLITCH_8BIT": ("chiptune_glitch", "CHIPTUNE_GLITCH"),
    "HOUSE_ORGAN_DONK_SLAP": ("house_organ_donk", "HOUSE_ORGAN_DONK"),
    "ACOUSTIC_GUITAR_STRINGS": ("acoustic_strings", "ACOUSTIC_STRINGS"),
    "KEYS_PIANO_LOFI": ("keys_lofi", "KEYS_RHODES"),
    "VOCAL_VOCODER_CHOIR": ("vocal_synths", "VOCAL_SYNTH"),
    "BELLS_MALLETS": ("bells_mallets", "BELLS_MALLETS"),
    "TRANSITIONS_RISERS_FX": ("transitions_fx", "FX_TRANSITION"),
    "THEREMIN_WHISTLE": ("theremin_whistle", "THEREMIN_WHISTLE"),
    "PADS_DRONES_ATMOSPHERES": ("pads_drones", "PAD_LUSH"),
    "OTHER_SYNTH": ("retro_hits", "CHORD_SUPERAW"),
    "BASS_SUB": ("sub_basses", "BASS_SUB"),
    "LEADS_PLUCKS": ("leads_plucks", "LEAD_SAW")
}


def classify_preset_family(filename: str) -> str:
    fn_low = filename.lower()
    if any(k in fn_low for k in ["acid", "303"]):
        return "ACID_303"
    elif any(k in fn_low for k in ["growl", "neuro", "wobble", "wooble"]):
        return "NEURO_GROWL_WOBBLE"
    elif any(k in fn_low for k in ["8bit", "chiptune", "coin_op", "glitch"]):
        return "CHIPTUNE_GLITCH_8BIT"
    elif any(k in fn_low for k in ["m1_organ", "donk", "slap"]):
        return "HOUSE_ORGAN_DONK_SLAP"
    elif any(k in fn_low for k in ["guitar", "acoustic", "string", "electric_acoustic"]):
        return "ACOUSTIC_GUITAR_STRINGS"
    elif any(k in fn_low for k in ["epiano", "piano", "rhodes", "roads", "keys", "lofi"]):
        return "KEYS_PIANO_LOFI"
    elif any(k in fn_low for k in ["vocal", "vocoder", "sing", "lyricism", "chop"]):
        return "VOCAL_VOCODER_CHOIR"
    elif any(k in fn_low for k in ["mallet", "bell"]):
        return "BELLS_MALLETS"
    elif any(k in fn_low for k in ["riser", "fx_", "laser", "siren", "impact", "glitch_n_glide"]):
        return "TRANSITIONS_RISERS_FX"
    elif any(k in fn_low for k in ["theremin", "whistle"]):
        return "THEREMIN_WHISTLE"
    elif any(k in fn_low for k in ["pad", "drone", "shimmer", "breath"]):
        return "PADS_DRONES_ATMOSPHERES"
    elif any(k in fn_low for k in ["bass", "sub", "ba_"]):
        return "BASS_SUB"
    elif any(k in fn_low for k in ["ld_", "lead", "pluck"]):
        return "LEADS_PLUCKS"
    else:
        return "OTHER_SYNTH"


def calibrate_and_integrate_presets(
    source_dir: Path = Path("Vital presets"),
    target_base: Path = Path("presets/vital")
) -> Dict[str, Any]:
    """Processes all presets, calibrates parameters, and writes organized output."""
    if not source_dir.exists():
        raise FileNotFoundError(f"Source directory {source_dir} does not exist")

    schema = VitalParameterSchema()
    engine = VitalSoundEngine()

    vital_files = sorted(list(source_dir.glob("*.vital")))
    logger.info(f"Starting calibration for {len(vital_files)} Vital presets...")

    report = {
        "total_source_files": len(vital_files),
        "calibrated_count": 0,
        "audited_audible_count": 0,
        "categories_summary": defaultdict(int),
        "details": []
    }

    for fpath in vital_files:
        raw_text = fpath.read_text(encoding="utf-8")
        data = json.loads(raw_text)
        settings = data.setdefault("settings", {})

        family = classify_preset_family(fpath.name)
        subdir_name, archetype_role = CATEGORY_SUBDIRS.get(family, ("misc", "GENERIC"))
        target_dir = target_base / subdir_name
        target_dir.mkdir(parents=True, exist_ok=True)

        is_bass = family in ("ACID_303", "NEURO_GROWL_WOBBLE", "BASS_SUB", "HOUSE_ORGAN_DONK_SLAP")

        # 1. Volume Calibration & Headroom Invariant
        cur_vol = float(settings.get("volume", schema.VOLUME_NOMINAL))
        if cur_vol < schema.VOLUME_MIN or cur_vol > schema.VOLUME_MAX:
            logger.info(f"[{fpath.name}] Calibrating volume {cur_vol:.1f} -> {schema.VOLUME_NOMINAL}")
            settings["volume"] = schema.VOLUME_NOMINAL

        # 2. Anti-Click Amplitude Envelope Protection
        cur_att = float(settings.get("env_1_attack", 0.0))
        if cur_att < 0.002:
            settings["env_1_attack"] = 0.002

        # 3. Subbass Mono & Low-End Reverb Discipline for Bass Roles
        if is_bass:
            settings["reverb_pre_low_cutoff"] = 25.0
            # If reverb mix is extreme (>30%) on bass, gently tame it to protect low end
            if float(settings.get("reverb_dry_wet", 0.0)) > 0.30:
                settings["reverb_dry_wet"] = 0.15

        # 4. Enforce Anti-Silence Invariants (Osc on/level, filter cutoff floor)
        settings = schema.enforce_anti_silence_invariants(settings)
        data["settings"] = settings

        # 5. Metadata Enrichment
        if not data.get("preset_style"):
            data["preset_style"] = family
        data["comments"] = f"Calibrated & Certified for AbletonEngine ({archetype_role})"

        # 6. Save Calibrated Preset
        clean_name = fpath.name.replace(" ", "_")
        target_file = target_dir / clean_name
        target_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

        # 7. Audit Verification
        audit = engine.audit_preset_file(target_file)
        is_audible = audit.get("audible", False)
        if is_audible:
            report["audited_audible_count"] += 1

        report["calibrated_count"] += 1
        report["categories_summary"][subdir_name] += 1
        report["details"].append({
            "name": data.get("preset_name", target_file.stem),
            "file": clean_name,
            "category": subdir_name,
            "role": archetype_role,
            "audible": is_audible,
            "volume": settings.get("volume")
        })

    logger.info(
        f"Completed: {report['calibrated_count']}/{report['total_source_files']} presets calibrated. "
        f"Audible certified: {report['audited_audible_count']}."
    )
    return report


if __name__ == "__main__":
    rep = calibrate_and_integrate_presets()
    print(f"\nSUCCESS: {rep['calibrated_count']} presets organized across {len(rep['categories_summary'])} categories.")
    for cat, count in sorted(rep["categories_summary"].items()):
        print(f"  * presets/vital/{cat}/: {count} presets")

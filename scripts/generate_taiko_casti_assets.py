# scripts/generate_taiko_casti_assets.py
"""
Generates the 20 High-Fidelity UHTS Continuous Audio Pad Textures
specifically tuned for the Taiko x Casti Hybrid Song in F Minor Phrygian @ 100.0 BPM.

Each texture corresponds to one of the 20 scenes/sections of the 80-bar composition.
"""

import sys
import os
from pathlib import Path
import soundfile as sf
import numpy as np

# Ensure project root in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from engine.sound_design.piano_chord_generator import generate_source_piano_chord
from engine.sound_design.reprocessing_pipeline import AudioReprocessingPipeline, CATALOG_METADATA


def generate_taiko_casti_assets(output_dir: Path = None) -> list:
    if output_dir is None:
        output_dir = root_dir / "cache" / "taiko_casti"
    output_dir.mkdir(parents=True, exist_ok=True)

    pipeline = AudioReprocessingPipeline()

    # 1. Generate 16-beat prolonged chord at 100 BPM (9.6 seconds)
    bpm = 100.0
    key = "F"
    scale = "Minor"
    duration_sec = 16.0 * (60.0 / bpm)  # 9.6s
    
    source_path = output_dir / "taiko_casti_source_chord.wav"
    print(f"[TAIKO x CASTI] Generating source sustained chord: {source_path.name} ({duration_sec:.1f}s at {bpm} BPM)...")
    generate_source_piano_chord(str(source_path), duration_sec=duration_sec, sample_rate=44100)

    # 2. Mutate across all 20 UHTS algorithms
    assets = []
    print(f"\n[TAIKO x CASTI] Mutating 20 UHTS Pad Textures (Fm Phrygian @ 100 BPM)...")
    for item in CATALOG_METADATA:
        idx = item["index"]
        name = item["name"]
        filename = f"taiko_casti_uhts_{idx:02d}_{item['registry_name'].lower()}.wav"
        dest_file = output_dir / filename
        
        print(f"  [{idx:02d}/20] Processing {name} -> {filename}...")
        res = pipeline.execute_mutation(
            source_wav_path=str(source_path),
            technique_selector=idx,
            key=key,
            scale=scale,
            bpm=bpm,
            custom_output_filename=filename
        )
        
        assets.append({
            "index": idx,
            "name": name,
            "id": item["id"],
            "category": item["category"],
            "path": res["output_path"],
            "filename": filename,
            "duration_sec": res["duration"]
        })

    print(f"\n[TAIKO x CASTI] Successfully generated all 20 Pad assets in: {output_dir}")
    return assets


if __name__ == "__main__":
    generate_taiko_casti_assets()

# scripts/generate_taiko_shimmer_assets.py
"""
Asset Generator for Taiko Shimmer:
1. Synthesizes the original source atmospheric pad in D Minor (105 BPM).
2. Reprocesses the source pad through UHTS Technique #06 (Pitch-Shifted Shimmer Diffusion).
3. Stores both in cache/taiko_shimmer and cache/resampled_mutations.
"""

import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import soundfile as sf
import numpy as np
from engine.sound_design.pad_sound_generator import generate_source_ambient_pad
from engine.sound_design.reprocessing_pipeline import AudioReprocessingPipeline


def generate_assets():
    print("=" * 70)
    print("=== GENERATING TAIKO SHIMMER ASSETS (ORIGINAL PAD + UHTS #06) ===")
    print("=" * 70)

    cache_dir = root_dir / "cache" / "taiko_shimmer"
    cache_dir.mkdir(parents=True, exist_ok=True)

    resampled_dir = root_dir / "cache" / "resampled_mutations"
    resampled_dir.mkdir(parents=True, exist_ok=True)

    # 1. Synthesize Source Pad WAV
    source_pad_path = cache_dir / "taiko_shimmer_source_pad.wav"
    duration_sec = 16.0 * (60.0 / 105.0)  # 16 beats (4 bars) @ 105 BPM = 9.1428 sec
    print(f"\n[1/2] Synthesizing Original Atmospheric Pad in D Minor @ 105 BPM ({duration_sec:.2f}s)...")
    generate_source_ambient_pad(
        output_path=str(source_pad_path),
        duration_sec=duration_sec,
        key="D",
        scale="Minor",
        bpm=105.0
    )
    data, sr = sf.read(str(source_pad_path))
    peak = np.max(np.abs(data))
    print(f"  [OK] Source Pad generated: {source_pad_path.name}")
    print(f"       Duration: {len(data)/sr:.2f}s | SR: {sr}Hz | Peak: {peak:.3f} ({20*np.log10(peak):.1f} dBFS)")

    # 2. Execute Single Processing Mutation (Technique #06: Pitch-Shifted Shimmer Diffusion)
    print("\n[2/2] Applying UHTS Technique #06 (Pitch-Shifted Shimmer Diffusion)...")
    pipeline = AudioReprocessingPipeline(conn=None)
    mut_res = pipeline.execute_mutation(
        source_wav_path=str(source_pad_path),
        technique_selector=6,
        key="D",
        scale="Minor",
        bpm=105.0,
        custom_output_filename="taiko_shimmer_uhts_06_pitch_shimmer.wav"
    )

    output_wav = mut_res["output_path"]
    m_data, m_sr = sf.read(output_wav)
    m_peak = np.max(np.abs(m_data))
    print(f"  [OK] Shimmer Diffusion Pad created: {Path(output_wav).name}")
    print(f"       Duration: {len(m_data)/m_sr:.2f}s | Peak: {m_peak:.3f} ({20*np.log10(m_peak):.1f} dBFS)")
    print(f"       Technique: {mut_res['technique']['name']} ({mut_res['technique']['category']})")

    # Also copy or link to taiko_shimmer directory for convenient reference
    target_copy = cache_dir / "taiko_shimmer_uhts_06_pitch_shimmer.wav"
    sf.write(str(target_copy), m_data, m_sr, subtype="PCM_24")

    print("\n" + "=" * 70)
    print(" [SUCCESS] ALL ASSETS GENERATED & VERIFIED FOR TAIKO SHIMMER!")
    print("=" * 70 + "\n")
    return {
        "source_pad": str(source_pad_path.resolve()),
        "processed_pad": str(Path(output_wav).resolve()),
        "technique": mut_res["technique"]["name"],
        "key": "D",
        "scale": "Minor",
        "bpm": 105.0
    }


if __name__ == "__main__":
    generate_assets()

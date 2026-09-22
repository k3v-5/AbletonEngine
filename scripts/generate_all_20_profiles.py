# scripts/generate_all_20_profiles.py
"""
Batch Audio Generator for all 20 UHTS Profiles:
Renders physical audio assets for every profile in the Universal Harmonic Transformation Suite,
aligned with the project's CompositionalDNA (F Minor Phrygian).
"""

import os
import sys
import json
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from engine.sound_design.harmonic_transformation_suite import (
    HarmonicTransformationSuite,
    HarmonicProfile,
)
from engine.composition.compositional_dna import (
    CompositionalDNA,
    PrimaryMotif,
    MotifNote,
    HarmonicPalette,
)

def main():
    print("=== Starting UHTS 20-Profile Batch Audio Generation ===")
    
    # Define project DNA in Fa Menor Frigio (Fm Phrygian)
    dna = CompositionalDNA(
        song_id="casti_type_uhts_showcase",
        title="Casti Type 90 Percent - UHTS Showcase",
        bpm=100.0,
        primary_motif=PrimaryMotif(
            name="Phrygian Lead FM",
            notes=[
                MotifNote(pitch=65, start_time=0.0, duration=0.75, velocity=95),  # F
                MotifNote(pitch=66, start_time=1.0, duration=0.75, velocity=98),  # Gb (Tensión Frigia)
                MotifNote(pitch=65, start_time=2.0, duration=0.75, velocity=95),  # F
                MotifNote(pitch=60, start_time=3.0, duration=0.75, velocity=90),  # C
            ]
        ),
        harmonic_palette=HarmonicPalette(
            key_root="F",
            scale="phrygian"
        )
    )

    manifest = []
    
    for idx, profile in enumerate(HarmonicProfile, start=1):
        print(f"[{idx}/20] Generating asset for {profile.value}...")
        
        # Determine appropriate source instrument name based on profile family
        p_val = profile.value.lower()
        if "bass" in p_val or "growl" in p_val:
            source_inst = "FAW SubLab XL"
            target_role = "BASS"
        elif "lead" in p_val or "wavefolder" in p_val or "fuzz" in p_val or "bell" in p_val:
            source_inst = "Arturia Pigments"
            target_role = "LEAD"
        elif "vocal" in p_val:
            source_inst = "Live Vocal Chop"
            target_role = "VOCALS"
        elif "snare" in p_val or "crunch" in p_val or "bit_crusher" in p_val:
            source_inst = "Drum Buss Percussion"
            target_role = "DRUMS"
        else:
            source_inst = "Ableton Drift Keys"
            target_role = "TEXTURE_FOLEY"

        res = HarmonicTransformationSuite.transform_source_to_layer(
            source_track_index=idx,
            target_role=target_role,
            song_dna=dna,
            profile=profile,
            source_instrument_name=source_inst,
            conn=None
        )
        
        manifest.append({
            "index": idx,
            "profile": profile.value,
            "source_instrument": source_inst,
            "target_role": target_role,
            "sample_id": res["transformed_sample_id"],
            "audio_path": res["audio_path"],
            "duration_sec": res["duration_sec"],
            "description": res["description"],
        })

    manifest_path = root_dir / "cache" / "mutations" / "uhts_20_profiles_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"\n=== Successfully generated all 20 physical audio assets! ===")
    print(f"Manifest written to: {manifest_path}")

if __name__ == "__main__":
    main()

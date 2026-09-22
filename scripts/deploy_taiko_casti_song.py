# scripts/deploy_taiko_casti_song.py
"""
Deployer for Taiko x Casti Epic Hybrid Song:
Constructs the full 80-bar composition (320.0 beats @ 100 BPM) in Ableton Live 12 Suite:
1. 20 Scenes in Session View (Scenes 1 to 20).
2. 5 Dedicated Tracks:
   - [TAIKO] Master Drums (MIDI - O-Daiko, Nagado, Shime, Bachi)
   - [CASTI] 808 Sub-Bass (MIDI - Deep Fm Phrygian subline)
   - [CASTI] Phrygian Lead (MIDI - Iconic Casti lead motif)
   - [CASTI] Dark Chords (MIDI - Lush Fm9 / Gbmaj / Bbm9 / C7alt harmony)
   - [PAD] UHTS 20-Stage Audio (Audio - Continuous mutated pads #01 to #20)
3. Full Arrangement View timeline (Bar 1 to Bar 80) with 20 Locators / Cue Points.
"""

import sys
from pathlib import Path

# Add project root
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from server import get_ableton_connection
from engine.composition.taiko_casti_composer import TaikoCastiComposer


def deploy_song(conn=None):
    print("=" * 80)
    print("=== DEPLOYING TAIKO x CASTI EPIC HYBRID SONG IN ABLETON LIVE 12 SUITE ===")
    print("=" * 80)

    if conn is None:
        conn = get_ableton_connection()

    if not conn:
        print("[ERROR] Could not establish connection to Ableton Live.")
        return False

    res = TaikoCastiComposer.deploy(conn)

    if res.get("success"):
        print("\n" + "=" * 80)
        print(" [SUCCESS] TAIKO x CASTI FULL EPIC SONG DEPLOYED IN ABLETON LIVE 12!")
        print(f" - Tempo: {res.get('bpm')} BPM | Tonality: {res.get('key')} {res.get('scale')} Phrygian")
        print(f" - 20 Scenes configured in Session View with custom names and clips")
        print(f" - 80 Bars (320.0 beats) arranged across the timeline with 20 Cue Points")
        print(f" - 5 Tracks active: Taiko Drums, 808 Sub-Bass, Phrygian Lead, Dark Chords, UHTS Audio Pad")
        print(f" - All 20 UHTS Pad Resampling Textures active and evolving across the song")
        print("=" * 80 + "\n")
        return res
    else:
        print(f"[ERROR] Deployment failed: {res.get('error')}")
        return False


if __name__ == "__main__":
    deploy_song()

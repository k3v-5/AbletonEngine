# engine/music/midi/compiler.py
from typing import List, Dict, Any, Tuple
from ..models import NoteEvent, PartFingerprint

def compile_notes_to_ableton_format(notes: List[NoteEvent]) -> List[Dict[str, Any]]:
    """
    Compiles internal NoteEvent models into the exact dict format expected by AbletonMCP:
    [{"pitch": 60, "start_time": 0.0, "duration": 0.5, "velocity": 90}]
    """
    ableton_notes = []
    for n in sorted(notes, key=lambda ev: (ev.start, ev.pitch)):
        ableton_notes.append({
            "pitch": int(n.pitch),
            "start_time": round(float(n.start), 4),
            "duration": round(float(n.duration), 4),
            "velocity": max(1, min(127, int(n.velocity)))
        })
    return ableton_notes

def compute_part_fingerprint(notes: List[NoteEvent]) -> PartFingerprint:
    """Computes a statistical fingerprint for similarity measurement and duplicate detection"""
    if not notes:
        return PartFingerprint(0, {}, {}, 0.0, 0, 0, 0)

    pc_hist = {i: 0 for i in range(12)}
    rhythm_hist: Dict[str, int] = {}
    pitches = [n.pitch for n in notes]

    for n in notes:
        pc_hist[n.pitch % 12] += 1
        dur_key = str(round(n.duration, 2))
        rhythm_hist[dur_key] = rhythm_hist.get(dur_key, 0) + 1

    total_span = max(n.start + n.duration for n in notes) - min(n.start for n in notes)
    density = len(notes) / max(1.0, total_span)
    min_p = min(pitches)
    max_p = max(pitches)

    return PartFingerprint(
        note_count=len(notes),
        pitch_class_histogram=pc_hist,
        rhythm_histogram=rhythm_hist,
        density=round(density, 3),
        range_semitones=max_p - min_p,
        min_pitch=min_p,
        max_pitch=max_p
    )

def compare_fingerprints(fp1: PartFingerprint, fp2: PartFingerprint) -> Dict[str, float]:
    """Calculates multidimensional similarity metrics between two musical parts"""
    if fp1.note_count == 0 or fp2.note_count == 0:
        return {"rhythmic_similarity": 0.0, "pitch_similarity": 0.0, "overall_similarity": 0.0}

    # Pitch class cosine similarity
    dot_pc = sum(fp1.pitch_class_histogram.get(i, 0) * fp2.pitch_class_histogram.get(i, 0) for i in range(12))
    mag1 = (sum(v ** 2 for v in fp1.pitch_class_histogram.values()) ** 0.5)
    mag2 = (sum(v ** 2 for v in fp2.pitch_class_histogram.values()) ** 0.5)
    pitch_sim = dot_pc / max(1e-6, (mag1 * mag2))

    # Density similarity
    d_sim = 1.0 - min(1.0, abs(fp1.density - fp2.density) / max(0.1, max(fp1.density, fp2.density)))

    overall = 0.6 * pitch_sim + 0.4 * d_sim
    return {
        "pitch_similarity": round(float(pitch_sim), 3),
        "rhythmic_similarity": round(float(d_sim), 3),
        "overall_similarity": round(float(overall), 3)
    }

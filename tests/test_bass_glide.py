# tests/test_bass_glide.py
import pytest
from engine.music.bass.glide import BassGlideEngine, SlideMode
from engine.music.models import NoteEvent


def test_drill_octave_glide_legato():
    # 4-bar 808 pattern with sustaining notes
    notes = [
        NoteEvent(pitch=29, start=0.0, duration=1.5, velocity=120),
        NoteEvent(pitch=32, start=4.0, duration=1.5, velocity=120),
        NoteEvent(pitch=25, start=8.0, duration=1.5, velocity=120),
        NoteEvent(pitch=29, start=12.0, duration=2.0, velocity=125), # Turnaround bar
    ]

    res = BassGlideEngine.generate_808_slides(
        notes=notes,
        slide_mode=SlideMode.DRILL_OCTAVE_GLIDE,
        bend_range_semitones=12,
        glide_probability=1.0,
        turnaround_only=True
    )

    assert res["slides_applied"] >= 1
    # Legato notes should include original notes + injected slide note
    assert len(res["legato_notes"]) > len(notes)

    # Injected slide note should be +12 semitones (29 + 12 = 41)
    slide_notes = [n for n in res["legato_notes"] if n.pitch == 41]
    assert len(slide_notes) >= 1
    # Slide note start time should overlap parent note tail
    assert slide_notes[0].start > 12.0


def test_pitch_bend_points_geometry():
    notes = [
        NoteEvent(pitch=36, start=12.0, duration=2.0, velocity=120)
    ]

    res = BassGlideEngine.generate_808_slides(
        notes=notes,
        slide_mode=SlideMode.DRILL_OCTAVE_GLIDE,
        bend_range_semitones=12,
        glide_probability=1.0,
        turnaround_only=False
    )

    pts = res["pitch_bend_points"]
    assert len(pts) >= 4
    # Max pitch bend corresponds to 12 semitones (+8191)
    max_bend = max(p["value"] for p in pts)
    assert max_bend == pytest.approx(8191.0, abs=10.0)
    # Trailing point resets to 0.0
    assert pts[-1]["value"] == 0.0


def test_pitch_drop_mode():
    notes = [
        NoteEvent(pitch=36, start=12.0, duration=2.0, velocity=120)
    ]

    res = BassGlideEngine.generate_808_slides(
        notes=notes,
        slide_mode=SlideMode.PITCH_DROP,
        bend_range_semitones=12,
        glide_probability=1.0,
        turnaround_only=False
    )

    pts = res["pitch_bend_points"]
    # Downward glide has negative pitch bend value
    min_bend = min(p["value"] for p in pts)
    assert min_bend == pytest.approx(-8192.0, abs=10.0)

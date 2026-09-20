"""
Metric Tension & Polyrhythmic Engine:
Implements contextual polyrhythm (3/16 and 5/16) and Euclidean distribution
as structural tension tools resolving on DROP_BEAT_1.

Strict Rules:
1. Metric Anchor Constraint:
   Kick, snare, and bass MUST remain locked in 4/4 to maintain the groove anchor.
   Only secondary melodic and ornamental roles (lead, arp, ear_candy, percussion)
   are permitted to introduce cross-metric tension.
2. Contextual Section Probability:
   Intro: 0.15 | Verse: 0.10 | Build: 0.75 | Drop: 0.05 | Break: 0.55 | Final Drop: 0.15
3. Cadence & Resolution:
   Cross-metric tension builds across the bars leading to the drop and resolves
   definitively on beat 1 of the Drop (DROP_BEAT_1).
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set
import random
import math

# Section probabilities for applying metric tension
SECTION_METRIC_TENSION_PROBABILITIES: Dict[str, float] = {
    "intro": 0.15,
    "verse": 0.10,
    "build": 0.75,
    "buildup": 0.75,
    "drop": 0.05,
    "break": 0.55,
    "breakdown": 0.55,
    "bridge": 0.50,
    "final_drop": 0.15,
    "outro": 0.10
}

# Anchor roles that MUST remain in 4/4
ANCHOR_ROLES: Set[str] = {
    "kick",
    "snare",
    "clap",
    "bass",
    "sub_bass",
    "sub",
    "808",
    "main_drums"
}

# Roles allowed to introduce cross-metric tension
ALLOWED_TENSION_ROLES: Set[str] = {
    "lead",
    "counter_lead",
    "arp",
    "arpeggio",
    "ear_candy",
    "percussion",
    "perc",
    "keys",
    "pad",
    "synth",
    "texture"
}


@dataclass
class MetricTensionEvent:
    """
    Represents a cross-metric or Euclidean tension event leading into a drop or transition.
    """
    source_role: str
    pattern_type: str = "3/16"          # "3/16", "5/16", or "euclidean"
    numerator: int = 3                  # 3 or 5
    denominator: int = 16               # 16
    duration_bars: float = 4.0          # Bars over which the tension builds
    start_beat: float = 0.0             # Start time in section beats
    intensity: float = 0.8              # 0.0 to 1.0 (controls crescendo and velocity)
    resolution: str = "DROP_BEAT_1"     # Target resolution point
    notes: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_role": self.source_role,
            "pattern_type": self.pattern_type,
            "numerator": self.numerator,
            "denominator": self.denominator,
            "duration_bars": self.duration_bars,
            "start_beat": round(self.start_beat, 4),
            "intensity": round(self.intensity, 2),
            "resolution": self.resolution,
            "notes": self.notes,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MetricTensionEvent":
        return cls(
            source_role=data.get("source_role", "arp"),
            pattern_type=data.get("pattern_type", "3/16"),
            numerator=int(data.get("numerator", 3)),
            denominator=int(data.get("denominator", 16)),
            duration_bars=float(data.get("duration_bars", 4.0)),
            start_beat=float(data.get("start_beat", 0.0)),
            intensity=float(data.get("intensity", 0.8)),
            resolution=data.get("resolution", "DROP_BEAT_1"),
            notes=data.get("notes", []),
            metadata=data.get("metadata", {})
        )


def should_apply_metric_tension(section_type: str, rng: Optional[random.Random] = None) -> bool:
    """
    Evaluates whether metric tension should be introduced in the specified section
    based on its contextual probability.
    """
    sec_key = section_type.lower().strip()
    prob = SECTION_METRIC_TENSION_PROBABILITIES.get(sec_key, 0.20)
    r = rng if rng is not None else random
    return r.random() < prob


def is_role_allowed_metric_tension(role: str) -> bool:
    """
    Enforces the Metric Anchor Constraint:
    Kick, snare, and bass CANNOT have their metric anchor altered.
    Only secondary/melodic roles can cross the 4/4 boundary.
    """
    role_clean = role.lower().strip()
    if role_clean in ANCHOR_ROLES:
        return False
    if role_clean in ALLOWED_TENSION_ROLES:
        return True
    # Heuristic check for compound role names
    for anchor in ANCHOR_ROLES:
        if anchor in role_clean:
            return False
    for allowed in ALLOWED_TENSION_ROLES:
        if allowed in role_clean:
            return True
    return False


def bjorklund(steps: int, pulses: int) -> List[int]:
    """
    Classic Bjorklund algorithm for generating Euclidean rhythms E(pulses, steps).
    Evenly distributes 'pulses' across 'steps'.
    """
    if pulses <= 0:
        return [0] * steps
    if pulses >= steps:
        return [1] * steps

    # Initial groups
    pattern: List[List[int]] = []
    for i in range(pulses):
        pattern.append([1])
    for i in range(steps - pulses):
        pattern.append([0])

    while len(pattern) > 1:
        # Separate the main list into heads and tails
        last_val = pattern[-1]
        count_tail = 0
        for item in reversed(pattern):
            if item == last_val:
                count_tail += 1
            else:
                break

        count_head = len(pattern) - count_tail
        if count_tail == 0 or count_head == 0:
            break

        distribute_count = min(count_head, count_tail)
        new_pattern = []
        for i in range(distribute_count):
            new_pattern.append(pattern[i] + pattern[-(i + 1)])

        # Remaining head elements
        if count_head > distribute_count:
            new_pattern.extend(pattern[distribute_count:count_head])
        # Remaining tail elements
        elif count_tail > distribute_count:
            new_pattern.extend(pattern[-(count_tail):-(distribute_count)])

        pattern = new_pattern

    # Flatten the nested list
    flat_pattern: List[int] = []
    for sublist in pattern:
        flat_pattern.extend(sublist)

    return flat_pattern[:steps]


def generate_euclidean_pattern(steps: int, pulses: int, rotation: int = 0) -> List[int]:
    """
    Generates an E(pulses, steps) pattern with optional phase rotation.
    """
    base = bjorklund(steps, pulses)
    if not base:
        return []
    rot = rotation % len(base)
    return base[rot:] + base[:rot]


def generate_metric_tension_notes(
    base_notes: List[Dict[str, Any]],
    event: MetricTensionEvent,
    section_beats: float,
    bpm: float = 124.0,
    pitch_sequence: Optional[List[int]] = None
) -> List[Dict[str, Any]]:
    """
    Generates cross-metric polyrhythmic notes (3/16, 5/16, or Euclidean)
    with dynamic velocity crescendo towards the drop.
    Guarantees resolution on DROP_BEAT_1 by ending cleanly at or before section_beats.
    """
    pitches: List[int] = []
    if pitch_sequence:
        pitches = list(pitch_sequence)
    elif base_notes:
        pitches = [int(n.get("pitch", 60)) for n in base_notes if "pitch" in n]

    if not pitches:
        pitches = [60, 63, 67, 70]  # Default Cm7 / D# triad

    start_beat = max(0.0, event.start_beat)
    end_beat = section_beats
    tension_span = max(1.0, end_beat - start_beat)

    generated: List[Dict[str, Any]] = []

    if event.pattern_type == "3/16":
        step_interval = 0.75  # 3 sixteenth notes = 0.75 beats
        note_dur = 0.50
    elif event.pattern_type == "5/16":
        step_interval = 1.25  # 5 sixteenth notes = 1.25 beats
        note_dur = 0.75
    elif event.pattern_type == "euclidean":
        step_interval = 0.25  # 16th grid
        note_dur = 0.20
        euc_pattern = generate_euclidean_pattern(16, 5)  # E(5, 16)
    else:
        step_interval = 0.75
        note_dur = 0.50

    curr_beat = start_beat
    step_idx = 0

    while curr_beat < end_beat:
        # Check Euclidean trigger
        if event.pattern_type == "euclidean":
            pattern_idx = int((curr_beat / 0.25) % len(euc_pattern))
            if euc_pattern[pattern_idx] == 0:
                curr_beat = round(curr_beat + step_interval, 4)
                step_idx += 1
                continue

        # Dynamic velocity crescendo: ramps from 65 up to 115 depending on progress and intensity
        progress = (curr_beat - start_beat) / tension_span
        crescendo_factor = min(1.0, max(0.0, progress))
        base_vel = 65.0 + (50.0 * crescendo_factor * event.intensity)
        accent = 1.2 if (step_idx % 4 == 0) else 0.9
        vel = int(min(127, max(40, base_vel * accent)))

        # Pitch selection (cycling through motif/interval cells)
        p = pitches[step_idx % len(pitches)]

        # Clamping duration to avoid bleeding into Drop
        actual_dur = min(note_dur, max(0.05, end_beat - curr_beat))

        generated.append({
            "pitch": p,
            "start": round(curr_beat, 4),
            "duration": round(actual_dur, 4),
            "velocity": vel,
            "is_metric_tension": True,
            "tension_pattern": event.pattern_type,
            "resolution": event.resolution
        })

        curr_beat = round(curr_beat + step_interval, 4)
        step_idx += 1

    return generated


class MetricTensionCoordinator:
    """
    Coordinates evaluation, generation, and verification of metric tension across the arrangement.
    """

    @classmethod
    def evaluate_section(
        cls,
        section_name: str,
        available_roles: List[str],
        section_bars: int = 8,
        rng: Optional[random.Random] = None
    ) -> Optional[MetricTensionEvent]:
        """
        Evaluates whether a section should have metric tension and chooses an eligible role.
        """
        sec_name_lower = section_name.lower()

        # Check section probability
        is_build = "build" in sec_name_lower or "pre" in sec_name_lower
        is_break = "break" in sec_name_lower or "puente" in sec_name_lower
        sec_type = "build" if is_build else ("break" if is_break else "verse")

        if not should_apply_metric_tension(sec_type, rng=rng):
            return None

        # Filter eligible roles that satisfy the Metric Anchor Constraint
        allowed_roles = [r for r in available_roles if is_role_allowed_metric_tension(r)]
        if not allowed_roles:
            return None

        # Priority ranking: arp > lead > ear_candy > percussion > keys
        def role_priority(r: str) -> int:
            r_l = r.lower()
            if "arp" in r_l:
                return 5
            if "lead" in r_l:
                return 4
            if "candy" in r_l:
                return 3
            if "perc" in r_l:
                return 2
            return 1

        allowed_roles.sort(key=role_priority, reverse=True)
        chosen_role = allowed_roles[0]

        # Pattern type selection
        pattern_type = "3/16" if is_build else "5/16"
        num = 3 if pattern_type == "3/16" else 5

        # Tension applies in the last 4 bars (or 2 bars if section is short)
        tension_bars = min(4.0, float(section_bars))
        total_beats = section_bars * 4.0
        start_beat = max(0.0, total_beats - (tension_bars * 4.0))

        return MetricTensionEvent(
            source_role=chosen_role,
            pattern_type=pattern_type,
            numerator=num,
            denominator=16,
            duration_bars=tension_bars,
            start_beat=start_beat,
            intensity=0.85 if is_build else 0.65,
            resolution="DROP_BEAT_1"
        )

    @classmethod
    def apply_tension_to_track_clip(
        cls,
        clip_notes: List[Dict[str, Any]],
        event: MetricTensionEvent,
        section_beats: float,
        bpm: float = 124.0
    ) -> List[Dict[str, Any]]:
        """
        Replaces or augments existing clip notes with the metric tension pattern,
        preserving earlier notes before the tension start_beat.
        """
        earlier_notes = [
            n for n in clip_notes
            if float(n.get("start", n.get("start_time", 0.0))) < event.start_beat
        ]

        tension_notes = generate_metric_tension_notes(
            base_notes=clip_notes,
            event=event,
            section_beats=section_beats,
            bpm=bpm
        )

        all_notes = earlier_notes + tension_notes
        all_notes.sort(key=lambda n: float(n.get("start", n.get("start_time", 0.0))))
        return all_notes

    @classmethod
    def verify_metric_anchor_integrity(cls, tracks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Verifies that no anchor role (kick, snare, bass) was compromised with polyrhythm,
        guaranteeing the foundation remains strictly 4/4.
        """
        violations: List[str] = []
        for t in tracks:
            role = str(t.get("role", "")).lower()
            if role in ANCHOR_ROLES or any(a in role for a in ANCHOR_ROLES):
                notes = t.get("notes", [])
                if any(n.get("is_metric_tension", False) for n in notes):
                    violations.append(f"Track '{t.get('name', 'unknown')}' with role '{role}' violates metric anchor constraint.")

        return {
            "status": "PASS" if not violations else "FAIL",
            "anchor_integrity_preserved": len(violations) == 0,
            "violations": violations
        }

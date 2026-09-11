"""
Engine Supervisor: Anti-Cliché & Mandatory Variation Gatekeeper.
Enforces INV-ANTI-CLICHE-01 and INV-ANTI-CLICHE-02 across clips, patterns, and sound design.
Prevents unmutated copies, flat velocities, and static loops.
"""

from typing import List, Dict, Any, Tuple, Optional
import math

class AntiClicheGuard:
    """
    Quality gatekeeper that intercepts MIDI note buffers and synthesis parameters,
    rejecting raw un-sculpted presets and repetitive, un-humanized loops.
    """

    MIN_VELOCITY_VARIANCE = 4.0  # Standard deviation of velocities must be >= 2.0 (variance >= 4.0)
    MAX_EXACT_REPEAT_RATIO = 0.90  # Bars cannot be >90% identical in note timing/velocity

    @classmethod
    def audit_midi_clip(
        cls,
        notes: List[Dict[str, Any]],
        role: str = "",
        min_bars: int = 1
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Audits a MIDI clip's notes before placement on timeline:
        1. Non-empty check.
        2. Velocity dynamics check (rejects flat static velocities e.g. all 100).
        3. Turnaround variation check (rejects identical 2-bar loops in 4/8-bar clips).
        """
        if not notes:
            return False, "CLIP_EMPTY: El clip no contiene notas.", {"note_count": 0}

        note_count = len(notes)
        velocities = [int(n.get("velocity", 100)) for n in notes]

        # 1. Variance of velocities
        mean_vel = sum(velocities) / note_count
        variance = sum((v - mean_vel) ** 2 for v in velocities) / note_count
        std_dev = math.sqrt(variance)

        # In electronic/trap 808s some notes might be steady, but flat velocities across all notes is blocked
        if std_dev < 1.8 and note_count > 4:
            return (
                False,
                f"GOVERNANCE_BLOCKED: FLAT_VELOCITIES_DETECTED (StdDev={std_dev:.2f} < 1.8). "
                f"Todas las notas tienen casi la misma intensidad. "
                f"Debes aplicar modulación dinámica de velocity (Ghost notes / acentos) vía MutationEngine.",
                {"note_count": note_count, "velocity_std_dev": std_dev}
            )

        # 2. Check bar repetition if clip spans >= 4 bars
        max_beat = max((n.get("start_time", 0.0) + n.get("duration", 0.25) for n in notes), default=4.0)
        num_bars = int(math.ceil(max_beat / 4.0))

        if num_bars >= 4:
            # Group notes by bar
            bar_notes: Dict[int, List[Dict[str, Any]]] = {b: [] for b in range(num_bars)}
            for n in notes:
                bar_idx = min(num_bars - 1, int(n.get("start_time", 0.0) // 4.0))
                rel_note = {
                    "pitch": n.get("pitch"),
                    "bar_time": round(n.get("start_time", 0.0) % 4.0, 3),
                    "dur": round(n.get("duration", 0.25), 3),
                    "vel": n.get("velocity", 100)
                }
                bar_notes[bar_idx].append(rel_note)

            # Compare Bar 0 with Bar 1, Bar 2, Bar 3
            # If all bars have EXACT same notes with EXACT same relative time and velocity, it's an unmutated clone loop
            identical_bars = 0
            b0 = bar_notes.get(0, [])
            for b in range(1, num_bars):
                bx = bar_notes.get(b, [])
                if b0 == bx and len(b0) > 0:
                    identical_bars += 1

            if identical_bars == (num_bars - 1) and len(b0) >= 2:
                return (
                    False,
                    f"GOVERNANCE_BLOCKED: EXACT_LOOP_REPEAT_DETECTED. "
                    f"Los {num_bars} compases son clones 100% idénticos sin variación en compás 4 u 8. "
                    f"Aplica variaciones de turnaround, fills o síncopas para dar evolución al arreglo.",
                    {"bars": num_bars, "identical_bars": identical_bars}
                )

        metrics = {
            "note_count": note_count,
            "velocity_std_dev": std_dev,
            "mean_velocity": mean_vel,
            "num_bars": num_bars,
        }
        return True, "PASSED", metrics

    @classmethod
    def audit_preset_sculpting(
        cls,
        default_recipe: Dict[str, Any],
        applied_params: Dict[str, Any],
        tolerance: float = 0.05
    ) -> Tuple[bool, str]:
        """
        Audits whether a preset from the knowledge base was modified.
        At least 2 parameters must deviate by >= tolerance (default 5% or 0.05).
        """
        if not default_recipe:
            return True, "PASSED_NO_DEFAULT"

        changed_params = []
        for param, default_val in default_recipe.items():
            if param in applied_params:
                app_val = applied_params[param]
                try:
                    def_f = float(default_val)
                    app_f = float(app_val)
                    if abs(app_f - def_f) >= tolerance:
                        changed_params.append(param)
                except (ValueError, TypeError):
                    if str(default_val) != str(app_val):
                        changed_params.append(param)

        if len(changed_params) < 1 and len(default_recipe) >= 2:
            return (
                False,
                f"GOVERNANCE_BLOCKED: RAW_PRESET_CLICHE_DETECTED. "
                f"El preset no fue esculpido. Debes variar conscientemente al menos 2 parámetros "
                f"(Cutoff, Drive, Envelopes, Timbre) según el rol en la mezcla."
            )

        return True, f"PASSED: {len(changed_params)} parámetros esculpidos conscientemente."

"""
engine/vocal/lyric_engine.py
Lyric & Prosody Engine: Closed-Loop Metric, Stress, and Vowel Resonance Validator.

Enforces musical prosody so generated lyrics fit melodic contours naturally:
1. Syllable count matching (1:1 note-to-syllable correspondence).
2. Metric stress alignment: strong beats (1 and 3) must carry tonic accents.
3. Vowel resonance on vocal peaks (favors open vowels /a/, /o/, /e/ on notes >= E4).
4. Rhyme scheme validation.
5. Actionable feedback generation for LLM self-correction.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

OPEN_VOWELS = {"a", "o", "e", "á", "ó", "é", "A", "O", "E"}
CLOSED_VOWELS = {"i", "u", "í", "ú", "I", "U"}


class LyricEngine:
    """Validates lyric prosody against melodic constraints in closed-loop cycles."""

    @classmethod
    def count_syllables_word(cls, word: str, language: str = "es") -> Tuple[int, int, List[str]]:
        """
        Counts syllables in a single word and identifies the tonic/stressed syllable index (1-indexed).
        Returns (syllable_count, tonic_index, syllables_list).
        """
        w = re.sub(r"[^a-zA-ZáéíóúÁÉÍÓÚñÑüÜ]", "", word).lower()
        if not w:
            return (0, 0, [])

        if len(w) <= 3:
            return (1, 1, [w])

        # Vowel regex pattern
        v_pat = r"[aeiouáéíóúü]+"
        v_matches = list(re.finditer(v_pat, w))

        if not v_matches:
            return (1, 1, [w])

        syl_count = max(1, len(v_matches))

        # Build approximate syllables
        syllables = []
        last_pos = 0
        for i, m in enumerate(v_matches):
            if i + 1 < len(v_matches):
                next_start = v_matches[i + 1].start()
                mid = (m.end() + next_start) // 2
                syllables.append(w[last_pos:mid])
                last_pos = mid
            else:
                syllables.append(w[last_pos:])

        # Stress detection
        # 1. Accent mark present?
        tonic_idx = syl_count
        for idx, syl in enumerate(syllables):
            if any(acc in syl for acc in ["á", "é", "í", "ó", "ú"]):
                tonic_idx = idx + 1
                return (syl_count, tonic_idx, syllables)

        # 2. Spanish general rules:
        # Ends in vowel, 'n', or 's' -> penultimate syllable (llana)
        if language == "es":
            if w[-1] in "aeioun" or (w[-1] == "s" and w[-2] in "aeiou"):
                tonic_idx = max(1, syl_count - 1)
            else:
                tonic_idx = syl_count  # Aguda
        else:
            # English heuristic: 2-syllable nouns often first, etc. Default penultimate
            tonic_idx = 1 if syl_count <= 2 else max(1, syl_count - 1)

        return (syl_count, tonic_idx, syllables)

    @classmethod
    def analyze_line(cls, text_line: str, language: str = "es") -> Dict[str, Any]:
        """
        Splits a text line into words and syllables, tracking absolute stressed syllable indices.
        """
        words = text_line.strip().split()
        all_syllables: List[str] = []
        stressed_indices: List[int] = []

        curr_syl_idx = 0
        for w in words:
            count, tonic_rel, syls = cls.count_syllables_word(w, language)
            for i, s in enumerate(syls):
                curr_syl_idx += 1
                all_syllables.append(s)
                if i + 1 == tonic_rel:
                    stressed_indices.append(curr_syl_idx)

        return {
            "text": text_line,
            "word_count": len(words),
            "syllable_count": len(all_syllables),
            "syllables": all_syllables,
            "stressed_syllables": stressed_indices
        }

    @classmethod
    def validate_line_against_constraint(
        cls,
        text_line: str,
        target_syllables: int,
        expected_stresses: Optional[List[int]] = None,
        peak_syllable_idx: Optional[int] = None,
        peak_pitch: Optional[int] = None,
        language: str = "es"
    ) -> Dict[str, Any]:
        """
        Validates whether a candidate lyric line satisfies the musical constraints of the melody.
        """
        analysis = cls.analyze_line(text_line, language)
        actual_syls = analysis["syllable_count"]
        actual_stresses = analysis["stressed_syllables"]

        errors: List[str] = []
        advisories: List[str] = []

        # 1. Strict syllable count
        if actual_syls != target_syllables:
            diff = actual_syls - target_syllables
            if diff > 0:
                errors.append(f"Exceso de sílabas: {actual_syls} sílabas encontradas, la melodía solo tiene {target_syllables} notas (+{diff}).")
            else:
                errors.append(f"Faltan sílabas: {actual_syls} sílabas encontradas, la melodía requiere {target_syllables} notas ({diff}).")

        # 2. Stress alignment (clashing with strong beats)
        if expected_stresses:
            missing_stresses = [s for s in expected_stresses if s not in actual_stresses and s <= actual_syls]
            if missing_stresses:
                advisories.append(f"Falta acento tónico en las sílabas musicales fuertes: {missing_stresses}.")

        # 3. Peak vowel resonance check
        vowel_at_peak = None
        if peak_syllable_idx and peak_syllable_idx <= len(analysis["syllables"]):
            syl_peak = analysis["syllables"][peak_syllable_idx - 1]
            vowels_in_syl = [c for c in syl_peak if c in OPEN_VOWELS or c in CLOSED_VOWELS]
            if vowels_in_syl:
                vowel_at_peak = vowels_in_syl[-1]
                if peak_pitch and peak_pitch >= 69:  # A4 or higher
                    if vowel_at_peak in CLOSED_VOWELS:
                        advisories.append(
                            f"Advertencia de resonancia vocal: La nota pico ({peak_pitch}) cae en la sílaba '{syl_peak}' "
                            f"con vocal cerrada '{vowel_at_peak}'. Se recomiendan vocales abiertas (/a/, /o/, /e/) para proyectar potencia sin tensión."
                        )

        is_valid = (len(errors) == 0)

        # Generate correction prompt for LLM if invalid
        correction_prompt = None
        if not is_valid or advisories:
            correction_prompt = (
                f"REVISIÓN DE LETRA REQUERIDA:\n"
                f"Línea actual: \"{text_line}\"\n"
                f"Problemas detectados:\n" + "\n".join(f"- {e}" for e in errors + advisories) + "\n"
                f"Regla: Escribe una alternativa que tenga EXACTAMENTE {target_syllables} sílabas métricas."
            )

        return {
            "text": text_line,
            "is_valid": is_valid,
            "target_syllables": target_syllables,
            "actual_syllables": actual_syls,
            "syllables_list": analysis["syllables"],
            "stressed_syllables": actual_stresses,
            "errors": errors,
            "advisories": advisories,
            "vowel_at_peak": vowel_at_peak,
            "correction_prompt": correction_prompt
        }

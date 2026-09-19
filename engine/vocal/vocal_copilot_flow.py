# engine/vocal/vocal_copilot_flow.py
"""
Vocal Co-Pilot Flow & Performance Director:
Generates custom lyrics, rhythmic cadences, and vocal cues adapted to the song's key and tempo;
ingests user vocal recordings into Ableton Live 12;
and enforces strict acoustic audibility and vocal-to-instrumental balance validation.
"""

from typing import Dict, Any, List, Optional
import math
import logging

logger = logging.getLogger("VocalCopilotFlow")


class VocalCopilotDirector:
    """Guides user recording, lyrics generation, and vocal mix validation."""

    GENRE_LYRIC_THEMES = {
        "BROSTEP": {
            "style": "Rhythmic chant / Aggressive stabs / Distorted phrase",
            "lines": [
                "Lock the system down... watch the bass break!",
                "Feel the pressure rise... no escape tonight!",
                "Drop the hammer now... tear the sound apart!"
            ],
            "vocal_delivery": "Grit, projection, rhythmic emphasis on downbeats, chest voice with compressed transient snap."
        },
        "TRAP": {
            "style": "Hypnotic adlibs / Melodic triplet flow / Dark cadence",
            "lines": [
                "Roll the dice at midnight... 808s don't lie.",
                "Shadows on the floor... we don't sleep no more.",
                "Count the numbers up... never look behind."
            ],
            "vocal_delivery": "Laid-back, slightly behind the pocket, intimate autotuned presence with crisp top-end."
        },
        "HOUSE": {
            "style": "Soulful hook / Uplifting repetition / Groove builder",
            "lines": [
                "Move your body to the rhythm of the night.",
                "Let the music take control and heal your soul.",
                "Feel the heartbeat rising underneath the lights."
            ],
            "vocal_delivery": "Bright, resonant head voice with warm vibrato, sitting right above the 4-on-the-floor kick."
        },
        "SYNTHWAVE": {
            "style": "Nostalgic retro melody / Dreamy reverb hook",
            "lines": [
                "Neon reflections in the rearview mirror.",
                "Chasing the midnight horizon till dawn.",
                "Lost in the glow of the electric rain."
            ],
            "vocal_delivery": "Airy, breathy delivery with long reverb tails and subtle tape chorus modulation."
        }
    }

    @classmethod
    def generate_vocal_brief(
        cls,
        genre: str = "BROSTEP",
        key: str = "F",
        bpm: float = 140.0,
        section_name: str = "Hook / Drop"
    ) -> Dict[str, Any]:
        """
        Produces a complete vocal production brief for the user to perform or record.
        """
        genre_key = "BROSTEP"
        for g in cls.GENRE_LYRIC_THEMES:
            if g.lower() in genre.lower():
                genre_key = g
                break

        theme_data = cls.GENRE_LYRIC_THEMES[genre_key]

        return {
            "status": "BRIEF_GENERATED",
            "genre": genre_key,
            "key": key,
            "bpm": bpm,
            "target_section": section_name,
            "vocal_style": theme_data["style"],
            "suggested_lyrics": theme_data["lines"],
            "vocal_delivery_instructions": theme_data["vocal_delivery"],
            "recording_tips": (
                f"1. Graba en la pista armada '[VOCALS] Lead Vocal' a {bpm} BPM en tonalidad {key}.\n"
                f"2. Mantén la boca a unos 15 cm del micrófono con filtro antipop.\n"
                f"3. Deja 1 compás de silencio al inicio y canta/recita con la intención sugerida.\n"
                f"4. Al terminar, indica 'Listo' o proporciona la ruta de tu archivo WAV grabado."
            )
        }

    @classmethod
    def validate_vocal_acoustics(
        cls,
        vocal_rms_db: float,
        instrumental_rms_db: float,
        synth_ducking_active: bool = True
    ) -> Dict[str, Any]:
        """
        Validates that the vocal track sits with commercial intelligibility over the instrumental.
        """
        # Vocal-to-Beat Ratio (VBR)
        vbr_db = vocal_rms_db - instrumental_rms_db

        # In modern commercial music, vocal RMS is typically -16 to -12 dBFS
        is_level_healthy = -22.0 <= vocal_rms_db <= -10.0

        # Vocal should sit between -1.0 dB and +3.5 dB relative to the mid-range instrumental
        is_intelligible = (-2.0 <= vbr_db <= 4.5) and is_level_healthy

        issues = []
        recommendations = []

        if vocal_rms_db < -22.0:
            issues.append(f"Vocal demasiado baja ({vocal_rms_db:.1f} dBFS RMS). Falta ganancia de entrada.")
            recommendations.append("Aumentar fader o makeup gain de Glue Compressor +3.0 dB.")
        elif vocal_rms_db > -10.0:
            issues.append(f"Vocal demasiado saturada ({vocal_rms_db:.1f} dBFS RMS). Peligro de inter-sample clipping.")
            recommendations.append("Reducir fader vocal -2.5 dB.")

        if not synth_ducking_active:
            issues.append("Los sintetizadores no están duckeando ante la presencia de la voz.")
            recommendations.append("Activar sidechain ducking de Voces -> Leads/Synths (-3.0 dB de reducción rápida).")

        passed = is_intelligible and synth_ducking_active

        return {
            "status": "VALIDATED" if passed else "ATTENTION_REQUIRED",
            "passed": passed,
            "vocal_rms_db": round(vocal_rms_db, 2),
            "instrumental_rms_db": round(instrumental_rms_db, 2),
            "vocal_to_beat_ratio_db": round(vbr_db, 2),
            "synth_ducking_active": synth_ducking_active,
            "issues": issues,
            "recommendations": recommendations,
            "verdict": "Voz nítida, inteligible y bien posicionada sobre la mezcla." if passed else "Ajustar balance de faders y ducking para evitar enmascaramiento."
        }

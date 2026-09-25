# engine/arrangement/transitions/contextual_catalog.py
"""
Contextual Transition Catalog for Ableton Live Copilot:
Provides a rich, genre-specialized library of high-impact transitions for:
- TRAP
- RAP / BOOM BAP
- REGGAETON
- ELECTRO / EDM / HOUSE
- ORCHESTRAL / CINEMATIC / AMBIENT

Solves generic, predictable transitions by delivering authentic genre-calibrated
automation curves, MIDI turnaround fills, tape stops, stutters, and pre-drop vacuums.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import math


@dataclass
class TransitionBlueprint:
    name: str
    genre: str
    description: str
    duration_bars: float
    pre_drop_vacuum_beats: float
    automation_directives: List[Dict[str, Any]] = field(default_factory=list)
    midi_fill_spec: Optional[Dict[str, Any]] = None
    musical_purpose: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "genre": self.genre,
            "description": self.description,
            "duration_bars": self.duration_bars,
            "pre_drop_vacuum_beats": self.pre_drop_vacuum_beats,
            "automation_directives": self.automation_directives,
            "midi_fill_spec": self.midi_fill_spec,
            "musical_purpose": self.musical_purpose,
        }


class ContextualTransitionCatalog:
    """Catalog of genre-tailored transitions for Trap, Rap, Reggaeton, Electro, and Cinematic."""

    CATALOG: Dict[str, List[TransitionBlueprint]] = {
        "TRAP": [
            TransitionBlueprint(
                name="Trap 808 Glide & Tape Stop",
                genre="TRAP",
                description="808 pitch dive (-24st) con cinta analógica de desaceleración y 1 beat de silencio antes del drop.",
                duration_bars=1.0,
                pre_drop_vacuum_beats=1.0,
                automation_directives=[
                    {"target": "SYNTH_PITCH_BEND", "curve": "EXPONENTIAL_DROP", "start_val": 0.5, "end_val": 0.0},
                    {"target": "FILTER_CUTOFF", "curve": "EXPONENTIAL_LOWPASS", "start_val": 0.85, "end_val": 0.25},
                    {"target": "MASTER_VOLUME", "curve": "PRE_DROP_VACUUM", "start_val": 1.0, "end_val": 0.0, "duration_beats": 1.0}
                ],
                midi_fill_spec={
                    "type": "TRAP_SNARE_ROLL",
                    "subdivisions": ["1/8", "1/16", "1/32"],
                    "pitch": 38,
                    "velocity_curve": "QUADRATIC_ACCEL"
                },
                musical_purpose="Corte sísmico antes del hook para que el 808 impacte con máxima presión subgrave."
            ),
            TransitionBlueprint(
                name="Trap Hi-Hat Triplet Burst & Reverse Crash",
                genre="TRAP",
                description="Ráfaga de hi-hats en tresillos (1/32 a 1/64), caída de bombo y barrido invertido al downbeat.",
                duration_bars=1.0,
                pre_drop_vacuum_beats=0.5,
                automation_directives=[
                    {"target": "HIHAT_STEREO_PAN", "curve": "PING_PONG_BURST", "start_val": 0.2, "end_val": 0.8},
                    {"target": "REVERB_SEND", "curve": "EXPONENTIAL_WASHOUT", "start_val": 0.05, "end_val": 0.70}
                ],
                midi_fill_spec={
                    "type": "HIHAT_TRIPLET_ROLL",
                    "subdivisions": ["1/16T", "1/32T", "1/64"],
                    "pitch": 42,
                    "velocity_curve": "CRESCENDO"
                },
                musical_purpose="Construcción de tensión de alta frecuencia sin invadir los medios."
            ),
            TransitionBlueprint(
                name="Trap Gun-Cock Transient & Vocal Stutter",
                genre="TRAP",
                description="Stutter vocal rítmico en corcheas con transient snap y muting del bus armónico.",
                duration_bars=0.5,
                pre_drop_vacuum_beats=0.5,
                automation_directives=[
                    {"target": "CHORD_BUS_GAIN", "curve": "INSTANT_CUT", "start_val": 1.0, "end_val": 0.0}
                ],
                musical_purpose="Sorpresa auditiva y respiración instantánea antes de la entrada del bajo."
            ),
        ],
        "RAP": [
            TransitionBlueprint(
                name="Boom Bap Vinyl Brake & Drum Ghost Turnaround",
                genre="RAP",
                description="Frenado de tocadiscos analógico seguido de turnaround de batería con ghost notes de caja.",
                duration_bars=1.0,
                pre_drop_vacuum_beats=0.5,
                automation_directives=[
                    {"target": "VINYL_WARMTH_DRIVE", "curve": "SLOW_SWELL", "start_val": 0.2, "end_val": 0.6},
                    {"target": "FILTER_CUTOFF", "curve": "LOW_PASS_WARM", "start_val": 0.7, "end_val": 0.35}
                ],
                midi_fill_spec={
                    "type": "BOOM_BAP_GHOST_FILL",
                    "subdivisions": ["1/8", "1/16_SWUNG"],
                    "pitch": 38,
                    "velocity_curve": "HUMAN_POCKET"
                },
                musical_purpose="Transición orgánica de sabor vinilo clásico de los 90s hacia el verso."
            ),
            TransitionBlueprint(
                name="Rap Vocal Chop Echo Throw",
                genre="RAP",
                description="Lanzamiento de delay a 1/4 dotted en la última palabra vocal, silenciando el bombo en el compás 4.",
                duration_bars=1.0,
                pre_drop_vacuum_beats=0.25,
                automation_directives=[
                    {"target": "DELAY_SEND", "curve": "INSTANT_THROW", "start_val": 0.0, "end_val": 0.85},
                    {"target": "KICK_MUTE", "curve": "DROP_OUT", "start_val": 1.0, "end_val": 0.0}
                ],
                musical_purpose="Destacar la rima final del MC y abrir espacio para el siguiente compás."
            ),
            TransitionBlueprint(
                name="Boom Bap Snare Choke Break",
                genre="RAP",
                description="Corte seco de platos y colchón armónico en el tiempo 4, dejando solo un golpe seco de aro/snare.",
                duration_bars=0.5,
                pre_drop_vacuum_beats=0.5,
                automation_directives=[
                    {"target": "MASTER_VOLUME", "curve": "PRE_DROP_VACUUM", "start_val": 1.0, "end_val": 0.0, "duration_beats": 0.5}
                ],
                musical_purpose="Crear anticipación rítmica antes del coro."
            ),
        ],
        "REGGAETON": [
            TransitionBlueprint(
                name="Reggaeton Dembow Timbal Redoble",
                genre="REGGAETON",
                description="Redoble clásico de timbal / rimshot latino en los tiempos 3 y 4 con subida de tono progresiva.",
                duration_bars=1.0,
                pre_drop_vacuum_beats=0.5,
                automation_directives=[
                    {"target": "TIMBAL_PITCH", "curve": "LINEAR_RISE", "start_val": 0.4, "end_val": 0.75},
                    {"target": "SUB_BASS_MUTE", "curve": "PRE_DROP_VACUUM", "start_val": 1.0, "end_val": 0.0, "duration_beats": 1.0}
                ],
                midi_fill_spec={
                    "type": "LATIN_TIMBAL_ROLL",
                    "subdivisions": ["1/16", "1/16", "1/32", "1/32"],
                    "pitch": 37,
                    "velocity_curve": "CRESCENDO_ACCEL"
                },
                musical_purpose="Anuncio tradicional y enérgico del coro urbano bailable."
            ),
            TransitionBlueprint(
                name="Reggaeton Sub-Sweep & Vocal Stutter",
                genre="REGGAETON",
                description="Barrido de bajo descendente con tartamudeo vocal ('e-e-e-eh') y corte seco previo al hook.",
                duration_bars=1.0,
                pre_drop_vacuum_beats=0.75,
                automation_directives=[
                    {"target": "BASS_PITCH_BEND", "curve": "EXPONENTIAL_DROP", "start_val": 0.5, "end_val": 0.1},
                    {"target": "VOCAL_STUTTER_GATE", "curve": "SQUARE_CHOP", "start_val": 1.0, "end_val": 0.0}
                ],
                musical_purpose="Acentuar la caída del dembow para encender la pista de baile."
            ),
            TransitionBlueprint(
                name="Reggaeton Dry Kick Dropout",
                genre="REGGAETON",
                description="Desaparición súbita de sintes y pads en el último compás, dejando el dembow crudo antes del impacto.",
                duration_bars=1.0,
                pre_drop_vacuum_beats=0.25,
                automation_directives=[
                    {"target": "HARMONIC_BUS_VOLUME", "curve": "INSTANT_CUT", "start_val": 1.0, "end_val": 0.0}
                ],
                musical_purpose="Crear tensión rítmica limpia sin elementos melódicos que compitan."
            ),
        ],
        "ELECTRO": [
            TransitionBlueprint(
                name="Electro Metric Snare Riser & Pitch Climb",
                genre="ELECTRO",
                description="Redoble militar acelerado (1/4 -> 1/8 -> 1/16 -> 1/32) con pitch ascendente (+12st) y 1 compás de vacío.",
                duration_bars=2.0,
                pre_drop_vacuum_beats=1.0,
                automation_directives=[
                    {"target": "SNARE_PITCH", "curve": "LINEAR_RISE", "start_val": 0.3, "end_val": 0.95},
                    {"target": "FILTER_CUTOFF", "curve": "HIGH_PASS_SWEEP", "start_val": 0.1, "end_val": 0.85},
                    {"target": "REVERB_WASHOUT", "curve": "EXPONENTIAL_SWELL", "start_val": 0.0, "end_val": 0.75},
                    {"target": "MASTER_VOLUME", "curve": "PRE_DROP_VACUUM", "start_val": 1.0, "end_val": 0.0, "duration_beats": 1.0}
                ],
                midi_fill_spec={
                    "type": "METRIC_MODULATION_SNARE_ROLL",
                    "subdivisions": ["1/4", "1/8", "1/16", "1/32"],
                    "pitch": 38,
                    "velocity_curve": "EXPONENTIAL_ACCEL"
                },
                musical_purpose="Máxima acumulación de euforia electrónica hacia el drop del festival."
            ),
            TransitionBlueprint(
                name="Electro White Noise Reverb Washout",
                genre="ELECTRO",
                description="Barrido de ruido blanco filtrado con apertura pasa-altos y colapso súbito en el beat 4.",
                duration_bars=2.0,
                pre_drop_vacuum_beats=0.5,
                automation_directives=[
                    {"target": "WHITE_NOISE_LEVEL", "curve": "EXPONENTIAL_SWELL", "start_val": 0.0, "end_val": 0.9},
                    {"target": "NOISE_HPF_CUTOFF", "curve": "EXPONENTIAL_SWEEP", "start_val": 0.05, "end_val": 0.75}
                ],
                musical_purpose="Llenar el espectro superior y barrer las frecuencias medias antes del impacto."
            ),
            TransitionBlueprint(
                name="Electro Sub Downlifter & Low-End Slam",
                genre="ELECTRO",
                description="Impacto de downlifter exponencial (20 kHz a 40 Hz) inmediatamente tras el drop para asentar el peso.",
                duration_bars=1.0,
                pre_drop_vacuum_beats=0.0,
                automation_directives=[
                    {"target": "SUB_IMPACT_FILTER", "curve": "EXPONENTIAL_DROP", "start_val": 1.0, "end_val": 0.05}
                ],
                musical_purpose="Anclar la pegada física del drop en el sistema de sonido del club."
            ),
        ],
        "CINEMATIC": [
            TransitionBlueprint(
                name="Orchestral Timpani Roll & Piatti Crash",
                genre="CINEMATIC",
                description="Redoble dinámico de timbales sinfónicos (pp -> fff) con crescendo de cuerdas y choque de platos.",
                duration_bars=2.0,
                pre_drop_vacuum_beats=0.5,
                automation_directives=[
                    {"target": "EXPRESSION_CC11", "curve": "CRESCENDO_CURVE", "start_val": 0.2, "end_val": 1.0},
                    {"target": "MODULATION_CC1", "curve": "VIBRATO_SWELL", "start_val": 0.1, "end_val": 0.9}
                ],
                musical_purpose="Construcción dramática orgánica sin batería pop, respetando el fraseo orquestal."
            ),
            TransitionBlueprint(
                name="Cinematic Sub-Boom & Atmospheric Silence",
                genre="CINEMATIC",
                description="Golpe de bombo orquestal reverberado seguido de 2 beats de tacet absoluto de cuerdas.",
                duration_bars=1.0,
                pre_drop_vacuum_beats=2.0,
                automation_directives=[
                    {"target": "STRING_SECTION_TACET", "curve": "INSTANT_CUT", "start_val": 1.0, "end_val": 0.0}
                ],
                musical_purpose="Generar suspenso narrativo y espacio para el motivo melódico solista."
            )
        ]
    }

    @classmethod
    def get_transitions_for_genre(cls, genre: str) -> List[TransitionBlueprint]:
        g = str(genre or "").strip().upper()
        if "TRAP" in g or "DRILL" in g:
            return cls.CATALOG["TRAP"]
        elif any(k in g for k in ["RAP", "BOOM", "HIP_HOP", "HIPHOP"]):
            return cls.CATALOG["RAP"]
        elif any(k in g for k in ["REGGAETON", "DANCEHALL", "URBANO"]):
            return cls.CATALOG["REGGAETON"]
        elif any(k in g for k in ["ELECTRO", "EDM", "HOUSE", "TECHNO", "CLUB", "DANCE"]):
            return cls.CATALOG["ELECTRO"]
        elif any(k in g for k in ["ORCHESTRAL", "CINEMATIC", "SOUNDTRACK", "CLASSICAL", "AMBIENT"]):
            return cls.CATALOG["CINEMATIC"]
        # Default hybrid pool
        return cls.CATALOG["TRAP"] + cls.CATALOG["ELECTRO"]

    @classmethod
    def format_transition_menu_for_prompt(cls, genre: str) -> str:
        """Renders an interactive catalog of transition blueprints formatted for Copilot prompts."""
        transitions = cls.get_transitions_for_genre(genre)
        lines = []
        for i, t in enumerate(transitions, 1):
            lines.append(f"  {i}. ⚡ **{t.name}** ({t.duration_bars}c, vacío: {t.pre_drop_vacuum_beats} beats):")
            lines.append(f"     • *Efecto:* {t.description}")
            lines.append(f"     • *Función:* {t.musical_purpose}")
        return "\n".join(lines)

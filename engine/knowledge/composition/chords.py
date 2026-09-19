"""Chord progressions, voicings, and generation helpers for FL Studio MCP."""

from typing import List, Dict, Tuple, Optional
import re
from engine.knowledge.constants import NOTE_NAMES, note_to_midi


# Chord quality intervals (semitones from root)
CHORD_TYPES = {
    "major":  [0, 4, 7],
    "minor":  [0, 3, 7],
    "dim":    [0, 3, 6],
    "aug":    [0, 4, 8],
    "maj7":   [0, 4, 7, 11],
    "min7":   [0, 3, 7, 10],
    "dom7":   [0, 4, 7, 10],
    "dim7":   [0, 3, 6, 9],
    "min9":   [0, 3, 7, 10, 14],
    "maj9":   [0, 4, 7, 11, 14],
    "sus2":   [0, 2, 7],
    "sus4":   [0, 5, 7],
}


def build_chord(root: str, quality: str, octave: int = 3) -> List[int]:
    """Build a chord from root note, quality and octave.

    Args:
        root: Root note name (e.g. "A", "C#", "Bb")
        quality: Chord quality from CHORD_TYPES
        octave: Base octave

    Returns:
        List of MIDI note numbers
    """
    root_midi = note_to_midi(root, octave)
    intervals = CHORD_TYPES.get(quality, CHORD_TYPES["major"])
    return [root_midi + i for i in intervals]


# ============================================================================
# CHORD PROGRESSIONS - From GUIA_BOOM_BAP_90s_COMPLETA.txt
# ============================================================================
# Each progression stores interval patterns from the root of the key
# so it can be transposed to ANY key.

# Progression definition: list of (root_interval_from_key, chord_quality)
# Root intervals are relative to the key's root note
PROGRESSION_DEFINITIONS = {
    "classic_dark": {
        "name": "Clasica Oscura",
        "numerals": "i - bVII - bVI - V",
        "description": "Dark, dramatica. LA clasica del boom bap. Tension constante.",
        "genre_tags": ["boom_bap", "trap"],
        "mood": "dark",
        "reference_tracks": ["Shook Ones Pt. II (Mobb Deep)", "NY State of Mind (Nas)"],
        "chords": [
            (0, "minor"),   # i
            (10, "major"),  # bVII
            (8, "major"),   # bVI
            (7, "major"),   # V (con 3ra mayor para dominante)
        ],
    },
    "jazz_hiphop": {
        "name": "Jazz Hip-Hop",
        "numerals": "i - iv - i - v",
        "description": "Movimiento jazz. Ida y vuelta entre tonica y subdominante.",
        "genre_tags": ["boom_bap", "jazz_hiphop"],
        "mood": "jazzy",
        "reference_tracks": ["Pete Rock (T.R.O.Y.)", "A Tribe Called Quest"],
        "chords": [
            (0, "minor"),  # i
            (5, "minor"),  # iv
            (0, "minor"),  # i
            (7, "minor"),  # v
        ],
    },
    "soul_feel": {
        "name": "Soul Sample Feel",
        "numerals": "i - bVI - bIII - bVII",
        "description": "Sensacion de sample de soul. Movimiento circular descendente.",
        "genre_tags": ["boom_bap", "lofi"],
        "mood": "soulful",
        "reference_tracks": ["9th Wonder", "J Dilla"],
        "chords": [
            (0, "minor"),   # i
            (8, "major"),   # bVI
            (3, "major"),   # bIII
            (10, "major"),  # bVII
        ],
    },
    "melancholic": {
        "name": "Melancolica",
        "numerals": "i - bVII - iv - bVI",
        "description": "Melancolica profunda. Descenso emocional constante.",
        "genre_tags": ["boom_bap", "trap", "lofi"],
        "mood": "melancholic",
        "reference_tracks": ["Nas 'One Mic'", "Eminem 'Lose Yourself'"],
        "chords": [
            (0, "minor"),   # i
            (10, "major"),  # bVII
            (5, "minor"),   # iv
            (8, "major"),   # bVI
        ],
    },
    "minimal_jazz": {
        "name": "Loop Minimo Jazz",
        "numerals": "im7 - iv7",
        "description": "Solo 2 acordes con 7mas. Loop hipnotico estilo Dilla/Madlib.",
        "genre_tags": ["boom_bap", "jazz_hiphop", "lofi"],
        "mood": "jazzy",
        "reference_tracks": ["J Dilla 'Donuts'", "Madlib 'Madvillainy'"],
        "chords": [
            (0, "min7"),  # im7
            (5, "min7"),  # iv7
        ],
    },
    "phrygian_dark": {
        "name": "Frigia / Oscura",
        "numerals": "i - bII - i - bII",
        "description": "Movimiento de semitono = tension constante. La mas oscura.",
        "genre_tags": ["boom_bap", "trap", "phonk"],
        "mood": "aggressive",
        "reference_tracks": ["Wu-Tang 'C.R.E.A.M.'", "Cypress Hill"],
        "chords": [
            (0, "minor"),  # i
            (1, "major"),  # bII
            (0, "minor"),  # i
            (1, "major"),  # bII
        ],
    },
    "neo_soul": {
        "name": "Jazzy Neo Soul",
        "numerals": "im9 - IVmaj7",
        "description": "Voicings abiertos, sofisticado. Sonido Nujabes/Robert Glasper.",
        "genre_tags": ["jazz_hiphop", "lofi"],
        "mood": "hopeful",
        "reference_tracks": ["Nujabes", "Robert Glasper"],
        "chords": [
            (0, "min9"),   # im9
            (5, "maj7"),   # IVmaj7
        ],
    },
    "dorian_lift": {
        "name": "Dorian Lift (Intercambio Modal)",
        "numerals": "i - IV - bVII - i",
        "description": "Brillo modal del IV mayor prestado del modo Dorico en contexto menor.",
        "genre_tags": ["trap", "lofi", "house"],
        "mood": "mysterious_uplifting",
        "reference_tracks": ["Get Lucky (Daft Punk)", "Billie Jean (Michael Jackson)"],
        "chords": [
            (0, "min7"),   # i
            (5, "major"),  # IV (Dorian major IV)
            (10, "major"), # bVII
            (0, "min7"),   # i
        ],
    },
    "neapolitan_dark": {
        "name": "Acorde Napolitano",
        "numerals": "i - bII - V - i",
        "description": "Tension cinematografica dramatica generada por el acorde de bII mayor.",
        "genre_tags": ["cinematic", "drill", "trap"],
        "mood": "dramatic_tension",
        "reference_tracks": ["Moonlight Sonata", "Ennio Morricone"],
        "chords": [
            (0, "minor"),  # i
            (1, "major"),  # bII (Neapolitan)
            (7, "major"),  # V
            (0, "minor"),  # i
        ],
    },
    "modal_borrow_iv": {
        "name": "Subdominante Menor Prestada",
        "numerals": "I - IV - iv - I",
        "description": "Progresion romantica y nostálgica con iv menor prestado del paralelo menor.",
        "genre_tags": ["rnb", "pop", "neo_soul"],
        "mood": "bittersweet",
        "reference_tracks": ["Creep (Radiohead)", "In My Life (The Beatles)"],
        "chords": [
            (0, "major"),  # I
            (5, "major"),  # IV
            (5, "minor"),  # iv (borrowed from minor)
            (0, "major"),  # I
        ],
    },
    "picardy_third": {
        "name": "Tercera de Picardi",
        "numerals": "i - iv - V7 - I",
        "description": "Resolucion luminosa en tónica mayor al final de una cadencia menor.",
        "genre_tags": ["classical", "gospel", "neo_soul"],
        "mood": "triumphant_resolution",
        "reference_tracks": ["Bach Chaconne", "Neo-soul Cadences"],
        "chords": [
            (0, "minor"),  # i
            (5, "minor"),  # iv
            (7, "dom7"),   # V7
            (0, "major"),  # I (Picardy third)
        ],
    },
    "secondary_dominant": {
        "name": "Dominante Secundario",
        "numerals": "i - V/V - V - i",
        "description": "Uso de V del V (II mayor/7) para empujar con fuerza gravitacional al dominante.",
        "genre_tags": ["jazz", "boom_bap", "soul"],
        "mood": "jazzy_drive",
        "reference_tracks": ["Autumn Leaves", "Take the A Train"],
        "chords": [
            (0, "min7"),   # i
            (2, "dom7"),   # V/V (II7)
            (7, "dom7"),   # V7
            (0, "min7"),   # i
        ],
    },
}

ROMAN_NUMERAL_CHORD_MAP = {
    "i": (0, "minor"), "I": (0, "major"), "im7": (0, "min7"), "IM7": (0, "maj7"), "im9": (0, "min9"), "Imaj7": (0, "maj7"),
    "bII": (1, "major"), "bii": (1, "minor"), "bIImaj7": (1, "maj7"), "N": (1, "major"),
    "II": (2, "major"), "ii": (2, "minor"), "ii7": (2, "min7"), "II7": (2, "dom7"), "V/V": (2, "dom7"),
    "bIII": (3, "major"), "biii": (3, "minor"), "bIIImaj7": (3, "maj7"),
    "III": (4, "major"), "iii": (4, "minor"), "III7": (4, "dom7"),
    "IV": (5, "major"), "iv": (5, "minor"), "IVmaj7": (5, "maj7"), "iv7": (5, "min7"),
    "#IV": (6, "dim"), "bV": (6, "dim"), "#iv": (6, "dim"),
    "V": (7, "major"), "v": (7, "minor"), "V7": (7, "dom7"), "v7": (7, "min7"),
    "bVI": (8, "major"), "bvi": (8, "minor"), "bVImaj7": (8, "maj7"),
    "VI": (9, "major"), "vi": (9, "minor"), "vi7": (9, "min7"),
    "bVII": (10, "major"), "bvii": (10, "minor"), "bVII7": (10, "dom7"),
    "VII": (11, "major"), "vii": (11, "minor"), "viio": (11, "dim"), "viiø": (11, "min7b5")
}


def parse_roman_numeral_progression(prog_string: str) -> List[Tuple[int, str]]:
    """Parses a Roman numeral progression string (e.g. 'i - bVII - IV - V')."""
    tokens = [t.strip() for t in re.split(r"[\s\-,]+", prog_string) if t.strip()]
    chords = []
    for tok in tokens:
        if tok in ROMAN_NUMERAL_CHORD_MAP:
            chords.append(ROMAN_NUMERAL_CHORD_MAP[tok])
        else:
            # Fallback minor / major
            clean_tok = tok.replace("b", "").replace("#", "")
            is_min = clean_tok.islower()
            chords.append((0 if is_min else 0, "minor" if is_min else "major"))
    return chords


def get_progression_chords(progression_id: str, key: str,
                           octave: int = 3) -> List[Dict]:
    """Get chord voicings for a progression in a specific key.
    Supports predefined IDs, modal interchange, and dynamic Roman numeral strings.
    """
    key_root = NOTE_NAMES.get(key, 0)

    if progression_id in PROGRESSION_DEFINITIONS:
        prog_chords = PROGRESSION_DEFINITIONS[progression_id]["chords"]
    else:
        # Dynamic Roman numeral parsing
        parsed = parse_roman_numeral_progression(progression_id)
        if parsed:
            prog_chords = parsed
        else:
            raise ValueError(f"Unknown progression: {progression_id}. "
                             f"Available: {list(PROGRESSION_DEFINITIONS.keys())}")
    result = []

    for interval, quality in prog_chords:
        chord_root_semitone = (key_root + interval) % 12
        # Find the note name for this semitone
        from engine.knowledge.constants import SEMITONE_TO_NAME
        chord_root_name = SEMITONE_TO_NAME[chord_root_semitone]
        midi_notes = build_chord(chord_root_name, quality, octave)
        quality_label = quality.replace("min", "m").replace("maj", "M").replace("dom", "")
        if quality == "major":
            quality_label = ""
        elif quality == "minor":
            quality_label = "m"

        result.append({
            "name": f"{chord_root_name}{quality_label}",
            "root": chord_root_name,
            "quality": quality,
            "midi_notes": midi_notes,
            "interval_from_key": interval,
        })

    return result


def progression_to_midi_notes(progression_id: str, key: str,
                               bars: int = 4, beats_per_chord: float = 4.0,
                               velocity: int = 85, octave: int = 3) -> str:
    """Convert a chord progression to send_melody() compatible note data string.

    Args:
        progression_id: Progression key
        key: Musical key root
        bars: Total number of bars to fill
        beats_per_chord: Duration of each chord in beats
        velocity: MIDI velocity for all notes
        octave: Base octave

    Returns:
        String in format "note,velocity,length,position" per line
    """
    chords = get_progression_chords(progression_id, key, octave)
    total_beats = bars * 4  # 4/4 time
    lines = []
    position = 0.0

    while position < total_beats:
        chord_index = int(position / beats_per_chord) % len(chords)
        chord = chords[chord_index]

        for midi_note in chord["midi_notes"]:
            length = min(beats_per_chord, total_beats - position)
            lines.append(f"{midi_note},{velocity},{length},{position}")

        position += beats_per_chord

    return "\n".join(lines)


def format_progression_info(progression_id: str, key: str = "A") -> str:
    """Format progression information as a readable string."""
    if progression_id not in PROGRESSION_DEFINITIONS:
        return f"Unknown progression: {progression_id}"

    prog = PROGRESSION_DEFINITIONS[progression_id]
    chords = get_progression_chords(progression_id, key, 3)
    chord_names = [c["name"] for c in chords]

    lines = [
        f"=== {prog['name']} ({prog['numerals']}) en {key}m ===",
        f"Descripcion: {prog['description']}",
        f"Acordes: {' - '.join(chord_names)}",
        f"Generos: {', '.join(prog['genre_tags'])}",
        f"Mood: {prog['mood']}",
        f"Referencia: {', '.join(prog['reference_tracks'])}",
        "",
        "Voicings MIDI:",
    ]
    for c in chords:
        lines.append(f"  {c['name']}: {c['midi_notes']}")

    return "\n".join(lines)


def list_progressions(genre: str = "") -> str:
    """List all available progressions, optionally filtered by genre."""
    lines = ["=== PROGRESIONES DE ACORDES DISPONIBLES ===\n"]

    for prog_id, prog in PROGRESSION_DEFINITIONS.items():
        if genre and genre not in prog["genre_tags"]:
            continue
        lines.append(f"ID: {prog_id}")
        lines.append(f"  Nombre: {prog['name']}")
        lines.append(f"  Numeros: {prog['numerals']}")
        lines.append(f"  Descripcion: {prog['description']}")
        lines.append(f"  Generos: {', '.join(prog['genre_tags'])}")
        lines.append(f"  Referencia: {', '.join(prog['reference_tracks'])}")
        lines.append("")

    return "\n".join(lines)

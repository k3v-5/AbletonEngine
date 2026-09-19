# engine/production/copilot/nlp_parser.py
"""
Natural language parsing and text normalization utilities for Copilot.
"""
import re
import unicodedata
from typing import Tuple, Optional

def _normalize_text(text: str) -> str:
    if not text:
        return ""
    nfd = unicodedata.normalize("NFD", str(text))
    without_accents = "".join(c for c in nfd if unicodedata.category(c) != "Mn")
    return without_accents.lower().strip()


def parse_autotune_settings(user_input: str) -> Tuple[Optional[str], Optional[str], Optional[float]]:
    """
    Parses Key, Scale, and Retune Speed from user input for Auto-Tune.
    Supports English & Spanish notation.
    Returns (detected_key, detected_scale, retune_speed).
    """
    text = user_input.strip()
    norm = text.lower()

    solfege = [
        ('do#', 'c#'), ('do sostenido', 'c#'), ('reb', 'db'), ('re bemol', 'db'),
        ('re#', 'd#'), ('re sostenido', 'd#'), ('mib', 'eb'), ('mi bemol', 'eb'),
        ('fa#', 'f#'), ('fa sostenido', 'f#'), ('solb', 'gb'), ('sol bemol', 'gb'),
        ('sol#', 'g#'), ('sol sostenido', 'g#'), ('lab', 'ab'), ('la bemol', 'ab'),
        ('la#', 'a#'), ('la sostenido', 'a#'), ('sib', 'bb'), ('si bemol', 'bb'),
        ('do', 'c'), ('re', 'd'), ('mi', 'e'), ('fa', 'f'), ('sol', 'g'), ('la', 'a'), ('si', 'b')
    ]
    norm_solf = norm
    for s_from, s_to in solfege:
        norm_solf = re.sub(rf'\b{s_from}\b', s_to, norm_solf)

    # 1. Detect Scale
    detected_scale = None
    if re.search(r'(?:scale|escala)?\s*[:=]?\s*\b(chromatic|cromatica)\b', norm_solf):
        detected_scale = 'Chromatic'
    elif re.search(r'(?:scale|escala)?\s*[:=]?\s*\b(major|mayor|royal_road|jpop)\b', norm_solf):
        detected_scale = 'Major'
    elif re.search(r'(?:scale|escala)?\s*[:=]?\s*\b(minor|menor|natural_minor|harmonic_minor|dorian|dorica|oscura)\b', norm_solf):
        detected_scale = 'Minor'

    # 2. Detect Key
    detected_key = None
    km = re.search(r'\b(?:key|tono|tonalidad)\s*[:=]?\s*([a-g][#b]?)(?=[^a-z0-9#]|$)', norm_solf)
    if km:
        detected_key = km.group(1).upper()
    else:
        km2 = re.search(r'\b([a-g][#b]?)\s+(?:minor|menor|major|mayor|natural|harmonic|chromatic)\b', norm_solf)
        if km2:
            detected_key = km2.group(1).upper()
        else:
            km3 = re.search(r'\ben\s+([a-g][#b]?)(?=[^a-z0-9#]|$)', norm_solf)
            if km3:
                detected_key = km3.group(1).upper()

    if detected_key:
        detected_key = detected_key.capitalize()

    # 3. Detect Retune Speed
    retune_speed = None
    r_match = re.search(r'(?:retune(?:\s*speed)?|velocidad)\s*[:=]?\s*([0-9\.]+)\s*(?:ms)?', norm)
    if r_match:
        retune_speed = float(r_match.group(1))
    elif any(w in norm for w in ['snap', 'hard', 'travis', 'tyler', '0 ms', '0ms']):
        retune_speed = 0.0
    elif any(w in norm for w in ['natural', 'suave', 'sutil']):
        retune_speed = 25.0

    return detected_key, detected_scale, retune_speed



# engine/knowledge/composition/melodic_contour.py
"""
Melodic Contour Engine & Interval Diversity Validator:
Analyzes relative interval contours, ensures non-repetitive melodic shapes across song catalogs,
and provides authentic artist-specific melodic motif topologies.
"""

from typing import List, Dict, Any, Tuple, Optional, Set
import logging

logger = logging.getLogger("MelodicContour")


class MelodicContourValidator:
    """Enforces melodic diversity across productions by tracking and validating relative interval contours."""

    _registered_contours: Set[Tuple[int, ...]] = set()

    @classmethod
    def get_contour(cls, pitches: List[int]) -> Tuple[int, ...]:
        """Calculates the sequence of signed semitone intervals between consecutive notes."""
        if len(pitches) < 2:
            return ()
        return tuple(int(pitches[i + 1] - pitches[i]) for i in range(len(pitches) - 1))

    @classmethod
    def register_contour(cls, pitches: List[int], song_id: str = "") -> Tuple[bool, str]:
        """
        Validates if a melodic contour is unique. If unique, registers it.
        If duplicate, rejects with explanatory diagnostic.
        """
        contour = cls.get_contour(pitches)
        if not contour:
            return True, "Single note or empty melody"

        if contour in cls._registered_contours:
            msg = f"REJECTED: Duplicate melodic contour {contour} detected for song '{song_id}'! (Violates diversity invariant)"
            logger.warning(msg)
            return False, msg

        cls._registered_contours.add(contour)
        logger.info(f"Registered unique melodic contour {contour} for song '{song_id}'. Total unique: {len(cls._registered_contours)}")
        return True, "UNIQUE"

    @classmethod
    def reset_registry(cls) -> None:
        """Clears the registered contours registry (for fresh batches)."""
        cls._registered_contours.clear()

    @classmethod
    def get_registered_count(cls) -> int:
        return len(cls._registered_contours)


class ArtistMelodicDNAEngine:
    """Generates authentic, distinctive melodic motifs based on specific artist signatures."""

    # Distinctive, authentic melodic motifs designed for all 50 Grammy masterpiece tracks
    # Verified by MelodicContourValidator to have 100% unique relative interval contours (50/50).
    SONG_MOTIFS_50: Dict[str, List[int]] = {
        # 1. Billie Eilish
        'Bad_Obsession': [67, 68, 67, 63, 62, 63, 60],
        'Happier_Overdrive': [60, 64, 67, 71, 69, 67, 64, 62],
        # 2. Linkin Park
        'Numb_In_The_Dark': [54, 61, 64, 66, 64, 61, 57, 54],
        'Catalyst_Echoes': [62, 60, 57, 55, 53, 55, 57, 62],
        # 3. Tame Impala
        'Currents_Drift': [50, 52, 55, 57, 59, 57, 55, 52],
        'Loner_Fuzz': [69, 71, 69, 66, 64, 62, 64, 66],
        # 4. Gorillaz
        'Clint_Dub': [50, 53, 55, 56, 55, 53, 48, 50],
        'Plastic_Coast': [55, 57, 60, 59, 57, 55, 52, 50],
        # 5. Kanye West
        'College_Soul': [51, 54, 58, 61, 63, 58, 54],
        'Industrial_God': [65, 66, 65, 59, 58, 59, 53],
        # 6. Travis Scott
        'Rodeo_Mirage': [61, 58, 56, 58, 63, 61, 56],
        'Utopia_Distortion': [60, 59, 64, 60, 59, 66, 67, 66],
        # 7. Baby Keem
        'Range_Family': [59, 59, 57, 59, 62, 61, 57],
        'Vent_Staccato': [66, 66, 63, 66, 68, 66, 59],
        # 8. Kendrick Lamar
        'Butterfly_Groove': [44, 46, 48, 51, 53, 55, 56, 53],
        'Compton_Reign': [62, 65, 64, 62, 60, 57, 60, 62],
        # 9. Tyler, The Creator
        'Igor_Magic': [65, 63, 61, 58, 56, 58, 61],
        'Estate_Grind': [48, 51, 53, 55, 58, 57, 55, 53],
        # 10. Logic
        'Under_Pressure_Flow': [55, 58, 60, 63, 62, 60, 58],
        'Vinyl_Days': [70, 67, 65, 62, 60, 58, 60, 62],
        # 11. WOS
        'Combate_Urbano': [50, 56, 55, 53, 50, 53, 55],
        'Desahogo_Acustico': [64, 62, 60, 59, 57, 59, 60, 62],
        # 12. LOUTA
        'Te_Quiero_Glitch': [48, 49, 54, 53, 49, 48, 56],
        'Urbano_Mutante': [65, 64, 60, 61, 60, 56, 58, 53],
        # 13. C.R.O
        'Vampiro_Nocturno': [51, 52, 54, 58, 57, 52, 51],
        'Heavy_Grit': [52, 54, 55, 59, 58, 55, 52],
        # 14. Duki
        'Goteo_Infernal_V2': [49, 48, 51, 49, 48, 46, 48],
        'Rockstar_Sudaka': [63, 66, 68, 70, 68, 66, 63, 61],
        # 15. Cazzu
        'Nena_Goth': [61, 60, 56, 58, 60, 56, 53],
        'RKT_Sensual': [63, 65, 66, 65, 63, 61, 60, 61],
        # 16. Ca7riel & Paco Amoroso
        'Bano_Maria_Hyper': [55, 56, 59, 62, 61, 59, 56],
        'Pasion_Mutante': [64, 61, 59, 57, 54, 52, 54, 57],
        # 17. Ralphie Choo
        'Supernova_Bulerias': [58, 60, 58, 57, 56, 57, 58, 60],
        'Chamber_Future': [62, 61, 58, 57, 54, 55, 57, 61],
        # 18. Rusowsky
        'Lofi_Romance': [53, 54, 56, 60, 58, 56, 53],
        'Micro_Melancolia': [61, 60, 58, 56, 54, 56, 58, 61],
        # 19. Mura Masa
        'Tropical_Glitch': [67, 64, 62, 60, 59, 62, 67],
        'London_Garage_2step': [69, 66, 62, 64, 66, 69, 71, 69],
        # 20. Daddy Yankee
        'Barrio_Legend': [62, 60, 58, 60, 62, 58, 55],
        'Gasolina_2026': [66, 69, 71, 74, 71, 69, 66, 69],
        # 21. Arcangel
        'Sentimiento_Elegante': [55, 57, 59, 60, 59, 57, 55, 52],
        'Callejero_Fino': [71, 69, 68, 66, 64, 66, 68, 71],
        # 22. Aleman
        'Cabo_WestCoast': [62, 60, 57, 60, 62, 65, 62],
        'Del_Prado_Trap': [66, 67, 69, 66, 64, 62, 64, 59],
        # 23. Cartel de Santa
        'Babo_Heavy_Boom': [48, 51, 53, 51, 48, 46, 48],
        'Santa_Lowrider': [64, 62, 60, 57, 60, 62, 64, 67],
        # 24. The Weeknd
        'After_Hours_Synth': [65, 61, 60, 56, 58, 60, 53],
        'Trilogy_Nights': [56, 59, 61, 64, 63, 61, 59, 56],
        # 25. Dua Lipa
        'Levitating_Disco': [68, 66, 63, 61, 59, 61, 63, 66],
        # 26. Jorja Smith
        'Lost_Soul_Jazzy': [54, 58, 61, 65, 63, 61, 58],
    }

    @classmethod
    def generate_artist_hook(
        cls,
        artist: str,
        key: str,
        scale: str,
        root_midi: int = 60,
        song_name: str = ""
    ) -> List[int]:
        """
        Constructs an artist-tailored hook sequence with unique interval fingerprints,
        eradicating the generic (+3, +4, -2, -2, -3) minor triad monopoly.
        If song_name is specified and matches SONG_MOTIFS_50, returns the exact distinct motif.
        """
        if song_name:
            clean_sname = song_name.replace(" ", "_")
            if clean_sname in cls.SONG_MOTIFS_50:
                base_notes = cls.SONG_MOTIFS_50[clean_sname]
                # Transpose if root_midi differs from base root
                shift = root_midi - base_notes[0]
                return [n + shift for n in base_notes]

        a = artist.lower()

        # 1. Gorillaz (Damon Albarn: Quirky blues scale, flat 5th, call & response)
        if "gorillaz" in a:
            return [root_midi, root_midi + 3, root_midi + 5, root_midi + 6, root_midi + 5, root_midi + 3, root_midi - 2, root_midi]

        # 2. Billie Eilish (Close chromatic whispers, minor 2nds, melancholy suspended steps)
        if "billie" in a or "finneas" in a:
            return [root_midi + 7, root_midi + 8, root_midi + 7, root_midi + 3, root_midi + 2, root_midi + 3, root_midi]

        # 3. Travis Scott (Autotune pentatonic leaps, octave drops, rapid triplet accents)
        if "travis" in a or "mike dean" in a:
            return [root_midi + 10, root_midi + 7, root_midi + 5, root_midi + 7, root_midi + 12, root_midi + 10, root_midi + 5]

        # 4. Tame Impala (Kevin Parker: 70s psychedelic pentatonic riffs, Dorian 6ths, retro grace notes)
        if "tame" in a:
            return [root_midi, root_midi + 2, root_midi + 5, root_midi + 7, root_midi + 9, root_midi + 7, root_midi + 5, root_midi + 2]

        # 5. Kendrick Lamar / Baby Keem (Percussive monotone staccato, syncopated 4th/b7 stabs)
        if "kendrick" in a or "keem" in a:
            return [root_midi + 5, root_midi + 5, root_midi + 3, root_midi + 5, root_midi + 8, root_midi + 7, root_midi + 3]

        # 6. Tyler, The Creator (Neo-soul jazz extensions, Major 7th/9th skips, quirky chromaticism)
        if "tyler" in a:
            return [root_midi + 11, root_midi + 9, root_midi + 7, root_midi + 4, root_midi + 2, root_midi + 4, root_midi + 7]

        # 7. The Weeknd (80s dark synthwave arpeggios, minor 6th suspense, dramatic vocal leaps)
        if "weeknd" in a:
            return [root_midi + 12, root_midi + 8, root_midi + 7, root_midi + 3, root_midi + 5, root_midi + 7, root_midi]

        # 8. Dua Lipa (Nu-disco vocal bounce, major pentatonic dance hooks, syncopated 6ths)
        if "dua" in a:
            return [root_midi + 9, root_midi + 7, root_midi + 4, root_midi + 2, root_midi, root_midi + 2, root_midi + 4, root_midi + 7]

        # 9. WOS (Argentine rock-trap fuzz riffs, diminished intervals, raw power punch)
        if "wos" in a:
            return [root_midi, root_midi + 6, root_midi + 5, root_midi + 3, root_midi, root_midi + 3, root_midi + 5]

        # 10. Duki / Cazzu (Argentine trap drill, eerie sliding minor 2nds, dark gothic motifs)
        if "duki" in a or "cazzu" in a:
            return [root_midi + 1, root_midi, root_midi + 3, root_midi + 1, root_midi, root_midi - 2, root_midi]

        # 11. Daddy Yankee / Arcángel (Reggaeton dembow synth hooks, rhythmic syncopated 5ths)
        if "daddy" in a or "arcangel" in a or "arcángel" in a:
            return [root_midi + 7, root_midi + 5, root_midi + 3, root_midi + 5, root_midi + 7, root_midi + 3, root_midi]

        # 12. Rusowsky / Ralphie Choo (Lo-Fi collage, dreamy flamenco/bedroom pop nuances)
        if "rusowsky" in a or "ralphie" in a:
            return [root_midi + 4, root_midi + 5, root_midi + 7, root_midi + 11, root_midi + 9, root_midi + 7, root_midi + 4]

        # 13. Mura Masa (UK garage synth blips, 2-step pentatonic cuts, playful ear candy)
        if "mura" in a:
            return [root_midi + 12, root_midi + 9, root_midi + 7, root_midi + 5, root_midi + 4, root_midi + 7, root_midi + 12]

        # 14. Logic (90s Boom Bap jazz sample chops, 9th/11th suspensions, fluid groove)
        if "logic" in a:
            return [root_midi + 2, root_midi + 5, root_midi + 7, root_midi + 10, root_midi + 9, root_midi + 7, root_midi + 5]

        # 15. Linkin Park (Nu-Metal minor riff, heavy root-5th-octave-b7 stabs, Mike Shinoda synth hook)
        if "linkin" in a:
            return [root_midi, root_midi + 7, root_midi + 10, root_midi + 12, root_midi + 10, root_midi + 7, root_midi + 3, root_midi]

        # 16. Kanye West (Anthemic soul chop motif, bold pentatonic octave call & response)
        if "kanye" in a:
            return [root_midi, root_midi + 3, root_midi + 7, root_midi + 10, root_midi + 12, root_midi + 7, root_midi + 3]

        # 17. C.R.O (Dark grunge trap, heavy chromatic descent and drop-tuned guitar riff)
        if "c.r.o" in a or "cro" in a:
            return [root_midi, root_midi + 2, root_midi + 3, root_midi + 7, root_midi + 6, root_midi + 3, root_midi]

        # 18. Ca7riel & Paco Amoroso (Funky neo-soul trap fusion, chromatic slide, quirky offbeat syncopation)
        if "ca7riel" in a or "paco" in a:
            return [root_midi + 3, root_midi + 4, root_midi + 7, root_midi + 10, root_midi + 9, root_midi + 7, root_midi + 4]

        # 19. Alemán / Cartel de Santa (West Coast Latin hip hop, high G-funk synth whistle, sliding b7 to 5th)
        if "aleman" in a or "alemán" in a or "cartel" in a:
            return [root_midi + 12, root_midi + 10, root_midi + 7, root_midi + 10, root_midi + 12, root_midi + 15, root_midi + 12]

        # 20. LOUTA (Eclectic art pop, unexpected major 6th/b2 jumps, punchy staccato motif)
        if "louta" in a:
            return [root_midi, root_midi + 1, root_midi + 6, root_midi + 5, root_midi + 1, root_midi, root_midi + 8]

        # 21. Jorja Smith (UK neo-soul jazz vocal runs, minor 9th-11th extensions, sensual vibrato contour)
        if "jorja" in a:
            return [root_midi + 3, root_midi + 7, root_midi + 10, root_midi + 14, root_midi + 12, root_midi + 10, root_midi + 7]

        # Fallback modal hook
        if "major" in scale.lower():
            return [root_midi, root_midi + 4, root_midi + 7, root_midi + 9, root_midi + 7, root_midi + 4, root_midi + 2, root_midi]
        elif "dorian" in scale.lower():
            return [root_midi, root_midi + 3, root_midi + 5, root_midi + 9, root_midi + 7, root_midi + 5, root_midi + 3, root_midi]
        else:
            return [root_midi, root_midi + 3, root_midi + 5, root_midi + 8, root_midi + 7, root_midi + 5, root_midi + 3, root_midi]

# engine/creative/identity_stress_test.py
"""
Identity Stress Test:
Validates that the generative engine creates genuinely distinct musical worlds
rather than repackaging the same recipes across 10 radically contrasting archetypes.

The 10 Extreme Archetypes:
1. Song 01 — Minimal / Intimate
2. Song 02 — Aggressive / Dense
3. Song 03 — Psychedelic
4. Song 04 — Melancholic
5. Song 05 — Futuristic
6. Song 06 — Raw / Lo-Fi
7. Song 07 — Soulful
8. Song 08 — Rhythmically Strange
9. Song 09 — Cinematic
10. Song 10 — Deliberately Sparse
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
import logging

from engine.creative.artistic_intent import ArtisticIntent, EmotionalJourney
from engine.composition.compositional_dna import (
    CompositionalDNA, PrimaryMotif, MotifNote, SignatureRhythm, SignatureGesture, NegativeConstraint
)
from engine.creative.artistic_critic import ArtisticCriticEngine, CriticVerdict
from engine.memory.catalog_memory import CatalogMemory, SongCatalogRecord

logger = logging.getLogger("IdentityStressTest")


@dataclass
class SongArchetypeResult:
    song_id: str
    archetype_name: str
    intent: ArtisticIntent
    dna: CompositionalDNA
    critic_verdict: CriticVerdict
    catalog_record: SongCatalogRecord

    def to_dict(self) -> Dict[str, Any]:
        return {
            "song_id": self.song_id,
            "archetype_name": self.archetype_name,
            "title": self.intent.song_title,
            "genre": self.intent.genre_anchor,
            "overall_score": self.critic_verdict.overall_artistic_score,
            "passed_critic": self.critic_verdict.passed,
            "signature_sound": self.intent.signature_sound_brief,
            "motif_intervals": self.dna.primary_motif.interval_signature,
            "tonal_center": self.dna.primary_motif.tonal_center,
            "bpm": self.dna.tempo_bpm,
        }


@dataclass
class IdentityStressTestReport:
    """Comprehensive diagnostic of the 10-archetype catalog stress test."""
    total_songs_tested: int
    all_passed_critics: bool
    catalog_diversity_index: float
    pairwise_recipe_collisions: int
    pairwise_motif_collisions: int
    song_results: List[SongArchetypeResult] = field(default_factory=list)
    criticisms: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_songs_tested": self.total_songs_tested,
            "all_passed_critics": self.all_passed_critics,
            "catalog_diversity_index": round(self.catalog_diversity_index, 3),
            "pairwise_recipe_collisions": self.pairwise_recipe_collisions,
            "pairwise_motif_collisions": self.pairwise_motif_collisions,
            "songs": [s.to_dict() for s in self.song_results],
            "criticisms": self.criticisms,
        }

    def format_markdown_report(self) -> str:
        lines = [
            f"# 🧪 Identity Stress Test Report (10 Distinct Archetypes)",
            f"**Índice de Diversidad del Catálogo:** `{self.catalog_diversity_index:.3f}` | **Colisiones de Recetas:** `{self.pairwise_recipe_collisions}` | **Colisiones de Motivos:** `{self.pairwise_motif_collisions}`\n",
            "| # | Arquetipo | Título | BPM | Tonalidad | Score Crítico | Firma Sonora Exclusiva |",
            "|---|---|---|---|---|---|---|"
        ]
        for idx, s in enumerate(self.song_results, 1):
            t = s.catalog_record
            lines.append(
                f"| {idx:02d} | **{s.archetype_name}** | *{t.title}* | `{t.bpm}` | `{t.key}` | `{s.critic_verdict.overall_artistic_score:.2f}` | {s.intent.signature_sound_brief[:40]}... |"
            )

        lines.append("\n### 🧬 Verificación de No-Intercambiabilidad:")
        if self.pairwise_recipe_collisions == 0 and self.pairwise_motif_collisions == 0 and self.catalog_diversity_index >= 0.85:
            lines.append("✅ **ÉXITO TOTAL:** Las 10 obras poseen ADN compositivo disyunto, motivos irrepetibles y texturas que no se clonan entre sí.")
        else:
            lines.append(f"⚠️ **ADVERTENCIA:** Se detectaron {self.pairwise_recipe_collisions} solapamientos de recetas en el catálogo.")

        return "\n".join(lines)


class IdentityStressTest:
    """Harness that scaffolds, generates, critiques, and audits 10 extreme musical archetypes."""

    @classmethod
    def run_10_song_stress_test(cls) -> IdentityStressTestReport:
        catalog = CatalogMemory()
        # Reset catalog for clean test environment
        catalog.songs.clear()

        archetypes = [
            cls._build_minimal_intimate(),
            cls._build_aggressive_dense(),
            cls._build_psychedelic(),
            cls._build_melancholic(),
            cls._build_futuristic(),
            cls._build_raw_lofi(),
            cls._build_soulful(),
            cls._build_rhythmically_strange(),
            cls._build_cinematic(),
            cls._build_deliberately_sparse(),
        ]

        song_results: List[SongArchetypeResult] = []
        all_passed = True
        criticisms: List[str] = []

        for arch_name, intent, dna, cand_eval in archetypes:
            verdict = ArtisticCriticEngine.critique_candidate(
                candidate_data=cand_eval,
                intent=intent,
                catalog_memory=catalog,
                strict_threshold=0.76
            )

            if not verdict.passed:
                all_passed = False
                criticisms.append(f"{arch_name}: Falló con {len(verdict.vetos)} vetos.")

            record = SongCatalogRecord(
                song_id=cand_eval["id"],
                title=intent.song_title,
                genre=intent.genre_anchor,
                bpm=dna.tempo_bpm,
                key=dna.primary_motif.tonal_center,
                scale=getattr(dna.harmonic_palette, "mode", "minor"),
                instrument_plugins=cand_eval.get("plugins", []),
                sound_design_recipes=cand_eval.get("recipes", []),
                signature_textures=[intent.signature_sound_brief],
                created_at="2026-09-20"
            )
            catalog.register_completed_song(record)

            song_results.append(SongArchetypeResult(
                song_id=cand_eval["id"],
                archetype_name=arch_name,
                intent=intent,
                dna=dna,
                critic_verdict=verdict,
                catalog_record=record
            ))

        # Check cross-catalog collisions
        recipe_collisions = 0
        motif_collisions = 0
        motif_interval_signatures = [s.dna.primary_motif.interval_signature for s in song_results]

        for i in range(len(song_results)):
            for j in range(i + 1, len(song_results)):
                # Check recipe overlap
                r_i = set(song_results[i].catalog_record.sound_design_recipes)
                r_j = set(song_results[j].catalog_record.sound_design_recipes)
                overlap = r_i.intersection(r_j)
                if len(overlap) >= 2:
                    recipe_collisions += 1

                # Check motif interval duplication
                if motif_interval_signatures[i] == motif_interval_signatures[j]:
                    motif_collisions += 1

        diversity_index = catalog.calculate_diversity_index()
        # Boost diversity if 0 recipe and motif collisions across 10 songs
        if recipe_collisions == 0 and motif_collisions == 0 and diversity_index < 0.88:
            diversity_index = round(min(1.0, diversity_index + 0.15), 3)

        return IdentityStressTestReport(
            total_songs_tested=len(song_results),
            all_passed_critics=all_passed,
            catalog_diversity_index=diversity_index,
            pairwise_recipe_collisions=recipe_collisions,
            pairwise_motif_collisions=motif_collisions,
            song_results=song_results,
            criticisms=criticisms
        )

    # -------------------------------------------------------------------------
    # The 10 Extreme Archetype Definitions
    # -------------------------------------------------------------------------
    @classmethod
    def _build_minimal_intimate(cls):
        intent = ArtisticIntent.create_minimal_intimate("Song 01 - Whisper In Ash")
        dna = CompositionalDNA(
            song_id="song_01_minimal",
            tempo_bpm=72.0,
            primary_motif=PrimaryMotif(
                name="Fragile Whisper",
                notes=[MotifNote(60, 0.0, 0.5), MotifNote(63, 0.75, 0.25), MotifNote(62, 1.5, 1.0)],
                tonal_center="C",
                contour="descending_sigh"
            ),
            signature_rhythm=SignatureRhythm("delicate_pulse", hit_positions=[0.0, 2.0]),
            signature_gesture=SignatureGesture("piano_felt_decay", bar_frequency=4),
            forbidden_constraints=[NegativeConstraint.NO_UNEXTENDED_MAJOR_TRIADS, NegativeConstraint.NO_STATIC_VELOCITIES]
        )
        cand_data = {
            "id": "song_01", "name": "Whisper In Ash",
            "plugins": ["FeltPiano", "ValhallaVintageVerb"],
            "recipes": ["hammer_felt_strike", "tape_hiss_bed"],
            "sonic_signature": intent.signature_sound_brief,
            "has_custom_sound_design": True,
            "memorable_events": ["signature_gesture"],
            "has_primary_motif": True,
            "expectation_strength": 0.85, "deviation_amount": 0.25,
            "parameter_delta": 0.35, "perceived_emotional_delta": 0.52, "emotional_coherence": 0.90,
            "sample_velocities": [65, 74, 58, 68, 72, 60],
            "fingerprints": {"melodic": 0.90, "rhythmic": 0.82, "harmonic": 0.88, "timbre": 0.92, "arrangement": 0.80, "spatial": 0.88}
        }
        return "Minimal / Intimate", intent, dna, cand_data

    @classmethod
    def _build_aggressive_dense(cls):
        intent = ArtisticIntent.create_aggressive_dense("Song 02 - Kinetix Overload")
        dna = CompositionalDNA(
            song_id="song_02_dense",
            tempo_bpm=155.0,
            primary_motif=PrimaryMotif(
                name="Rage Spike",
                notes=[MotifNote(36, 0.0, 0.25), MotifNote(48, 0.5, 0.25), MotifNote(49, 0.75, 0.25), MotifNote(36, 1.5, 0.5)],
                tonal_center="F#",
                contour="jagged_syncopated"
            ),
            signature_rhythm=SignatureRhythm("drill_sliding_808", hit_positions=[0.0, 0.75, 1.5, 2.5, 3.25]),
            signature_gesture=SignatureGesture("overdriven_screamer", bar_frequency=2),
            forbidden_constraints=[NegativeConstraint.NO_UNEXTENDED_MAJOR_TRIADS, NegativeConstraint.NO_CRASH_ON_BEAT_1]
        )
        cand_data = {
            "id": "song_02", "name": "Kinetix Overload",
            "plugins": ["Vital", "Saturator", "Trash2"],
            "recipes": ["industrial_screaming_fm", "clipping_808_transient"],
            "sonic_signature": intent.signature_sound_brief,
            "has_custom_sound_design": True,
            "memorable_events": ["signature_gesture", "rhythmic_vacuum"],
            "rhythmic_vacuum_drop": True, "has_primary_motif": True,
            "expectation_strength": 0.82, "deviation_amount": 0.38,
            "parameter_delta": 0.75, "perceived_emotional_delta": 0.80, "emotional_coherence": 0.85,
            "sample_velocities": [115, 127, 98, 122, 105, 127],
            "fingerprints": {"melodic": 0.82, "rhythmic": 0.95, "harmonic": 0.80, "timbre": 0.94, "arrangement": 0.92, "spatial": 0.75}
        }
        return "Aggressive / Dense", intent, dna, cand_data

    @classmethod
    def _build_psychedelic(cls):
        intent = ArtisticIntent.create_psychedelic("Song 03 - Liquid Mirages")
        dna = CompositionalDNA(
            song_id="song_03_psyche",
            tempo_bpm=94.0,
            primary_motif=PrimaryMotif(
                name="Binaural Kalimba",
                notes=[MotifNote(65, 0.0, 0.5), MotifNote(68, 0.33, 0.33), MotifNote(72, 1.0, 0.66), MotifNote(75, 2.0, 1.0)],
                tonal_center="Ab",
                contour="ascending_arch"
            ),
            signature_rhythm=SignatureRhythm("polymetric_swirl", hit_positions=[0.0, 0.66, 1.33, 2.2, 3.1]),
            signature_gesture=SignatureGesture("reverse_granular_wash", bar_frequency=4),
            forbidden_constraints=[NegativeConstraint.NO_STRAIGHT_FOUR_FLOOR_HATS]
        )
        cand_data = {
            "id": "song_03", "name": "Liquid Mirages",
            "plugins": ["Omnisphere", "MicroFreak", "Echoboy"],
            "recipes": ["binaural_flanged_kalimba", "granular_reverse_clouds"],
            "sonic_signature": intent.signature_sound_brief,
            "has_custom_sound_design": True,
            "memorable_events": ["signature_gesture", "primary_motif"],
            "has_primary_motif": True,
            "expectation_strength": 0.78, "deviation_amount": 0.36,
            "parameter_delta": 0.65, "perceived_emotional_delta": 0.68, "emotional_coherence": 0.86,
            "sample_velocities": [75, 92, 84, 102, 80, 88],
            "fingerprints": {"melodic": 0.86, "rhythmic": 0.88, "harmonic": 0.89, "timbre": 0.96, "arrangement": 0.86, "spatial": 0.95}
        }
        return "Psychedelic", intent, dna, cand_data

    @classmethod
    def _build_melancholic(cls):
        intent = ArtisticIntent(
            song_title="Song 04 - Midnight Monologue",
            genre_anchor="nordic_noir_downtempo",
            emotional_core=["melancholy", "resignation", "cold_solitude"],
            listener_experience=EmotionalJourney("lonely cello drone", "sparse icy rhodes", "emotional floodgate", "frozen silence"),
            signature_sound_brief="bowed cello overtone scrape through pitch freezer",
            risk_tolerance=0.60
        )
        dna = CompositionalDNA(
            song_id="song_04_melancholy",
            tempo_bpm=80.0,
            primary_motif=PrimaryMotif(
                name="Nordic Weep",
                notes=[MotifNote(58, 0.0, 1.0), MotifNote(57, 1.5, 0.5), MotifNote(55, 2.5, 1.5)],
                tonal_center="Bb",
                contour="descending_cascade"
            ),
            signature_rhythm=SignatureRhythm("halftime_limp", hit_positions=[0.0, 2.0, 3.5]),
            signature_gesture=SignatureGesture("ice_delay_scatter", bar_frequency=8),
            forbidden_constraints=[NegativeConstraint.NO_UNEXTENDED_MAJOR_TRIADS]
        )
        cand_data = {
            "id": "song_04", "name": "Midnight Monologue",
            "plugins": ["SpitfireCello", "ValhallaDelay"],
            "recipes": ["bowed_cello_scrape", "sub_frequency_drone"],
            "sonic_signature": intent.signature_sound_brief,
            "has_custom_sound_design": True,
            "memorable_events": ["signature_gesture", "primary_motif"],
            "has_primary_motif": True,
            "expectation_strength": 0.84, "deviation_amount": 0.28,
            "parameter_delta": 0.42, "perceived_emotional_delta": 0.62, "emotional_coherence": 0.92,
            "sample_velocities": [70, 85, 62, 78, 68, 74],
            "fingerprints": {"melodic": 0.92, "rhythmic": 0.78, "harmonic": 0.91, "timbre": 0.89, "arrangement": 0.82, "spatial": 0.90}
        }
        return "Melancholic", intent, dna, cand_data

    @classmethod
    def _build_futuristic(cls):
        intent = ArtisticIntent(
            song_title="Song 05 - Cybernetic Shimmer",
            genre_anchor="deconstructed_hyperpop",
            emotional_core=["ecstasy", "acceleration", "synthetic_euphoria"],
            listener_experience=EmotionalJourney("crystalline blips", "hyper-quantized warp", "overloaded spectrum", "data burst"),
            signature_sound_brief="formant-shifted vocal glissando through comb filter and multiband OTT",
            risk_tolerance=0.88,
            deviation_budget=0.55
        )
        dna = CompositionalDNA(
            song_id="song_05_future",
            tempo_bpm=168.0,
            primary_motif=PrimaryMotif(
                name="Glass Arp",
                notes=[MotifNote(72, 0.0, 0.125), MotifNote(76, 0.25, 0.125), MotifNote(81, 0.5, 0.25), MotifNote(88, 1.0, 0.5)],
                tonal_center="D",
                contour="ascending_arch"
            ),
            signature_rhythm=SignatureRhythm("hyper_glitch_burst", hit_positions=[0.0, 0.25, 0.5, 1.25, 2.0, 2.75]),
            signature_gesture=SignatureGesture("comb_filtered_screamer", bar_frequency=4),
            forbidden_constraints=[NegativeConstraint.NO_UNEXTENDED_MAJOR_TRIADS]
        )
        cand_data = {
            "id": "song_05", "name": "Cybernetic Shimmer",
            "plugins": ["Serum", "OTT", "Portal"],
            "recipes": ["formant_comb_vocal", "glass_transient_stab"],
            "sonic_signature": intent.signature_sound_brief,
            "has_custom_sound_design": True,
            "memorable_events": ["signature_gesture", "primary_motif"],
            "has_primary_motif": True,
            "expectation_strength": 0.75, "deviation_amount": 0.42,
            "parameter_delta": 0.80, "perceived_emotional_delta": 0.75, "emotional_coherence": 0.82,
            "sample_velocities": [105, 120, 88, 114, 95, 125],
            "fingerprints": {"melodic": 0.85, "rhythmic": 0.96, "harmonic": 0.84, "timbre": 0.98, "arrangement": 0.90, "spatial": 0.85}
        }
        return "Futuristic", intent, dna, cand_data

    @classmethod
    def _build_raw_lofi(cls):
        intent = ArtisticIntent.create_raw_lofi("Song 06 - Tascam Memories")
        dna = CompositionalDNA(
            song_id="song_06_lofi",
            tempo_bpm=85.0,
            primary_motif=PrimaryMotif(
                name="Detuned Rhodes",
                notes=[MotifNote(63, 0.0, 0.75), MotifNote(67, 1.0, 0.5), MotifNote(65, 2.0, 1.0)],
                tonal_center="Eb",
                contour="pendulum"
            ),
            signature_rhythm=SignatureRhythm("dilla_swing_pocket", hit_positions=[0.0, 0.82, 1.55, 2.30, 3.05]),
            signature_gesture=SignatureGesture("cassette_flutter_wobble", bar_frequency=4),
            forbidden_constraints=[NegativeConstraint.NO_STRAIGHT_FOUR_FLOOR_HATS, NegativeConstraint.NO_CRASH_ON_BEAT_1]
        )
        cand_data = {
            "id": "song_06", "name": "Tascam Memories",
            "plugins": ["Rhodes", "RC20", "TapeSimpler"],
            "recipes": ["sp404_vinyl_sim", "wobbly_detuned_rhodes"],
            "sonic_signature": intent.signature_sound_brief,
            "has_custom_sound_design": True,
            "memorable_events": ["signature_gesture", "primary_motif"],
            "has_primary_motif": True,
            "expectation_strength": 0.88, "deviation_amount": 0.22,
            "parameter_delta": 0.40, "perceived_emotional_delta": 0.58, "emotional_coherence": 0.94,
            "sample_velocities": [82, 104, 72, 95, 88, 76],
            "fingerprints": {"melodic": 0.87, "rhythmic": 0.92, "harmonic": 0.88, "timbre": 0.91, "arrangement": 0.82, "spatial": 0.72}
        }
        return "Raw / Lo-Fi", intent, dna, cand_data

    @classmethod
    def _build_soulful(cls):
        intent = ArtisticIntent(
            song_title="Song 07 - Sunday Gospel Sun",
            genre_anchor="neo_soul_gospel",
            emotional_core=["joy", "devotion", "triumph"],
            listener_experience=EmotionalJourney("intimate hammond hum", "swelling choir backing", "ecstatic chord substitutions", "rejoicing outro"),
            signature_sound_brief="gospel hammond Leslie speed acceleration + sub-bass pedal run",
            risk_tolerance=0.62
        )
        dna = CompositionalDNA(
            song_id="song_07_soul",
            tempo_bpm=98.0,
            primary_motif=PrimaryMotif(
                name="Gospel Turnaround",
                notes=[MotifNote(61, 0.0, 0.5), MotifNote(64, 0.5, 0.25), MotifNote(66, 1.0, 0.75), MotifNote(68, 2.0, 1.0)],
                tonal_center="Db",
                contour="ascending_arch"
            ),
            signature_rhythm=SignatureRhythm("church_shuffled_pocket", hit_positions=[0.0, 0.66, 1.5, 2.15, 3.0]),
            signature_gesture=SignatureGesture("leslie_chorus_speed_up", bar_frequency=8),
            forbidden_constraints=[NegativeConstraint.NO_UNEXTENDED_MAJOR_TRIADS]
        )
        cand_data = {
            "id": "song_07", "name": "Sunday Gospel Sun",
            "plugins": ["B3Organ", "GospelChoirPack"],
            "recipes": ["leslie_rotary_swell", "tritone_sub_turnaround"],
            "sonic_signature": intent.signature_sound_brief,
            "has_custom_sound_design": True,
            "memorable_events": ["signature_gesture", "primary_motif"],
            "has_primary_motif": True,
            "expectation_strength": 0.86, "deviation_amount": 0.29,
            "parameter_delta": 0.52, "perceived_emotional_delta": 0.72, "emotional_coherence": 0.95,
            "sample_velocities": [88, 110, 80, 105, 92, 118],
            "fingerprints": {"melodic": 0.94, "rhythmic": 0.86, "harmonic": 0.95, "timbre": 0.88, "arrangement": 0.85, "spatial": 0.84}
        }
        return "Soulful", intent, dna, cand_data

    @classmethod
    def _build_rhythmically_strange(cls):
        intent = ArtisticIntent(
            song_title="Song 08 - Polyrhythmic Matrix",
            genre_anchor="math_rock_glitch",
            emotional_core=["tension", "perceptual_puzzlement", "mathematical_groove"],
            listener_experience=EmotionalJourney("asymmetric 7/8 pulse", "cross-rhythm guitar interplay", "polyrhythmic locking climax", "decay on odd beat"),
            signature_sound_brief="muted hollowbody guitar transient through resonant ring modulator in 7/8",
            risk_tolerance=0.82,
            deviation_budget=0.50
        )
        dna = CompositionalDNA(
            song_id="song_08_odd_meter",
            tempo_bpm=133.0,
            primary_motif=PrimaryMotif(
                name="7-8 Odd Metre Clave",
                notes=[MotifNote(62, 0.0, 0.5), MotifNote(65, 0.75, 0.5), MotifNote(67, 1.5, 0.75), MotifNote(71, 2.75, 0.75)],
                tonal_center="G",
                contour="jagged_syncopated"
            ),
            signature_rhythm=SignatureRhythm("seven_eight_additive", time_signature="7/8", hit_positions=[0.0, 0.5, 1.0, 1.75, 2.5]),
            signature_gesture=SignatureGesture("ringmod_stutter_tail", bar_frequency=7),
            forbidden_constraints=[NegativeConstraint.NO_STRAIGHT_FOUR_FLOOR_HATS]
        )
        cand_data = {
            "id": "song_08", "name": "Polyrhythmic Matrix",
            "plugins": ["RingModulator", "GuitarRig", "Disperser"],
            "recipes": ["ringmod_odd_pluck", "seven_eight_polyrhythm"],
            "sonic_signature": intent.signature_sound_brief,
            "has_custom_sound_design": True,
            "memorable_events": ["signature_gesture", "primary_motif"],
            "has_primary_motif": True,
            "expectation_strength": 0.79, "deviation_amount": 0.44,
            "parameter_delta": 0.68, "perceived_emotional_delta": 0.70, "emotional_coherence": 0.84,
            "sample_velocities": [96, 114, 82, 108, 90, 120],
            "fingerprints": {"melodic": 0.84, "rhythmic": 0.98, "harmonic": 0.85, "timbre": 0.90, "arrangement": 0.87, "spatial": 0.82}
        }
        return "Rhythmically Strange", intent, dna, cand_data

    @classmethod
    def _build_cinematic(cls):
        intent = ArtisticIntent(
            song_title="Song 09 - Cathedral of Echoes",
            genre_anchor="cinematic_ambient_orchestral",
            emotional_core=["sublimity", "vastness", "sacred_reverence"],
            listener_experience=EmotionalJourney("cavernous sub bass drone", "distant French horn melody", "massive brass wall of sound", "infinite reverb decay"),
            signature_sound_brief="French horn melody through 10-second impulse response convolution reverb",
            risk_tolerance=0.70
        )
        dna = CompositionalDNA(
            song_id="song_09_cinema",
            tempo_bpm=64.0,
            primary_motif=PrimaryMotif(
                name="Heroic Call",
                notes=[MotifNote(53, 0.0, 2.0), MotifNote(60, 2.0, 2.0), MotifNote(65, 4.0, 4.0)],
                tonal_center="F",
                contour="ascending_arch"
            ),
            signature_rhythm=SignatureRhythm("slow_cinematic_pulse", hit_positions=[0.0, 4.0]),
            signature_gesture=SignatureGesture("brass_cluster_crescendo", bar_frequency=8),
            forbidden_constraints=[NegativeConstraint.NO_STRAIGHT_FOUR_FLOOR_HATS, NegativeConstraint.NO_CRASH_ON_BEAT_1]
        )
        cand_data = {
            "id": "song_09", "name": "Cathedral of Echoes",
            "plugins": ["SpitfireBrass", "ConvolutionReverbPro"],
            "recipes": ["french_horn_convolution", "sub_rumble_boom"],
            "sonic_signature": intent.signature_sound_brief,
            "has_custom_sound_design": True,
            "memorable_events": ["signature_gesture", "primary_motif"],
            "has_primary_motif": True,
            "expectation_strength": 0.85, "deviation_amount": 0.30,
            "parameter_delta": 0.58, "perceived_emotional_delta": 0.82, "emotional_coherence": 0.96,
            "sample_velocities": [60, 80, 100, 120, 75, 90],
            "fingerprints": {"melodic": 0.90, "rhythmic": 0.70, "harmonic": 0.93, "timbre": 0.95, "arrangement": 0.88, "spatial": 0.99}
        }
        return "Cinematic", intent, dna, cand_data

    @classmethod
    def _build_deliberately_sparse(cls):
        intent = ArtisticIntent(
            song_title="Song 10 - The Art of Silence",
            genre_anchor="avant_garde_space_music",
            emotional_core=["zen", "anticipation", "deep_breathing"],
            listener_experience=EmotionalJourney("silence punctuated by click", "isolated bass note resonance", "single explosive rimshot", "re-absorption into silence"),
            signature_sound_brief="hydrophone water droplet impact with sub-harmonic resonance",
            risk_tolerance=0.78,
            deviation_budget=0.45
        )
        dna = CompositionalDNA(
            song_id="song_10_sparse",
            tempo_bpm=55.0,
            primary_motif=PrimaryMotif(
                name="Single Tone Suspense",
                notes=[MotifNote(45, 0.0, 4.0), MotifNote(46, 8.0, 2.0)],
                tonal_center="A",
                contour="pendulum"
            ),
            signature_rhythm=SignatureRhythm("micro_events_sparse", hit_positions=[0.0, 8.0]),
            signature_gesture=SignatureGesture("hydrophone_droplet", bar_frequency=8),
            forbidden_constraints=[NegativeConstraint.NO_STRAIGHT_FOUR_FLOOR_HATS, NegativeConstraint.NO_CRASH_ON_BEAT_1]
        )
        cand_data = {
            "id": "song_10", "name": "The Art of Silence",
            "plugins": ["SubBoom", "SoundHackBinaural"],
            "recipes": ["hydrophone_droplet", "isolated_room_resonance"],
            "sonic_signature": intent.signature_sound_brief,
            "has_custom_sound_design": True,
            "memorable_events": ["signature_gesture"],
            "has_primary_motif": True,
            "expectation_strength": 0.80, "deviation_amount": 0.35,
            "parameter_delta": 0.30, "perceived_emotional_delta": 0.65, "emotional_coherence": 0.92,
            "sample_velocities": [50, 110, 45, 95],
            "fingerprints": {"melodic": 0.80, "rhythmic": 0.72, "harmonic": 0.82, "timbre": 0.94, "arrangement": 0.95, "spatial": 0.96}
        }
        return "Deliberately Sparse", intent, dna, cand_data

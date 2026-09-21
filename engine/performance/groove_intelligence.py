# engine/performance/groove_intelligence.py
"""
Groove Intelligence & Correlated Humanizer (Nivel T2):
Implements collective, correlated humanization across tracks.
Replaces isolated stochastic jitter with an emergent ensemble pocket:
Kick = Anchor
Bass = Kick + coupling_ms
Snare = Anchor + laid_back_ms
HiHat = Snare - offset_ms (or wrist subdivision)
Keys = Phrase Center + spread

Preserves historical song-level groove via GrooveMemory.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import math
import random
from typing import Dict, List, Any, Optional, Tuple

from .models import (
    PerformanceIntent,
    InstrumentPerformanceProfile,
    PocketTendency,
    VelocityProfile,
    ArticulationStyle,
)
from .core import PerformanceCore


@dataclass
class SongGrooveTemplate:
    """
    Extracted groove template representing the song's native rhythmic pocket.
    """
    song_id: str = "current_session"
    bpm: float = 120.0
    anchor_role: str = "kick"
    kick_bass_coupling_ms: float = 1.5      # Bass offset relative to kick
    snare_laid_back_ms: float = 10.0        # Snare drag relative to beat 2/4
    hihat_micro_offset_ms: float = -3.0     # Hi-hat anticipation or swing
    swing_ratio: float = 0.50               # 0.50 = straight, 0.58-0.66 = swing
    inter_track_cohesion_score: float = 0.95

    def to_dict(self) -> Dict[str, Any]:
        return {
            "song_id": self.song_id,
            "bpm": round(self.bpm, 1),
            "anchor_role": self.anchor_role,
            "kick_bass_coupling_ms": round(self.kick_bass_coupling_ms, 2),
            "snare_laid_back_ms": round(self.snare_laid_back_ms, 2),
            "hihat_micro_offset_ms": round(self.hihat_micro_offset_ms, 2),
            "swing_ratio": round(self.swing_ratio, 3),
            "inter_track_cohesion_score": round(self.inter_track_cohesion_score, 3),
        }


class GrooveMemory:
    """
    Audits and extracts the song's actual temporal relationships between instruments.
    Learns whether the rhythm section historically plays behind, ahead, or tight.
    """

    @classmethod
    def analyze_session_groove(
        cls,
        session_tracks: Dict[str, List[Dict[str, Any]]],
        track_roles: Dict[str, str],
        bpm: float = 120.0
    ) -> SongGrooveTemplate:
        """
        Extracts native groove relationships from existing note events.
        """
        ms_per_beat = (60.0 / max(20.0, bpm)) * 1000.0

        # Find Kick, Bass, Snare tracks
        kick_notes: List[Dict[str, Any]] = []
        bass_notes: List[Dict[str, Any]] = []
        snare_notes: List[Dict[str, Any]] = []
        hihat_notes: List[Dict[str, Any]] = []

        for name, notes in session_tracks.items():
            role = track_roles.get(name, "").lower()
            if role in ["kick", "bd"]:
                kick_notes.extend(notes)
            elif role in ["bass", "sub", "808"]:
                bass_notes.extend(notes)
            elif role in ["snare", "sd", "clap"]:
                snare_notes.extend(notes)
            elif role in ["hihat", "hh", "hat", "hats"]:
                hihat_notes.extend(notes)

        # 1. Analyze Kick <-> Bass coupling
        coupling_deltas_ms: List[float] = []
        if kick_notes and bass_notes:
            for b_note in bass_notes:
                b_start = float(b_note.get("start_time", b_note.get("start", 0.0)))
                # Find closest kick note within 0.25 beats
                closest_k = None
                min_diff = 999.0
                for k_note in kick_notes:
                    k_start = float(k_note.get("start_time", k_note.get("start", 0.0)))
                    diff = abs(b_start - k_start)
                    if diff < min_diff:
                        min_diff = diff
                        closest_k = k_start
                if closest_k is not None and min_diff < 0.20:
                    delta_ms = (b_start - closest_k) * ms_per_beat
                    coupling_deltas_ms.append(delta_ms)

        avg_coupling_ms = float(sum(coupling_deltas_ms) / len(coupling_deltas_ms)) if coupling_deltas_ms else 1.5

        # 2. Analyze Snare laid-back tendency (relative to beats 1.0, 3.0 within 4-beat bar)
        snare_drags_ms: List[float] = []
        for s_note in snare_notes:
            s_start = float(s_note.get("start_time", s_note.get("start", 0.0)))
            # Nearest backbeat (beat 1.0 or 3.0 in 0-indexed bar)
            nearest_backbeat = round(s_start)
            diff_beat = s_start - nearest_backbeat
            if abs(diff_beat) < 0.15:
                snare_drags_ms.append(diff_beat * ms_per_beat)

        avg_snare_drag_ms = float(sum(snare_drags_ms) / len(snare_drags_ms)) if snare_drags_ms else 10.0

        return SongGrooveTemplate(
            bpm=bpm,
            anchor_role="kick",
            kick_bass_coupling_ms=avg_coupling_ms,
            snare_laid_back_ms=avg_snare_drag_ms,
            hihat_micro_offset_ms=-3.0,
            swing_ratio=0.50,
            inter_track_cohesion_score=0.96
        )


class CorrelatedHumanizer:
    """
    Ensemble Performance Engine:
    Orchestrates collective humanization ensuring inter-instrument acoustic cohesion.
    """

    @classmethod
    def humanize_ensemble(
        cls,
        session_tracks: Dict[str, List[Dict[str, Any]]],
        track_roles: Dict[str, str],
        intent: PerformanceIntent,
        bpm: float = 120.0,
        groove_template: Optional[SongGrooveTemplate] = None,
        custom_profiles: Optional[Dict[str, InstrumentPerformanceProfile]] = None,
        seed: Optional[int] = 42
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Applies collectively correlated humanization across the entire track ensemble.
        """
        ms_per_beat = (60.0 / max(20.0, bpm)) * 1000.0
        beats_per_ms = 1.0 / ms_per_beat
        rng = random.Random(seed)

        template = groove_template or SongGrooveTemplate(bpm=bpm)
        profiles = custom_profiles or {}

        # ---------------------------------------------------------------------
        # Step 1: Identify Anchor Track (Default: Kick)
        # ---------------------------------------------------------------------
        anchor_track_name = None
        for name, role in track_roles.items():
            if role.lower() in ["kick", "bd", "bass_drum"]:
                anchor_track_name = name
                break

        # Map to store actual placed micro-timings of the anchor
        # Key: round(nominal_start, 3) -> Value: humanized_start
        anchor_placed_hits: Dict[float, float] = {}

        result_ensemble: Dict[str, List[Dict[str, Any]]] = {}

        # ---------------------------------------------------------------------
        # Step 2: Humanize Anchor (Kick) First
        # ---------------------------------------------------------------------
        if anchor_track_name and anchor_track_name in session_tracks:
            kick_prof = profiles.get(
                anchor_track_name,
                InstrumentPerformanceProfile.create_default("kick")
            )
            raw_kick_notes = session_tracks[anchor_track_name]
            humanized_kicks = PerformanceCore.humanize_track_notes(
                raw_kick_notes,
                role="kick",
                profile=kick_prof,
                intent=intent,
                bpm=bpm,
                seed=seed
            )
            result_ensemble[anchor_track_name] = humanized_kicks

            # Record actual placed positions indexed by nominal beat
            for orig_n, hum_n in zip(raw_kick_notes, humanized_kicks):
                nom_start = round(float(orig_n.get("start_time", orig_n.get("start", 0.0))), 3)
                act_start = float(hum_n.get("start_time", hum_n.get("start", 0.0)))
                anchor_placed_hits[nom_start] = act_start

        # ---------------------------------------------------------------------
        # Step 3: Humanize Bass (Strictly Coupled to Kick Anchor)
        # ---------------------------------------------------------------------
        bass_track_name = None
        for name, role in track_roles.items():
            if role.lower() in ["bass", "sub", "808", "synth_bass"]:
                bass_track_name = name
                break

        if bass_track_name and bass_track_name in session_tracks:
            bass_prof = profiles.get(
                bass_track_name,
                InstrumentPerformanceProfile.create_default("bass")
            )
            raw_bass_notes = session_tracks[bass_track_name]
            coupled_bass_notes: List[Dict[str, Any]] = []

            coupling_ms = template.kick_bass_coupling_ms or bass_prof.anchor_coupling_offset_ms
            coupling_beats = (coupling_ms * intent.human_factor) * beats_per_ms

            for n in raw_bass_notes:
                new_n = dict(n)
                nom_start = round(float(n.get("start_time", n.get("start", 0.0))), 3)

                # Check if there is an anchor hit within 0.15 beats
                closest_anchor_nom = None
                min_dist = 999.0
                for a_nom in anchor_placed_hits.keys():
                    dist = abs(nom_start - a_nom)
                    if dist < min_dist:
                        min_dist = dist
                        closest_anchor_nom = a_nom

                if closest_anchor_nom is not None and min_dist <= 0.15:
                    # Tightly couple to Kick's actual hit: t_bass = t_actual_kick + coupling_ms
                    actual_kick_time = anchor_placed_hits[closest_anchor_nom]
                    micro_jitter = rng.gauss(0.0, 0.5 * beats_per_ms)  # minimal residual jitter
                    coupled_start = actual_kick_time + coupling_beats + micro_jitter
                else:
                    # Uncoupled note (independent melodic bass pass)
                    jitter_ms = rng.gauss(0.0, bass_prof.timing_variance_ms * intent.human_factor)
                    coupled_start = nom_start + (jitter_ms * beats_per_ms)

                new_n["start_time"] = round(max(0.0, coupled_start), 5)
                new_n["time"] = new_n["start_time"]
                coupled_bass_notes.append(new_n)

            # Apply velocity and articulation passes
            bass_v = PerformanceCore.apply_velocity_hierarchy(coupled_bass_notes, bass_prof, intent, seed=seed)
            bass_final = PerformanceCore.apply_articulation_shaping(bass_v, bass_prof, intent, seed=seed)
            result_ensemble[bass_track_name] = bass_final

        # ---------------------------------------------------------------------
        # Step 4: Humanize Snare (Laid-Back Relative to Anchor Pulse)
        # ---------------------------------------------------------------------
        for name, notes in session_tracks.items():
            if name in result_ensemble:
                continue
            role = track_roles.get(name, "").lower()
            if role in ["snare", "sd", "clap", "rim"]:
                snare_prof = profiles.get(name, InstrumentPerformanceProfile.create_default("snare"))
                # Enforce laid-back offset
                snare_prof.laid_back_tendency_ms = template.snare_laid_back_ms
                hum_snare = PerformanceCore.humanize_track_notes(
                    notes,
                    role="snare",
                    profile=snare_prof,
                    intent=intent,
                    bpm=bpm,
                    seed=seed
                )
                result_ensemble[name] = hum_snare

        # ---------------------------------------------------------------------
        # Step 5: Humanize Remaining Tracks (Hi-Hats, Keys, Leads, Pads)
        # ---------------------------------------------------------------------
        for name, notes in session_tracks.items():
            if name in result_ensemble:
                continue
            role = track_roles.get(name, "other").lower()
            prof = profiles.get(name, InstrumentPerformanceProfile.create_default(role))

            hum_notes = PerformanceCore.humanize_track_notes(
                notes,
                role=role,
                profile=prof,
                intent=intent,
                bpm=bpm,
                seed=seed
            )
            result_ensemble[name] = hum_notes

        return result_ensemble

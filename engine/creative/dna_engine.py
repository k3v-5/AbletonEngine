# engine/creative/dna_engine.py
"""
Creative Direction Engine (Phase 1):
Orchestrates aesthetic world-building, reference acoustic profiling,
harmonic DNA selection, frequency-slot track scaffolding, and arrangement energy blueprints.
Directly translates creative intent into physical Ableton Live session architecture.
"""

from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import json

from .models import (
    SongCreativeDNA,
    SonicWorld,
    AestheticMood,
    ReferenceProfile,
    SpectralTargetBand,
    HarmonicDNA,
    ModalFlavor,
    TrackRoleAllocation,
    ArrangementBlueprint,
    ArrangementSectionBlueprint
)


class CreativeDirectionEngine:
    """The master creative architect for Phase 1 of musical production."""

    # Curated Acoustic & Stylistic Reference Profiles
    REFERENCE_PROFILES: Dict[str, ReferenceProfile] = {
        "tyler_jid_neo_soul_trap": ReferenceProfile(
            reference_name="Tyler & JID - Hybrid Neo-Soul Trap (IGOR / Bones)",
            target_lufs=-14.0,
            true_peak_dbtp=-1.0,
            groove_signature="dilla_swing",
            groove_swing_amount=0.58,
            transient_character="punchy_clipped",
            spectral_bands={
                "sub": SpectralTargetBand(20.0, 60.0, target_energy_pct=22.0, width_stereo_pct=0.0),
                "low": SpectralTargetBand(60.0, 250.0, target_energy_pct=24.0, width_stereo_pct=20.0),
                "mid": SpectralTargetBand(250.0, 2500.0, target_energy_pct=32.0, width_stereo_pct=75.0),
                "presence": SpectralTargetBand(2500.0, 8000.0, target_energy_pct=14.0, width_stereo_pct=90.0),
                "air": SpectralTargetBand(8000.0, 20000.0, target_energy_pct=8.0, width_stereo_pct=120.0),
            }
        ),
        "atlanta_dark_trap": ReferenceProfile(
            reference_name="Metro Boomin / Future - Atlanta Dark Trap",
            target_lufs=-11.0,
            true_peak_dbtp=-1.0,
            groove_signature="atlanta_trap",
            groove_swing_amount=0.52,
            transient_character="punchy_clipped",
            spectral_bands={
                "sub": SpectralTargetBand(20.0, 60.0, target_energy_pct=28.0, width_stereo_pct=0.0),
                "low": SpectralTargetBand(60.0, 250.0, target_energy_pct=22.0, width_stereo_pct=15.0),
                "mid": SpectralTargetBand(250.0, 2500.0, target_energy_pct=28.0, width_stereo_pct=60.0),
                "presence": SpectralTargetBand(2500.0, 8000.0, target_energy_pct=14.0, width_stereo_pct=85.0),
                "air": SpectralTargetBand(8000.0, 20000.0, target_energy_pct=8.0, width_stereo_pct=110.0),
            }
        ),
        "melodic_neo_soul": ReferenceProfile(
            reference_name="J Dilla / Erykah Badu - Melodic Neo-Soul",
            target_lufs=-14.0,
            true_peak_dbtp=-1.0,
            groove_signature="dilla_swing",
            groove_swing_amount=0.62,
            transient_character="soft_warm",
            spectral_bands={
                "sub": SpectralTargetBand(20.0, 60.0, target_energy_pct=18.0, width_stereo_pct=0.0),
                "low": SpectralTargetBand(60.0, 250.0, target_energy_pct=26.0, width_stereo_pct=30.0),
                "mid": SpectralTargetBand(250.0, 2500.0, target_energy_pct=36.0, width_stereo_pct=80.0),
                "presence": SpectralTargetBand(2500.0, 8000.0, target_energy_pct=12.0, width_stereo_pct=85.0),
                "air": SpectralTargetBand(8000.0, 20000.0, target_energy_pct=8.0, width_stereo_pct=100.0),
            }
        ),
        "west_coast_bounce": ReferenceProfile(
            reference_name="Kendrick Lamar / Dr. Dre - West Coast Funk Bounce",
            target_lufs=-12.5,
            true_peak_dbtp=-1.0,
            groove_signature="mpc_60_swing",
            groove_swing_amount=0.55,
            transient_character="punchy_clipped",
            spectral_bands={
                "sub": SpectralTargetBand(20.0, 60.0, target_energy_pct=22.0, width_stereo_pct=0.0),
                "low": SpectralTargetBand(60.0, 250.0, target_energy_pct=25.0, width_stereo_pct=20.0),
                "mid": SpectralTargetBand(250.0, 2500.0, target_energy_pct=30.0, width_stereo_pct=70.0),
                "presence": SpectralTargetBand(2500.0, 8000.0, target_energy_pct=15.0, width_stereo_pct=95.0),
                "air": SpectralTargetBand(8000.0, 20000.0, target_energy_pct=8.0, width_stereo_pct=115.0),
            }
        )
    }

    @classmethod
    def get_available_reference_profiles(cls) -> Dict[str, Dict[str, Any]]:
        """Returns metadata for all built-in acoustic reference profiles."""
        out = {}
        for key, p in cls.REFERENCE_PROFILES.items():
            out[key] = {
                "name": p.reference_name,
                "target_lufs": p.target_lufs,
                "groove_signature": p.groove_signature,
                "groove_swing_amount": p.groove_swing_amount,
                "transient_character": p.transient_character,
            }
        return out

    @classmethod
    def build_default_track_scaffold(cls) -> List[TrackRoleAllocation]:
        """
        Creates the standard 8-track acoustic scaffolding, reserving distinct
        frequency slots to avoid masking from the start.
        """
        return [
            TrackRoleAllocation(
                track_name="Kick (808)",
                role="KICK",
                frequency_reservation="40 - 120 Hz",
                pan=0.0,
                initial_volume_db=-3.0,
                instrument_suggestion="Drum Rack / Simpler",
                recommended_preset="808 Tight Punch Kick",
                track_color="#D32F2F"
            ),
            TrackRoleAllocation(
                track_name="Snare & Clap",
                role="SNARE",
                frequency_reservation="180 - 6000 Hz",
                pan=0.0,
                initial_volume_db=-4.5,
                instrument_suggestion="Drum Rack / Simpler",
                recommended_preset="Layered Rim & Crisp Clap",
                track_color="#E64A19"
            ),
            TrackRoleAllocation(
                track_name="Hi-Hats",
                role="HATS",
                frequency_reservation="350 - 16000 Hz",
                pan=0.10,
                initial_volume_db=-7.0,
                instrument_suggestion="Drum Rack / Simpler",
                recommended_preset="Closed 808 & Open Tape Hat",
                track_color="#FFA000"
            ),
            TrackRoleAllocation(
                track_name="Perc & Foley",
                role="FOLEY",
                frequency_reservation="1000 - 14000 Hz",
                pan=-0.25,
                initial_volume_db=-10.0,
                instrument_suggestion="Audio / Simpler",
                recommended_preset="Vinyl Crackle & Shaker Bed",
                track_color="#388E3C"
            ),
            TrackRoleAllocation(
                track_name="808 Sub Bass",
                role="BASS",
                frequency_reservation="25 - 180 Hz",
                pan=0.0,
                initial_volume_db=-4.0,
                instrument_suggestion="Vital / Simpler",
                recommended_preset="Deep 808 Sine + 2nd Harmonic Tape",
                track_color="#FBC02D"
            ),
            TrackRoleAllocation(
                track_name="Rhodes Piano",
                role="CHORDS",
                frequency_reservation="150 - 6000 Hz",
                pan=-0.15,
                initial_volume_db=-6.0,
                instrument_suggestion="Electric / Rhodes Mark I",
                recommended_preset="Warm Vintage Tremolo Rhodes",
                track_color="#1976D2"
            ),
            TrackRoleAllocation(
                track_name="Lead Synth",
                role="LEAD",
                frequency_reservation="500 - 8000 Hz",
                pan=0.20,
                initial_volume_db=-8.0,
                instrument_suggestion="Vital / Wavetable",
                recommended_preset="Smooth Portamento Flute Lead",
                track_color="#0097A7"
            ),
            TrackRoleAllocation(
                track_name="Vocal Chops",
                role="VOCAL_HOOK",
                frequency_reservation="300 - 10000 Hz",
                pan=0.0,
                initial_volume_db=-7.5,
                instrument_suggestion="Simpler",
                recommended_preset="Formant-Shifted Pitched Chops",
                track_color="#7B1FA2"
            ),
        ]

    @classmethod
    def build_default_arrangement_blueprint(
        cls,
        total_bars: int = 96,
        tempo_bpm: float = 142.0
    ) -> ArrangementBlueprint:
        """
        Builds the 96-bar dynamic energy arrangement blueprint.
        Sections: Intro (8) -> Verse 1 (16) -> Pre-Chorus (8) -> Chorus (16)
        -> Verse 2 (16) -> Bridge (8) -> Final Chorus (16) -> Outro (8).
        """
        sections = [
            ArrangementSectionBlueprint(
                name="Intro",
                start_bar=0,
                duration_bars=8,
                target_energy=0.25,
                active_roles=["CHORDS", "FOLEY", "VOCAL_HOOK"],
                description="Intimate filtered Rhodes with vinyl foley bed and distant vocal chop."
            ),
            ArrangementSectionBlueprint(
                name="Verse 1",
                start_bar=8,
                duration_bars=16,
                target_energy=0.45,
                active_roles=["KICK", "SNARE", "HATS", "CHORDS", "BASS"],
                description="Groove locks in. Bass enters at bar 16. Vocal pocket wide open."
            ),
            ArrangementSectionBlueprint(
                name="Pre-Chorus",
                start_bar=24,
                duration_bars=8,
                target_energy=0.65,
                active_roles=["SNARE", "HATS", "CHORDS", "LEAD", "FOLEY"],
                description="Rising tension with high-pass filtering sweep and 16th-note hat builds."
            ),
            ArrangementSectionBlueprint(
                name="Chorus",
                start_bar=32,
                duration_bars=16,
                target_energy=0.90,
                active_roles=["KICK", "SNARE", "HATS", "BASS", "CHORDS", "LEAD", "VOCAL_HOOK"],
                description="Full drop: heavy 808 sub, wide stereo chords, and lead counter-melody."
            ),
            ArrangementSectionBlueprint(
                name="Verse 2",
                start_bar=48,
                duration_bars=16,
                target_energy=0.50,
                active_roles=["KICK", "SNARE", "HATS", "BASS", "CHORDS"],
                description="Subtle rhythmic evolution with syncopated 808 variations."
            ),
            ArrangementSectionBlueprint(
                name="Bridge",
                start_bar=64,
                duration_bars=8,
                target_energy=0.60,
                active_roles=["HATS", "CHORDS", "LEAD", "FOLEY"],
                description="Harmonic departure, half-time feel, leading into pre-drop vacuum."
            ),
            ArrangementSectionBlueprint(
                name="Final Chorus",
                start_bar=72,
                duration_bars=16,
                target_energy=1.00,
                active_roles=["KICK", "SNARE", "HATS", "FOLEY", "BASS", "CHORDS", "LEAD", "VOCAL_HOOK"],
                description="Peak climax: maximum polyphony, ear candy, and driving sub-bass."
            ),
            ArrangementSectionBlueprint(
                name="Outro",
                start_bar=88,
                duration_bars=8,
                target_energy=0.20,
                active_roles=["CHORDS", "FOLEY"],
                description="Deconstructive decay with Rhodes tail and fading vinyl dust."
            ),
        ]
        return ArrangementBlueprint(
            total_bars=total_bars,
            tempo_bpm=tempo_bpm,
            meter="4/4",
            sections=sections
        )

    @classmethod
    def formulate_creative_brief(
        cls,
        title: str = "Bones Groove Pt 3",
        artist: str = "Tyler & JID Tribute",
        genre: str = "hip_hop_neo_soul",
        reference_preset: str = "tyler_jid_neo_soul_trap",
        tempo_bpm: float = 142.0,
        key_root: str = "F",
        scale: str = "natural_minor",
        mood: AestheticMood = AestheticMood.NEO_SOUL_GROOVE
    ) -> SongCreativeDNA:
        """
        Formulates the complete creative and sonic direction brief.
        Combines world-building, acoustic reference DNA, harmonic rules,
        track slots, and arrangement energy curve into a master contract.
        """
        ref_profile = cls.REFERENCE_PROFILES.get(
            reference_preset,
            cls.REFERENCE_PROFILES["tyler_jid_neo_soul_trap"]
        )

        sonic_world = SonicWorld(
            mood=mood,
            harmonic_warmth=0.72,
            acoustic_space="intimate_dry",
            reverb_decay_seconds=1.6,
            dynamic_spread_db=12.5,
            saturation_character="tape_warmth",
            foley_texture="vinyl_dust"
        )

        harmonic_dna = HarmonicDNA(
            key_root=key_root,
            scale=scale,
            secondary_modes=[ModalFlavor.DORIAN, ModalFlavor.PHRYGIAN],
            chord_tension_level=0.70,
            voicing_density=4,
            voicing_spread="drop_2",
            allow_modal_interchange=True,
            bass_root_motion="functional_stepwise"
        )

        track_scaffold = cls.build_default_track_scaffold()
        arrangement = cls.build_default_arrangement_blueprint(total_bars=96, tempo_bpm=tempo_bpm)

        return SongCreativeDNA(
            title=title,
            artist=artist,
            genre=genre,
            sonic_world=sonic_world,
            reference_profile=ref_profile,
            harmonic_dna=harmonic_dna,
            track_scaffold=track_scaffold,
            arrangement_blueprint=arrangement,
            metadata={
                "created_by": "CreativeDirectionEngine",
                "phase": "PHASE_1_DNA",
                "version": "2.0.0"
            }
        )

    @classmethod
    def scaffold_live_project(
        cls,
        conn: Any,
        dna: SongCreativeDNA,
        create_cues: bool = True
    ) -> Dict[str, Any]:
        """
        Physically instantiates the creative DNA in Ableton Live:
        1. Configures global session tempo and signature.
        2. Creates and names each track in the scaffold.
        3. Configures initial track pan.
        4. Registers track roles in the Session Graph.
        5. Places arrangement section Cue Points (locators) along the timeline.
        """
        results: Dict[str, Any] = {
            "status": "SUCCESS",
            "tempo_applied": dna.arrangement_blueprint.tempo_bpm,
            "tracks_created": [],
            "cues_created": []
        }

        # 1. Apply tempo
        try:
            conn.send_command("set_tempo", {"tempo": float(dna.arrangement_blueprint.tempo_bpm)})
        except Exception:
            pass

        # 2. Query existing tracks
        existing_tracks = []
        try:
            s_info = conn.send_command("get_session_info", {})
            cnt = int(s_info.get("result", {}).get("track_count", 0)) if isinstance(s_info, dict) else 0
            for t_idx in range(cnt):
                t_info = conn.send_command("get_track_info", {"track_index": t_idx})
                t_name = t_info.get("result", {}).get("name", "") if isinstance(t_info, dict) else ""
                existing_tracks.append({"index": t_idx, "name": t_name})
        except Exception:
            pass

        # 3. Create or reuse tracks according to scaffold
        for alloc in dna.track_scaffold:
            target_idx = None
            # Check if track already exists with matching name
            for et in existing_tracks:
                if alloc.track_name.lower() in et["name"].lower() or alloc.role.lower() in et["name"].lower():
                    target_idx = et["index"]
                    break

            if target_idx is None:
                # Create new track
                try:
                    create_res = conn.send_command("create_midi_track", {})
                    # Find index of newly created track
                    s_info = conn.send_command("get_session_info", {})
                    new_cnt = int(s_info.get("result", {}).get("track_count", 0)) if isinstance(s_info, dict) else 0
                    target_idx = max(0, new_cnt - 1)
                except Exception:
                    target_idx = len(existing_tracks)

            # Set track name
            try:
                conn.send_command("set_track_name", {
                    "track_index": target_idx,
                    "name": alloc.track_name
                })
            except Exception:
                pass

            # Set panning
            try:
                # Normalize pan: -1.0..1.0 -> 0.0..1.0 in Live (0.5 = center)
                norm_pan = float((alloc.pan + 1.0) / 2.0)
                conn.send_command("set_track_panning", {
                    "track_index": target_idx,
                    "panning": norm_pan
                })
            except Exception:
                pass

            # Register in Session Graph
            try:
                from engine.core.graph import SessionGraph
                graph = SessionGraph()
                graph.set_role(target_idx, alloc.role.lower())
                graph.set_tags(target_idx, ["scaffolded", "phase_1", alloc.role.lower()])
            except Exception:
                pass

            results["tracks_created"].append({
                "track_index": target_idx,
                "track_name": alloc.track_name,
                "role": alloc.role,
                "pan": alloc.pan,
                "frequency_reservation": alloc.frequency_reservation
            })

        # 4. Create arrangement Cue Points if requested
        if create_cues:
            for sec in dna.arrangement_blueprint.sections:
                # Time in beats: 4 beats per bar
                time_beats = float(sec.start_bar * 4.0)
                try:
                    cue_res = conn.send_command("create_cue_point", {
                        "time": time_beats,
                        "name": f"{sec.name} (Energy {int(sec.target_energy * 100)}%)"
                    })
                    results["cues_created"].append({
                        "name": sec.name,
                        "bar": sec.start_bar,
                        "time_beats": time_beats,
                        "status": cue_res.get("status", "SUCCESS")
                    })
                except Exception:
                    results["cues_created"].append({
                        "name": sec.name,
                        "bar": sec.start_bar,
                        "time_beats": time_beats,
                        "status": "FAILED_OR_UNAVAILABLE"
                    })

        return results

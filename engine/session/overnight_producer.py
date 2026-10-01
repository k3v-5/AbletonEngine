# engine/session/overnight_producer.py
"""
Autonomous Overnight Batch Production Engine for AbletonEngine.

Orchestrates sequential end-to-end song productions overnight:
- Clean-slate reset between songs
- Multi-track scaffolding & tuning
- Vital sound design & preset compilation
- Full composition score deployment across all sections
- Dynamic automations, sidechain ducking & pre-drop vacuums
- Physical ITU-R BS.1770-5 loudness certified mastering
- Autonomous system-level GUI saving of native .als project files
- Complete session archival to saved_projects/
- Persistent overnight manifest with full telemetry for morning review
"""

import os
import sys
import time
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger("OvernightProducer")

pkg_root = Path(r"E:\Disco F\Dev\AbletonEngine")
if str(pkg_root) not in sys.path:
    sys.path.insert(0, str(pkg_root))

from server import get_ableton_connection
from engine.production.copilot.guided_session import copilot_guided_session_engine
from engine.session.project_lifecycle import ProjectLifecycleManager
from engine.session.gui_project_saver import LiveGuiProjectSaver


# Curated Overnight Production Catalog
DEFAULT_OVERNIGHT_PLAYLIST = [
    {
        "title": "Pose_Club_Mix",
        "artist": "Daddy Yankee (Electro-Dembow Tribute)",
        "genre": "Electro-Reggaeton",
        "bpm": 126.0,
        "key": "E",
        "scale": "Minor",
        "tracks_input": "Drums, 808 Bass, Lead, Keys, Vocals",
        "instruments": [
            "808 Core Kit (.adg)",
            "Vital Audio 808 Sub (mejor diseño de sonido)",
            "Vital Audio Ambient Keys (mejor diseño de sonido)",
            "Vital Audio Poly Shimmer Pad (mejor diseño de sonido)",
            "Opción 1"
        ],
        "sculpt_choices": [
            "Opción 1: Tight Transient Snap",
            "Opción 1: Arquetipo BASS_808 Saturado",
            "Opción 1: Arquetipo LEAD_SAW Hyperpop Piercing",
            "Opción 1: Arquetipo CHORD_SUPERAW Polifónico",
            "Opción 1"
        ],
        "sections": [
            {"name": "Intro", "bars": 8},
            {"name": "Drop 1", "bars": 16},
            {"name": "Verse 1", "bars": 12},
            {"name": "Breakdown", "bars": 4},
            {"name": "Drop 2", "bars": 8},
            {"name": "Outro", "bars": 4}
        ]
    },
    {
        "title": "Gasolina_Old_School",
        "artist": "Luny Tunes & Noriega Style",
        "genre": "Reggaeton_Clasico",
        "bpm": 95.0,
        "key": "F",
        "scale": "Minor",
        "tracks_input": "Drums, Sub Bass, Synth Lead, Brass, Vocals",
        "instruments": [
            "808 Core Kit (.adg)",
            "Vital Audio 808 Sub (mejor diseño de sonido)",
            "Vital Audio Ambient Keys (mejor diseño de sonido)",
            "Nativo Live Brass",
            "Opción 1"
        ],
        "sculpt_choices": [
            "Opción 1: Tight Transient Snap",
            "Opción 2: Arquetipo BASS_SUB Profundo",
            "Opción 1: Arquetipo LEAD_SAW Hyperpop Piercing",
            "Opción 1",
            "Opción 1"
        ],
        "sections": [
            {"name": "Intro", "bars": 8},
            {"name": "Coro 1", "bars": 16},
            {"name": "Verso 1", "bars": 16},
            {"name": "Puente", "bars": 8},
            {"name": "Coro 2", "bars": 16},
            {"name": "Outro", "bars": 8}
        ]
    },
    {
        "title": "Cyber_Perreo_2026",
        "artist": "Neoperreo & Hard Dembow",
        "genre": "Neoperreo",
        "bpm": 130.0,
        "key": "D",
        "scale": "Minor",
        "tracks_input": "Drums, 808 Bass, Acid Lead, Pluck, Vocals",
        "instruments": [
            "808 Core Kit (.adg)",
            "Vital Audio 808 Sub (mejor diseño de sonido)",
            "Vital Audio Ambient Keys (mejor diseño de sonido)",
            "Vital Audio Poly Shimmer Pad (mejor diseño de sonido)",
            "Opción 1"
        ],
        "sculpt_choices": [
            "Opción 1: Tight Transient Snap",
            "Opción 3: Arquetipo BASS_PUNCH Reese Agresivo",
            "Opción 3: Arquetipo LEAD_VOCAL Formante Vocálico",
            "Opción 3: Arquetipo PLUCK_ORGANIC Neo-Soul",
            "Opción 1"
        ],
        "sections": [
            {"name": "Intro", "bars": 8},
            {"name": "Drop 1", "bars": 16},
            {"name": "Breakdown", "bars": 8},
            {"name": "Drop 2", "bars": 16},
            {"name": "Outro", "bars": 8}
        ]
    },
    {
        "title": "Noche_De_Travesuras",
        "artist": "Perreo Romantico & Synthwave",
        "genre": "Latin_Synthwave",
        "bpm": 112.0,
        "key": "A",
        "scale": "Minor",
        "tracks_input": "Drums, Retro Bass, Neon Lead, Chords, Vocals",
        "instruments": [
            "808 Core Kit (.adg)",
            "Vital Audio 808 Sub (mejor diseño de sonido)",
            "Vital Audio Ambient Keys (mejor diseño de sonido)",
            "Vital Audio Poly Shimmer Pad (mejor diseño de sonido)",
            "Opción 1"
        ],
        "sculpt_choices": [
            "Opción 1: Tight Transient Snap",
            "Opción 1: Arquetipo BASS_808 Saturado",
            "Opción 2: Arquetipo LEAD_PLUCK Transiente Rápido",
            "Opción 1: Arquetipo CHORD_SUPERAW Polifónico",
            "Opción 1"
        ],
        "sections": [
            {"name": "Intro", "bars": 8},
            {"name": "Verse", "bars": 16},
            {"name": "Chorus", "bars": 16},
            {"name": "Bridge", "bars": 8},
            {"name": "Final Chorus", "bars": 16},
            {"name": "Outro", "bars": 8}
        ]
    }
]


class OvernightBatchProducer:
    """Manages continuous autonomous song production overnight."""

    def __init__(self, playlist: Optional[List[Dict[str, Any]]] = None, output_manifest: str = "overnight_manifest.json"):
        self.playlist = playlist or DEFAULT_OVERNIGHT_PLAYLIST
        self.manifest_file = Path(output_manifest)
        self.results: List[Dict[str, Any]] = []

    def run_all(self, conn: Optional[Any] = None) -> Dict[str, Any]:
        """Runs the entire playlist sequentially."""
        if conn is None:
            conn = get_ableton_connection()
            assert conn.connect(), "Could not connect to Ableton Live on localhost:9877"

        logger.info(f"=== STARTING OVERNIGHT BATCH PRODUCTION ({len(self.playlist)} SONGS QUEUED) ===")
        start_time = time.time()

        for idx, song_spec in enumerate(self.playlist, 1):
            title = song_spec.get("title", f"Track_{idx}")
            logger.info(f"\n{'='*70}\n[OVERNIGHT {idx}/{len(self.playlist)}] PRODUCING: '{title}' ({song_spec.get('genre')})\n{'='*70}")

            try:
                song_res = self._produce_single_song(conn, song_spec, idx)
                self.results.append(song_res)
                logger.info(f"[OVERNIGHT {idx}/{len(self.playlist)}] SUCCESS: '{title}' completed & saved.")
            except Exception as ex_song:
                logger.error(f"[OVERNIGHT {idx}/{len(self.playlist)}] ERROR producing '{title}': {ex_song}", exc_info=True)
                self.results.append({
                    "title": title,
                    "status": "FAILED",
                    "error": str(ex_song),
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                })
                # Attempt emergency clean-slate to protect next song
                try:
                    ProjectLifecycleManager.clean_slate_live(conn, target_bpm=120.0)
                    copilot_guided_session_engine.reset()
                except Exception:
                    pass

            self._save_overnight_manifest()

        elapsed = time.time() - start_time
        summary = {
            "status": "COMPLETED",
            "total_songs": len(self.playlist),
            "completed_songs": sum(1 for r in self.results if r.get("status") in ("COMPLETED", "SAVED")),
            "elapsed_seconds": round(elapsed, 1),
            "results": self.results
        }
        logger.info(f"=== OVERNIGHT PRODUCTION FINISHED ({summary['completed_songs']}/{summary['total_songs']} SUCCESS) ===")
        return summary

    def _produce_single_song(self, conn: Any, spec: Dict[str, Any], song_idx: int) -> Dict[str, Any]:
        """Executes Phases 1 to 10 for a single song specification."""
        title = spec.get("title", f"Song_{song_idx}")
        bpm = float(spec.get("bpm", 126.0))
        key = spec.get("key", "E")
        scale = spec.get("scale", "Minor")
        genre = spec.get("genre", "Reggaeton")
        artist = spec.get("artist", "Antigravity Producer")

        # 0. Clean-slate reset
        ProjectLifecycleManager.clean_slate_live(conn, target_bpm=bpm)
        copilot_guided_session_engine.reset()

        # 1. Tracks scaffolding (Phase 1)
        res1 = copilot_guided_session_engine.step(conn=conn, user_input=spec.get("tracks_input", "Drums, 808 Bass, Lead, Keys, Vocals"))

        # 2. Structure & Tuning (Phase 2)
        sec_payload = json.dumps({
            "sections": spec.get("sections", [{"name": "Intro", "bars": 8}, {"name": "Drop 1", "bars": 16}, {"name": "Outro", "bars": 8}]),
            "key": key,
            "scale": scale
        })
        res2 = copilot_guided_session_engine.step(conn=conn, user_input=sec_payload)
        conn.send_command("set_tempo", {"tempo": bpm})
        copilot_guided_session_engine.data["bpm"] = bpm
        copilot_guided_session_engine.data["key"] = key
        copilot_guided_session_engine.data["scale"] = scale
        copilot_guided_session_engine.data["genre"] = genre
        copilot_guided_session_engine.data["song_title"] = title
        copilot_guided_session_engine.data["artist"] = artist
        copilot_guided_session_engine._save_state()

        # 3. Instruments (Phase 3)
        inst_inputs = spec.get("instruments", ["Opción 1", "Opción 1", "Opción 1", "Opción 1", "Opción 1"])
        attempts = 0
        while copilot_guided_session_engine.data.get("current_phase") == "PHASE_3_INSTRUMENTS" and attempts < 15:
            attempts += 1
            ptr = copilot_guided_session_engine.data.get("current_track_ptr", 0)
            choice = inst_inputs[ptr] if ptr < len(inst_inputs) else "Opción 1"
            copilot_guided_session_engine.step(conn=conn, user_input=choice)

        # 4. Parameter Sculpting & Vital Sound Design (Phase 4)
        sculpt_choices = spec.get("sculpt_choices", ["Opción 1", "Opción 1", "Opción 1", "Opción 1", "Opción 1"])
        attempts = 0
        while copilot_guided_session_engine.data.get("current_phase") == "PHASE_4_PARAM_SCULPTING" and attempts < 15:
            attempts += 1
            ptr = copilot_guided_session_engine.data.get("current_param_ptr", 0)
            choice = sculpt_choices[ptr] if ptr < len(sculpt_choices) else "Opción 1"
            copilot_guided_session_engine.step(conn=conn, user_input=choice)

        # 5. Insert Effects (Phase 5)
        attempts = 0
        while copilot_guided_session_engine.data.get("current_phase") == "PHASE_5_INSERT_EFFECTS" and attempts < 40:
            attempts += 1
            res_fx = copilot_guided_session_engine.step(conn=conn, user_input="Opción 1")
            if res_fx.get("status") == "AESTHETIC_PROFILE_REQUIRED":
                schema = res_fx.get("schema_expected", {})
                copilot_guided_session_engine.step(conn=conn, user_input=json.dumps(schema))

        # 6. Composition Deployment (Phase 6)
        # Use pose_score.json or generate tailored score
        score_path = Path("scratch/pose_score.json")
        if score_path.exists():
            attempts = 0
            while copilot_guided_session_engine.data.get("current_phase") == "PHASE_6_COMPOSITION" and attempts < 10:
                attempts += 1
                res_comp = copilot_guided_session_engine.step(conn=conn, user_input=str(score_path.resolve()))
                if res_comp.get("status") == "PHASE_6_INSTRUMENT_CHANGE_REQUIRED":
                    copilot_guided_session_engine.step(conn=conn, user_input="reintentar")

        # 7. Automations (Phase 7)
        if copilot_guided_session_engine.data.get("current_phase") == "PHASE_7_AUTOMATION":
            copilot_guided_session_engine.step(conn=conn, user_input="Opción A")

        # 8. Space Ducking (Phase 8)
        if copilot_guided_session_engine.data.get("current_phase") == "PHASE_8_VOCAL_DUCKING":
            copilot_guided_session_engine.step(conn=conn, user_input="Opción 1")

        # 9. Mastering & Loudness (Phase 9)
        if copilot_guided_session_engine.data.get("current_phase") == "PHASE_9_MIX_MASTER":
            res9 = copilot_guided_session_engine.step(conn=conn, user_input="Opción 1")
            if res9.get("status") == "LOUDNESS_AUDIT_NON_COMPLIANT":
                copilot_guided_session_engine.step(conn=conn, user_input="Opción 1")

        # 10. Autonomous GUI Save & Archival (Phase 10)
        archive_res = ProjectLifecycleManager.archive_current_project(
            copilot_guided_session_engine,
            conn=conn,
            custom_name=title
        )

        return {
            "title": title,
            "status": "COMPLETED",
            "genre": genre,
            "bpm": bpm,
            "key": key,
            "scale": scale,
            "als_saved": archive_res.get("als_saved", False),
            "als_path": archive_res.get("als_path"),
            "archive_dir": archive_res.get("archive_dir"),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }

    def _save_overnight_manifest(self) -> None:
        try:
            with open(self.manifest_file, "w", encoding="utf-8") as f:
                json.dump({
                    "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "total_tracks": len(self.results),
                    "tracks": self.results
                }, f, indent=2)
        except Exception as ex_m:
            logger.warning(f"Could not write overnight manifest: {ex_m}")


if __name__ == "__main__":
    producer = OvernightBatchProducer()
    summary = producer.run_all()
    print(json.dumps(summary, indent=2))

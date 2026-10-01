# engine/session/project_lifecycle.py
"""
Project Lifecycle Manager:
Orchestrates saving, archiving, and clean-slate resets between song productions.
Enables the producer to safely persist completed tracks (metadata, MIDI scores, Vital presets,
mix/master state) and seamlessly start a new production from Phase 1 without restarting Ableton Live.
"""

import os
import json
import time
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

from engine.session.clean_slate import CleanSlateManager
from engine.production.copilot.state_manager import CopilotStateManager
from engine.production.copilot.nlp_parser import _normalize_text

logger = logging.getLogger("ProjectLifecycle")


class ProjectLifecycleManager:
    """Manages project persistence, archiving, and clean transitions between productions."""

    SAVED_PROJECTS_DIR = Path("saved_projects")
    PRIMARY_SONGS_DIR = Path(r"F:\Canciones")
    FALLBACK_SONGS_DIR = Path(r"E:\Disco F\Proyectos Musicales")

    @classmethod
    def get_current_project_name(cls, session: Any) -> str:
        """Derives a meaningful project name from session data or fallback."""
        if hasattr(session, "data") and isinstance(session.data, dict):
            # Try to get song title, artist, or style
            title = session.data.get("song_title") or session.data.get("title")
            if title:
                return str(title).strip()
            genre = session.data.get("genre", "")
            key = session.data.get("key", "")
            scale = session.data.get("scale", "")
            tracks = session.data.get("tracks", [])
            if tracks:
                first_name = tracks[0].get("name", "Beat")
                return f"{genre}_{first_name}".strip("_") or "Current_Project"
        return "Ableton_Production"

    @classmethod
    def archive_current_project(
        cls,
        session: Any,
        conn: Any = None,
        custom_name: Optional[str] = None,
        genre: Optional[str] = None
    ) -> Dict[str, Any]:
        r"""
        Creates a complete, self-contained project archive inside F:\Canciones\<Genre>\<Song_Name>:
        - <Song_Name> Project / <Song_Name>.als (Native Ableton Live Project)
        - Presets/ (Synthesized .vital presets and presets manifest)
        - GuidedSession_Info/ (guided_session_state.json, scores, project_manifest.json, report)
        - saved_projects/ historical rollback snapshot
        """
        from engine.session.gui_project_saver import LiveGuiProjectSaver, normalize_genre_family

        s_data = session.data if hasattr(session, "data") else {}
        proj_genre = genre or s_data.get("genre") or "Reggaeton"
        safe_genre = normalize_genre_family(proj_genre)

        proj_name = custom_name or cls.get_current_project_name(session)
        safe_name = "".join(c for c in proj_name if c.isalnum() or c in ("_", "-")).strip() or "Project"
        timestamp = time.strftime("%Y%m%d_%H%M%S")

        # 1. Base Target Directories: Primary in F:\Canciones\<Genre>\<Song_Name>
        base_songs_root = cls.PRIMARY_SONGS_DIR if (cls.PRIMARY_SONGS_DIR.exists() or Path("F:/").exists()) else cls.FALLBACK_SONGS_DIR
        song_project_dir = base_songs_root / safe_genre / safe_name
        song_project_dir.mkdir(parents=True, exist_ok=True)

        target_dir = cls.SAVED_PROJECTS_DIR / f"{safe_name}_{timestamp}"
        target_dir.mkdir(parents=True, exist_ok=True)

        archived_files = []

        # 2. Presets Directory inside Song Project: F:\Canciones\<Genre>\<Song_Name>\Presets
        song_presets_dir = song_project_dir / "Presets"
        song_presets_dir.mkdir(parents=True, exist_ok=True)
        archive_presets_dir = target_dir / "presets"
        archive_presets_dir.mkdir(parents=True, exist_ok=True)

        vital_cache = Path("cache/vital_presets")
        vital_user = Path(r"D:\Documentos\Vital\User\Presets\PIE_Presets")
        active_presets = []

        # Collect presets from cache and user dir
        for p_dir in [vital_cache, vital_user]:
            if p_dir.exists():
                for v_file in p_dir.glob("*.vital"):
                    dst_song = song_presets_dir / v_file.name
                    dst_arch = archive_presets_dir / v_file.name
                    shutil.copy2(v_file, dst_song)
                    shutil.copy2(v_file, dst_arch)
                    archived_files.append(str(dst_song))
                    if v_file.name not in active_presets:
                        active_presets.append(v_file.name)

        # Write presets manifest
        tracks = s_data.get("tracks", [])
        presets_manifest = {
            "song": safe_name,
            "genre": safe_genre,
            "total_presets": len(active_presets),
            "presets": active_presets,
            "tracks": [
                {
                    "track_index": t.get("index", idx),
                    "track_name": t.get("name", f"Track {idx}"),
                    "role": t.get("role", "OTHER"),
                    "instrument": t.get("instrument", "Unknown")
                }
                for idx, t in enumerate(tracks)
            ]
        }
        with open(song_presets_dir / "presets_manifest.json", "w", encoding="utf-8") as f_pm:
            json.dump(presets_manifest, f_pm, indent=2)
        archived_files.append(str(song_presets_dir / "presets_manifest.json"))

        # 3. Guided Session Info inside Song Project: F:\Canciones\<Genre>\<Song_Name>\GuidedSession_Info
        song_info_dir = song_project_dir / "GuidedSession_Info"
        song_info_dir.mkdir(parents=True, exist_ok=True)

        session_state_file = CopilotStateManager.STATE_FILE
        if session_state_file.exists():
            dst_info = song_info_dir / "guided_session_state.json"
            dst_arch = target_dir / "guided_session_state.json"
            shutil.copy2(session_state_file, dst_info)
            shutil.copy2(session_state_file, dst_arch)
            archived_files.append(str(dst_info))

        # Copy Active Score Files
        scratch_dir = Path("scratch")
        if scratch_dir.exists():
            song_scores_dir = song_info_dir / "scores"
            song_scores_dir.mkdir(parents=True, exist_ok=True)
            arch_scores_dir = target_dir / "scores"
            arch_scores_dir.mkdir(parents=True, exist_ok=True)
            for score_file in scratch_dir.glob("*score*.json"):
                dst_score = song_scores_dir / score_file.name
                dst_arch = arch_scores_dir / score_file.name
                shutil.copy2(score_file, dst_score)
                shutil.copy2(score_file, dst_arch)
                archived_files.append(str(dst_score))

        # 4. Generate Project Manifest and Summary Report
        manifest = {
            "project_name": proj_name,
            "genre": safe_genre,
            "archived_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "bpm": s_data.get("bpm", 120.0),
            "key": s_data.get("key", "C"),
            "scale": s_data.get("scale", "natural_minor"),
            "phase_reached": s_data.get("current_phase", "PHASE_10_COMPLETED"),
            "tracks_count": len(tracks),
            "tracks": [
                {
                    "index": t.get("index", idx),
                    "name": t.get("name", f"Track {idx}"),
                    "role": t.get("role", "OTHER"),
                    "instrument": t.get("instrument", "Unknown")
                }
                for idx, t in enumerate(tracks)
            ],
            "archived_files_count": len(archived_files)
        }

        manifest_path_song = song_info_dir / "project_manifest.json"
        manifest_path_arch = target_dir / "project_manifest.json"
        for m_p in [manifest_path_song, manifest_path_arch]:
            with open(m_p, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)
        archived_files.append(str(manifest_path_song))

        # Generate Guided Session Human-Readable Report
        report_path = song_info_dir / "guided_session_report.md"
        report_content = f"""# 🎵 Guided Session Production Report: {safe_name}

- **Genre Family:** {safe_genre}
- **Tempo:** {manifest['bpm']} BPM
- **Key & Scale:** {manifest['key']} {manifest['scale']}
- **Produced via:** AbletonEngine Guided Session Engine (Phases 1-10)
- **Saved Location:** `{song_project_dir}`

## Track Architecture
| Index | Track Name | Role | Instrument / Device Chain |
|-------|------------|------|---------------------------|
"""
        for t in manifest["tracks"]:
            report_content += f"| {t['index']} | {t['name']} | {t['role']} | {t['instrument']} |\n"

        report_content += f"""
## Presets & Sound Design
All synthesized Vital presets used for this production have been exported into:
`{song_presets_dir}`

## Project Files
- Ableton Live Set: `{safe_name}.als` (located in `{song_project_dir}`)
- Presets Manifest: `presets_manifest.json`
- Session Metadata: `guided_session_state.json`
"""
        with open(report_path, "w", encoding="utf-8") as f_rep:
            f_rep.write(report_content)
        archived_files.append(str(report_path))

        # 5. Autonomous Native Live Set (.als) Save via GUI Automation
        als_saved_info = None
        is_test_env = bool(
            os.environ.get("PYTEST_CURRENT_TEST")
            or getattr(session, "_is_test_mode", False)
            or (conn is not None and getattr(conn, "__class__", None).__name__ == "MockAbletonAdapter")
            or "test" in str(proj_name).lower()
        )
        if not is_test_env:
            try:
                als_saved_info = LiveGuiProjectSaver.save_live_set(
                    project_name=safe_name,
                    genre=safe_genre,
                    base_dir=base_songs_root
                )
                if als_saved_info.get("success"):
                    logger.info(f"Native Ableton Live Set (.als) saved autonomously: {als_saved_info.get('path')}")
                    target_als = Path(als_saved_info.get("path", ""))
                    if target_als.exists():
                        archive_als = target_dir / target_als.name
                        try:
                            shutil.copy2(target_als, archive_als)
                            archived_files.append(str(archive_als))
                        except Exception:
                            pass
            except Exception as ex_als_save:
                logger.warning(f"Notice on autonomous Live Set save: {ex_als_save}")

        # 6. Create Checkpoint Snapshot
        snapshot_file = CleanSlateManager.create_snapshot(s_data, tag=f"archive_{safe_name}")

        logger.info(f"Project '{proj_name}' persisted to {song_project_dir} and archived to {target_dir}")

        return {
            "status": "ARCHIVED",
            "project_name": proj_name,
            "genre": safe_genre,
            "song_project_dir": str(song_project_dir),
            "archive_dir": str(target_dir),
            "archived_files": archived_files,
            "snapshot_file": str(snapshot_file),
            "als_saved": als_saved_info.get("success", False) if als_saved_info else False,
            "als_path": als_saved_info.get("path") if als_saved_info else None
        }

    @classmethod
    def clean_slate_live(cls, conn: Any, target_bpm: float = 120.0) -> Dict[str, Any]:
        """
        Deep-cleans Ableton Live to a pristine 1-track baseline:
        - Stops playback
        - Sets default tempo
        - Deletes clips in arrangement and session view
        - Deletes extra tracks (keeps Track 0)
        - Clears devices from Track 0 and Master Track
        - Clears cue points
        """
        if not conn or not hasattr(conn, "send_command"):
            return {"status": "SKIPPED_NO_CONN"}

        try:
            conn.send_command("stop_playback", {})
            conn.send_command("set_tempo", {"tempo": target_bpm})

            # 1. Purge cue points via Remote Script delete_cue_point loop
            try:
                for _ in range(30):
                    cues_info = conn.send_command("get_cue_points", {})
                    c_data = cues_info.get("result", cues_info) if isinstance(cues_info, dict) else {}
                    c_list = c_data.get("cue_points", []) if isinstance(c_data, dict) else []
                    if not c_list:
                        break
                    conn.send_command("delete_cue_point", {"time_or_index": 0})
            except Exception as ex_cues:
                logger.debug(f"Cue purge notice: {ex_cues}")

            # 2. LOM Deep Clean: Reduce tracks and groups to 1 pristine track and clear master
            clean_code = """
import Live

# 1. Stop playback
song.stop_playing()

# 2. Clean Master Track devices and restore safe volume
m = song.master_track
while len(m.devices) > 0:
    m.delete_device(len(m.devices) - 1)
m.mixer_device.volume.value = 0.85

# 3. Remove all tracks cleanly down to 1 pristine MIDI track
# Always create a fresh MIDI track first so we never have 0 tracks or leave an empty group header
song.create_midi_track()
initial_count = len(song.tracks) - 1
for i in range(initial_count - 1, -1, -1):
    try:
        song.delete_track(i)
    except Exception:
        pass

# 4. Reset remaining Track 0
if len(song.tracks) >= 1:
    t0 = song.tracks[0]
    t0.name = "1-MIDI"
    t0.mute = False
    t0.solo = False
    t0.arm = False
    t0.mixer_device.volume.value = 0.85
    t0.mixer_device.panning.value = 0.0
    while len(t0.devices) > 0:
        t0.delete_device(len(t0.devices) - 1)
    for cs in t0.clip_slots:
        if cs.has_clip:
            cs.delete_clip()

result = {"tracks_remaining": len(song.tracks), "tempo": song.tempo}
"""
            res = conn.send_command("execute_code", {"code": clean_code})
            logger.info(f"Live deep clean executed: {res}")
            return {"status": "LIVE_CLEANED", "details": res}
        except Exception as e:
            logger.warning(f"Live deep clean notice: {e}")
            # Fallback to standard CleanSlateManager
            return CleanSlateManager.reset_session(conn, target_bpm=target_bpm)

    @classmethod
    def start_new_project(
        cls,
        session: Any,
        conn: Any = None,
        target_bpm: float = 120.0,
        save_first: bool = True,
        project_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes end-to-end lifecycle transition:
        1. Archives current project (if save_first is True)
        2. Cleans Ableton Live to pristine baseline
        3. Resets CopilotGuidedSession state to Phase 1
        4. Returns the Phase 1 questionnaire
        """
        archive_info = None
        if save_first:
            archive_info = cls.archive_current_project(session, conn, custom_name=project_name)

        # Clean Live DAW
        live_clean_res = cls.clean_slate_live(conn, target_bpm=target_bpm)

        # Reset Guided Session state to Phase 1
        session.reset()

        # Prompt Phase 1
        phase1_prompt = session._prompt_phase_1()

        action_summary = "Proyecto anterior archivado y nuevo proyecto iniciado." if save_first else "Nuevo proyecto iniciado (sin archivar)."

        return {
            "current_step": "PASO 1 DE 7: ARQUITECTURA DE PISTAS (NUEVO PROYECTO)",
            "action_taken": f"{action_summary} Live restablecido a lienzo virgen (1 pista limpia, tempo {target_bpm} BPM).",
            "question": (
                f"🎉 **¡Nuevo Proyecto Iniciado con Éxito!**\n\n"
                + (f"📁 *El proyecto anterior '{archive_info.get('project_name')}' fue archivado de forma segura en:*\n`{archive_info.get('archive_dir')}`\n\n" if archive_info else "")
                + f"Live ha sido restablecido a su estado inicial limpio.\n\n"
                f"---\n\n"
                + phase1_prompt.get("question", "")
            ),
            "instructions_for_ai": "Guía al usuario en la concepción del nuevo track (género, tempo, escala y asignación de pistas).",
            "phase": "PHASE_1_TRACKS",
            "status": "NEW_PROJECT_STARTED",
            "archive_info": archive_info,
            "live_status": live_clean_res
        }

    @classmethod
    def prompt_lifecycle_decision(cls, session: Any, project_name: Optional[str] = None) -> Dict[str, Any]:
        """Renders the interactive decision modal/prompt to the user."""
        current_name = project_name or cls.get_current_project_name(session)
        phase = session.data.get("current_phase", "SESSION") if hasattr(session, "data") else "SESSION"

        question = (
            f"💾 **Decisión de Ciclo de Vida del Proyecto**\n\n"
            f"Proyecto actual: **'{current_name}'** (Estado: `{phase}`)\n\n"
            f"¿Deseas guardar y archivar el proyecto actual y comenzar una nueva producción desde cero?\n\n"
            f"📋 **Opciones Disponibles:**\n"
            f"• **Opción 1: Guardar y Empezar de Nuevo (Recomendado)**\n"
            f"  *Archiva todo el estado actual (metadata, partituras MIDI, presets de Vital, mezclas) en `saved_projects/`, "
            f"limpia Ableton Live a lienzo virgen y arranca el Paso 1 para un nuevo track.*\n\n"
            f"• **Opción 2: Empezar de Nuevo sin Guardar**\n"
            f"  *Descarta el estado actual, restablece Live a estado limpio y reinicia el motor en Fase 1.*\n\n"
            f"• **Opción 3: Solo Guardar y Archivar**\n"
            f"  *Guarda el paquete completo del proyecto actual y permanece en la sesión actual.*\n\n"
            f"• **Opción 4: Cancelar**\n"
            f"  *Cancela la operación y continúa trabajando en la sesión actual.*\n\n"
            f"*Responde con el número de opción (ej: 'Opción 1') o escribe tu decisión.*"
        )

        return {
            "current_step": "DECISIÓN: GUARDAR PROYECTO Y EMPEZAR DE NUEVO",
            "action_taken": f"Menú de ciclo de vida del proyecto abierto para '{current_name}'.",
            "question": question,
            "instructions_for_ai": "Consulta al usuario si desea archivar y reiniciar la sesión para un nuevo track.",
            "phase": phase,
            "lifecycle_decision_active": True
        }

    @classmethod
    def handle_lifecycle_decision(cls, session: Any, conn: Any, user_input: str) -> Dict[str, Any]:
        """Executes the chosen decision branch."""
        text = _normalize_text(user_input)

        # Cancel
        if any(w in text for w in ["cancelar", "seguir", "continuar", "quedarme", "no hacer nada", "opcion 4", "opción 4"]):
            session.data["lifecycle_decision_active"] = False
            curr_phase = session.data.get("current_phase", "PHASE_10_COMPLETED")
            return {
                "current_step": "OPERACIÓN CANCELADA",
                "action_taken": "Operación de reinicio cancelada. Permaneciendo en la sesión actual.",
                "question": f"Operación cancelada. Seguimos en el proyecto actual ({curr_phase}). ¿Qué deseas ajustar?",
                "instructions_for_ai": "Continúa asistiendo al usuario en el proyecto actual.",
                "phase": curr_phase
            }

        # Save and start new
        if any(w in text for w in ["opcion 1", "opción 1", "guardar y empezar", "guardar y nuevo", "si, guardar", "si guardar", "archivar y nuevo"]):
            session.data["lifecycle_decision_active"] = False
            return cls.start_new_project(session, conn, save_first=True)

        # Start new without saving
        if any(w in text for w in ["opcion 2", "opción 2", "sin guardar", "descartar", "empezar sin guardar"]):
            session.data["lifecycle_decision_active"] = False
            return cls.start_new_project(session, conn, save_first=False)

        # Only save
        if any(w in text for w in ["opcion 3", "opción 3", "solo guardar", "guardar proyecto", "solamente guardar"]):
            session.data["lifecycle_decision_active"] = False
            res = cls.archive_current_project(session, conn)
            curr_phase = session.data.get("current_phase", "PHASE_10_COMPLETED")
            return {
                "current_step": "PROYECTO GUARDADO Y ARCHIVADO",
                "action_taken": f"Proyecto '{res.get('project_name')}' archivado exitosamente en `{res.get('archive_dir')}`.",
                "question": (
                    f"✅ **Proyecto Guardado Exitosamente**\n\n"
                    f"Archivado en: `{res.get('archive_dir')}`\n"
                    f"Total de archivos empaquetados: {len(res.get('archived_files', []))}\n\n"
                    f"La sesión en Live sigue intacta. ¿Deseas hacer algún otro ajuste o empezar un nuevo proyecto?"
                ),
                "instructions_for_ai": "Confirma el guardado del proyecto al usuario y permanece atento.",
                "phase": curr_phase,
                "archive_info": res
            }

        # Fallback: re-prompt
        return cls.prompt_lifecycle_decision(session)

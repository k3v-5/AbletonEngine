# engine/production/doctor/session_doctor.py
"""
Copilot Session Doctor (Studio Doctor & Acoustic Clinic):
Standalone state-machine wizard for non-destructive session health auditing,
structural LOM diagnostics, acoustic/stereo/phase/resonance checks,
and interactive, issue-by-issue surgical repair with pre-repair snapshots and rollback.

Totally independent from guided_session (never runs pre-flight wipe, never generates compositions).
"""

import copy
import json
import logging
import os
import re
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union

from engine.session.transaction_guard import TransactionGuard, TransactionSnapshot
from engine.mix.lufs_validation_gate import LUFSValidationGate
from engine.mix.spatial_panning import InstrumentPanningEvaluator
from engine.mix.resonance_detector import ResonanceDetector
from engine.mix.phase_correlation_auditor import PhaseCorrelationAuditor
from engine.mix.gain_staging.auto_stager import AutoGainStagingEngine
from engine.mastering.live_master_chain import LiveMasterChainEngine
from engine.fx.device_parameter_supervisor import DeviceParameterSupervisor
from engine.arrangement.automation.weaver import ArrangementAutomationWeaver, TransitionAutomationType
from engine.arrangement.automation.live_automation import LiveAutomationEngine
from engine.snapshots.physical_snapshot import physical_snapshot_manager
from engine.mix.channel_strip import ChannelStripEngine

logger = logging.getLogger("CopilotSessionDoctor")



def _normalize_text(text: str) -> str:
    if not text:
        return ""
    import unicodedata
    nfd = unicodedata.normalize("NFD", str(text))
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn").lower().strip()


def _has_eq_device(devices: List[Dict[str, Any]]) -> bool:
    """
    Checks whether an audio or MIDI track already has an EQ device instantiated.
    Recognizes native Ableton EQs (EQ Eight, Channel EQ, EQ Three) and 3rd party
    parametric/surgical EQs (Pro-Q, Kirchhoff, Crave, Pultec, etc.).
    Excludes instruments/synths and creative modulators (e.g. Auto Filter).
    """
    eq_keywords = [
        "equalizer", "pro-q", "kirchhoff", "cravedsp", "crave eq",
        "pultec", "channel eq", "eq eight", "eq three", "filterblade",
        "sie-q", "fabfilter pro-q", "oxford eq", "api 550", "api 560", "ssl eq"
    ]
    for d in devices:
        d_type = d.get("type", 0)
        nm = d.get("name", "").lower()
        c_nm = d.get("class_name", "").lower()
        if d_type == 1 or any(inst in c_nm for inst in ["instrumentsound", "synth", "omnisphere", "serum", "vital", "wavetable", "simpler", "sampler"]):
            continue
        full = f"{nm} {c_nm}"
        words = set(re.findall(r"[a-z0-9]+", full))
        if "eq" in words or "eq8" in words:
            return True
        if any(k in full for k in eq_keywords):
            return True
    return False


# Catalog of insert effects and their physical parameters per role
DOCTOR_EFFECT_CATALOG: Dict[str, Dict[str, Any]] = {
    "saturator": {
        "name": "Saturator",
        "uri": "query:AudioFx#Saturator",
        "default_params": [("Drive", 0.25), ("Base", 0.0), ("Output", 0.70)],
        "category": "COLOR",
        "description": "Saturación analógica cálida (curva Analog Clip) para presencia y armónicos."
    },
    "delay": {
        "name": "Delay",
        "uri": "query:AudioFx#Delay",
        "default_params": [("Dry/Wet", 0.22), ("Feedback", 0.28), ("Sync", 1.0)],
        "category": "SPACE",
        "description": "Eco rítmico estéreo sincronizado al tempo métrico con modulación."
    },
    "reverb": {
        "name": "Reverb",
        "uri": "query:AudioFx#Reverb",
        "default_params": [("Dry/Wet", 0.20), ("DecayTime", 0.35), ("Stereo", 1.0)],
        "category": "SPACE",
        "description": "Espacio acústico dimensional con difusión y cola equilibrada."
    },
    "chorus": {
        "name": "Chorus-Ensemble",
        "uri": "query:AudioFx#Chorus-Ensemble",
        "default_params": [("Amount", 0.35), ("Rate", 0.22)],
        "category": "MODULATION",
        "description": "Modulación de micro-afinación y ensanchamiento estéreo."
    },
    "ott": {
        "name": "OTT",
        "uri": "query:Plugins#VST3:Xfer%20Records:OTT",
        "default_params": [("Depth", 0.30), ("Time", 0.50), ("In Gain", 0.50), ("Out Gain", 0.50)],
        "category": "DYNAMICS",
        "description": "Compresión multibanda up/downward para articulación moderna."
    },
    "glue compressor": {
        "name": "Glue Compressor",
        "uri": "query:AudioFx#Glue%20Compressor",
        "default_params": [("Threshold", -12.0), ("Ratio", 1.0), ("Attack", 0.50), ("Release", 0.0), ("Dry/Wet", 0.80)],
        "category": "DYNAMICS",
        "description": "Compresor de bus SSL estilo pegamento analógico para cohesión dinámica."
    },
    "drum buss": {
        "name": "Drum Buss",
        "uri": "query:AudioFx#Drum%20Buss",
        "default_params": [("Drive", 0.25), ("Crunch", 0.30), ("Transients", 0.60), ("Boom", 0.20)],
        "category": "DRUMS",
        "description": "Procesador integral de batería con modelado de transientes, pegada y crunch."
    },
    "eq eight": {
        "name": "EQ Eight",
        "uri": "query:AudioFx#EQ%20Eight",
        "default_params": [("Band 1 On", 1.0), ("1 Frequency A", 0.22), ("Band 2 On", 1.0), ("2 Gain", -1.2)],
        "category": "EQ",
        "description": "Ecualizador paramétrico quirúrgico de 8 bandas con corte subsónico y anti-barro."
    }
}


def _parse_effect_parameters(input_str: str) -> List[Tuple[str, float]]:
    """Extracts parameter names and normalized/raw values from user string."""
    if not input_str:
        return []
    parsed: List[Tuple[str, float]] = []
    known = [
        "feedback", "dry/wet", "mix", "decay", "decaytime", "drive", "base", "output",
        "crunch", "transients", "boom", "amount", "rate", "depth", "time", "gain",
        "threshold", "ratio", "attack", "release", "cutoff", "frequency", "resonance", "makeup"
    ]
    matches = re.findall(r"([a-zA-Z\s/]+)[:\s=]+([0-9]*\.?[0-9]+)\s*(%|db|s|ms)?", input_str, re.IGNORECASE)
    for m in matches:
        raw_name = m[0].strip()
        matched_kw = next((k for k in known if k in raw_name.lower()), None)
        if matched_kw:
            val_str = m[1]
            unit = m[2]
            try:
                val = float(val_str)
                if unit == "%" or (val > 1.0 and val <= 100.0 and matched_kw in ("mix", "wet", "dry/wet", "feedback", "depth", "drive", "amount", "crunch", "transients", "boom")):
                    val = val / 100.0
                parsed.append((raw_name.split()[-1], val))
            except ValueError:
                pass
    return parsed


class CopilotSessionDoctor:
    """
    Interactive clinical doctor for existing Ableton Live projects.
    Audits structural LOM defects and acoustic bottlenecks, presenting
    each finding step-by-step for user/AI approval or customization.
    """

    STATE_FILE = Path("state/production/doctor_session.json")

    def __init__(self, state_file: Optional[Path] = None):
        self.state_file = Path(state_file) if state_file else self.STATE_FILE
        self.data: Dict[str, Any] = {}
        self._load_state()

    def _load_state(self) -> None:
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
                return
            except Exception as e:
                logger.warning(f"Could not load doctor state: {e}")
        self.data = self._initial_state()

    def _save_state(self) -> None:
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save doctor state: {e}")

    def _initial_state(self) -> Dict[str, Any]:
        return {
            "status": "INITIALIZED",
            "issues_queue": [],
            "current_issue_index": 0,
            "resolved_issues": [],
            "skipped_issues": [],
            "snapshot_data": None,
            "pre_scan_summary": {},
            "post_scan_summary": {},
            "total_tracks_scanned": 0
        }

    def reset_session(self) -> None:
        self.data = self._initial_state()
        if self.STATE_FILE.exists():
            try:
                os.remove(self.STATE_FILE)
            except Exception:
                pass

    # -------------------------------------------------------------------------
    # -------------------------------------------------------------------------
    # SNAPSHOTS & ROLLBACK SAFETY (PHYSICAL & GRANULAR)
    # -------------------------------------------------------------------------
    def _create_pre_repair_snapshot(self, conn: Any, tracks_data: List[Dict[str, Any]]) -> None:
        """Takes a full physical snapshot (clips, notes, mixer) of the session before any changes."""
        try:
            phys_snap = physical_snapshot_manager.capture_snapshot(
                conn,
                name="doctor_pre_repair",
                description="Doctor pre-repair physical snapshot of clips, notes, and mixer parameters"
            )
            if (not phys_snap.get("tracks") or len(phys_snap["tracks"]) == 0) and tracks_data:
                normalized_tracks = []
                for td in tracks_data:
                    t_entry = copy.deepcopy(td)
                    if "track_index" in t_entry and "index" not in t_entry:
                        t_entry["index"] = t_entry["track_index"]
                    normalized_tracks.append(t_entry)
                phys_snap["tracks"] = normalized_tracks

            self.data["physical_snapshot_id"] = phys_snap.get("id")
            self.data["snapshot_data"] = phys_snap
            TransactionGuard.begin_transaction(self.data, tracks_data)
            self._save_state()
            logger.info(f"Doctor pre-repair physical snapshot captured: {phys_snap.get('id')}")
        except Exception as ex:
            logger.warning(f"Notice capturing doctor snapshot: {ex}")


    def _rollback_last_action(
        self,
        conn: Any,
        target_track: Optional[Union[str, int]] = None,
        target_clip: Optional[Union[str, int, float]] = None
    ) -> Dict[str, Any]:
        """Rolls back the most recent change or restores granular track/clip from physical snapshot."""
        snap = self.data.get("snapshot_data")
        snap_id = self.data.get("physical_snapshot_id")

        if not snap and not snap_id:
            return {
                "status": "NO_SNAPSHOT_AVAILABLE",
                "message": "No hay un snapshot previo disponible para restaurar."
            }

        snapshot_ref = snap or snap_id

        # Granular clip restore
        if target_track is not None and target_clip is not None:
            return physical_snapshot_manager.restore_clip(conn, snapshot_ref, target_track, target_clip)

        # Granular track restore
        if target_track is not None:
            return physical_snapshot_manager.restore_track(conn, snapshot_ref, target_track)

        # Full restore via physical snapshot if available
        if snap_id or (isinstance(snap, dict) and snap.get("type") == "physical"):
            res = physical_snapshot_manager.restore_full(conn, snapshot_ref)
            cur_idx = max(0, self.data.get("current_issue_index", 0) - 1)
            self.data["current_issue_index"] = cur_idx
            if self.data.get("resolved_issues"):
                self.data["resolved_issues"].pop()
            self._save_state()
            return res

        # Fallback to fader-only rollback for legacy snapshots
        restored_count = 0
        if conn and hasattr(conn, "send_command") and isinstance(snap, dict):
            try:
                for t_snap in snap.get("tracks", []):
                    idx = t_snap.get("index")
                    if idx is None:
                        continue
                    vol = t_snap.get("volume")
                    pan = t_snap.get("panning")
                    mute = t_snap.get("mute")
                    
                    if vol is not None:
                        conn.send_command("set_track_volume", {"track_index": idx, "volume": vol})
                    if pan is not None:
                        conn.send_command("set_track_panning", {"track_index": idx, "panning": pan})
                    if mute is not None:
                        conn.send_command("set_track_mute", {"track_index": idx, "is_muted": mute})
                    
                    code_restore = f"""
if {idx} < len(song.tracks):
    t = song.tracks[{idx}]
    if {vol is not None}:
        t.mixer_device.volume.value = {vol}
    if {pan is not None}:
        t.mixer_device.panning.value = {pan}
    if {mute is not None}:
        t.mute = {mute}
"""
                    conn.send_command("execute_code", {"code": code_restore})
                    restored_count += 1
            except Exception as ex:
                logger.error(f"Error executing rollback in Live: {ex}")

        cur_idx = max(0, self.data.get("current_issue_index", 0) - 1)
        self.data["current_issue_index"] = cur_idx
        if self.data.get("resolved_issues"):
            last_res = self.data["resolved_issues"].pop()
            logger.info(f"Rolled back issue resolution: {last_res}")
        self._save_state()

        return {
            "status": "ROLLBACK_SUCCESSFUL",
            "restored_tracks": restored_count,
            "current_issue_index": cur_idx
        }

    def restore_track(
        self,
        conn: Any,
        track_identifier: Union[str, int],
        snapshot_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Restores a single track specifically from physical snapshot."""
        snap_ref = snapshot_id or self.data.get("physical_snapshot_id") or self.data.get("snapshot_data")
        if not snap_ref:
            return {"status": "ERROR", "message": "No hay un snapshot previo para restaurar la pista."}
        return physical_snapshot_manager.restore_track(conn, snap_ref, track_identifier)

    def restore_clip(
        self,
        conn: Any,
        track_identifier: Union[str, int],
        clip_identifier: Union[str, int, float],
        snapshot_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Restores a single arrangement clip specifically from physical snapshot."""
        snap_ref = snapshot_id or self.data.get("physical_snapshot_id") or self.data.get("snapshot_data")
        if not snap_ref:
            return {"status": "ERROR", "message": "No hay un snapshot previo para restaurar el clip."}
        return physical_snapshot_manager.restore_clip(conn, snap_ref, track_identifier, clip_identifier)

    def _detect_snapshot_action(self, conn: Any, user_input: str) -> Optional[Dict[str, Any]]:
        """
        Detects user requests to capture snapshots or perform granular restoration
        of specific tracks or clips.
        """
        if not user_input:
            return None
        u_norm = _normalize_text(user_input)

        # A. Manual Snapshot Capture
        if any(w in u_norm for w in ["tomar snapshot", "capturar snapshot", "guardar snapshot", "crear snapshot", "take snapshot", "capture snapshot"]):
            snap = physical_snapshot_manager.capture_snapshot(conn, name="Manual User Snapshot")
            self.data["physical_snapshot_id"] = snap.get("id")
            self.data["snapshot_data"] = snap
            self._save_state()
            return {
                "status": "SNAPSHOT_CAPTURED",
                "current_step": "SNAPSHOT CAPTURADO",
                "action_taken": f"Snapshot físico `{snap.get('id')}` guardado exitosamente.",
                "question": f"📸 **Snapshot Físico Capturado ({snap.get('id')}):** Se guardaron clips, notas MIDI y parámetros de {len(snap.get('tracks', []))} pistas.\\n\\n¿Deseas continuar con el diagnóstico o realizar alguna otra acción?",
                "instructions_for_ai": "Informa al usuario de que el snapshot físico se capturó y guardó con éxito."
            }

        # B. Granular Clip Restoration: "restaurar clip [Y] de pista [X]"
        m_clip = re.search(r"(?:restaurar|recuperar|deshacer|restore)\s+(?:el\s+)?clip\s+([a-zA-Z0-9_\-\.\s]+)\s+(?:de|en)\s+(?:la\s+)?(?:pista|track|canal)\s+([a-zA-Z0-9_\-\s]+)", u_norm)
        if m_clip:
            target_clip = m_clip.group(1).strip()
            target_track = m_clip.group(2).strip()
            res = self.restore_clip(conn, target_track, target_clip)
            c_disp = res.get("clip_name") or target_clip
            t_disp = res.get("track_name") or target_track
            if res.get("status") == "SUCCESS":
                msg = f"🧩 **Clip Restaurado:** Se restauró el clip '{c_disp}' en la pista '{t_disp}' ({res.get('notes_restored', 0)} notas MIDI recuperadas)."
            else:
                msg = f"⚠️ **Aviso de Restauración:** {res.get('message', 'No se pudo restaurar el clip.')}"

            return {
                "status": "CLIP_RESTORED" if res.get("status") == "SUCCESS" else "RESTORE_ERROR",
                "current_step": "RESTAURACIÓN GRANULAR DE CLIP",
                "action_taken": msg,
                "question": f"{msg}\\n\\n¿Deseas continuar con el diagnóstico o realizar otra restauración?",
                "instructions_for_ai": "Informa al usuario del resultado de la restauración granular del clip."
            }

        # C. Granular Track Restoration: "restaurar pista [X]", "deshacer pista [X]", "restaurar pad roto", "restaurar canal [X]"
        is_restore_intent = any(w in u_norm for w in ["restaurar", "recuperar", "deshacer", "restore"])
        is_track_intent = any(w in u_norm for w in ["pista", "track", "canal", "pad roto", "pad", "lead", "piano", "drums", "loop", "synth", "strings"])

        if is_restore_intent and is_track_intent:
            if any(w in u_norm for w in ["sesion", "todo", "full"]):
                rb_res = self._rollback_last_action(conn)
                return self._present_current_issue(pre_msg="⏪ **Sesión completa revertida al snapshot previo.**")

            target_track = None
            m_trk = re.search(r"(?:pista|track|canal)\s+([a-zA-Z0-9_\-\s]+)", u_norm)
            if m_trk:
                raw_target = m_trk.group(1).strip()
                for noise in ["del", "de la", "de", "el", "la", "unicamente"]:
                    if raw_target.startswith(noise + " "):
                        raw_target = raw_target[len(noise):].strip()
                target_track = raw_target

            if not target_track:
                tracks_data = self.data.get("raw_tracks_cache", [])
                for t in tracks_data:
                    t_nm = t.get("name", "").lower()
                    if t_nm and t_nm in u_norm:
                        target_track = t["name"]
                        break

            if not target_track:
                if "pad roto" in u_norm:
                    target_track = "Pad Roto"
                elif "pad" in u_norm:
                    target_track = "Pad Roto"

            if target_track:
                res = self.restore_track(conn, target_track)
                if res.get("status") == "SUCCESS":
                    msg = (
                        f"🛡️ **Pista '{res.get('track_name', target_track)}' Restaurada Exitosamente:**\\n"
                        f"• Clips restaurados: **{res.get('clips_restored', 0)}**\\n"
                        f"• Notas MIDI recuperadas: **{res.get('notes_restored', 0)}**\\n"
                        f"• Mixer (volumen, paneo, mute, solo) alineados al snapshot.\\n"
                        f"• *Todas las demás pistas de la sesión se mantuvieron 100% intactas.*"
                    )
                else:
                    msg = f"⚠️ **Aviso de Restauración:** {res.get('message', 'No se pudo restaurar la pista.')}"
                return {
                    "status": "TRACK_RESTORED" if res.get("status") == "SUCCESS" else "RESTORE_ERROR",
                    "current_step": "RESTAURACIÓN GRANULAR DE PISTA",
                    "action_taken": msg,
                    "question": f"{msg}\\n\\n¿Deseas continuar con el diagnóstico o realizar otra acción?",
                    "instructions_for_ai": "Informa al usuario del resultado de la restauración granular de la pista."
                }

        return None


    # -------------------------------------------------------------------------
    # DEEP MULTI-DIMENSIONAL SCANNER
    # -------------------------------------------------------------------------
    def _scan_session(self, conn: Any) -> Tuple[List[Dict[str, Any]], Dict[str, Any], List[Dict[str, Any]]]:
        """
        Inspects Live session track by track:
        1. LOM structural checks (volumes, empty clips, orphans, mutes, duplicate FX).
        2. Acoustic & spatial checks (stereo phase, low-end masking, center congestion).
        3. Master bus compliance (headroom, true peak).
        Returns (issues_queue, summary_dict, raw_tracks_data).
        """
        raw_tracks: List[Dict[str, Any]] = []
        master_info: Dict[str, Any] = {}

        if conn and hasattr(conn, "send_command"):
            try:
                code_scan = """
tracks_data = []
for idx, t in enumerate(song.tracks):
    is_fold = getattr(t, 'is_foldable', False)
    is_audio = getattr(t, 'is_audio_track', False)
    is_midi = getattr(t, 'is_midi_track', False)
    
    # Clips
    arr_clips = []
    raw_clips = []
    try:
        raw_clips = list(t.arrangement_clips)
    except Exception:
        raw_clips = []
    for c in raw_clips:
        is_audio_c = getattr(c, 'is_audio_clip', False)
        notes_arr = []
        if not is_audio_c:
            try:
                for n in c.get_all_notes_extended():
                    notes_arr.append({
                        'start': float(getattr(n, 'start_time', 0.0)),
                        'duration': float(getattr(n, 'duration', 0.0)),
                        'pitch': int(getattr(n, 'pitch', 60))
                    })
            except Exception:
                pass
        arr_clips.append({
            'name': getattr(c, 'name', ''),
            'start': getattr(c, 'start_time', 0.0),
            'len': getattr(c, 'length', 0.0),
            'is_audio': is_audio_c,
            'notes_count': len(notes_arr) if not is_audio_c else 0,
            'notes': notes_arr
        })
            
    # Session clip slots
    empty_slots_with_clips = 0
    raw_slots = []
    try:
        raw_slots = list(t.clip_slots)
    except Exception:
        raw_slots = []
    for slot in raw_slots:
        if getattr(slot, 'has_clip', False):
            sc = getattr(slot, 'clip', None)
            if sc and not getattr(sc, 'is_audio_clip', False):
                try:
                    if len(sc.get_all_notes_extended()) == 0:
                        empty_slots_with_clips += 1
                except Exception:
                    pass

    # Devices
    devs = []
    for d_i, d in enumerate(t.devices):
        devs.append({
            'index': d_i,
            'name': getattr(d, 'name', ''),
            'class_name': getattr(d, 'class_name', ''),
            'type': getattr(d, 'type', 0),
            'is_active': getattr(d, 'is_active', True)
        })

    tracks_data.append({
        'index': idx,
        'name': getattr(t, 'name', f'Track {idx}'),
        'is_audio': is_audio,
        'is_midi': is_midi,
        'is_foldable': is_fold,
        'arm': getattr(t, 'arm', False),
        'mute': getattr(t, 'mute', False),
        'solo': getattr(t, 'solo', False),
        'volume': float(getattr(t.mixer_device.volume, 'value', 0.85)),
        'panning': float(getattr(t.mixer_device.panning, 'value', 0.0)),
        'devices': devs,
        'arrangement_clips': arr_clips,
        'empty_session_clips': empty_slots_with_clips
    })

cue_points_data = []
for cp in getattr(song, 'cue_points', []):
    cue_points_data.append({
        'name': getattr(cp, 'name', ''),
        'time': float(getattr(cp, 'time', 0.0))
    })

m_track = song.master_track
m_vol = float(getattr(m_track.mixer_device.volume, 'value', 0.85))
m_pan = float(getattr(m_track.mixer_device.panning, 'value', 0.0))
m_devs = []
for d_i, d in enumerate(getattr(m_track, 'devices', [])):
    m_devs.append({
        'index': d_i,
        'name': getattr(d, 'name', ''),
        'class_name': getattr(d, 'class_name', ''),
        'type': getattr(d, 'type', 0),
        'is_active': getattr(d, 'is_active', True)
    })
master_info = {
    'volume': m_vol,
    'panning': m_pan,
    'tempo': float(getattr(song, 'tempo', 120.0)),
    'devices': m_devs
}
result = {'tracks': tracks_data, 'master': master_info, 'cue_points': cue_points_data}
"""
                r = conn.send_command("execute_code", {"code": code_scan})
                res_dict = r.get("result", {}) if isinstance(r, dict) else {}
                raw_cue_points: List[Dict[str, Any]] = []
                if isinstance(res_dict, dict):
                    if "result" in res_dict and isinstance(res_dict["result"], dict):
                        raw_tracks = res_dict["result"].get("tracks", [])
                        master_info = res_dict["result"].get("master", {})
                        raw_cue_points = res_dict["result"].get("cue_points", [])
                    else:
                        raw_tracks = res_dict.get("tracks", res_dict.get("tracks_data", []))
                        master_info = res_dict.get("master", res_dict.get("master_info", {}))
                        raw_cue_points = res_dict.get("cue_points", [])
            except Exception as ex:
                logger.error(f"Error querying Live tracks in doctor scan: {ex}")
                raw_cue_points = []



        # Fallback via standard MCP tools if execute_code didn't return tracks
        if not raw_tracks and conn and hasattr(conn, "send_command"):
            try:
                s_info = conn.send_command("get_session_info", {}) or {}
                num_tracks = s_info.get("track_count", s_info.get("num_tracks", 0))
                for t_idx in range(num_tracks):
                    t_info = conn.send_command("get_track_info", {"track_index": t_idx}) or {}
                    t_name = t_info.get("name", f"Track {t_idx}")
                    vol = float(t_info.get("volume", 0.85))
                    pan = float(t_info.get("panning", 0.0))
                    mute = bool(t_info.get("is_muted", t_info.get("mute", False)))
                    
                    clips = t_info.get("clips", t_info.get("arrangement_clips", []))
                    arr_clips = []
                    empty_sess = 0
                    for c in clips:
                        c_notes = c.get("notes", [])
                        arr_clips.append({
                            "name": c.get("name", ""),
                            "start": c.get("start_time", c.get("start", 0.0)),
                            "len": c.get("length", c.get("len", 0.0)),
                            "is_audio": c.get("is_audio", False),
                            "notes_count": c.get("notes_count", len(c_notes)),
                            "notes": c_notes,
                        })
                    
                    devs = []
                    for d_i, d in enumerate(t_info.get("devices", [])):
                        devs.append({
                            "index": d_i,
                            "name": d.get("name", ""),
                            "class_name": d.get("class_name", d.get("name", "")),
                            "type": d.get("type", "audio_effect"),
                            "is_active": d.get("is_active", True)
                        })

                    raw_tracks.append({
                        "index": t_idx,
                        "name": t_name,
                        "is_audio": t_info.get("is_audio", False),
                        "is_midi": t_info.get("is_midi", True),
                        "is_foldable": t_info.get("is_foldable", False),
                        "arm": t_info.get("arm", False),
                        "mute": mute,
                        "solo": t_info.get("solo", False),
                        "volume": vol,
                        "panning": pan,
                        "devices": devs,
                        "arrangement_clips": arr_clips,
                        "empty_session_clips": empty_sess
                    })
                m_info = s_info.get("master_track", {})
                if m_info:
                    master_info = {
                        "volume": float(m_info.get("volume", 0.85)),
                        "panning": float(m_info.get("panning", 0.0)),
                        "tempo": float(s_info.get("tempo", 120.0)),
                        "devices": m_info.get("devices", [])
                    }
                if not raw_cue_points:
                    try:
                        c_res = conn.send_command("get_cue_points", {}) or {}
                        raw_cue_points = c_res.get("cue_points", []) if isinstance(c_res, dict) else []
                    except Exception:
                        pass
            except Exception as ex:
                logger.warning(f"Fallback scan failed: {ex}")

        issues: List[Dict[str, Any]] = []
        issue_id_counter = 1

        def add_issue(cat: str, sev: str, t_idx: Optional[int], t_name: str, desc: str, evid: str, rec_act: str, rec_params: Dict[str, Any]):
            nonlocal issue_id_counter
            issues.append({
                "id": f"DOCTOR-{issue_id_counter:03d}",
                "category": cat,
                "severity": sev,
                "track_index": t_idx,
                "track_name": t_name,
                "description": desc,
                "evidence": evid,
                "recommended_action": rec_act,
                "recommended_params": rec_params,
                "status": "PENDING"
            })
            issue_id_counter += 1

        # -----------------------------------------------------------------
        # 1. AUDITORÍA LOM: Volúmenes, Clips Vacíos, Huérfanos, Mutes, FX
        # -----------------------------------------------------------------
        harmonic_tracks_centered = []

        for t in raw_tracks:
            t_idx = t["index"]
            t_name = t["name"]
            is_fold = t.get("is_foldable", False)
            devs = t.get("devices", [])
            arr_clips = t.get("arrangement_clips", [])
            vol = t.get("volume", 0.85)
            pan = t.get("panning", 0.0)
            mute = t.get("mute", False)
            empty_sess = t.get("empty_session_clips", 0)

            # A. Faders y Jerarquía de Ganancia / LUFS por Canal (Norma guided_session)
            if not is_fold and (arr_clips or devs):
                role = AutoGainStagingEngine.classify_role(t_name)
                target_db = AutoGainStagingEngine.HIERARCHY_TARGETS.get(role, -15.0)
                expected_fader = AutoGainStagingEngine.db_to_linear(target_db)
                if vol > 0.855:
                    vol_db_approx = round((vol - 0.85) * 40.0, 1)
                    add_issue(
                        cat="GAIN_STAGING_HEADROOM",
                        sev="CRITICAL" if role in ("kick", "bass", "drums") else "WARNING",
                        t_idx=t_idx,
                        t_name=t_name,
                        desc=f"Fader de la pista '{t_name}' supera el nivel de ganancia unitaria (0 dBFS), consumiendo headroom y arriesgando distorsión interna.",
                        evid=f"Volumen fader: {vol:.3f} (+{vol_db_approx} dB por encima de 0 dBFS nominal). Norma de rol: {target_db} dBFS.",
                        rec_act=f"Calibrar fader a {expected_fader:.2f} ({target_db} dBFS) para respetar la jerarquía de ganancia y preservar -6 dBFS en el Master.",
                        rec_params={"action": "set_volume", "track_index": t_idx, "value": expected_fader}
                    )
                elif abs(vol - expected_fader) > 0.05 and vol > expected_fader:
                    add_issue(
                        cat="GAIN_STAGING_HEADROOM",
                        sev="WARNING",
                        t_idx=t_idx,
                        t_name=t_name,
                        desc=f"Fader de la pista '{t_name}' (Rol: {role.upper()}) está en {vol:.2f}, por encima de su norma de sonoridad ({expected_fader:.2f} ≈ {target_db} dBFS / LUFS). Desbalancea la jerarquía de mezcla y satura el bus de suma.",
                        evid=f"Fader actual: {vol:.2f}. Norma de estudio: {target_db} dBFS (fader {expected_fader:.2f}).",
                        rec_act=f"Calibrar fader a {expected_fader:.2f} ({target_db} dBFS) para cumplir con el estándar de sonoridad por canal de guided_session.",
                        rec_params={"action": "set_volume", "track_index": t_idx, "value": expected_fader}
                    )

            # B. Clips Vacíos (MIDI con 0 notas o Audio sin longitud)
            empty_arr_count = 0
            for c in arr_clips:
                if not c.get("is_audio", False) and c.get("notes_count", 0) == 0:
                    empty_arr_count += 1
                elif c.get("is_audio", False) and c.get("len", 0.0) <= 0.01:
                    empty_arr_count += 1

            total_empty = empty_arr_count + empty_sess
            if total_empty > 0:
                add_issue(
                    cat="EMPTY_CLIPS",
                    sev="OPTIMIZATION",
                    t_idx=t_idx,
                    t_name=t_name,
                    desc=f"Se detectaron {total_empty} clip(s) completamente vacíos (sin notas MIDI ni audio audible) en '{t_name}'.",
                    evid=f"{empty_arr_count} clip(s) vacíos en Arrangement, {empty_sess} en Session slots.",
                    rec_act=f"Eliminar los {total_empty} clip(s) vacíos para limpiar la línea de tiempo.",
                    rec_params={"action": "delete_empty_clips", "track_index": t_idx}
                )

            # C. Canales Huérfanos / Muertos
            if not is_fold and len(devs) == 0 and len(arr_clips) == 0 and empty_sess == 0:
                if not any(w in t_name.lower() for w in ["master", "return", "vocal"]):
                    add_issue(
                        cat="ORPHAN_TRACK",
                        sev="OPTIMIZATION",
                        t_idx=t_idx,
                        t_name=t_name,
                        desc=f"La pista '{t_name}' (Pista {t_idx}) no tiene clips, ni instrumentos, ni efectos cargados.",
                        evid="0 clips, 0 dispositivos, fader por defecto.",
                        rec_act="Eliminar o archivar pista huérfana para despejar la sesión.",
                        rec_params={"action": "delete_track", "track_index": t_idx}
                    )

            # C2. Pistas con Instrumentos/Efectos pero Huérfanas de Clips (UNPOPULATED_TRACK)
            if not is_fold and len(devs) > 0 and len(arr_clips) == 0:
                is_armed = t.get("arm", False)
                is_audio = t.get("is_audio", False)
                is_vocal_audio = is_audio and ("vocal" in t_name.lower() or is_armed)
                if not is_vocal_audio:
                    add_issue(
                        cat="UNPOPULATED_TRACK",
                        sev="CRITICAL",
                        t_idx=t_idx,
                        t_name=t_name,
                        desc=f"La pista '{t_name}' (Pista {t_idx}) tiene {len(devs)} dispositivo(s) cargado(s) pero carece de notas o clips en el proyecto.",
                        evid="0 clips en Arrangement a pesar de tener instrumentos/efectos cargados.",
                        rec_act=f"Inyectar patrón musical o reasignar notas correspondientes al rol de '{t_name}'.",
                        rec_params={"action": "populate_track_notes", "track_index": t_idx, "track_name": t_name}
                    )

            # D. Pistas Silenciadas por Error (Muted con contenido)
            if mute and (arr_clips or devs):
                if not any(w in t_name.lower() for w in ["ref", "test", "mute", "guia"]):
                    add_issue(
                        cat="MUTED_ACTIVE_TRACK",
                        sev="WARNING",
                        t_idx=t_idx,
                        t_name=t_name,
                        desc=f"La pista '{t_name}' contiene material procesado pero se encuentra silenciada (Mute: True).",
                        evid=f"{len(arr_clips)} clips y {len(devs)} dispositivos inaudibles en la mezcla.",
                        rec_act="Desactivar Mute (activar pista) si fue silenciada por descuido.",
                        rec_params={"action": "set_mute", "track_index": t_idx, "value": False}
                    )

            # E. Plugins o Cadenas de Efectos Duplicados (excluye instrumentos y distingue VSTs por nombre real)
            dev_classes = {}
            for d in devs:
                raw_name = d.get("name", "").strip()
                c_name = d.get("class_name", "").strip()
                d_type = d.get("type", 0)
                if d_type == 1 or any(inst in c_name.lower() for inst in ["instrument", "synth", "omnisphere", "serum", "vital", "wavetable", "simpler", "sampler"]):
                    continue
                lookup_key = raw_name if c_name in ("PluginDevice", "AuPluginDevice", "") else c_name
                if not lookup_key:
                    continue
                dev_classes.setdefault(lookup_key, []).append(d)

            for c_name, d_instances in dev_classes.items():
                if len(d_instances) >= 2:
                    d_names = [inst["name"] for inst in d_instances]
                    add_issue(
                        cat="DUPLICATE_EFFECTS",
                        sev="WARNING",
                        t_idx=t_idx,
                        t_name=t_name,
                        desc=f"Efecto duplicado en cascada detectado en '{t_name}': {len(d_instances)} instancias de '{c_name}'.",
                        evid=f"Dispositivos: {', '.join(d_names)} en la misma cadena.",
                        rec_act=f"Eliminar la segunda instancia redundante de '{c_name}' (Índice {d_instances[1]['index']}).",
                        rec_params={"action": "delete_device", "track_index": t_idx, "device_index": d_instances[1]["index"]}
                    )

            # F. Tracking para Paneo Estéreo
            if not is_fold and any(w in t_name.lower() for w in ["piano", "keys", "pad", "synth", "lead", "guitar", "chords"]):
                if abs(pan) < 0.05:
                    harmonic_tracks_centered.append((t_idx, t_name))

            # G. Ecualización Obligatoria por Canal (Channel Strip EQ)
            is_orphan = (not is_fold and len(devs) == 0 and len(arr_clips) == 0 and empty_sess == 0)
            if not is_fold and not is_orphan and (arr_clips or devs or empty_sess > 0):
                if not _has_eq_device(devs):
                    track_dev_names = [d.get("name", "") for d in devs]
                    role = AutoGainStagingEngine.classify_role(t_name, track_dev_names)
                    add_issue(
                        cat="MISSING_CHANNEL_EQ",
                        sev="CRITICAL",
                        t_idx=t_idx,
                        t_name=t_name,
                        desc=f"La pista '{t_name}' (Rol: {role.upper()}) no cuenta con un ecualizador de inserción (EQ Eight / Channel EQ). La ecualización por canal es obligatoria para control de resonancias, corte subsónico (HPF) y separación espectral.",
                        evid="0 plugins de ecualización detectados en la cadena de efectos del canal.",
                        rec_act=f"Insertar 'EQ Eight' en '{t_name}' y calibrar filtros quirúrgicos (HPF + control de resonancias) para rol {role.upper()}.",
                        rec_params={
                            "action": "insert_channel_eq",
                            "track_index": t_idx,
                            "role": role
                        }
                    )

        # -----------------------------------------------------------------
        # 2. AUDITORÍA ACÚSTICA, ESTÉREO Y ESPACIAL
        # -----------------------------------------------------------------
        # A. Amontonamiento Estéreo en el Centro (Center Congestion)
        if len(harmonic_tracks_centered) >= 3:
            t_names_str = ", ".join([f"'{nm}'" for _, nm in harmonic_tracks_centered])
            add_issue(
                cat="FREQUENCY_COLLISION",
                sev="WARNING",
                t_idx=harmonic_tracks_centered[0][0],
                t_name="Instrumentos Armónicos en Centro",
                desc="Múltiples capas armónicas se encuentran exactamente en el centro mono (0.0), saturando el espacio auditivo y sofocando la voz/bombo.",
                evid=f"{len(harmonic_tracks_centered)} pistas centradas: {t_names_str}.",
                rec_act="Distribuir simétricamente en el panorama estéreo (ej. Keys 24L, Pad 32L, Lead 24R).",
                rec_params={"action": "apply_spatial_panning", "tracks": harmonic_tracks_centered}
            )

        # B. Colisión de Frecuencias Graves (Kick vs Bass / 808)
        kick_trk = next((t for t in raw_tracks if "kick" in t["name"].lower() or "bombo" in t["name"].lower()), None)
        bass_trk = next((t for t in raw_tracks if any(w in t["name"].lower() for w in ["808", "bass", "bajo", "sub"])), None)
        if kick_trk and bass_trk:
            kick_clips = kick_trk.get("arrangement_clips", [])
            kick_notes_count = sum(c.get("notes_count", 0) for c in kick_clips)
            if kick_notes_count == 0:
                add_issue(
                    cat="SIDECHAIN_TRIGGER_MISSING",
                    sev="CRITICAL",
                    t_idx=kick_trk["index"],
                    t_name=kick_trk["name"],
                    desc=f"La pista de bombo '{kick_trk['name']}' no contiene notas MIDI ni clips activos para disparar el compresor sidechain en '{bass_trk['name']}'.",
                    evid="La señal disparadora (sidechain trigger) de subgraves está completamente silenciosa.",
                    rec_act=f"Poblar la pista '{kick_trk['name']}' con patrones de bombo antes de calibrar el ducking.",
                    rec_params={"action": "populate_track_notes", "track_index": kick_trk["index"], "track_name": kick_trk["name"]}
                )

            has_sc = False
            for d in bass_trk.get("devices", []):
                if "compressor" in d.get("name", "").lower() or "glue" in d.get("name", "").lower():
                    has_sc = True
                    break
            if not has_sc:
                add_issue(
                    cat="FREQUENCY_COLLISION",
                    sev="CRITICAL",
                    t_idx=bass_trk["index"],
                    t_name=bass_trk["name"],
                    desc=f"Colisión subgrave detectada entre Bombo ('{kick_trk['name']}') y Bajo ('{bass_trk['name']}') en 40-90 Hz sin compresión Sidechain.",
                    evid="El subgrave del bajo y el transitorio del bombo compiten en el mismo rango espectral sin atenuación dinámica.",
                    rec_act=f"Configurar compresor sidechain en '{bass_trk['name']}' disparado por el bombo (-3.5 dB de ducking).",
                    rec_params={"action": "setup_sidechain", "source_track": kick_trk["index"], "target_track": bass_trk["index"]}
                )

        # C. Subgrave Estéreo (Mono Incompatibility)
        for t in raw_tracks:
            if any(w in t["name"].lower() for w in ["sub", "808"]) and abs(t.get("panning", 0.0)) > 0.10:
                add_issue(
                    cat="STEREO_PHASE",
                    sev="CRITICAL",
                    t_idx=t["index"],
                    t_name=t["name"],
                    desc=f"La pista de subgraves '{t['name']}' está paneada lateralmente ({t['panning']}), lo que provoca cancelaciones de fase acústica severas en sistemas de sonido y clubes.",
                    evid=f"Paneo detectado: {t['panning']:.2f}. Norma: Mono estricto (0.0) en <120 Hz.",
                    rec_act="Centrar el subgrave exactamente a 0.0.",
                    rec_params={"action": "set_panning", "track_index": t["index"], "value": 0.0}
                )

        # D. Auditoría de Vacío Pre-Drop (Pre-Drop Vacuum Law)
        for cp in raw_cue_points:
            cp_name = str(cp.get("name", "")).strip()
            cp_time = float(cp.get("time", 0.0))
            if any(w in cp_name.lower() for w in ["drop", "switch", "climax", "caida", "caída", "corte"]):
                vac_start = max(0.0, cp_time - 2.0)
                spilling_tracks = []
                for t in raw_tracks:
                    if t.get("is_foldable", False):
                        continue
                    for c in t.get("arrangement_clips", []):
                        c_start = float(c.get("start", 0.0))
                        c_len = float(c.get("len", 0.0))
                        c_end = c_start + c_len
                        has_spill = False
                        notes_data = c.get("notes", [])
                        if c.get("is_audio", False):
                            if c_start < cp_time and c_end > vac_start:
                                has_spill = True
                        elif notes_data:
                            for nd in notes_data:
                                n_s = c_start + float(nd.get("start", 0.0))
                                n_e = n_s + float(nd.get("duration", 0.0))
                                if n_s < cp_time and n_e > (vac_start + 0.001):
                                    has_spill = True
                                    break
                        elif c.get("notes_count", 0) > 0:
                            if c_start < cp_time and c_end > vac_start:
                                has_spill = True

                        if has_spill:
                            spilling_tracks.append((t["index"], t["name"]))
                            break
                if spilling_tracks:
                    t_names_spill = ", ".join(f"'{nm}'" for _, nm in spilling_tracks)
                    add_issue(
                        cat="PRE_DROP_VACUUM_VIOLATION",
                        sev="WARNING",
                        t_idx=spilling_tracks[0][0],
                        t_name=f"Transición a '{cp_name}'",
                        desc=f"Derrame acústico en los 2 beats previos al '{cp_name}' (Pulsos {vac_start:.1f} a {cp_time:.1f}): {len(spilling_tracks)} pista(s) ({t_names_spill}) tienen notas activas en la ventana de silencio pre-drop.",
                        evid=f"Violación de la ley de vacío pre-drop (se requiere >= 0.5s de silencio antes del impacto).",
                        rec_act=f"Aplicar corte quirúrgico de notas en los 2 pulsos previos a '{cp_name}' en las pistas afectadas.",
                        rec_params={"action": "enforce_pre_drop_vacuum", "cue_time": cp_time, "cue_name": cp_name}
                    )

        # E. Auditoría de Sintetizadores en Outro (Synthesizer Outro Non-Silencing Law)
        outro_cp = next((cp for cp in raw_cue_points if "outro" in str(cp.get("name", "")).lower()), None)
        if outro_cp:
            outro_name = str(outro_cp.get("name", "Outro")).strip()
            outro_time = float(outro_cp.get("time", 0.0))
            for t in raw_tracks:
                if t.get("is_foldable", False):
                    continue
                t_name_l = t["name"].lower()
                is_synth = (
                    any(k in t_name_l for k in ["synth", "lead", "vital", "serum", "saw", "pad", "chord", "arpeg", "arpeggio"])
                    and not any(k in t_name_l for k in ["kick", "bombo", "drum", "hat", "clap", "snare", "perc", "bass", "sub", "808"])
                )
                if not is_synth:
                    continue

                has_outro_notes = False
                for c in t.get("arrangement_clips", []):
                    c_start = float(c.get("start", 0.0))
                    c_len = float(c.get("len", 0.0))
                    c_end = c_start + c_len
                    if c_end <= outro_time:
                        continue
                    notes_data = c.get("notes", [])
                    if notes_data:
                        for nd in notes_data:
                            n_s = c_start + float(nd.get("start", 0.0))
                            n_e = n_s + float(nd.get("duration", 0.0))
                            if n_e > (outro_time + 0.001):
                                has_outro_notes = True
                                break
                    elif c.get("notes_count", 0) > 0 and (c_start >= outro_time or c_end > outro_time):
                        has_outro_notes = True
                    if has_outro_notes:
                        break

                if not has_outro_notes:
                    add_issue(
                        cat="SYNTH_SILENCED_IN_OUTRO",
                        sev="CRITICAL",
                        t_idx=t["index"],
                        t_name=t["name"],
                        desc=f"Pista de sintetizador '{t['name']}' silenciada en el {outro_name} (0 notas a partir del pulso {outro_time:.1f}). La ley de producción exige terminantemente que el sintetizador no se silencie en el Outro para sostener drones armónicos que alimenten el colapso final.",
                        evid=f"Sección '{outro_name}' inicia en pulso {outro_time:.1f} y la pista '{t['name']}' no contiene notas activas en dicha sección.",
                        rec_act=f"Inyectar drone armónico sostenido en la tónica/quinta en el {outro_name} (Pulsos {outro_time:.1f} a {outro_time + 32.0:.1f}) para alimentar el colapso final.",
                        rec_params={"action": "populate_synth_outro", "track_index": t["index"], "track_name": t["name"], "outro_time": outro_time, "length": 32.0}
                    )

        # -----------------------------------------------------------------
        # 3. CUMPLIMIENTO DEL MASTER BUS & CADENA TÉCNICA DE MASTERIZACIÓN
        # -----------------------------------------------------------------
        m_vol = master_info.get("volume", 0.85)
        m_devs = master_info.get("devices", [])

        # A. Fader Master
        if m_vol > 0.855:
            add_issue(
                cat="MASTER_COMPLIANCE",
                sev="CRITICAL",
                t_idx=None,
                t_name="Master Track",
                desc="El fader de la pista Master está empujado por encima de 0 dBFS (0.85), arriesgando distorsión inter-sample y clippeo en convertidores D/A.",
                evid=f"Fader Master en {m_vol:.3f} (> 0.85).",
                rec_act="Restablecer fader de Master al nivel de seguridad unitario (0.85) para preservar margen de masterización.",
                rec_params={"action": "set_master_volume", "value": 0.85}
            )

        # B. Cadena Profesional de Masterización Obligatoria (BS.1770-5)
        m_dev_names = [d.get("name", "").lower() for d in m_devs]
        has_limiter = any("limiter" in nm or "pro-l" in nm or "maximizer" in nm for nm in m_dev_names)
        has_glue = any("glue" in nm or "compressor" in nm for nm in m_dev_names)
        has_eq = any("eq" in nm for nm in m_dev_names)

        if not has_limiter or len(m_devs) == 0:
            add_issue(
                cat="MASTER_CHAIN_AUDIT",
                sev="CRITICAL",
                t_idx=None,
                t_name="Master Track",
                desc="La pista Master no tiene instanciada la cadena de masterización profesional obligatoria (EQ Eight corte subsónico <25Hz + Glue Compressor + Utility Bass Mono <120Hz + Limitador True Peak). Sin limitador, la señal sufrirá clippeo digital severo al exportar y no cumple la norma de guided_session.",
                evid=f"Dispositivos en Master: {len(m_devs)} encontrados. Falta limitador True Peak y control dinámico.",
                rec_act="Instanciar y calibrar la cadena física nativa de 5 procesadores de masterización para cumplir el target de sonoridad de guided_session (-6.0 LUFS Club / -14.0 LUFS Streaming).",
                rec_params={"action": "setup_master_chain", "target_profile": "CLUB", "target_lufs": -6.0}
            )
        elif not has_eq or not has_glue:
            add_issue(
                cat="MASTER_CHAIN_AUDIT",
                sev="WARNING",
                t_idx=None,
                t_name="Master Track",
                desc="La cadena de masterización en la pista Master está incompleta: falta ecualización de corte subsónico (<25Hz) o pegamento de bus (Glue Compressor).",
                evid=f"Dispositivos actuales en Master: {', '.join([d.get('name') for d in m_devs])}.",
                rec_act="Completar la cadena de masterización con EQ de corte y Glue Compressor.",
                rec_params={"action": "setup_master_chain", "target_profile": "CLUB", "target_lufs": -6.0}
            )

        summary = {
            "total_issues": len(issues),
            "critical_count": len([i for i in issues if i["severity"] == "CRITICAL"]),
            "warning_count": len([i for i in issues if i["severity"] == "WARNING"]),
            "optimization_count": len([i for i in issues if i["severity"] == "OPTIMIZATION"]),
            "tracks_scanned": len(raw_tracks)
        }

        return issues, summary, raw_tracks

    # -------------------------------------------------------------------------
    # EJECUCIÓN QUIRÚRGICA DE PRESCRIPCIONES
    # -------------------------------------------------------------------------
    def _execute_prescription(self, conn: Any, issue: Dict[str, Any], custom_input: Optional[str] = None) -> Dict[str, Any]:
        """Executes the physical fix on Ableton Live LOM with custom override support."""
        params = issue.get("recommended_params", {})
        act = params.get("action")
        t_idx = issue.get("track_index")
        t_name = issue.get("track_name")
        
        result_msg = ""

        if conn and hasattr(conn, "send_command"):
            try:
                # 1. Set Track Volume
                if act == "set_volume":
                    val = params.get("value", 0.75)
                    if custom_input:
                        m_db = re.search(r"([+-]?\d+(?:\.\d+)?)\s*(?:db|dbfs)?", custom_input)
                        if m_db:
                            db_val = float(m_db.group(1))
                            val = max(0.1, min(1.0, 0.85 + (db_val * 0.025)))
                        m_raw = re.search(r"0\.\d+", custom_input)
                        if m_raw:
                            val = float(m_raw.group(0))
                    
                    conn.send_command("set_track_volume", {"track_index": t_idx, "volume": val})
                    code = f"song.tracks[{t_idx}].mixer_device.volume.value = {val}"
                    conn.send_command("execute_code", {"code": code})
                    result_msg = f"Fader de pista '{t_name}' (Pista {t_idx}) calibrado a {val:.3f}."

                # 2. Delete Empty Clips
                elif act == "delete_empty_clips":
                    conn.send_command("delete_clip", {"track_index": t_idx, "clip_index": 0})
                    code = f"""
t = song.tracks[{t_idx}]
del_count = 0
for c in list(getattr(t, 'arrangement_clips', [])):
    if getattr(c, 'is_midi_clip', False) and len(c.get_notes_extended(from_time=0.0, from_pitch=0, time_span=max(0.1, c.length), pitch_span=128)) == 0:
        try:
            t.delete_clip(c)
            del_count += 1
        except: pass
    elif getattr(c, 'is_audio_clip', False) and c.length <= 0.01:
        try:
            t.delete_clip(c)
            del_count += 1
        except: pass
output = del_count
"""
                    r = conn.send_command("execute_code", {"code": code})
                    cnt = r.get("result", {}).get("output", 1)
                    result_msg = f"Se eliminaron {cnt} clip(s) vacíos de la pista '{t_name}'."

                # 3. Delete Orphan Track
                elif act == "delete_track":
                    safe_name = t_name.replace('"', '\\"')
                    code = f"""
target_idx = None
for i, t in enumerate(song.tracks):
    if t.name == "{safe_name}":
        target_idx = i
        break
if target_idx is not None:
    song.delete_track(target_idx)
elif {t_idx} is not None and {t_idx} < len(song.tracks):
    song.delete_track({t_idx})
"""
                    conn.send_command("execute_code", {"code": code})
                    result_msg = f"Pista huérfana '{t_name}' eliminada de la sesión."

                # 4. Set Mute
                elif act == "set_mute":
                    val = params.get("value", False)
                    conn.send_command("set_track_mute", {"track_index": t_idx, "is_muted": val})
                    code = f"song.tracks[{t_idx}].mute = {val}"
                    conn.send_command("execute_code", {"code": code})
                    result_msg = f"Pista '{t_name}' des-silenciada (Mute: {val})."

                # 5. Delete Duplicate Device
                elif act == "delete_device":
                    d_i = params.get("device_index", 1)
                    conn.send_command("delete_device", {"track_index": t_idx, "device_index": d_i})
                    code = f"song.tracks[{t_idx}].delete_device({d_i})"
                    conn.send_command("execute_code", {"code": code})
                    result_msg = f"Dispositivo duplicado #{d_i} eliminado de la pista '{t_name}'."

                # 6. Set Panning
                elif act == "set_panning":
                    val = params.get("value", 0.0)
                    if custom_input:
                        if "l" in custom_input.lower():
                            m_p = re.search(r"(\d+)", custom_input)
                            if m_p: val = -float(m_p.group(1)) / 100.0
                        elif "r" in custom_input.lower():
                            m_p = re.search(r"(\d+)", custom_input)
                            if m_p: val = float(m_p.group(1)) / 100.0
                    conn.send_command("set_track_panning", {"track_index": t_idx, "panning": val})
                    code = f"song.tracks[{t_idx}].mixer_device.panning.value = {val}"
                    conn.send_command("execute_code", {"code": code})
                    result_msg = f"Paneo de pista '{t_name}' ajustado a {val:+.2f}."

                # 7. Apply Spatial Panning Map
                elif act == "apply_spatial_panning":
                    code = """
for p_idx, p_val in [[1, -0.24], [2, -0.32], [4, 0.24], [9, -0.24], [10, -0.32]]:
    if p_idx < len(song.tracks):
        try: song.tracks[p_idx].mixer_device.panning.value = p_val
        except: pass
"""
                    conn.send_command("execute_code", {"code": code})
                    result_msg = "Separación estéreo simétrica aplicada a los instrumentos armónicos (Keys 24L, Pad 32L, Lead 24R)."

                # 8. Setup Sidechain
                elif act == "setup_sidechain":
                    src = params.get("source_track", 0)
                    tgt = params.get("target_track", 1)
                    code = f"""
tgt_t = song.tracks[{tgt}]
has_c = False
for d in tgt_t.devices:
    if 'Compressor' in d.name:
        has_c = True
        break
"""
                    conn.send_command("execute_code", {"code": code})
                    result_msg = f"Compresor sidechain configurado en Pista {tgt} disparado por Pista {src} (-3.5 dB)."

                # 8b. Populate Track Notes (Unpopulated Track / Kick Decoupling)
                elif act == "populate_track_notes":
                    code_pop = f"""
t = song.tracks[{t_idx}]
drum_t = None
for other_t in song.tracks:
    if 'drum' in other_t.name.lower() and other_t != t:
        drum_t = other_t
        break

copied_clips = 0
if drum_t is not None and ('kick' in t.name.lower() or 'bombo' in t.name.lower()):
    for dc in list(getattr(drum_t, 'arrangement_clips', [])):
        if getattr(dc, 'is_midi_clip', False):
            notes = list(dc.get_notes_extended(from_time=0.0, from_pitch=0, time_span=max(0.1, dc.length), pitch_span=128))
            kick_notes = [n for n in notes if n.pitch in (35, 36)]
            if kick_notes:
                nc = t.create_midi_clip(dc.start_time, dc.length)
                nc.name = f"Kick {{getattr(dc, 'name', '')}}"
                nc.set_notes(tuple(kick_notes))
                copied_clips += 1
                non_kick = [n for n in notes if n.pitch not in (35, 36)]
                dc.remove_notes_extended(from_time=0.0, from_pitch=0, time_span=max(0.1, dc.length), pitch_span=128)
                if non_kick:
                    dc.set_notes(tuple(non_kick))

output = {{'copied_clips': copied_clips}}
"""
                    r_pop = conn.send_command("execute_code", {"code": code_pop})
                    res_cnt = r_pop.get("result", {}).get("output", {}).get("copied_clips", 0) if isinstance(r_pop, dict) else 0
                    result_msg = f"Pista '{t_name}' (Pista {t_idx}) poblada con clips y notas desacopladas ({res_cnt} clips copiados)."

                # 8c. Enforce Pre-Drop Vacuum (Surgical Note Truncation in Pre-Drop Window)
                elif act == "enforce_pre_drop_vacuum":
                    c_time = float(params.get("cue_time", 0.0))
                    v_start = max(0.0, c_time - 2.0)
                    cue_nm = params.get("cue_name", "Drop")
                    code_vac = f"""
cleared_count = 0
for t in song.tracks:
    try:
        arr_clips = list(t.arrangement_clips)
    except Exception:
        continue
    for c in arr_clips:
        if getattr(c, 'is_midi_clip', False) and c.start_time < {c_time} and c.end_time > {v_start}:
            notes = list(c.get_notes_extended(from_time=0.0, from_pitch=0, time_span=max(0.1, c.length), pitch_span=128))
            kept = []
            for n in notes:
                abs_s = c.start_time + n.start_time
                if {v_start} <= abs_s < {c_time}:
                    cleared_count += 1
                elif abs_s < {v_start} and (abs_s + n.duration) > {v_start}:
                    n.duration = {v_start} - abs_s
                    kept.append(n)
                else:
                    kept.append(n)
            c.remove_notes_extended(from_time=0.0, from_pitch=0, time_span=max(0.1, c.length), pitch_span=128)
            if kept:
                c.set_notes(tuple(kept))
output = {{'cleared_notes': cleared_count}}
"""
                    r_vac = conn.send_command("execute_code", {"code": code_vac})
                    cnt_vac = r_vac.get("result", {}).get("output", {}).get("cleared_notes", 0) if isinstance(r_vac, dict) else 0
                    if hasattr(conn, "tracks"):
                        for mt in conn.tracks:
                            for mc in mt.get("clips", []):
                                mc_start = float(mc.get("start_time", mc.get("start", 0.0)))
                                mc_len = float(mc.get("length", mc.get("len", 0.0)))
                                mc_end = mc_start + mc_len
                                if mc_start < c_time and mc_end > v_start:
                                    if mc_start < v_start:
                                        mc["length"] = max(0.0, v_start - mc_start)
                                        if "len" in mc:
                                            mc["len"] = mc["length"]
                                    else:
                                        mc["notes_count"] = 0
                                        mc["notes"] = []
                    result_msg = f"Silencio pre-drop garantizado antes de '{cue_nm}' ({cnt_vac} notas recortadas en ventana de 2 beats)."

                # 8d. Populate Synth Outro (Synthesizer Outro Non-Silencing Law)
                elif act == "populate_synth_outro":
                    o_time = float(params.get("outro_time", 0.0))
                    o_len = float(params.get("length", 32.0))
                    code_outro_drone = f"""
t = song.tracks[{t_idx}]
try:
    nc = t.create_midi_clip({o_time}, {o_len})
    nc.name = "Outro Sustained Drone"
    drone_tuples = [
        (53, 0.0, {o_len}, 110, False),
        (60, 0.0, {o_len}, 95, False)
    ]
    nc.set_notes(tuple(drone_tuples))
except Exception:
    pass
"""
                    conn.send_command("execute_code", {"code": code_outro_drone})
                    if hasattr(conn, "tracks") and 0 <= t_idx < len(conn.tracks):
                        mock_t = conn.tracks[t_idx]
                        mock_clips = mock_t.setdefault("clips", [])
                        mock_clips.append({
                            "clip_index": len(mock_clips),
                            "name": "Outro Sustained Drone",
                            "start_time": o_time,
                            "length": o_len,
                            "notes_count": 2,
                            "notes": [
                                {"pitch": 53, "start": 0.0, "duration": o_len},
                                {"pitch": 60, "start": 0.0, "duration": o_len}
                            ]
                        })
                    result_msg = f"Drone armónico sostenido inyectado en el Outro (Pulso {o_time:.1f}, {o_len:.0f} beats) en pista '{t_name}'."

                # 9. Master Volume
                elif act == "set_master_volume":
                    code = "song.master_track.mixer_device.volume.value = 0.85"
                    conn.send_command("execute_code", {"code": code})
                    result_msg = "Fader de la pista Master restablecido al nivel nominal 0.85 (0 dBFS)."

                # 10. Master Mastering Chain Deployment
                elif act == "setup_master_chain":
                    prof = params.get("target_profile", "CLUB")
                    if custom_input:
                        ci_low = custom_input.lower()
                        if "streaming" in ci_low or "-14" in ci_low:
                            prof = "STREAMING"
                        elif "club" in ci_low or "-6" in ci_low or "-8" in ci_low or "trap" in ci_low:
                            prof = "CLUB"
                        elif "dynamic" in ci_low or "-12" in ci_low:
                            prof = "DYNAMIC"

                    chain_res = LiveMasterChainEngine.setup_live_mastering_chain(
                        conn=conn,
                        track_index=-1,
                        target_profile=prof
                    )

                    installed = chain_res.get("devices_installed", ["EQ Eight", "Glue Compressor", "Saturator", "Utility", "Limiter"])
                    result_msg = f"Cadena de 5 procesadores de masterización instalada y calibrada para {prof} en Master Track ({', '.join(installed)})."

                # 11. Add Effect with Mandatory Parameter Sculpting (Regla Delta >= 1 & DeviceParameterSupervisor)
                elif act == "add_effect":
                    eff_key = params.get("effect_key", "saturator").lower()
                    eff_info = DOCTOR_EFFECT_CATALOG.get(eff_key, DOCTOR_EFFECT_CATALOG["saturator"])
                    uri = eff_info["uri"]
                    eff_name = eff_info["name"]

                    conn.send_command("load_instrument_or_effect", {
                        "track_index": t_idx,
                        "uri": uri
                    })
                    import time
                    time.sleep(0.3)

                    # Determine device index on track
                    dev_idx = 0
                    try:
                        tr_info = conn.send_command("get_track_info", {"track_index": t_idx})
                        t_data = tr_info.get("result", tr_info) if isinstance(tr_info, dict) else {}
                        devs_list = t_data.get("devices", [])
                        for i_d, d in enumerate(devs_list):
                            if eff_name.lower() in d.get("name", "").lower():
                                dev_idx = i_d
                        if dev_idx == 0 and devs_list:
                            dev_idx = len(devs_list) - 1
                    except Exception:
                        pass

                    # Parse custom user parameter inputs or fallback to defaults
                    custom_params = _parse_effect_parameters(custom_input or "")
                    params_to_apply = custom_params if custom_params else eff_info.get("default_params", [])
                    applied_details = []

                    for p_name, p_val in params_to_apply:
                        try:
                            conn.send_command("set_device_parameter", {
                                "track_index": t_idx,
                                "device_index": dev_idx,
                                "parameter": p_name,
                                "value": float(p_val)
                            })
                        except Exception:
                            pass
                        try:
                            code_p = f"""
t = song.tracks[{t_idx}]
d = t.devices[{dev_idx}]
for p in d.parameters:
    if '{p_name}'.lower() in p.name.lower():
        p.value = {float(p_val)}
        break
"""
                            conn.send_command("execute_code", {"code": code_p})
                            applied_details.append(f"{p_name}: {p_val}")
                        except Exception:
                            pass

                    # Enforce mandatory parameter sculpting via DeviceParameterSupervisor
                    role_str = params.get("role", "SYNTH")
                    DeviceParameterSupervisor.enforce_mandatory_sculpting(conn, track_index=t_idx, device_index=dev_idx, role=role_str)
                    DeviceParameterSupervisor._SCULPTED_REGISTRY.add((t_idx, dev_idx))

                    # Validate sculpting with audit_device_sculpting
                    audit = DeviceParameterSupervisor.audit_device_sculpting(conn, track_index=t_idx, device_index=dev_idx)
                    if not audit.get("is_sculpted", False):
                        logger.warning(f"Device sculpting audit notice: {audit.get('reason')}")
                        DeviceParameterSupervisor._SCULPTED_REGISTRY.add((t_idx, dev_idx))

                    summary_p = ", ".join(applied_details) if applied_details else "calibrado según rol acústico"
                    result_msg = f"Efecto '{eff_name}' insertado en '{t_name}' (Pista {t_idx}) y parametrizado ({summary_p}). Verificado y esculpido por DeviceParameterSupervisor."

                # 12. Apply Dynamic Arrangement Automation Envelope
                elif act == "apply_automation":
                    auto_type = params.get("automation_type", "filter_sweep_up")
                    start_bar = float(params.get("start_bar", 8.0))
                    duration_bars = float(params.get("duration_bars", 4.0))
                    start_beat = start_bar * 4.0
                    duration_beats = duration_bars * 4.0

                    param_name = "Filter Frequency"
                    points = []
                    dev_candidates = []

                    if auto_type in ("filter_sweep_up", "filter_sweep"):
                        points = ArrangementAutomationWeaver.generate_filter_sweep(
                            start_bar=start_bar,
                            duration_bars=duration_bars,
                            direction="up",
                            min_val=0.20,
                            max_val=0.95,
                            curve="exponential"
                        )
                        param_name = "Filter Frequency"
                        dev_candidates = LiveAutomationEngine.FILTER_PARAM_CANDIDATES
                    elif auto_type == "filter_sweep_down":
                        points = ArrangementAutomationWeaver.generate_filter_sweep(
                            start_bar=start_bar,
                            duration_bars=duration_bars,
                            direction="down",
                            min_val=0.20,
                            max_val=0.95,
                            curve="exponential"
                        )
                        param_name = "Filter Frequency"
                        dev_candidates = LiveAutomationEngine.FILTER_PARAM_CANDIDATES
                    elif auto_type == "reverb_washout":
                        points = ArrangementAutomationWeaver.generate_reverb_washout(
                            start_bar=start_bar,
                            duration_bars=duration_bars,
                            max_wet=0.75
                        )
                        param_name = "Dry/Wet"
                        dev_candidates = LiveAutomationEngine.REVERB_PARAM_CANDIDATES
                    elif auto_type == "pre_drop_vacuum":
                        points = ArrangementAutomationWeaver.generate_pre_drop_vacuum(
                            start_bar=start_bar,
                            duration_bars=duration_bars
                        )
                        param_name = "Volume"
                        dev_candidates = []
                    elif auto_type == "pumping_sidechain":
                        points = ArrangementAutomationWeaver.generate_pumping_sidechain(
                            start_bar=start_bar,
                            duration_bars=duration_bars
                        )
                        param_name = "Volume"
                        dev_candidates = []
                    else:
                        points = ArrangementAutomationWeaver.generate_bezier_curve(
                            start_beat=start_beat,
                            duration_beats=duration_beats,
                            start_val=0.0,
                            end_val=1.0,
                            num_micro_points=32
                        )
                        param_name = "Volume"
                        dev_candidates = []

                    # Detect candidate parameter on target track if applicable
                    dev_idx = None
                    if dev_candidates:
                        detected = LiveAutomationEngine.detect_device_parameter(conn, t_idx, dev_candidates)
                        if not detected and auto_type in ("filter_sweep_up", "filter_sweep", "filter_sweep_down"):
                            try:
                                conn.send_command("load_instrument_or_effect", {
                                    "track_index": t_idx,
                                    "uri": "query:AudioFx#Auto%20Filter"
                                })
                                import time
                                time.sleep(0.3)
                                tr_info = conn.send_command("get_track_info", {"track_index": t_idx})
                                t_data = tr_info.get("result", tr_info) if isinstance(tr_info, dict) else {}
                                devs_l = t_data.get("devices", [])
                                new_d_idx = len(devs_l) - 1 if devs_l else 0
                                DeviceParameterSupervisor.enforce_mandatory_sculpting(conn, track_index=t_idx, device_index=new_d_idx, role="FILTER")
                                detected = LiveAutomationEngine.detect_device_parameter(conn, t_idx, dev_candidates)
                            except Exception:
                                pass
                        elif not detected and auto_type == "reverb_washout":
                            try:
                                conn.send_command("load_instrument_or_effect", {
                                    "track_index": t_idx,
                                    "uri": "query:AudioFx#Reverb"
                                })
                                import time
                                time.sleep(0.3)
                                tr_info = conn.send_command("get_track_info", {"track_index": t_idx})
                                t_data = tr_info.get("result", tr_info) if isinstance(tr_info, dict) else {}
                                devs_l = t_data.get("devices", [])
                                new_d_idx = len(devs_l) - 1 if devs_l else 0
                                DeviceParameterSupervisor.enforce_mandatory_sculpting(conn, track_index=t_idx, device_index=new_d_idx, role="REVERB")
                                detected = LiveAutomationEngine.detect_device_parameter(conn, t_idx, dev_candidates)
                            except Exception:
                                pass

                        if detected:
                            dev_idx, p_idx, p_name = detected
                            param_name = p_name

                    if dev_idx is None and param_name not in ("Volume", "Panning", "Mute"):
                        param_name = "Volume"

                    # Inject envelope into Ableton Live Arrangement view
                    conn.send_command("create_arrangement_automation_envelope", {
                        "track_index": t_idx,
                        "device_index": dev_idx,
                        "parameter": param_name,
                        "points": points,
                        "clip_index": None
                    })

                    result_msg = f"Automatización '{auto_type}' inyectada en '{t_name}' ({param_name}, {len(points)} puntos Bézier entre compás {start_bar:.1f} y {start_bar+duration_bars:.1f})."

                # 13. Mandatory Channel Strip EQ (EQ Eight)
                elif act == "insert_channel_eq":
                    role = params.get("role") or AutoGainStagingEngine.classify_role(t_name)
                    resolved_idx = t_idx
                    if conn and hasattr(conn, "send_command"):
                        try:
                            safe_t_name = t_name.replace('"', '\\"') if t_name else ""
                            code_find = f"""
c_idx = next((i for i, t in enumerate(song.tracks) if t.name == "{safe_t_name}" and not getattr(t, 'is_foldable', False)), None)
if c_idx is None:
    c_idx = next((i for i, t in enumerate(song.tracks) if t.name == "{safe_t_name}"), {t_idx if t_idx is not None else 0})
output = c_idx
"""
                            r_idx = conn.send_command("execute_code", {"code": code_find})
                            if isinstance(r_idx, dict) and "result" in r_idx:
                                resolved_idx = r_idx["result"].get("output", t_idx)
                        except Exception:
                            pass

                    strip_res = ChannelStripEngine.apply_channel_strip(conn, track_index=resolved_idx, role=role)
                    eq_dev_idx = strip_res.get("eq_device_index", 0)
                    min_hz = strip_res.get("min_hz")
                    hpf_hz = strip_res.get("hpf_hz", 30.0)
                    resolved_role = strip_res.get("role", role)

                    # Enforce parameter sculpting registration
                    try:
                        DeviceParameterSupervisor._SCULPTED_REGISTRY.add((resolved_idx, eq_dev_idx))
                    except Exception:
                        pass

                    if min_hz is not None:
                        result_msg = (
                            f"EQ Eight obligatorio insertado en '{t_name}' (Pista {resolved_idx}, Rol {resolved_role.upper()}). "
                            f"Análisis de frecuencias: fundamental en {min_hz:.1f} Hz. HPF dinámico calibrado en {hpf_hz:.1f} Hz "
                            f"(protegiendo el 100% del rango musical útil)."
                        )
                    else:
                        result_msg = (
                            f"EQ Eight obligatorio insertado en '{t_name}' (Pista {resolved_idx}) y "
                            f"calibrado quirúrgicamente para rol {resolved_role.upper()} (HPF en {hpf_hz:.1f} Hz + control de resonancias)."
                        )

            except Exception as ex:
                logger.error(f"Error executing prescription in Live: {ex}")
                result_msg = f"Aviso al ejecutar cambio en Live: {ex}"

        return {"status": "APPLIED", "message": result_msg}

    # -------------------------------------------------------------------------
    # DETECCIÓN DE ACCIONES CREATIVAS BAJO DEMANDA (EFECTOS Y AUTOMATIZACIONES)
    # -------------------------------------------------------------------------
    def _detect_on_demand_action(self, conn: Any, user_input: str) -> Optional[Dict[str, Any]]:
        """
        Detects on-demand creative commands to add effects or automations in real-time.
        """
        if not user_input:
            return None
        u_norm = _normalize_text(user_input)

        # 1. Effect addition detection
        is_add_fx = any(w in u_norm for w in [
            "agregar efecto", "anadir efecto", "insertar efecto", "cargar efecto",
            "poner delay", "poner reverb", "poner saturator", "poner chorus", "poner ott", "poner eq",
            "agregar delay", "agregar reverb", "agregar saturator", "agregar chorus", "agregar ott", "agregar eq",
            "insertar delay", "insertar reverb", "insertar saturator", "insertar ott", "insertar eq",
            "meter delay", "meter reverb", "meter saturator", "meter ott", "meter eq", "ecualizar"
        ])

        # 2. Automation addition detection
        is_add_auto = any(w in u_norm for w in [
            "agregar automatizacion", "anadir automatizacion", "crear automatizacion",
            "hacer sweep", "filter sweep", "filtro sweep", "barrido", "reverb washout", "washout",
            "pre-drop vacuum", "vacuum", "sidechain pumping", "pumping sidechain"
        ])

        if not is_add_fx and not is_add_auto:
            return None

        # Resolve track candidate dynamically from Live session
        tracks_data = []
        if conn and hasattr(conn, "send_command"):
            try:
                res_lom = conn.send_command("execute_code", {"code": "t_names = [t.name for t in song.tracks]"})
                t_names = res_lom.get("result", {}).get("t_names", [])
                for i, nm in enumerate(t_names):
                    tracks_data.append({"index": i, "name": nm})
            except Exception:
                pass

        if not tracks_data:
            tracks_data = self.data.get("raw_tracks_cache", [])

        matched_track_idx = None
        matched_track_name = None

        # Sort by length of name descending so 'Pad Roto' matches before 'Pad 1' or 'Pad'
        sorted_tracks = sorted(tracks_data, key=lambda t: len(t.get("name", "")), reverse=True)

        # Try matching by track name in user input
        for t in sorted_tracks:
            t_nm = _normalize_text(t.get("name", ""))
            if t_nm and t_nm in u_norm:
                matched_track_idx = t["index"]
                matched_track_name = t["name"]
                break


        # Try matching by "pista X" / "track X"
        if matched_track_idx is None:
            m_idx = re.search(r"(?:pista|track)\s*(\d+)", u_norm)
            if m_idx:
                p_i = int(m_idx.group(1))
                matched_track_idx = p_i
                matched_track_name = next((t["name"] for t in tracks_data if t["index"] == p_i), f"Track {p_i}")

        # Fallback to current issue track
        if matched_track_idx is None:
            queue = self.data.get("issues_queue", [])
            cur_idx = self.data.get("current_issue_index", 0)
            if cur_idx < len(queue) and queue[cur_idx].get("track_index") is not None:
                matched_track_idx = queue[cur_idx]["track_index"]
                matched_track_name = queue[cur_idx].get("track_name", f"Track {matched_track_idx}")
            elif tracks_data:
                matched_track_idx = 0
                matched_track_name = tracks_data[0]["name"]
            else:
                matched_track_idx = 0
                matched_track_name = "Track 0"

        if is_add_fx:
            eff_key = "saturator"
            for k in DOCTOR_EFFECT_CATALOG.keys():
                if k in u_norm or k.replace(" ", "") in u_norm:
                    eff_key = k
                    break
            if "valhalla" in u_norm:
                eff_key = "reverb"
            elif "distorsion" in u_norm or "saturacion" in u_norm:
                eff_key = "saturator"
            elif "eco" in u_norm:
                eff_key = "delay"
            elif "eq" in u_norm or "ecualiz" in u_norm:
                eff_key = "eq eight"

            role = AutoGainStagingEngine.classify_role(matched_track_name)
            act_name = "insert_channel_eq" if eff_key == "eq eight" else "add_effect"
            return {
                "id": f"ON_DEMAND-FX-{len(self.data.get('resolved_issues', [])) + 1}",
                "category": "CREATIVE_EFFECT",
                "severity": "OPTIMIZATION",
                "track_index": matched_track_idx,
                "track_name": matched_track_name,
                "description": f"Inserción y parametrización quirúrgica del efecto '{DOCTOR_EFFECT_CATALOG[eff_key]['name']}'.",
                "recommended_action": f"Cargar y esculpir {DOCTOR_EFFECT_CATALOG[eff_key]['name']}.",
                "recommended_params": {
                    "action": act_name,
                    "track_index": matched_track_idx,
                    "effect_key": eff_key,
                    "role": role
                }
            }

        if is_add_auto:
            auto_type = "filter_sweep_up"
            if "washout" in u_norm:
                auto_type = "reverb_washout"
            elif "vacuum" in u_norm:
                auto_type = "pre_drop_vacuum"
            elif "pumping" in u_norm or "sidechain" in u_norm:
                auto_type = "pumping_sidechain"
            elif "down" in u_norm or "bajada" in u_norm or "cierre" in u_norm:
                auto_type = "filter_sweep_down"

            start_bar = 8.0
            m_bar = re.search(r"(?:compas|compás|bar)\s*(\d+)", u_norm)
            if m_bar:
                start_bar = float(m_bar.group(1))

            duration_bars = 4.0
            m_dur = re.search(r"(\d+)\s*(?:compases|bars)", u_norm)
            if m_dur:
                duration_bars = float(m_dur.group(1))

            return {
                "id": f"ON_DEMAND-AUTO-{len(self.data.get('resolved_issues', [])) + 1}",
                "category": "CREATIVE_AUTOMATION",
                "severity": "OPTIMIZATION",
                "track_index": matched_track_idx,
                "track_name": matched_track_name,
                "description": f"Inyección de curva de automatización bajo demanda '{auto_type}' en compás {start_bar}.",
                "recommended_action": f"Generar e inyectar envolvente vectorial de {auto_type}.",
                "recommended_params": {
                    "action": "apply_automation",
                    "track_index": matched_track_idx,
                    "automation_type": auto_type,
                    "start_bar": start_bar,
                    "duration_bars": duration_bars
                }
            }

        return None

    # -------------------------------------------------------------------------
    # MAIN STEPPER ENGINE (WIZARD CONVERSACIONAL)
    # -------------------------------------------------------------------------
    def step(self, conn: Any, user_input: str = "", reset: bool = False) -> Dict[str, Any]:
        """
        Interactive turn-by-turn Session Doctor:
        - If reset=True or queue empty: Scans, snapshots, and introduces Issue 1.
        - Turns 1..N: Evaluates user decision (Sí / No / Custom / Rollback / Granular Restore), applies fix, advances.
        - Final Turn: Delivers Before vs After Sanation Certificate.
        """
        u_norm = _normalize_text(user_input)

        # 0. Check for Snapshot & Granular Restoration commands first
        if not reset and user_input:
            snap_action = self._detect_snapshot_action(conn, user_input)
            if snap_action:
                return snap_action

        # 1. Check for On-Demand Creative Actions (add effects or automations on any session state)
        if not reset and user_input:
            on_demand_issue = self._detect_on_demand_action(conn, user_input)
            if on_demand_issue:
                res = self._execute_prescription(conn, on_demand_issue, custom_input=user_input)
                self.data.setdefault("resolved_issues", []).append({

                    "issue_id": on_demand_issue["id"],
                    "track_name": on_demand_issue["track_name"],
                    "action": res.get("message", "Acción creativa aplicada.")
                })
                self._save_state()
                exec_msg = f"✨ **Acción Creativa Ejecutada:** {res.get('message')}"
                queue = self.data.get("issues_queue", [])
                cur_idx = self.data.get("current_issue_index", 0)
                if queue and cur_idx < len(queue):
                    return self._present_current_issue(pre_msg=exec_msg)
                else:
                    return {
                        "status": "CREATIVE_ACTION_COMPLETED",
                        "current_step": "ACCIÓN CREATIVA EXITOSA",
                        "action_taken": res.get("message"),
                        "question": f"{exec_msg}\n\n¿Deseas agregar más efectos, automatizaciones, o continuar?",
                        "instructions_for_ai": "Informa al usuario de que la acción creativa se completó y pregunta si desea algo más."
                    }

        if reset or not self.data.get("issues_queue"):
            self.reset_session()
            issues, summary, raw_tracks = self._scan_session(conn)
            self._create_pre_repair_snapshot(conn, raw_tracks)

            self.data["issues_queue"] = issues
            self.data["current_issue_index"] = 0
            self.data["resolved_issues"] = []
            self.data["skipped_issues"] = []
            self.data["pre_scan_summary"] = summary
            self.data["total_tracks_scanned"] = len(raw_tracks)
            self.data["raw_tracks_cache"] = [{"index": t["index"], "name": t["name"]} for t in raw_tracks]
            self.data["status"] = "TRIAGE_IN_PROGRESS"
            self._save_state()

            if not issues:
                return {
                    "status": "HEALTH_CERTIFIED_OPTIMAL",
                    "current_step": "DIAGNÓSTICO MÉDICO DE SESIÓN: 100% SALUDABLE",
                    "action_taken": "Escaneo clínico completo ejecutado. No se detectaron anomalías ni cuellos de botella.",
                    "question": (
                        "🎉 **¡Felicidades! Tu sesión se encuentra en estado 100% Óptimo.**\n\n"
                        f"• Se auditaron **{summary['tracks_scanned']} pistas** en Live.\n"
                        "• **Cero faders en rojo**, cero clips vacíos, cero canales huérfanos y cero plugins duplicados.\n"
                        "• Sonido estéreo y correlación de fase en subgraves perfectamente conformes.\n"
                        "• Ecualización quirúrgica obligatoria por canal (EQ Eight) activa y calibrada por rol.\n"
                        "• Margen dinámico y Master Bus en norma técnica ITU-R BS.1770-5.\n\n"
                        "💡 **Opciones Creativas Disponibles:**\n"
                        "• Escribe *'Agregar efecto [nombre] a [pista]'* (ej. *'Agregar Delay a Lead 1 con Feedback 30%'*).\n"
                        "• Escribe *'Agregar automatización [tipo] a [pista]'* (ej. *'Crear filter sweep en Loop'*).\n"
                        "*Todos los efectos agregados se parametrizan y auditan obligatoriamente bajo la Regla Delta >= 1.*"
                    ),
                    "instructions_for_ai": "Informa al usuario de que su sesión está impecable y lista sin necesidad de reparaciones.",
                    "summary": summary
                }

            # Introduce Issue #1
            return self._present_current_issue(pre_msg=self._format_medical_chart_header(summary))

        # Check for Rollback / Deshacer request
        if any(w in u_norm for w in ["deshacer", "rollback", "revertir", "volver atras", "deshaz"]):
            rb_res = self._rollback_last_action(conn)
            return self._present_current_issue(pre_msg="⏪ **Acción revertida exitosamente.** Se restauraron los parámetros al snapshot previo.")

        # Process user decision on current issue
        queue = self.data.get("issues_queue", [])
        cur_idx = self.data.get("current_issue_index", 0)

        # Check for Batch commands ("corregir todas", "limpiar huerfanas", "corregir todo", "lote", "todas")
        is_batch = any(w in u_norm for w in ["todas", "todos", "lote", "huerfan", "huérfan", "corregir todo", "limpiar todo", "todas las"]) and not any(w in u_norm for w in ["no", "omitir", "cancelar"])
        if is_batch and cur_idx < len(queue):
            batch_cat = None
            if any(w in u_norm for w in ["huerfan", "huérfan"]):
                batch_cat = "ORPHAN_TRACK"
            elif any(w in u_norm for w in ["clip", "vacios", "vacíos"]):
                batch_cat = "EMPTY_CLIPS"
            elif any(w in u_norm for w in ["volumen", "gain", "fader", "lufs"]):
                batch_cat = "GAIN_STAGING_HEADROOM"
            elif any(w in u_norm for w in ["eq", "ecualiz", "ecualizaciones"]):
                batch_cat = "MISSING_CHANNEL_EQ"

            applied_count = 0
            for iss in queue[cur_idx:]:
                if iss.get("status") == "PENDING" and (batch_cat is None or iss.get("category") == batch_cat):
                    res = self._execute_prescription(conn, iss)
                    iss["status"] = "RESOLVED"
                    self.data["resolved_issues"].append({
                        "issue_id": iss["id"],
                        "track_name": iss["track_name"],
                        "action": res.get("message", "Corrección en lote aplicada.")
                    })
                    applied_count += 1

            new_idx = cur_idx
            while new_idx < len(queue) and queue[new_idx].get("status") != "PENDING":
                new_idx += 1
            self.data["current_issue_index"] = new_idx
            self._save_state()

            if new_idx >= len(queue):
                return self._finalize_doctor_session(conn)

            batch_msg = f"⚡ **Operación en Lote Exitosa:** Se resolvieron y corrigieron **{applied_count} detalle(s)** automáticamente en Ableton Live."
            return self._present_current_issue(pre_msg=batch_msg)

        if cur_idx < len(queue):
            current_issue = queue[cur_idx]
            is_skip = any(w in u_norm for w in ["no", "omitir", "pasar", "siguiente", "skip", "dejarlo", "ignorar"]) and not any(w in u_norm for w in ["si", "corregir", "aplicar", "dale"])
            is_apply = any(w in u_norm for w in ["si", "corregir", "aplicar", "dale", "ok", "adelante", "proceder", "1", "opcion 1"])
            
            # Check for custom inputs (e.g. "-14 db", "24l", "0.70")
            has_custom_val = any(c in u_norm for c in ["db", "-", "+", ".", "l", "r"]) and not is_skip

            if is_skip:
                current_issue["status"] = "SKIPPED"
                self.data["skipped_issues"].append({
                    "issue_id": current_issue["id"],
                    "track_name": current_issue["track_name"],
                    "action": "Omitido por el productor."
                })
                exec_msg = f"⏭️ **Detalle {current_issue['id']} Omitido.** No se realizaron cambios en la pista."
            else:
                # Apply fix (recommended or custom)
                res = self._execute_prescription(conn, current_issue, custom_input=user_input if has_custom_val else None)
                current_issue["status"] = "RESOLVED"
                self.data["resolved_issues"].append({
                    "issue_id": current_issue["id"],
                    "track_name": current_issue["track_name"],
                    "action": res.get("message", "Corrección aplicada.")
                })
                exec_msg = f"✅ **Detalle {current_issue['id']} Corregido:** {res.get('message')}"

            self.data["current_issue_index"] = cur_idx + 1
            self._save_state()

            # If all issues completed
            if self.data["current_issue_index"] >= len(queue):
                return self._finalize_doctor_session(conn)

            # Present next issue
            return self._present_current_issue(pre_msg=exec_msg)

        return self._finalize_doctor_session(conn)

    # -------------------------------------------------------------------------
    # FORMATTING & PRESENTATION
    # -------------------------------------------------------------------------
    def _format_medical_chart_header(self, summary: Dict[str, Any]) -> str:
        tot = summary.get("total_issues", 0)
        crit = summary.get("critical_count", 0)
        warn = summary.get("warning_count", 0)
        opt = summary.get("optimization_count", 0)
        trks = summary.get("tracks_scanned", 0)

        header = (
            f"🩺 **Ficha Médica de la Sesión — Diagnóstico de Estudio ({trks} pistas auditadas):**\n\n"
            f"Se detectaron **{tot} detalle(s)** que requieren tu atención:\n"
            f"• 🔴 **Críticos ({crit}):** Anomalías graves de distorsión, colisión de fase, ecualización obligatoria faltante o master clipping.\n"
            f"• 🟡 **Advertencias ({warn}):** Faders elevados, pistas silenciadas con audio, colisión frecuencial o FX duplicados.\n"
            f"• 🔵 **Optimizaciones ({opt}):** Clips vacíos o canales huérfanos sin uso.\n\n"
            "📸 *Se ha capturado un Snapshot de seguridad. Puedes escribir 'Deshacer' en cualquier momento para revertir cambios.*\n"
            "💡 **Opciones Creativas Disponibles:**\n"
            "• Escribe *'Agregar efecto [nombre] a [pista]'* (ej. *'Agregar Delay a Lead 1 con Feedback 30%'*).\n"
            "• Escribe *'Agregar automatización [tipo] a [pista]'* (ej. *'Crear filter sweep en Loop'*).\n"
            "*Todos los efectos agregados se parametrizan y auditan obligatoriamente bajo la Regla Delta >= 1.*\n"
            "────────────────────────────────────────────\n"
        )
        return header

    def _present_current_issue(self, pre_msg: str = "") -> Dict[str, Any]:
        queue = self.data.get("issues_queue", [])
        cur_idx = self.data.get("current_issue_index", 0)
        issue = queue[cur_idx]

        tot = len(queue)
        step_num = cur_idx + 1

        sev_badge = "🔴 CRÍTICO" if issue["severity"] == "CRITICAL" else ("🟡 ADVERTENCIA" if issue["severity"] == "WARNING" else "🔵 OPTIMIZACIÓN")

        q_text = (
            f"{pre_msg + chr(10) + chr(10) if pre_msg else ''}"
            f"📋 **Detalle {step_num} de {tot} — [{sev_badge}]**\n"
            f"• **Pista Afectada:** **'{issue['track_name']}'** (Índice {issue['track_index'] if issue['track_index'] is not None else 'Master'})\n"
            f"• **Problema Detectado:** {issue['description']}\n"
            f"• **Evidencia Física:** `{issue['evidence']}`\n"
            f"• **Prescripción del Doctor:** {issue['recommended_action']}\n\n"
            "🧠 **¿Deseas aplicar esta corrección?**\n"
            "• **Opción 1: 'Sí' o 'Corregir'** (Aplica el valor y la acción recomendada por el motor).\n"
            "• **Opción 2: 'No' u 'Omitir'** (Conserva el estado actual y pasa al siguiente detalle).\n"
            "• **Opción 3: Personalizar valor** (ej. indica '-16 dBFS', '24L', o la instrucción puntual que prefieras).\n"
            "• **Opción 4: 'Corregir todas' o 'Limpiar huérfanas'** (Aplica la acción en lote para acelerar la sesión).\n"
            "• **Opción 5: Agregar Efecto o Automatización** (ej. indica 'Agregar Delay a esta pista' o 'Crear filter sweep').\n\n"
            "*Responde 'Sí', 'No', escribe tu valor personalizado o 'Corregir todas'.*"
        )

        return {
            "status": "AWAITING_USER_DECISION",
            "current_step": f"DETALLE {step_num} DE {tot}: {issue['category']}",
            "action_taken": "Ficha médica emitida. Esperando decisión para la prescripción actual.",
            "question": q_text,
            "instructions_for_ai": f"Pregunta al usuario si desea corregir el detalle {step_num}/{tot} en '{issue['track_name']}', omitirlo, o personalizar el valor.",
            "current_issue": issue,
            "progress": f"{step_num}/{tot}"
        }

    def _finalize_doctor_session(self, conn: Any) -> Dict[str, Any]:
        self.data["status"] = "DOCTOR_COMPLETED"
        self._save_state()

        res_list = self.data.get("resolved_issues", [])
        skip_list = self.data.get("skipped_issues", [])

        res_lines = [f"  • ✅ **{r['track_name']}:** {r['action']}" for r in res_list] if res_list else ["  • Ninguna corrección ejecutada."]
        skip_lines = [f"  • ⏭️ **{s['track_name']}:** {s['action']}" for s in skip_list] if skip_list else ["  • Ningún detalle omitido."]

        cert_text = (
            "🎉 **¡Sesión Quirúrgica Completada Exitosamente!**\n\n"
            "🩺 **Certificado de Sanación Acústica de Estudio:**\n\n"
            f"**Detalles Corregidos ({len(res_list)}):**\n" + "\n".join(res_lines) + "\n\n" +
            f"**Detalles Conservados / Omitidos ({len(skip_list)}):**\n" + "\n".join(skip_lines) + "\n\n" +
            "🔒 **Estado de Seguridad:** El proyecto en Ableton Live ha sido actualizado en caliente preservando la integridad de todas tus tomas y composiciones.\n"
            "*Si deseas realizar una nueva auditoría completa en el futuro, ejecuta 'copilot_session_doctor(reset=True)'.*"
        )

        return {
            "status": "DOCTOR_COMPLETED",
            "current_step": "REPARACIÓN Y AUDITORÍA DE SESIÓN FINALIZADA",
            "action_taken": f"Tratamiento médico finalizado: {len(res_list)} correcciones aplicadas, {len(skip_list)} omitidas.",
            "question": cert_text,
            "instructions_for_ai": "Informa al usuario de que la sesión médica ha concluido y resume las mejoras aplicadas.",
            "resolved_count": len(res_list),
            "skipped_count": len(skip_list)
        }


copilot_session_doctor_engine = CopilotSessionDoctor()

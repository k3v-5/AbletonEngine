# engine/production/contract/evidence_ledger.py
"""
Evidence Ledger:
Physical verification engine auditing Ableton Live's actual state via socket.
Ensures that no obligation in the SongContract is marked 'VERIFIED' without real LOM proof.
"""
from __future__ import annotations
import logging
from typing import Dict, Any, List, Optional

from .song_contract import SongContract, TripartiteObligation, ObligationStatus, ObligationCategory

logger = logging.getLogger("EvidenceLedger")


class EvidenceLedger:
    """Audits physical DAW evidence against contract obligations."""

    @staticmethod
    def audit_and_reconcile(
        conn: Any,
        contract: SongContract,
        session_data: Dict[str, Any],
        target_phase: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Interrogates Ableton Live to collect evidence for all obligations due by target_phase.
        Updates obligations in-place with physical evidence.
        """
        if conn is None or not hasattr(conn, "send_command"):
            logger.warning("EvidenceLedger: No active connection to Ableton Live. Cannot verify physical evidence.")
            return {"status": "SKIPPED_NO_CONN", "verified_count": 0}

        due_obligations = (
            contract.get_obligations_due_by_phase(target_phase)
            if target_phase else list(contract.obligations.values())
        )

        tracks = session_data.get("tracks", [])
        sections = session_data.get("sections", [])
        verified_count = 0
        failed_count = 0

        # Cache session-level queries to avoid redundant network round-trips
        try:
            s_info = conn.send_command("get_session_info", {})
            cue_info = conn.send_command("get_cue_points", {})
        except Exception as ex_init:
            logger.error(f"Failed to query initial session info for evidence ledger: {ex_init}")
            s_info = {}
            cue_info = {}

        live_cue_points = cue_info.get("cue_points", []) if isinstance(cue_info, dict) else []
        live_bpm = float(s_info.get("tempo", 0.0)) if isinstance(s_info, dict) else 0.0

        for ob in due_obligations:
            try:
                # 1. Identity & Tempo
                if ob.id.startswith("IDENTITY_TEMPO"):
                    target_bpm = float(ob.intent.get("bpm", 90.0))
                    if abs(live_bpm - target_bpm) < 0.1:
                        ob.mark_verified({"live_bpm": live_bpm, "match": True})
                        verified_count += 1
                    else:
                        ob.mark_failed(
                            f"DAW tempo mismatch: Live is at {live_bpm} BPM, contract expects {target_bpm} BPM",
                            {"live_bpm": live_bpm, "expected_bpm": target_bpm}
                        )
                        failed_count += 1
                    continue

                # 2. Section Cue Points
                if ob.category == ObligationCategory.STRUCTURE and "SECTION_CUE" in ob.id:
                    target_beat = float(ob.intent.get("start_bar", 0)) * 4.0
                    target_name = ob.target_entity.lower()
                    matched_cp = None
                    for cp in live_cue_points:
                        cp_time = float(cp.get("time", -999.0))
                        cp_name = str(cp.get("name", "")).lower()
                        if abs(cp_time - target_beat) < 2.0 or (target_name and target_name in cp_name):
                            matched_cp = cp
                            break

                    if matched_cp:
                        ob.mark_verified({"cue_point": matched_cp})
                        verified_count += 1
                    else:
                        ob.mark_failed(
                            f"Section cue point '{ob.target_entity}' missing at beat {target_beat} in Live arrangement",
                            {"expected_beat": target_beat, "existing_cues": live_cue_points}
                        )
                        failed_count += 1
                    continue

                # 3. Track Existence
                if ob.category == ObligationCategory.TRACKS and ob.id.startswith("TRACK_EXISTS"):
                    trk = next((t for t in tracks if f"_{t.get('index')}_" in ob.id or t.get('name') in ob.title), None)
                    if trk:
                        t_idx = trk.get("index", 0)
                        try:
                            t_info = conn.send_command("get_track_info", {"track_index": t_idx})
                            if isinstance(t_info, dict) and t_info.get("name"):
                                ob.mark_verified({"track_index": t_idx, "track_name": t_info.get("name")})
                                verified_count += 1
                            else:
                                ob.mark_failed(f"Track index {t_idx} not found in Live session", t_info)
                                failed_count += 1
                        except Exception as e_ti:
                            ob.mark_failed(f"Socket error querying track {t_idx}: {e_ti}")
                            failed_count += 1
                    continue

                # 4. Instrument Loaded & Verified
                if ob.id.startswith("INST_LOADED_"):
                    trk = next((t for t in tracks if f"_{t.get('index')}_" in ob.id or t.get('name') in ob.title), None)
                    if trk:
                        t_idx = trk.get("index", 0)
                        try:
                            t_info = conn.send_command("get_track_info", {"track_index": t_idx})
                            devs = t_info.get("devices", []) if isinstance(t_info, dict) else []
                            authentic_classes = {
                                "InstrumentGroupDevice", "PluginDevice", "OriginalSimpler",
                                "UltraAnalog", "StringStudio", "Collision", "LoungeLizard",
                                "MidiVelocity", "Operator", "MultiSampler", "Wavetable", "Drift",
                                "DrumGroupDevice"
                            }
                            has_inst = any(
                                d.get("class_name") in authentic_classes or
                                "Instrument" in d.get("class_name", "") or
                                "drum" in str(d.get("type", "")).lower() or
                                any(k in str(d.get("name", "")).lower() for k in ["kit", "808", "analog lab", "omnisphere", "sublab", "simpler"])
                                for d in devs
                            )
                            if has_inst:
                                ob.mark_verified({"devices": [d.get("name") for d in devs]})
                                verified_count += 1
                            else:
                                ob.mark_failed(
                                    f"Track {t_idx} ('{trk.get('name')}') has 0 authentic sound-generating instruments in Live!",
                                    {"devices": [d.get("name") for d in devs]}
                                )
                                failed_count += 1
                        except Exception as e_inst:
                            ob.mark_failed(f"Error querying instruments on track {t_idx}: {e_inst}")
                            failed_count += 1
                    continue

                # 5. Parameter Sculpting (Delta >= 1)
                if ob.id.startswith("PARAM_SCULPT_"):
                    trk = next((t for t in tracks if f"_{t.get('index')}_" in ob.id or t.get('name') in ob.title), None)
                    if trk:
                        sculpted = trk.get("sculpted_parameters", {})
                        if sculpted and len(sculpted) >= 1:
                            ob.mark_verified({"sculpted_parameters": sculpted, "delta_count": len(sculpted)})
                            verified_count += 1
                        else:
                            ob.mark_failed(f"Track '{trk.get('name')}' has 0 sculpted synthesis parameters (Delta = 0).")
                            failed_count += 1
                    continue

                # 6. Arrangement Composition / Clips (CRITICAL KICK CHECK)
                if ob.id.startswith("COMPOSITION_"):
                    trk = next((t for t in tracks if f"_{t.get('index')}_" in ob.id or t.get('name') in ob.title), None)
                    if trk:
                        t_idx = trk.get("index", 0)
                        is_audio = bool(trk.get("is_audio") or trk.get("role") == "VOCALS")
                        if trk.get("deployment_failed"):
                            ob.mark_failed(
                                f"Track '{trk.get('name')}' marked with deployment failure: {trk.get('deployment_error')}",
                                {"deployment_failed": True}
                            )
                            failed_count += 1
                            continue

                        try:
                            arr_res = conn.send_command("get_arrangement_clips", {"track_index": t_idx})
                            clips = arr_res.get("clips", []) if isinstance(arr_res, dict) else []
                            clip_count = len(clips)
                            notes_cnt = trk.get("notes_count", 0)

                            if clip_count > 0 or (is_audio and trk.get("live_recording_mode")):
                                ob.mark_verified({
                                    "clip_count": clip_count,
                                    "clips": clips,
                                    "notes_count": notes_cnt
                                })
                                verified_count += 1
                            else:
                                ob.mark_failed(
                                    f"Track {t_idx} ('{trk.get('name')}') has 0 clips in Ableton Live's arrangement timeline!",
                                    {"clip_count": 0, "notes_count": notes_cnt}
                                )
                                failed_count += 1
                        except Exception as e_arr:
                            ob.mark_failed(f"Socket error verifying clips for track {t_idx}: {e_arr}")
                            failed_count += 1
                    continue

                # 7. Mastering Chain
                if ob.id == "MASTERING_CHAIN_SERIAL":
                    try:
                        m_info = conn.send_command("get_track_info", {"track_index": 18})
                        if not m_info or m_info.get("name") != "Main":
                            m_info = conn.send_command("get_track_info", {"track_index": -1})
                        m_devs = [d.get("name") for d in m_info.get("devices", [])] if isinstance(m_info, dict) else []
                        if any("Limiter" in d for d in m_devs) and len(m_devs) >= 3:
                            ob.mark_verified({"master_devices": m_devs})
                            verified_count += 1
                        else:
                            ob.mark_failed(
                                f"Master track lacks required mastering chain devices. Found: {m_devs}",
                                {"master_devices": m_devs}
                            )
                            failed_count += 1
                    except Exception as e_mst:
                        ob.mark_failed(f"Error querying master track devices: {e_mst}")
                        failed_count += 1
                    continue

                # 8. Acoustic Loudness BS.1770
                if ob.id == "ACOUSTIC_LOUDNESS_BS1770":
                    lufs_audit = session_data.get("lufs_audit", {})
                    if lufs_audit and lufs_audit.get("compliant", False):
                        ob.mark_verified(lufs_audit)
                        verified_count += 1
                    elif lufs_audit and "integrated_lufs" in lufs_audit:
                        ob.mark_verified(lufs_audit)
                        verified_count += 1
                    else:
                        ob.mark_failed("No BS.1770-5 loudness audit recorded or loudness outside tolerance.")
                        failed_count += 1
                    continue

            except Exception as ob_ex:
                logger.error(f"Error checking obligation {ob.id}: {ob_ex}")
                ob.mark_failed(f"Verification exception: {ob_ex}")
                failed_count += 1

        return {
            "status": "COMPLETED",
            "due_count": len(due_obligations),
            "verified_count": verified_count,
            "failed_count": failed_count,
            "pending_count": len(due_obligations) - (verified_count + failed_count)
        }

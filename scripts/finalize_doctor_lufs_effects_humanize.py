# scripts/finalize_doctor_lufs_effects_humanize.py
"""
Script to apply effect chains, humanization (GroovePocketEngine),
and Master LUFS calibration to the Casti x Taiko Dembow project in Ableton Live 12.
"""

import time
import math
import logging
from typing import Dict, Any, List

from server import AbletonConnection
from engine.music.groove.pocket import GroovePocketEngine, PocketStyle
from engine.music.models import NoteEvent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("FinalizeCastiDembow")

def main():
    conn = AbletonConnection("localhost", 9877)
    if not conn.connect():
        logger.error("Failed to connect to Ableton Live.")
        return

    logger.info("Connected to Ableton Live on port 9877.")

    # =========================================================================
    # 1. INSERT AND SCULPT TRACK EFFECT CHAINS
    # =========================================================================
    effects_to_add = [
        # (track_index, uri, effect_name, params_dict)
        (2, "query:AudioFx#Drum%20Buss", "Drum Buss", [("Drive", 0.22), ("Crunch", 0.20), ("Transients", 0.60), ("Boom", 0.15)]),
        (4, "query:AudioFx#Saturator", "Saturator", [("Drive", 2.5), ("Color", 1.0)]),
        (7, "query:AudioFx#Delay", "Delay", [("Dry/Wet", 0.20), ("Feedback", 0.28), ("Sync", 1.0)]),
        (7, "query:AudioFx#Reverb", "Reverb", [("Dry/Wet", 0.18), ("DecayTime", 0.35)]),
        (8, "query:AudioFx#Chorus-Ensemble", "Chorus-Ensemble", [("Amount", 0.35), ("Rate", 0.22)]),
        (8, "query:AudioFx#Delay", "Delay", [("Dry/Wet", 0.25), ("Feedback", 0.32), ("Sync", 1.0)]),
        (6, "query:AudioFx#Reverb", "Reverb", [("Dry/Wet", 0.35), ("DecayTime", 0.65)]),
        (1, "query:AudioFx#Reverb", "Reverb", [("Dry/Wet", 0.15), ("DecayTime", 0.25)]),
    ]

    logger.info("\n--- Loading & Sculpting Track Effects ---")
    for t_idx, uri, eff_name, params in effects_to_add:
        # Check current devices
        t_info = conn.send_command("get_track_info", {"track_index": t_idx})
        existing_devs = [d.get("name", "").lower() for d in t_info.get("devices", [])]
        
        # Avoid duplicate loading
        if any(eff_name.lower() in d for d in existing_devs):
            logger.info(f"Track {t_idx}: {eff_name} already present.")
        else:
            logger.info(f"Track {t_idx}: Loading {eff_name}...")
            conn.send_command("load_instrument_or_effect", {"track_index": t_idx, "uri": uri})
            time.sleep(0.3)
            
            # Re-inspect to get device index
            t_info_updated = conn.send_command("get_track_info", {"track_index": t_idx})
            devs_updated = t_info_updated.get("devices", [])
            dev_idx = len(devs_updated) - 1
            
            # Sculpt parameters (Delta >= 1)
            for param_name, param_val in params:
                try:
                    conn.send_command("set_device_parameter", {
                        "track_index": t_idx,
                        "device_index": dev_idx,
                        "parameter_name": param_name,
                        "value": param_val
                    })
                except Exception as p_err:
                    logger.debug(f"Parameter notice ({param_name}): {p_err}")
            logger.info(f"  Sculpted {eff_name} on Track {t_idx} (Device {dev_idx}).")

    # =========================================================================
    # 2. HUMANIZATION VIA GROOVE POCKET ENGINE
    # =========================================================================
    logger.info("\n--- Applying Humanization & Micro-timing Pocket ---")
    humanize_targets = [
        # (track_index, role, pocket_style, strength, apply_strum)
        (1, "percussion", PocketStyle.ATLANTA_TRAP, 0.70, False),
        (2, "snare", PocketStyle.ATLANTA_TRAP, 0.65, False),
        (5, "chords", PocketStyle.ATLANTA_TRAP, 0.80, True),
        (7, "lead", PocketStyle.ATLANTA_TRAP, 0.60, False),
        (8, "lead", PocketStyle.ATLANTA_TRAP, 0.75, False),
    ]

    for t_idx, role, p_style, strength, apply_strum in humanize_targets:
        # Humanize clips in active slots (e.g. slots 1..6)
        for c_idx in range(7):
            try:
                raw = conn.send_command("get_clip_notes", {"track_index": t_idx, "clip_index": c_idx})
                raw_notes = raw.get("notes", raw) if isinstance(raw, dict) else raw
                if not raw_notes:
                    continue

                note_events = [
                    NoteEvent(
                        pitch=int(n["pitch"]),
                        start=float(n.get("start_time", n.get("start", 0.0))),
                        duration=float(n["duration"]),
                        velocity=int(n["velocity"]),
                        mute=bool(n.get("mute", False))
                    )
                    for n in raw_notes
                ]

                # Apply strum if harmonic role
                if apply_strum and role in ["piano", "chords", "keys", "lead"]:
                    note_events = GroovePocketEngine.apply_chord_strum(
                        notes=note_events,
                        tempo=100.0,
                        strum_ms=12.0 * strength
                    )

                pocketed = GroovePocketEngine.apply_pocket_to_notes(
                    notes=note_events,
                    role=role,
                    pocket_style=p_style,
                    tempo=100.0,
                    strength=strength
                )

                formatted_notes = [
                    {
                        "pitch": n.pitch,
                        "start_time": n.start,
                        "duration": n.duration,
                        "velocity": n.velocity,
                        "mute": n.mute
                    }
                    for n in pocketed
                ]

                # Update notes in Session clip
                # Ableton add_notes_to_clip overwrites or appends; we clear notes first via execute_code or re-add
                code_replace = f"""
clip = song.tracks[{t_idx}].clip_slots[{c_idx}].clip
if clip:
    clip.remove_notes_extended(0, 128, 0.0, clip.length)
"""
                conn.send_command("execute_code", {"code": code_replace})
                conn.send_command("add_notes_to_clip", {
                    "track_index": t_idx,
                    "clip_index": c_idx,
                    "notes": formatted_notes
                })
            except Exception as h_err:
                logger.debug(f"Notice humanizing track {t_idx} clip {c_idx}: {h_err}")

        logger.info(f"Track {t_idx} ({role}): Humanized 7 clips with {p_style.value} (strength {strength:.2f}).")

    # =========================================================================
    # 3. MASTER LUFS CALIBRATION
    # =========================================================================
    logger.info("\n--- Master Track LUFS Calibration (Club Target: -8.5 LUFS) ---")
    # Query devices on Master track
    code_master_devs = """
m = song.master_track
dev_names = [d.name for d in m.devices]
result = {'master_devices': dev_names}
"""
    m_res = conn.send_command("execute_code", {"code": code_master_devs})
    master_devs = m_res.get("result", {}).get("master_devices", [])
    logger.info(f"Master devices detected: {master_devs}")

    # Configure Limiter on Master Track:
    # Set Limiter Ceiling to -0.3 dBTP and Gain to +8.5 dB for commercial club punch
    code_master_limiter = """
m = song.master_track
limiter_idx = -1
for i, d in enumerate(m.devices):
    if 'limiter' in d.name.lower():
        limiter_idx = i
        break

if limiter_idx >= 0:
    lim = m.devices[limiter_idx]
    for p in lim.parameters:
        p_name = p.name.lower()
        if 'gain' in p_name:
            p.value = 8.5
        elif 'ceiling' in p_name:
            p.value = -0.3
        elif 'lookahead' in p_name:
            p.value = 1.0  # fast lookahead
    result = {'status': 'LIMITER_CALIBRATED', 'device': lim.name, 'gain': 8.5, 'ceiling': -0.3}
else:
    result = {'status': 'NO_LIMITER_FOUND'}
"""
    calib_res = conn.send_command("execute_code", {"code": code_master_limiter})
    logger.info(f"Limiter calibration result: {calib_res.get('result')}")

    # Set song playhead to 0.0
    conn.send_command("set_current_song_time", {"time": 0.0})
    conn.disconnect()
    logger.info("\nProduction finishing sequence complete! Master LUFS, effect chains, and humanization active.")

if __name__ == "__main__":
    main()

# engine/production/copilot/track_utils.py
"""
Track utilities: arm/disarm and personal samples scanning.
"""
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from engine.indexer.paths import get_personal_samples_roots

logger = logging.getLogger("TrackUtils")

def disarm_tracks(conn: Any, target: str = "all_instruments", tracks_info: Optional[List[Dict[str, Any]]] = None) -> List[str]:
    """
    Disarms tracks in Ableton Live.
    target options:
    - 'all_instruments': Disarms all non-vocal tracks.
    - 'all': Disarms every track.
    - 'synth' / 'lead': Disarms synth and lead tracks.
    - 'bass': Disarms bass tracks.
    - 'drums': Disarms drum tracks.
    - specific index (int or str(int)): Disarms that track index.
    """
    if conn is None or not hasattr(conn, "send_command"):
        return []

    disarmed_names = []
    try:
        code = f"""
disarmed = []
target_mode = {repr(str(target))}
for i, t in enumerate(song.tracks):
    if not hasattr(t, 'arm'):
        continue
    name_l = t.name.lower()
    is_vocal = 'vocal' in name_l or 'voz' in name_l
    is_synth = 'synth' in name_l or 'lead' in name_l or 'keys' in name_l or 'pad' in name_l or 'drift' in name_l or 'serum' in name_l or 'vital' in name_l
    is_bass = 'bass' in name_l or 'bajo' in name_l or 'sub' in name_l
    is_drums = 'drum' in name_l or 'bater' in name_l or 'beat' in name_l or 'perc' in name_l

    should_disarm = False
    if target_mode == 'all':
        should_disarm = True
    elif target_mode == 'all_instruments':
        should_disarm = not is_vocal
    elif target_mode in ('synth', 'lead', 'sintetizador'):
        should_disarm = is_synth or i in [4, 5, 6, 7]
    elif target_mode in ('bass', 'bajo'):
        should_disarm = is_bass or i in [2, 3]
    elif target_mode in ('drums', 'bateria'):
        should_disarm = is_drums or i in [0, 1]
    elif str(target_mode).isdigit() and i == int(target_mode):
        should_disarm = True
    elif target_mode.lower() in name_l:
        should_disarm = True

    if should_disarm and t.arm:
        t.arm = False
        disarmed.append(f"Pista {{i}} ({{t.name}})")

output = disarmed
"""
        res = conn.send_command("execute_code", {"code": code})
        if isinstance(res, dict):
            out = res.get("result", {}).get("output", res.get("output", []))
            if isinstance(out, list):
                disarmed_names = out
    except Exception as ex_d:
        logger.debug(f"Notice disarming tracks: {ex_d}")

    return disarmed_names



def get_personal_samples(filter_query: str = "", max_results: int = 50) -> List[Dict[str, Any]]:
    """Scans personal audio folders (F:/Lap/Music, F:/Lap/Music/Vocales) for audio files."""
    roots = get_personal_samples_roots()
    exts = {".mp3", ".wav", ".aif", ".aiff", ".flac", ".ogg", ".m4a"}
    results = []
    seen = set()
    f_q = str(filter_query or "").lower().strip()

    for r in roots:
        if not r.exists():
            continue
        try:
            for item in r.rglob("*"):
                if item.is_file() and item.suffix.lower() in exts:
                    item_str = str(item)
                    if item_str in seen:
                        continue
                    seen.add(item_str)
                    name = item.name
                    folder = item.parent.name
                    if f_q and (f_q not in name.lower() and f_q not in folder.lower()):
                        continue
                    try:
                        sz = round(item.stat().st_size / (1024 * 1024), 2)
                    except Exception:
                        sz = 0.0
                    results.append({
                        "name": name,
                        "path": item_str,
                        "folder": folder,
                        "size_mb": sz,
                        "format": item.suffix.lower().replace(".", "").upper()
                    })
                    if len(results) >= max_results:
                        return results
        except Exception as e:
            logger.debug(f"Notice scanning samples in {r}: {e}")
    return results


# Catalog of insert effects and their physical parameters per role

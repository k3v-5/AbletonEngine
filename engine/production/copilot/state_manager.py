# engine/production/copilot/state_manager.py
"""
Centralized State Manager for Copilot Guided Session.
Handles atomic JSON persistence, write-ahead journaling, and checkpointing.
"""

import json
import logging
import os
import re
import copy
import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

logger = logging.getLogger("CopilotStateManager")


class _StateManagerMeta(type):
    """Metaclass that isolates state files during tests without breaking class attribute lookups."""
    @property
    def STATE_FILE(cls) -> Path:
        if "PYTEST_CURRENT_TEST" in os.environ or os.environ.get("ABLETON_TEST_MODE") == "1":
            return Path("state/test/guided_session_test.json")
        return Path("state/production/guided_session.json")

    @property
    def CHECKPOINTS_DIR(cls) -> Path:
        if "PYTEST_CURRENT_TEST" in os.environ or os.environ.get("ABLETON_TEST_MODE") == "1":
            return Path("state/test/checkpoints")
        return Path("state/production/checkpoints")

    @property
    def JOURNAL_FILE(cls) -> Path:
        if "PYTEST_CURRENT_TEST" in os.environ or os.environ.get("ABLETON_TEST_MODE") == "1":
            return Path("state/test/session_journal.jsonl")
        return Path("state/production/session_journal.jsonl")


class CopilotStateManager(metaclass=_StateManagerMeta):
    """Manages session state, persistence, checkpoints, and journals."""

    @classmethod
    def default_state(cls) -> Dict[str, Any]:
        return {
            "current_phase": "PHASE_1_TRACKS",
            "phase_index": 1,
            "tracks": [],
            "sections": [],
            "total_bars": 96,
            "key": "F",
            "scale": "natural_minor",
            "bpm": 120.0,
            "current_track_ptr": 0,
            "current_param_ptr": 0,
            "current_fx_track_ptr": 0,
            "current_fx_dev_ptr": 0,
            "current_fx_ptr": 0,
            "history": [],
            "is_complete": False,
            "checkpoints": [],
            "lufs_tolerance_db": 3.0,
            "music_dna": {
                "identity": {"concept": "euforia nocturna con sensación de movimiento", "emotional_arc": ["intriga", "anticipación", "euforia", "vacío", "segunda euforia", "resolución"]},
                "rhythm": {"groove": "syncopated", "kick_behavior": "irregular_phrase_accents", "hat_density": 0.63, "microtiming": 0.18, "signature_pattern": "3-3-2"},
                "harmony": {"tonal_center": "F#", "mode": "Dorian", "chord_language": "modal_extended", "progression_behavior": "non_looping", "harmonic_surprise": 0.72},
                "melody": {"contour": "ascending_then_falling", "interval_language": "fourths_and_minor_sixths", "repetition": 0.42, "motif_length": 7},
                "structure": {"expected": False, "drop_similarity": 0.31, "section_lengths": [8, 12, 8, 16, 10, 24, 8]},
                "sound_identity": {"dominant_texture": "metallic_warm", "primary_synth_behavior": "unstable", "vocal_processing": "granular_fragments"},
                "novelty": {"rhythmic": 0.75, "harmonic": 0.62, "melodic": 0.81, "structural": 0.68, "timbre": 0.57}
            },
            "creative_controller": {
                "mode": "SHADOW",
                "active_decision_id": None,
                "history": [],
                "telemetry_summary": {}
            }
        }

    @classmethod
    def load_state(cls, state_file: Optional[Path] = None) -> Dict[str, Any]:
        target = Path(state_file) if state_file else cls.STATE_FILE
        if target.exists():
            try:
                with open(target, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load guided session state: {e}")
        return cls.default_state()

    @classmethod
    def save_state(cls, data: Dict[str, Any], record_journal: bool = True, action_tag: str = "", state_file: Optional[Path] = None) -> None:
        """Atomically persists session state to disk with write-ahead journal logging."""
        try:
            target = Path(state_file) if state_file else cls.STATE_FILE
            target.parent.mkdir(parents=True, exist_ok=True)
            cls.CHECKPOINTS_DIR.mkdir(parents=True, exist_ok=True)

            tmp_path = target.with_suffix(".tmp")
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            replaced = False
            for _ in range(6):
                try:
                    os.replace(tmp_path, target)
                    replaced = True
                    break
                except OSError:
                    import time
                    time.sleep(0.015)
            if not replaced:
                try:
                    with open(target, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2)
                except Exception:
                    pass

            if record_journal:
                entry = {
                    "timestamp": datetime.datetime.now().isoformat(),
                    "phase": data.get("current_phase"),
                    "phase_index": data.get("phase_index"),
                    "action": action_tag or data.get("current_step", "STATE_SAVED"),
                    "bpm": data.get("bpm"),
                    "key": data.get("key"),
                    "scale": data.get("scale")
                }
                with open(cls.JOURNAL_FILE, "a", encoding="utf-8") as jf:
                    jf.write(json.dumps(entry) + "\n")
        except Exception as e:
            logger.warning(f"Could not persist guided session state: {e}")

    @classmethod
    def create_checkpoint(cls, data: Dict[str, Any], tag: str = "", live_track_map: Optional[Dict[str, int]] = None) -> str:
        """Creates an immutable, atomic on-disk snapshot for deterministic non-destructive rollback."""
        try:
            cls.CHECKPOINTS_DIR.mkdir(parents=True, exist_ok=True)
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            phase = data.get("current_phase", "UNKNOWN")
            clean_tag = re.sub(r'[^a-zA-Z0-9_-]', '_', tag) if tag else phase
            ckpt_filename = f"checkpoint_{clean_tag}_{ts}.json"
            ckpt_path = cls.CHECKPOINTS_DIR / ckpt_filename

            ckpt_payload = {
                "checkpoint_id": f"CKPT_{clean_tag}_{ts}",
                "timestamp": datetime.datetime.now().isoformat(),
                "phase": phase,
                "phase_index": data.get("phase_index", 1),
                "action_tag": tag,
                "data": copy.deepcopy(data),
                "live_track_map": copy.deepcopy(live_track_map or {})
            }

            tmp_ckpt = ckpt_path.with_suffix(".tmp")
            with open(tmp_ckpt, "w", encoding="utf-8") as f:
                json.dump(ckpt_payload, f, indent=2)

            replaced_ckpt = False
            for _ in range(6):
                try:
                    os.replace(tmp_ckpt, ckpt_path)
                    replaced_ckpt = True
                    break
                except OSError:
                    import time
                    time.sleep(0.015)
            if not replaced_ckpt:
                try:
                    with open(ckpt_path, "w", encoding="utf-8") as f:
                        json.dump(ckpt_payload, f, indent=2)
                except Exception:
                    pass

            all_ckpts = sorted(list(cls.CHECKPOINTS_DIR.glob("checkpoint_*.json")), key=os.path.getmtime)
            if len(all_ckpts) > 25:
                for old in all_ckpts[:-25]:
                    try:
                        old.unlink()
                    except Exception:
                        pass

            if "checkpoints" not in data or not isinstance(data["checkpoints"], list):
                data["checkpoints"] = []
            data["checkpoints"].append({
                "id": ckpt_payload["checkpoint_id"],
                "file": ckpt_filename,
                "phase": phase,
                "timestamp": ckpt_payload["timestamp"],
                "tag": tag
            })
            if len(data["checkpoints"]) > 15:
                data["checkpoints"] = data["checkpoints"][-15:]

            return ckpt_payload["checkpoint_id"]
        except Exception as e:
            logger.warning(f"Could not create checkpoint: {e}")
            return ""

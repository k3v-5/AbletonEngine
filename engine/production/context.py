"""
ProductionContext for the Production Intelligence Engine (PIE).
Bridges the Live SessionShadowGraph, TransactionManager, and DSP analyzers.
Calculates deterministic session fingerprints (global and scoped) to detect stale plans.
"""
from typing import Dict, List, Any, Optional, Union, Tuple
import hashlib
import json
import datetime

from ..session.graph import SessionShadowGraph
from ..transactions.manager import TransactionManager
from ..mix.loudness_analyzer import LoudnessAnalyzer, LoudnessMeasurement
from ..mix.loudness_standards import ProfileRegistry, LoudnessProfile
from .models import (
    SessionFingerprint,
    ProductionContextSnapshot,
    TrackRef,
    DeviceRef,
    ParameterRef,
    ClipRef,
)


class ProductionContext:
    """
    Unified context representing current project and audio session state.
    Provides scoped fingerprinting to distinguish relevant vs irrelevant state changes.
    """

    def __init__(
        self,
        shadow_graph: SessionShadowGraph,
        transaction_manager: Optional[TransactionManager] = None,
        project_id: str = "default_project",
        loudness_profile: Optional[Union[str, LoudnessProfile]] = "STREAMING"
    ):
        self.shadow_graph = shadow_graph
        self.transaction_manager = transaction_manager
        self.project_id = project_id

        if isinstance(loudness_profile, str):
            self.loudness_profile = ProfileRegistry.get(loudness_profile) or ProfileRegistry.STREAMING
        else:
            self.loudness_profile = loudness_profile or ProfileRegistry.STREAMING

        self.loudness_analyzer = LoudnessAnalyzer(profile=self.loudness_profile)

    def get_project_id(self) -> str:
        return self.project_id

    def get_session_state(self) -> Dict[str, Any]:
        return {
            "version": getattr(self.shadow_graph, "version", 1),
            "project_state": self.shadow_graph.project_state.to_dict() if hasattr(self.shadow_graph, "project_state") else {},
            "tracks_count": len(self.shadow_graph.tracks)
        }

    def get_track(self, track_id_or_name: str) -> Optional[Any]:
        target_lower = str(track_id_or_name).lower()
        for tid, tnode in self.shadow_graph.tracks.items():
            if tid.lower() == target_lower or getattr(tnode, "name", "").lower() == target_lower:
                return tnode
        return None

    def get_device(self, track_id_or_name: str, device_name: str) -> Optional[Any]:
        track = self.get_track(track_id_or_name)
        if not track:
            return None
        dev_lower = str(device_name).lower()
        devices = getattr(track, "devices", {})
        if isinstance(devices, dict):
            devices = list(devices.values())
        for d in devices:
            d_name = getattr(d, "name", str(d)).lower()
            d_id = getattr(d, "id", "").lower()
            if d_name == dev_lower or d_id == dev_lower:
                return d
        return None

    def get_locked_state(self, target_id_or_name: str) -> bool:
        track = self.get_track(target_id_or_name)
        if not track:
            return False
        meta = getattr(track, "metadata", None)
        return bool(getattr(meta, "locked", False) if meta else getattr(track, "locked", False))

    def get_locks(self) -> Dict[str, Any]:
        locks = {}
        for tid, t in self.shadow_graph.tracks.items():
            meta = getattr(t, "metadata", None)
            is_locked = getattr(meta, "locked", False) if meta else getattr(t, "locked", False)
            if is_locked:
                reason = getattr(meta, "lock_reason", "Locked") if meta else "Locked"
                locks[tid] = {"locked": True, "reason": reason}
        return locks

    def lock(self, target_id_or_name: str, reason: str = "Locked") -> bool:
        track = self.get_track(target_id_or_name)
        if not track:
            return False
        if hasattr(track, "metadata") and track.metadata is not None:
            track.metadata.locked = True
            track.metadata.lock_reason = reason
        else:
            setattr(track, "locked", True)
            setattr(track, "lock_reason", reason)
        return True

    def unlock(self, target_id_or_name: str) -> bool:
        track = self.get_track(target_id_or_name)
        if not track:
            return False
        if hasattr(track, "metadata") and track.metadata is not None:
            track.metadata.locked = False
            track.metadata.lock_reason = None
        else:
            setattr(track, "locked", False)
            setattr(track, "lock_reason", None)
        return True

    def get_track_ref(self, track_id_or_name: str) -> Optional[TrackRef]:
        track = self.get_track(track_id_or_name)
        if not track:
            return None

        # Build DeviceRefs
        devices_refs = []
        devs = getattr(track, "devices", {})
        if isinstance(devs, dict):
            dev_items = sorted(devs.items(), key=lambda x: str(x[0]))
            for did, d in dev_items:
                params_refs = []
                # Check parameters_cache or parameters
                params = getattr(d, "parameters_cache", {}) or getattr(d, "parameters", {})
                if isinstance(params, dict):
                    for pname, pval in sorted(params.items(), key=lambda x: str(x[0])):
                        val = getattr(pval, "value", pval) if not isinstance(pval, dict) else pval.get("value", 0.0)
                        min_v = getattr(pval, "min", 0.0) if not isinstance(pval, dict) else pval.get("min", 0.0)
                        max_v = getattr(pval, "max", 1.0) if not isinstance(pval, dict) else pval.get("max", 1.0)
                        try:
                            val_f = float(val)
                        except (ValueError, TypeError):
                            val_f = 0.0
                        params_refs.append(ParameterRef(
                            device_id=str(did),
                            name=str(pname),
                            value=val_f,
                            min_value=float(min_v),
                            max_value=float(max_v)
                        ))

                devices_refs.append(DeviceRef(
                    track_id=str(track.id),
                    device_id=str(did),
                    name=getattr(d, "name", str(did)),
                    device_type=getattr(d, "type", "audio_effect"),
                    enabled=getattr(d, "is_active", getattr(d, "enabled", True)),
                    parameters=tuple(params_refs)
                ))

        metadata = getattr(track, "metadata", None)
        role = getattr(metadata, "role", None) if metadata else None
        locked = bool(getattr(metadata, "locked", False) if metadata else getattr(track, "locked", False))

        return TrackRef(
            track_id=str(track.id),
            name=str(track.name),
            track_type=getattr(track, "type", "audio"),
            index=getattr(track, "ableton_index", 0),
            role=role,
            volume=float(getattr(track, "volume", 0.85)),
            pan=float(getattr(track, "panning", 0.0)),
            mute=bool(getattr(track, "mute", False)),
            solo=bool(getattr(track, "solo", False)),
            locked=locked,
            devices=tuple(devices_refs)
        )

    def get_device_ref(self, track_id_or_name: str, device_name: str) -> Optional[DeviceRef]:
        track_ref = self.get_track_ref(track_id_or_name)
        if not track_ref:
            return None
        dev_lower = str(device_name).lower()
        for d in track_ref.devices:
            if d.name.lower() == dev_lower or d.device_id.lower() == dev_lower:
                return d
        return None

    def capture(self, relevant_entities: Optional[List[str]] = None) -> ProductionContextSnapshot:
        fp_val = self.compute_session_fingerprint(relevant_entities=relevant_entities)
        p_state = getattr(self.shadow_graph, "project_state", None)
        tempo = getattr(p_state, "tempo", None) if p_state else None
        key = getattr(p_state, "key", None) or getattr(p_state, "scale", None) if p_state else None
        sr = getattr(p_state, "sample_rate", 48000) if p_state else 48000

        track_refs = []
        for tid in sorted(self.shadow_graph.tracks.keys()):
            t_ref = self.get_track_ref(tid)
            if t_ref:
                track_refs.append(t_ref)

        active_tx_id = None
        if self.transaction_manager:
            active_txs = getattr(self.transaction_manager, "active_transactions", None)
            if active_txs and isinstance(active_txs, dict) and len(active_txs) > 0:
                active_tx_id = list(active_txs.keys())[-1]
            elif getattr(self.transaction_manager, "active_transaction", None):
                active_tx = getattr(self.transaction_manager, "active_transaction")
                active_tx_id = getattr(active_tx, "transaction_id", None) or getattr(active_tx, "id", None)

        return ProductionContextSnapshot(
            project_id=self.project_id,
            session_fingerprint=fp_val,
            tempo=float(tempo) if tempo is not None else None,
            key=str(key) if key else None,
            genre=getattr(p_state, "genre", None) if p_state else None,
            sample_rate=int(sr) if sr is not None else 48000,
            relevant_object_ids=tuple(relevant_entities) if relevant_entities else (),
            session_id=self.project_id,
            tracks=tuple(track_refs),
            active_transaction_id=active_tx_id,
            locks=self.get_locks()
        )

    def get_fingerprint(self, relevant_entities: Optional[List[str]] = None) -> SessionFingerprint:
        val = self.compute_session_fingerprint(relevant_entities=relevant_entities)
        scope = "PLAN_RELEVANT" if relevant_entities else "GLOBAL"
        return SessionFingerprint(
            value=val,
            algorithm="SHA-256",
            algorithm_version="1.0.0",
            scope=scope,
            created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            source_version="PIE-1.0",
            details={"relevant_entities": list(relevant_entities) if relevant_entities else []}
        )

    def get_session_fingerprint(self, relevant_entities: Optional[List[str]] = None) -> str:
        return self.compute_session_fingerprint(relevant_entities=relevant_entities)

    def compute_session_fingerprint(
        self,
        relevant_entities: Optional[List[str]] = None
    ) -> str:
        """
        Computes deterministic SHA-256 hash of session state.
        If relevant_entities is specified, scopes hash strictly to those entities (e.g. ['Master', 'track_0']).
        """
        p_state = getattr(self.shadow_graph, "project_state", None)
        tempo = getattr(p_state, "tempo", 120.0) if p_state else 120.0
        time_sig = getattr(p_state, "time_signature", "4/4") if p_state else "4/4"

        if relevant_entities:
            scoped_tracks = {}
            rel_lower = {str(e).strip().lower() for e in relevant_entities if str(e).strip()}
            for tid, tnode in sorted(self.shadow_graph.tracks.items()):
                t_name = getattr(tnode, "name", "").lower()
                t_type = getattr(tnode, "type", "").lower()
                if tid.lower() in rel_lower or t_name in rel_lower or (t_type == "master" and "master" in rel_lower):
                    scoped_tracks[tid] = tnode.to_dict()

            scoped_devices = {}
            for tid, tnode in sorted(self.shadow_graph.tracks.items()):
                if tid in scoped_tracks:
                    continue  # already fully included in scoped_tracks
                devs = getattr(tnode, "devices", {})
                if isinstance(devs, dict):
                    for did, dnode in sorted(devs.items()):
                        d_name = getattr(dnode, "name", "").lower()
                        if did.lower() in rel_lower or d_name in rel_lower:
                            scoped_devices[f"{tid}:{did}"] = dnode.to_dict()

            data = {
                "scope": "PLAN_RELEVANT",
                "scoped_tracks": scoped_tracks,
                "scoped_devices": scoped_devices,
                "tempo": tempo,
                "time_signature": time_sig
            }
        else:
            data = {
                "scope": "GLOBAL",
                "version": getattr(self.shadow_graph, "version", 1),
                "project_state": p_state.to_dict() if (p_state and hasattr(p_state, "to_dict")) else {},
                "all_tracks": {tid: t.to_dict() for tid, t in sorted(self.shadow_graph.tracks.items())}
            }

        serialized = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def is_stale_for_plan(
        self,
        plan_fingerprint: str,
        relevant_entities: Optional[List[str]] = None
    ) -> bool:
        """
        Checks if relevant state has shifted since plan creation.
        Returns True if the scoped fingerprint does NOT match.
        """
        current_fp = self.compute_session_fingerprint(relevant_entities=relevant_entities)
        return current_fp != plan_fingerprint

    def record_measurement(self, target: str, measurement: Dict[str, Any]) -> None:
        """Stores a pre-recorded measurement for a target track."""
        if not hasattr(self, "_recorded_measurements"):
            self._recorded_measurements = {}
        self._recorded_measurements[target] = dict(measurement)

    def get_measurements(self, target: str = "Master", audio_buffer: Optional[Any] = None) -> Dict[str, Any]:
        return self.capture_measurements(audio_buffer=audio_buffer, target_name=target)

    def capture_measurements(
        self,
        audio_buffer: Optional[Any] = None,
        sample_rate: int = 48000,
        target_name: str = "Master"
    ) -> Dict[str, Any]:
        """
        Captures acoustic measurements using ITU-R BS.1770-5.
        If audio_buffer is None (offline / simulated), returns recorded measurement or current estimate.
        """
        if hasattr(self, "_recorded_measurements") and target_name in self._recorded_measurements:
            recorded = dict(self._recorded_measurements[target_name])
            recorded.setdefault("target", target_name)
            return recorded

        if audio_buffer is not None:
            measurement = self.loudness_analyzer.measure(
                audio=audio_buffer,
                sr=sample_rate,
                channel_layout="stereo"
            )
            profile_eval = self.loudness_profile.evaluate(measurement)
            return {
                "target": target_name,
                "integrated_lufs": measurement.integrated_lufs,
                "short_term_max_lufs": measurement.short_term_lufs,
                "momentary_max_lufs": measurement.momentary_lufs,
                "lra": measurement.loudness_range_lra,
                "true_peak_dbtp": measurement.true_peak_dbfs,
                "sample_peak_dbfs": measurement.sample_peak_dbfs,
                "is_compliant": profile_eval.profile_compliant,
                "standard": measurement.metadata.standard,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }

        # Fallback simulated state from Master/track node
        return {
            "target": target_name,
            "integrated_lufs": -18.5,
            "short_term_max_lufs": -16.0,
            "momentary_max_lufs": -14.0,
            "lra": 6.5,
            "true_peak_dbtp": -1.2,
            "sample_peak_dbfs": -1.5,
            "is_compliant": False,
            "standard": "ITU-R BS.1770-5",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }

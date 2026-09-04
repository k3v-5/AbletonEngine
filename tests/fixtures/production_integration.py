"""
Integration Test Fixtures for AbletonEngine / PIE Production Governance Layer.
Implements Document 14 Section 5, 6, 7 & 8:
- FakeAbletonAdapter (Test Double for Ableton Live with failure injection)
- Canonical initial project state (Melodic Techno, 124 BPM, A minor, 5 tracks)
- Baseline capture and verification utilities
- Self-contained environment factory wiring all governance components.
"""
from dataclasses import dataclass, field
import datetime
import math
import os
import shutil
import tempfile
from typing import Dict, Any, List, Optional, Tuple, Union

from engine.models import TrackNode, DeviceNode, ProjectState
from engine.session.graph import SessionShadowGraph
from engine.adapters.mock_adapter import MockAbletonAdapter
from engine.transactions.manager import TransactionManager
from engine.production.models import (
    ProductionIntent,
    ProductionNode,
    NodeType,
    EdgeType,
    EvidenceType,
    DecisionStatus
)
from engine.production.serializer import ProductionStorage, production_storage
from engine.production.context import ProductionContext
from engine.production.policies import ProductionPolicyEngine
from engine.production.planner import ProductionPlanner
from engine.production.graph import ProductionGraph
from engine.production.memory import DecisionMemory
from engine.production.verification import VerificationMatrix, VerificationResult
from engine.production.rollback import RollbackEngine
from engine.production.executor import ProductionExecutor
from engine.production.boundary import ProductionAPIBoundary
from engine.mix.loudness_standards import (
    LoudnessMeasurement,
    MeasurementMetadata,
    MeasurementStatus
)


# =============================================================================
# 1. FakeAbletonAdapter (Test Double for Ableton Live — Doc 14 Sec 6)
# =============================================================================
class FakeAbletonAdapter(MockAbletonAdapter):
    """
    Test double for Ableton Live (Doc 14 Sec 6).
    Implements standard operations and controllable failure injection:
    - socket disconnect simulation
    - action failure at specific execution index
    - measurement failure simulation
    """

    def __init__(self, tempo: float = 124.0, key: str = "A minor", genre: str = "Melodic Techno"):
        super().__init__()
        self._connected = True
        self.tempo = tempo
        self.key = key
        self.genre = genre
        self.signature_numerator = 4
        self.signature_denominator = 4

        # Canonical initial tracks (Doc 14 Sec 7)
        self.tracks: List[Dict[str, Any]] = [
            {"index": 0, "name": "Kick", "volume": 0.85, "panning": 0.0, "is_audio_track": True, "is_midi_track": False, "devices": []},
            {"index": 1, "name": "Bass", "volume": 0.80, "panning": 0.0, "is_audio_track": True, "is_midi_track": False, "devices": []},
            {"index": 2, "name": "Lead", "volume": 0.75, "panning": 0.0, "is_audio_track": False, "is_midi_track": True, "devices": []},
            {"index": 3, "name": "Pad", "volume": 0.70, "panning": 0.0, "is_audio_track": False, "is_midi_track": True, "devices": []},
        ]
        self.master_track: Dict[str, Any] = {
            "name": "Master",
            "volume": 0.85,
            "panning": 0.0,
            "devices": [
                {
                    "index": 0,
                    "name": "Limiter",
                    "class_name": "Limiter",
                    "parameters": {
                        "gain_reduction": 0.0,
                        "ceiling": -0.3,
                        "lookahead": 3.0
                    }
                },
                {
                    "index": 1,
                    "name": "EQ Eight",
                    "class_name": "Eq8",
                    "parameters": {
                        "band_1_gain": 0.0,
                        "band_2_gain": 0.0
                    }
                }
            ]
        }

        # Failure injection flags
        self.fail_on_socket = False
        self.fail_on_action_index: Optional[int] = None
        self.fail_on_measurement = False
        self.action_call_count = 0
        self.applied_mutations: List[Dict[str, Any]] = []

    def is_connected(self) -> bool:
        return self._connected and not self.fail_on_socket

    def disconnect(self):
        self._connected = False

    def reconnect(self):
        self._connected = True
        self.fail_on_socket = False

    def _check_connection(self):
        if not self.is_connected():
            raise ConnectionError("Ableton socket connection unavailable (simulated failure).")

    def get_session_info(self) -> Dict[str, Any]:
        self._check_connection()
        return {
            "tempo": self.tempo,
            "key": self.key,
            "genre": self.genre,
            "signature_numerator": self.signature_numerator,
            "signature_denominator": self.signature_denominator,
            "track_count": len(self.tracks),
            "master_track": dict(self.master_track)
        }

    def get_track_info(self, track_index: int) -> Dict[str, Any]:
        self._check_connection()
        if track_index == -1 or track_index == len(self.tracks):
            return dict(self.master_track)
        if 0 <= track_index < len(self.tracks):
            return dict(self.tracks[track_index])
        raise IndexError(f"Track index {track_index} out of range")

    def create_track(self, name: str = "New Track", track_type: str = "audio") -> Dict[str, Any]:
        self._check_connection()
        new_track = {
            "index": len(self.tracks),
            "name": name,
            "volume": 0.85,
            "panning": 0.0,
            "is_audio_track": track_type == "audio",
            "is_midi_track": track_type == "midi",
            "devices": []
        }
        self.tracks.append(new_track)
        return dict(new_track)

    def delete_track(self, track_index: int) -> bool:
        self._check_connection()
        if 0 <= track_index < len(self.tracks):
            self.tracks.pop(track_index)
            return True
        return False

    def set_volume(self, track_name_or_idx: Union[str, int], volume: float) -> bool:
        self._check_connection()
        self.action_call_count += 1
        if self.fail_on_action_index is not None and self.action_call_count == self.fail_on_action_index:
            raise RuntimeError(f"Simulated action failure on action step {self.action_call_count}")

        if str(track_name_or_idx).lower() == "master" or track_name_or_idx == -1:
            self.master_track["volume"] = float(volume)
            self.applied_mutations.append({"target": "Master", "type": "SET_VOLUME", "value": volume})
            return True

        for t in self.tracks:
            if t["name"].lower() == str(track_name_or_idx).lower() or t["index"] == track_name_or_idx:
                t["volume"] = float(volume)
                self.applied_mutations.append({"target": t["name"], "type": "SET_VOLUME", "value": volume})
                return True
        return False

    def set_pan(self, track_name_or_idx: Union[str, int], pan: float) -> bool:
        self._check_connection()
        self.action_call_count += 1
        if str(track_name_or_idx).lower() == "master" or track_name_or_idx == -1:
            self.master_track["panning"] = float(pan)
            return True
        for t in self.tracks:
            if t["name"].lower() == str(track_name_or_idx).lower() or t["index"] == track_name_or_idx:
                t["panning"] = float(pan)
                return True
        return False

    def set_track_volume(self, track_index: int, volume: float) -> Dict[str, Any]:
        self.set_volume(track_index, volume)
        return {"track_index": track_index, "volume": volume}

    def set_track_panning(self, track_index: int, panning: float) -> Dict[str, Any]:
        self.set_pan(track_index, panning)
        return {"track_index": track_index, "panning": panning}

    def set_device_parameter(self, track_name: str, device_name: str, param_name: str, value: float) -> bool:
        self._check_connection()
        self.action_call_count += 1
        if self.fail_on_action_index is not None and self.action_call_count == self.fail_on_action_index:
            raise RuntimeError(f"Simulated action failure on action step {self.action_call_count}")

        devices = self.master_track["devices"] if str(track_name).lower() == "master" else []
        for dev in devices:
            if dev["name"].lower() == device_name.lower():
                dev.setdefault("parameters", {})[param_name] = value
                self.applied_mutations.append({"target": track_name, "device": device_name, "param": param_name, "value": value})
                return True
        return False

    def set_limiter_gain_reduction(self, track_name: str, gr_db: float) -> bool:
        return self.set_device_parameter(track_name, "Limiter", "gain_reduction", gr_db)

    def set_eq_gain(self, track_name: str, band: int, gain_db: float) -> bool:
        return self.set_device_parameter(track_name, "EQ Eight", f"band_{band}_gain", gain_db)

    def get_session_state(self) -> Dict[str, Any]:
        return self.get_session_info()

    def get_track_state(self, track_id_or_name: Union[str, int]) -> Optional[Dict[str, Any]]:
        self._check_connection()
        if str(track_id_or_name).lower() == "master" or track_id_or_name == -1:
            return dict(self.master_track)
        for t in self.tracks:
            if t["name"].lower() == str(track_id_or_name).lower() or t["index"] == track_id_or_name:
                return dict(t)
        return None


# =============================================================================
# 2. Canonical Baseline Fixture & Snapshot (Doc 14 Sec 7 & 8)
# =============================================================================
@dataclass(frozen=True)
class BaselineSnapshot:
    """Immutable record of the canonical initial state (Doc 14 Sec 8)."""
    session_fingerprint: str
    track_state: Dict[str, Any]
    device_state: Dict[str, Any]
    mixer_state: Dict[str, Any]
    relevant_measurements: Dict[str, Any]
    production_graph_version: int
    memory_version: int

    @property
    def fingerprint(self) -> str:
        return self.session_fingerprint


def capture_baseline(
    context: ProductionContext,
    graph: Optional[ProductionGraph] = None,
    memory: Optional[DecisionMemory] = None,
    relevant_entities: Optional[List[str]] = None
) -> BaselineSnapshot:
    """
    Captures complete stable baseline state (Doc 14 Sec 8).
    Two consecutive calls without modification are guaranteed to yield identical fingerprints.
    """
    fp = context.compute_session_fingerprint(relevant_entities=relevant_entities)
    tracks_info = {t.name: {"volume": t.volume, "panning": t.panning} for t in context.shadow_graph.tracks.values()}
    mixer_info = dict(tracks_info)
    devices_info = {}
    if hasattr(context.shadow_graph, "devices"):
        devices_info = {d.id: d.to_dict() for d in context.shadow_graph.devices.values()}

    measurements = context.capture_measurements(target_name="Master")
    g_ver = graph.graph_version if graph else 1
    m_ver = getattr(memory, "version", 1) if memory else 1

    return BaselineSnapshot(
        session_fingerprint=fp,
        track_state=tracks_info,
        device_state=devices_info,
        mixer_state=mixer_info,
        relevant_measurements=measurements,
        production_graph_version=g_ver,
        memory_version=m_ver
    )


def create_canonical_measurement(
    integrated_lufs: float = -14.8,
    true_peak_dbtp: float = -1.2,
    sample_peak_dbfs: float = -1.0,
    crest_factor_db: float = 13.6,
    loudness_range_lra: float = 6.2,
    valid: bool = True
) -> LoudnessMeasurement:
    """Creates a strictly valid canonical baseline LoudnessMeasurement (Doc 14 Sec 12)."""
    meta = MeasurementMetadata(
        standard="ITU-R BS.1770-5",
        standard_version="BS.1770-5",
        algorithm_version="1.0",
        sample_rate=48000,
        bit_depth=24,
        channel_layout="stereo",
        duration_seconds=30.0,
        measurement_window="integrated"
    )
    return LoudnessMeasurement(
        integrated_lufs=integrated_lufs,
        short_term_lufs=integrated_lufs + 0.3,
        momentary_lufs=integrated_lufs + 0.8,
        loudness_range_lra=loudness_range_lra,
        true_peak_dbtp=true_peak_dbtp,
        sample_peak_dbfs=sample_peak_dbfs,
        crest_factor_db=crest_factor_db,
        measurement_valid=valid,
        metadata=meta,
        status=MeasurementStatus.VALID if valid else MeasurementStatus.INVALID
    )


# =============================================================================
# 3. Canonical Environment Factory (Doc 14 Sec 5 & 7)
# =============================================================================
def create_integration_env(base_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Constructs an isolated, fully wired integration environment with real components.
    Zero internal mocking of Planner, PolicyEngine, Graph, Memory, or Executor.
    """
    temp_dir = base_dir or tempfile.mkdtemp(prefix="pie_integration_")
    project_id = "integration_project_001"

    # 1. Test Double Adapter
    adapter = FakeAbletonAdapter(tempo=124.0, key="A minor", genre="Melodic Techno")

    # 2. Session Shadow Graph with 5 canonical tracks
    shadow_graph = SessionShadowGraph()
    shadow_graph.project_state = ProjectState(
        tempo=124.0,
        time_signature="4/4"
    )

    t_kick = TrackNode(id="track_kick", name="Kick", ableton_index=0, type="audio", volume=0.85, panning=0.0)
    t_bass = TrackNode(id="track_bass", name="Bass", ableton_index=1, type="audio", volume=0.80, panning=0.0)
    t_lead = TrackNode(id="track_lead", name="Lead", ableton_index=2, type="midi", volume=0.75, panning=0.0)
    t_pad = TrackNode(id="track_pad", name="Pad", ableton_index=3, type="midi", volume=0.70, panning=0.0)
    t_master = TrackNode(id="track_master", name="Master", ableton_index=4, type="master", volume=0.85, panning=0.0)

    for t in [t_kick, t_bass, t_lead, t_pad, t_master]:
        shadow_graph.add_track(t)

    # 3. Transaction Manager
    tm = TransactionManager(graph=shadow_graph, adapter=adapter)

    # 4. Storage
    storage = ProductionStorage(base_path=temp_dir, project_id=project_id)

    # 5. Production Context
    context = ProductionContext(
        shadow_graph=shadow_graph,
        transaction_manager=tm,
        project_id=project_id,
        loudness_profile="STREAMING"
    )

    # Inject baseline measurement
    initial_meas = create_canonical_measurement(
        integrated_lufs=-14.8,
        true_peak_dbtp=-1.2,
        sample_peak_dbfs=-1.0,
        crest_factor_db=13.6,
        loudness_range_lra=6.2
    )
    context.record_measurement("Master", initial_meas.to_dict())

    # 6. Policy Engine
    policy_engine = ProductionPolicyEngine()

    # 7. Production Graph & Decision Memory
    graph = ProductionGraph(project_id=project_id)
    memory = DecisionMemory(project_id=project_id, storage=storage)

    # 8. Planner
    planner = ProductionPlanner(
        policy_engine=policy_engine,
        memory=memory,
        storage=storage
    )

    # 9. Verification Matrix & Rollback Engine
    verification_matrix = VerificationMatrix()
    rollback_engine = RollbackEngine(
        storage=storage,
        policy_engine=policy_engine,
        verification_matrix=verification_matrix
    )

    # 10. Executor
    executor = ProductionExecutor(
        verification_matrix=verification_matrix,
        memory=memory,
        policy_engine=policy_engine,
        storage=storage,
        rollback_engine=rollback_engine
    )

    # 11. API Boundary (MCP Transport Layer)
    boundary = ProductionAPIBoundary(
        project_id=project_id,
        storage=storage,
        graph=graph,
        memory=memory,
        policy_engine=policy_engine,
        context=context,
        planner=planner,
        executor=executor,
        rollback_engine=rollback_engine
    )

    return {
        "project_id": project_id,
        "temp_dir": temp_dir,
        "adapter": adapter,
        "shadow_graph": shadow_graph,
        "transaction_manager": tm,
        "storage": storage,
        "context": context,
        "policy_engine": policy_engine,
        "graph": graph,
        "memory": memory,
        "planner": planner,
        "verification_matrix": verification_matrix,
        "rollback_engine": rollback_engine,
        "executor": executor,
        "boundary": boundary,
        "initial_measurement": initial_meas
    }

# engine/__init__.py
from typing import Optional, Dict, Any, List, Union
from .config import config
from .errors import *
from .models import (
    TrackNode, ClipNode, DeviceNode, SectionNode,
    ProjectState, SyncStatus, RoleEnum, TrackMetadata
)
from .session.graph import SessionShadowGraph
from .session.resolver import SessionResolver
from .session.synchronizer import SessionSynchronizer
from .session.diff import SessionDiff
from .snapshots.manager import snapshot_manager, SnapshotManager
from .transactions.manager import TransactionManager
from .persistence.storage import storage
from .events.event_logger import event_logger
from .adapters.base import BaseAbletonAdapter
from .adapters.ableton_adapter import LiveAbletonAdapter
from .adapters.mock_adapter import MockAbletonAdapter
from .music import (
    music_engine, MusicEngine, MusicalIntent,
    NoteEvent, Chord, Motif, compile_notes_to_ableton_format
)
from .instruments import (
    instrument_engine, InstrumentEngine, InstrumentRole,
    DrumMap, SoundProfile, InstrumentSource
)
from .arrangement import (
    ArrangementGenerator, ArrangementCompiler,
    Song, Section, SectionType,
    EnergyDimensions, EnergyCurveGenerator,
    RoleMatrix, RoleOrchestrator,
    TransitionEngine, DropDifferentiationEngine,
    ArrangementLinter, ArrangementScorer, ArrangementLockManager
)
from .sound import SoundEngine
from .mix import MixEngine
from .mastering import MasteringEngine
from .production import (
    ProductionGraph, DecisionMemory, ProductionPolicyEngine,
    ProductionContext, ProductionPlanner, ProductionExecutor,
    ProductionStorage, production_storage, ProductionPlan
)
from .forensics import (
    AudioForensicsEngine, ForensicsStorage,
    ForensicReport, ForensicEvent, CausalHypothesis
)


class ProductionEngine:
    """Production Intelligence Engine (PIE) - Core Middleware for Ableton Live"""
    def __init__(self, adapter: Optional[BaseAbletonAdapter] = None):
        self.graph = SessionShadowGraph()
        self.adapter = adapter
        self.resolver = SessionResolver(self.graph)
        self.synchronizer = SessionSynchronizer(self.graph, self.adapter) if self.adapter else None
        self.transactions = TransactionManager(self.graph, self.adapter) if self.adapter else None
        self.snapshots = snapshot_manager
        self.music = music_engine
        self.instruments = instrument_engine
        if self.adapter:
            self.instruments.set_adapter(self.adapter)
        self.arrangement = ArrangementGenerator(self)
        self.sound = SoundEngine(self)
        if self.adapter:
            self.sound.set_adapter(self.adapter)
        self.mix = MixEngine(self)
        self.mastering = MasteringEngine(self)

        # Hito 1: Governance, Causal Memory & Production Planning
        self.production_storage = production_storage
        self.production_graph = self.production_storage.load_graph()
        self.production_memory = self.production_storage.load_memory()
        self.production_policy_engine = ProductionPolicyEngine()
        self.production_context = ProductionContext(
            shadow_graph=self.graph,
            transaction_manager=self.transactions
        )
        self.production_planner = ProductionPlanner(
            policy_engine=self.production_policy_engine,
            memory=self.production_memory
        )
        self.production_executor = ProductionExecutor(
            memory=self.production_memory
        )

        # Phase 7: Audio Forensics Engine
        self.forensics_storage = ForensicsStorage()
        self.forensics = AudioForensicsEngine(storage=self.forensics_storage)


    def set_adapter(self, adapter: BaseAbletonAdapter):
        self.adapter = adapter
        self.synchronizer = SessionSynchronizer(self.graph, self.adapter)
        self.transactions = TransactionManager(self.graph, self.adapter)
        self.production_context.transaction_manager = self.transactions
        self.instruments.set_adapter(self.adapter)
        self.arrangement = ArrangementGenerator(self)
        self.sound.set_adapter(self.adapter)
        self.mix = MixEngine(self)
        self.mastering = MasteringEngine(self)


    def initialize(self):
        """Startup bootstrap: load persisted state, connect to Ableton, reconcile"""
        persisted = storage.load_graph()
        if persisted:
            try:
                self.graph = SessionShadowGraph.from_dict(persisted)
                self.resolver = SessionResolver(self.graph)
                if self.adapter:
                    self.synchronizer = SessionSynchronizer(self.graph, self.adapter)
                    self.transactions = TransactionManager(self.graph, self.adapter)
            except Exception:
                pass

        if self.adapter and self.adapter.is_connected():
            try:
                self.synchronizer.reconcile(persisted)
            except Exception:
                self.graph.project_state.sync_status = SyncStatus.DESYNCHRONIZED.value
        else:
            self.graph.project_state.sync_status = SyncStatus.OFFLINE.value

    # Semantic Session API
    def inspect(self, compact: bool = True, detail: str = "summary", object_id: Optional[str] = None) -> Dict[str, Any]:
        """Compact / detailed view of session state for context-efficient LLM interaction"""
        if object_id:
            track = self.graph.get_track(object_id)
            if not track:
                raise ObjectNotFoundError(f"Object '{object_id}' not found", {"object_id": object_id})
            return track.to_dict()

        if compact and detail == "summary":
            return {
                "project": {
                    "tempo": self.graph.project_state.tempo,
                    "time_signature": self.graph.project_state.time_signature,
                    "version": self.graph.version,
                    "sync_status": self.graph.project_state.sync_status,
                    "track_count": len(self.graph.tracks)
                },
                "tracks": [
                    {
                        "id": t.id,
                        "name": t.name,
                        "role": t.metadata.role,
                        "type": t.type,
                        "volume": round(t.volume, 2),
                        "mute": t.mute,
                        "locked": t.metadata.locked
                    }
                    for t in self.graph.tracks.values()
                ],
                "sections": [s.to_dict() for s in self.graph.sections.values()]
            }

        # Full detailed view
        return self.graph.to_dict()

    def refresh(self) -> Dict[str, Any]:
        if not self.synchronizer:
            raise AbletonConnectionError("Adapter is not initialized")
        diff = self.synchronizer.refresh()
        storage.save_graph(self.graph.to_dict())
        return {
            "status": "SYNCHRONIZED",
            "diff": diff.to_dict(),
            "graph_version": self.graph.version
        }

    def diff(self) -> Dict[str, Any]:
        if not self.adapter or not self.adapter.is_connected():
            raise AbletonConnectionError("Ableton is not connected to calculate live diff")
        
        session_info = self.adapter.get_session_info()
        track_count = int(session_info.get("track_count", 0))
        real_tracks = [self.adapter.get_track_info(i) for i in range(track_count)]
        diff_report = SessionDiff.compute_diff(self.graph.tracks, real_tracks)
        return diff_report.to_dict()

    def resolve(
        self,
        query: Optional[str] = None,
        role: Optional[str] = None,
        name: Optional[str] = None,
        object_type: Optional[str] = None,
        tags: Optional[Union[str, List[str]]] = None
    ) -> Dict[str, Any]:
        res = self.resolver.resolve(
            query=query, role=role, name=name,
            object_type=object_type, tags=tags,
            require_single=True
        )
        return res.to_dict()

    def compile_part_to_clip(
        self,
        track_id: str,
        role: str,
        intent: Optional[MusicalIntent] = None,
        chords: Optional[List[Chord]] = None,
        clip_index: int = 0,
        mode: str = "create",
        preview: bool = False,
        tx_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        End-to-end music orchestration:
        1. Resolves track
        2. Generates musical part via MusicEngine
        3. Compiles notes into Ableton batch format
        4. If preview=True, returns generated notes without modifying Ableton
        5. If preview=False, opens transaction, stages add_notes, commits atomically
        """
        track = self.graph.get_track(track_id)
        if not track:
            # Fallback: attempt resolution by role or name
            resolved = self.resolver.resolve(query=track_id, role=role, require_single=False)
            if resolved:
                track = resolved[0]
            else:
                raise ObjectNotFoundError(f"Track '{track_id}' not found", {"track_id": track_id})

        notes, metadata = self.music.generate_part(role=role, intent=intent, chords=chords)
        ableton_notes = compile_notes_to_ableton_format(notes)

        if preview:
            return {
                "track_id": track.id,
                "track_name": track.name,
                "clip_index": clip_index,
                "metadata": metadata,
                "note_count": len(ableton_notes),
                "notes_sample": ableton_notes[:10],
                "dry_run": True
            }

        if not self.transactions:
            raise AbletonConnectionError("Transactions manager not initialized")

        tx_id = self.transactions.begin(name=tx_name or f"generate_{role.lower()}_notes")
        self.transactions.stage_add_notes(
            tx_id=tx_id,
            track_id=track.id,
            clip_index=clip_index,
            notes=ableton_notes,
            mode=mode
        )
        commit_res = self.transactions.commit(tx_id)

        return {
            "transaction": commit_res,
            "track_id": track.id,
            "track_name": track.name,
            "clip_index": clip_index,
            "metadata": metadata,
            "note_count": len(ableton_notes)
        }

# Global production engine singleton
engine = ProductionEngine()

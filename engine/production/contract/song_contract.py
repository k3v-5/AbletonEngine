# engine/production/contract/song_contract.py
"""
Song Contract:
The persistent, cross-phase ledger of obligations for the song currently in production.
Ensures that technical intent, state implementation, and physical DAW evidence remain
synchronized and that no critical production requirement is forgotten or bypassed between phases.
"""
from __future__ import annotations
import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional
import logging

from .song_intent_memory import SongIntentMemory
from .musical_memory import MusicalMemory

logger = logging.getLogger("SongContract")


class ObligationCategory(str, Enum):
    IDENTITY = "IDENTITY"
    STRUCTURE = "STRUCTURE"
    TRACKS = "TRACKS"
    PRODUCTION = "PRODUCTION"
    MIX = "MIX"
    EVOLUTION = "EVOLUTION"


class ObligationStatus(str, Enum):
    PENDING = "PENDING"
    IMPLEMENTED = "IMPLEMENTED"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    OMITTED = "OMITTED"
    WAIVED = "WAIVED"


@dataclass
class TripartiteObligation:
    """
    Fundamental unit of production integrity:
    Strictly decouples what we intend, what the code generated, and what Ableton Live actually has.
    """
    id: str
    title: str
    category: ObligationCategory
    due_phase: str
    is_critical: bool = True
    target_entity: str = ""
    intent: Dict[str, Any] = field(default_factory=dict)
    implementation: Dict[str, Any] = field(default_factory=dict)
    evidence: Dict[str, Any] = field(default_factory=dict)
    status: ObligationStatus = ObligationStatus.PENDING
    failure_reason: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    last_verified_at: Optional[str] = None

    def mark_implemented(self, data: Optional[Dict[str, Any]] = None):
        """Records generated data in state memory."""
        if data:
            self.implementation.update(data)
        if self.status != ObligationStatus.VERIFIED:
            self.status = ObligationStatus.IMPLEMENTED

    def mark_verified(self, evidence_data: Dict[str, Any]):
        """Records physical evidence queried directly from Ableton Live."""
        self.evidence = evidence_data
        self.status = ObligationStatus.VERIFIED
        self.failure_reason = None
        self.last_verified_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

    def mark_failed(self, reason: str, evidence_data: Optional[Dict[str, Any]] = None):
        """Records physical verification failure or governance blockage."""
        self.status = ObligationStatus.FAILED
        self.failure_reason = reason
        if evidence_data:
            self.evidence = evidence_data
        self.last_verified_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

    def mark_omitted(self, reason: str = "Deadline reached without implementation"):
        """Marks that the obligation was expected by phase closure but not fulfilled."""
        self.status = ObligationStatus.OMITTED
        self.failure_reason = reason

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category.value if isinstance(self.category, ObligationCategory) else str(self.category),
            "due_phase": self.due_phase,
            "is_critical": self.is_critical,
            "target_entity": self.target_entity,
            "intent": dict(self.intent),
            "implementation": dict(self.implementation),
            "evidence": dict(self.evidence),
            "status": self.status.value if isinstance(self.status, ObligationStatus) else str(self.status),
            "failure_reason": self.failure_reason,
            "created_at": self.created_at,
            "last_verified_at": self.last_verified_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TripartiteObligation:
        cat_str = data.get("category", "PRODUCTION")
        try:
            category = ObligationCategory(cat_str)
        except ValueError:
            category = ObligationCategory.PRODUCTION

        stat_str = data.get("status", "PENDING")
        try:
            status = ObligationStatus(stat_str)
        except ValueError:
            status = ObligationStatus.PENDING

        return cls(
            id=data["id"],
            title=data.get("title", data["id"]),
            category=category,
            due_phase=data.get("due_phase", "PHASE_6_COMPOSITION"),
            is_critical=bool(data.get("is_critical", True)),
            target_entity=data.get("target_entity", ""),
            intent=data.get("intent", {}),
            implementation=data.get("implementation", {}),
            evidence=data.get("evidence", {}),
            status=status,
            failure_reason=data.get("failure_reason"),
            created_at=data.get("created_at", datetime.datetime.now(datetime.timezone.utc).isoformat()),
            last_verified_at=data.get("last_verified_at"),
        )


@dataclass
class SongContract:
    """
    Contract governing the specific song across all phases.
    Survives all phase transitions and prevents forgotten obligations.
    """
    song_id: str = field(default_factory=lambda: f"song_{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S')}")
    title: str = "Untitled Project"
    intent_memory: SongIntentMemory = field(default_factory=SongIntentMemory)
    musical_memory: MusicalMemory = field(default_factory=lambda: MusicalMemory(song_id="default_song"))
    obligations: Dict[str, TripartiteObligation] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    PHASE_ORDER = [
        "PHASE_1_TRACKS",
        "PHASE_2_SECTIONS",
        "PHASE_3_INSTRUMENTS",
        "PHASE_4_PARAM_SCULPTING",
        "PHASE_5_INSERT_EFFECTS",
        "PHASE_6_COMPOSITION",
        "PHASE_7_AUTOMATION",
        "PHASE_8_VOCAL_DUCKING",
        "PHASE_9_MIX_MASTER",
        "PHASE_10_COMPLETED"
    ]

    def register_obligation(
        self,
        id: str,
        title: str,
        category: ObligationCategory,
        due_phase: str,
        is_critical: bool = True,
        target_entity: str = "",
        intent: Optional[Dict[str, Any]] = None
    ) -> TripartiteObligation:
        """Registers a new requirement in the contract ledger."""
        if id in self.obligations:
            ob = self.obligations[id]
            ob.title = title
            ob.category = category
            ob.due_phase = due_phase
            ob.is_critical = is_critical
            ob.target_entity = target_entity
            if intent:
                ob.intent.update(intent)
            return ob

        ob = TripartiteObligation(
            id=id,
            title=title,
            category=category,
            due_phase=due_phase,
            is_critical=is_critical,
            target_entity=target_entity,
            intent=intent or {}
        )
        self.obligations[id] = ob
        return ob

    def record_intent(self, obligation_id: str, intent_data: Dict[str, Any]) -> None:
        """Records or updates artistic intent on an obligation."""
        if obligation_id in self.obligations:
            self.obligations[obligation_id].intent.update(intent_data)

    def record_implementation(self, obligation_id: str, implementation_data: Dict[str, Any]) -> None:
        """Records that data was generated in state memory."""
        if obligation_id in self.obligations:
            self.obligations[obligation_id].mark_implemented(implementation_data)

    def record_evidence(
        self,
        obligation_id: str,
        evidence_data: Dict[str, Any],
        verified: bool = True,
        failure_reason: Optional[str] = None
    ) -> None:
        """Records physical proof queried from Ableton Live."""
        if obligation_id in self.obligations:
            ob = self.obligations[obligation_id]
            if verified:
                ob.mark_verified(evidence_data)
            else:
                ob.mark_failed(failure_reason or "Evidence verification failed in Ableton Live", evidence_data)

    def get_obligations_due_by_phase(self, phase: str) -> List[TripartiteObligation]:
        """Returns all obligations that must be fulfilled on or before the given phase."""
        if phase not in self.PHASE_ORDER:
            return list(self.obligations.values())
        target_idx = self.PHASE_ORDER.index(phase)
        due = []
        for ob in self.obligations.values():
            ob_due_idx = self.PHASE_ORDER.index(ob.due_phase) if ob.due_phase in self.PHASE_ORDER else 99
            if ob_due_idx <= target_idx:
                due.append(ob)
        return due

    def get_pending_critical(self, phase: str) -> List[TripartiteObligation]:
        """Returns critical obligations due by this phase that are not verified."""
        due = self.get_obligations_due_by_phase(phase)
        return [
            ob for ob in due
            if ob.is_critical and ob.status not in (ObligationStatus.VERIFIED, ObligationStatus.WAIVED)
        ]

    def get_summary(self) -> Dict[str, int]:
        """Returns breakdown of obligation counts."""
        summary = {
            "total": len(self.obligations),
            "verified": sum(1 for ob in self.obligations.values() if ob.status == ObligationStatus.VERIFIED),
            "implemented": sum(1 for ob in self.obligations.values() if ob.status == ObligationStatus.IMPLEMENTED),
            "pending": sum(1 for ob in self.obligations.values() if ob.status == ObligationStatus.PENDING),
            "failed": sum(1 for ob in self.obligations.values() if ob.status == ObligationStatus.FAILED),
            "omitted": sum(1 for ob in self.obligations.values() if ob.status == ObligationStatus.OMITTED),
            "waived": sum(1 for ob in self.obligations.values() if ob.status == ObligationStatus.WAIVED),
        }
        return summary

    def to_dict(self) -> Dict[str, Any]:
        return {
            "song_id": self.song_id,
            "title": self.title,
            "intent_memory": self.intent_memory.to_dict(),
            "musical_memory": self.musical_memory.to_dict(),
            "obligations": {k: ob.to_dict() for k, ob in self.obligations.items()},
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SongContract:
        if not data or not isinstance(data, dict):
            return cls()
        intent = SongIntentMemory.from_dict(data.get("intent_memory", {}))
        mus_mem_data = data.get("musical_memory")
        mus_mem = MusicalMemory.from_dict(mus_mem_data) if mus_mem_data else MusicalMemory(song_id=data.get("song_id", "untitled_song"))
        obs = {}
        for k, v in data.get("obligations", {}).items():
            obs[k] = TripartiteObligation.from_dict(v)
        return cls(
            song_id=data.get("song_id", "untitled_song"),
            title=data.get("title", "Untitled Project"),
            intent_memory=intent,
            musical_memory=mus_mem,
            obligations=obs,
            metadata=data.get("metadata", {})
        )

    @classmethod
    def scaffold_from_session_state(cls, session_data: Dict[str, Any]) -> SongContract:
        """
        Creates or reconstructs a full SongContract dynamically from existing session state.
        Ensures 100% backward compatibility with active projects.
        """
        genre = session_data.get("genre", "rap/neo-soul")
        key = session_data.get("key", "F#")
        scale = session_data.get("scale", "minor")
        bpm = float(session_data.get("bpm", 90.0))
        s_id = f"song_{session_data.get('bpm', 90)}_{key}"

        intent_mem = SongIntentMemory.create_for_style(
            genre=genre,
            artist="Tyler, The Creator" if "tyler" in str(session_data.get("history", "")).lower() else "Contemporary Artist",
            key=key,
            scale=scale,
            bpm=bpm
        )
        contract = cls(
            song_id=s_id,
            title=f"{genre.upper()} in {key} {scale}",
            intent_memory=intent_mem,
            musical_memory=MusicalMemory.scaffold_for_neo_soul(song_id=s_id)
        )

        # 1. Identity Obligations
        contract.register_obligation(
            id="IDENTITY_TEMPO_AND_KEY",
            title=f"Tempo & Key Alignment ({bpm} BPM, {key} {scale})",
            category=ObligationCategory.IDENTITY,
            due_phase="PHASE_1_TRACKS",
            is_critical=True,
            intent={"bpm": bpm, "key": key, "scale": scale}
        )

        # 2. Track & Instrument Obligations
        tracks = session_data.get("tracks", [])
        for trk in tracks:
            t_idx = trk.get("index", 0)
            t_name = trk.get("name", f"Track {t_idx}")
            t_role = trk.get("role", "OTHER")
            is_audio = bool(trk.get("is_audio") or t_role == "VOCALS")

            # Track existence obligation
            contract.register_obligation(
                id=f"TRACK_EXISTS_{t_idx}_{t_role}",
                title=f"Track Allocation: [{t_role}] {t_name}",
                category=ObligationCategory.TRACKS,
                due_phase="PHASE_1_TRACKS",
                is_critical=True,
                target_entity=f"Track {t_idx} ({t_name})",
                intent={"role": t_role, "name": t_name}
            )

            # Instrument verification obligation
            if not is_audio:
                contract.register_obligation(
                    id=f"INST_LOADED_{t_idx}_{t_role}",
                    title=f"Verified Instrument: {trk.get('instrument', 'Default')}",
                    category=ObligationCategory.PRODUCTION,
                    due_phase="PHASE_3_INSTRUMENTS",
                    is_critical=True,
                    target_entity=f"Track {t_idx} ({t_name})",
                    intent={"instrument": trk.get("instrument"), "role": t_role}
                )

                # Parameter sculpting obligation (Delta >= 1 rule)
                contract.register_obligation(
                    id=f"PARAM_SCULPT_{t_idx}_{t_role}",
                    title=f"Synthesis Character Sculpting (Delta >= 1)",
                    category=ObligationCategory.PRODUCTION,
                    due_phase="PHASE_4_PARAM_SCULPTING",
                    is_critical=True,
                    target_entity=f"Track {t_idx} ({t_name})",
                    intent={"role": t_role}
                )

            # Composition / Clips in arrangement obligation
            contract.register_obligation(
                id=f"COMPOSITION_{t_idx}_{t_role}",
                title=f"Arrangement Composition ({t_name})",
                category=ObligationCategory.PRODUCTION,
                due_phase="PHASE_6_COMPOSITION",
                is_critical=True,
                target_entity=f"Track {t_idx} ({t_name})",
                intent={"role": t_role, "is_audio": is_audio}
            )

        # 3. Structure & Cue Points Obligations
        sections = session_data.get("sections", [])
        for s_idx, sec in enumerate(sections):
            sec_name = sec.get("name", f"Section {s_idx + 1}")
            contract.register_obligation(
                id=f"SECTION_CUE_{s_idx}_{sec_name.replace(' ', '_').upper()}",
                title=f"Section Locator: {sec_name} (Bar {sec.get('start_bar', 0)})",
                category=ObligationCategory.STRUCTURE,
                due_phase="PHASE_2_SECTIONS",
                is_critical=True,
                target_entity=sec_name,
                intent={"bars": sec.get("bars", 8), "start_bar": sec.get("start_bar", 0)}
            )

        # 4. Master Bus & Loudness Obligations
        contract.register_obligation(
            id="MASTERING_CHAIN_SERIAL",
            title="5-Stage Serial Mastering Chain on Main Bus",
            category=ObligationCategory.MIX,
            due_phase="PHASE_9_MIX_MASTER",
            is_critical=True,
            target_entity="Main / Master Track",
            intent={"stages": ["EQ Eight", "Glue Compressor", "Saturator", "Utility", "Limiter"]}
        )
        contract.register_obligation(
            id="ACOUSTIC_LOUDNESS_BS1770",
            title="BS.1770-5 Integrated Loudness (-14 LUFS +-1.0 dB)",
            category=ObligationCategory.MIX,
            due_phase="PHASE_9_MIX_MASTER",
            is_critical=True,
            target_entity="Audio Output",
            intent={"target_lufs": -14.0, "tolerance_db": 1.0, "max_true_peak_dbtp": -1.0}
        )

        return contract

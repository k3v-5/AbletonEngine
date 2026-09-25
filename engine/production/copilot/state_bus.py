"""
InterPhaseStateBus: Unified Persistent State Bus for Copilot Guided Session.
Maintains scale, tempo, acoustic roles, timbral decisions, frequency slotting,
and structural contracts immutable and consistent across all production phases.
"""

from dataclasses import dataclass, field
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field as PydanticField

from engine.governance.contract import StructuralDecisionContract
from engine.governance.provenance import canonical_json, compute_sha256

logger = logging.getLogger("InterPhaseStateBus")


class MusicalContextAnchor(BaseModel):
    bpm: float
    root_note: str
    scale: str
    genre: str
    sub_genre: Optional[str] = None
    time_signature: str = "4/4"


class TrackRoleAnchor(BaseModel):
    track_index: int
    track_name: str
    role: str
    frequency_slot: Optional[str] = None
    timbre_archetype: Optional[str] = None
    is_frozen: bool = False

    @property
    def track_id(self) -> int:
        return self.track_index


class InterPhaseStateBus:
    """
    Persistent state bus guaranteeing cross-phase consistency.
    Eliminates AI hallucinations, forgotten scales, altered BPMs, and orphaned tracks.
    """

    def __init__(self, session_data: Optional[Dict[str, Any]] = None):
        self._data: Dict[str, Any] = session_data if session_data is not None else {}
        self._init_bus_structure()

    def _init_bus_structure(self) -> None:
        if "state_bus" not in self._data:
            self._data["state_bus"] = {
                "musical_context": None,
                "track_roles": {},
                "frequency_slots": {},
                "timbral_decisions": {},
                "structural_contracts": {},
                "phase_history": [],
                "bus_version": "1.0.0",
            }

    @property
    def bus_data(self) -> Dict[str, Any]:
        return self._data["state_bus"]

    # --------------------------------------------------------------------------
    # 1. Musical Context Anchors (BPM, Root Note, Scale, Genre)
    # --------------------------------------------------------------------------
    def set_musical_context(
        self,
        bpm: float,
        root_note: str,
        scale: str,
        genre: str,
        sub_genre: Optional[str] = None,
        time_signature: str = "4/4",
    ) -> MusicalContextAnchor:
        """Sets or locks the global musical context anchor."""
        anchor = MusicalContextAnchor(
            bpm=float(bpm),
            root_note=str(root_note).strip().upper(),
            scale=str(scale).strip().lower(),
            genre=str(genre).strip().upper(),
            sub_genre=str(sub_genre).strip().upper() if sub_genre else None,
            time_signature=str(time_signature).strip(),
        )
        self.bus_data["musical_context"] = anchor.model_dump()
        logger.info(
            f"[StateBus] Musical context set: {anchor.root_note} {anchor.scale}, "
            f"{anchor.bpm} BPM, Genre={anchor.genre}"
        )
        return anchor

    def get_musical_context(self) -> Optional[MusicalContextAnchor]:
        """Returns the active musical context anchor if registered."""
        raw = self.bus_data.get("musical_context")
        return MusicalContextAnchor.model_validate(raw) if raw else None

    # --------------------------------------------------------------------------
    # 2. Track Acoustic Roles & Spectrum Slotting
    # --------------------------------------------------------------------------
    def register_track_role(
        self,
        track_index: int,
        track_name: str,
        role: str,
        frequency_slot: Optional[str] = None,
        timbre_archetype: Optional[str] = None,
    ) -> TrackRoleAnchor:
        """Registers and locks an acoustic role and frequency slot for a track."""
        clean_role = str(role).strip().upper()
        # Default slot inference if omitted
        if not frequency_slot:
            if clean_role in ("SUB", "808_BASS", "SUB_BASS"):
                frequency_slot = "SUB_20_120HZ_MONO"
            elif clean_role in ("KICK", "DRUMS"):
                frequency_slot = "LOW_TRANSIENT_50_100HZ"
            elif clean_role in ("VOCALS", "LEAD_VOCAL"):
                frequency_slot = "MID_PRESENCE_1K_4KHZ"
            elif clean_role in ("KEYS", "PIANO", "PAD"):
                frequency_slot = "BODY_250_2500HZ_STEREO"
            else:
                frequency_slot = "WIDE_SPECTRUM"

        anchor = TrackRoleAnchor(
            track_index=track_index,
            track_name=track_name,
            role=clean_role,
            frequency_slot=frequency_slot,
            timbre_archetype=timbre_archetype,
        )
        self.bus_data["track_roles"][str(track_index)] = anchor.model_dump()
        self.bus_data["frequency_slots"][str(track_index)] = frequency_slot
        return anchor

    def get_track_role(self, track_index_or_name: Any) -> Optional[TrackRoleAnchor]:
        """Lookups track role anchor by track index or track name."""
        roles = self.bus_data.get("track_roles", {})
        # Check by index string
        if str(track_index_or_name) in roles:
            return TrackRoleAnchor.model_validate(roles[str(track_index_or_name)])
        # Check by name
        target_name = str(track_index_or_name).strip().lower()
        for raw in roles.values():
            if str(raw.get("track_name", "")).strip().lower() == target_name:
                return TrackRoleAnchor.model_validate(raw)
        return None

    def get_all_track_roles(self) -> List[TrackRoleAnchor]:
        roles = self.bus_data.get("track_roles", {})
        return [TrackRoleAnchor.model_validate(r) for r in roles.values()]

    # --------------------------------------------------------------------------
    # 3. Timbral Decisions
    # --------------------------------------------------------------------------
    def register_timbre_decision(
        self,
        track_index: int,
        timbre_archetype: Optional[str] = None,
        engine_quadrants: Optional[Dict[str, Any]] = None,
        archetype: Optional[str] = None,
        quadrants: Optional[Dict[str, Any]] = None,
        timbre_dna: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Records synthesis and timbral decisions made in Phase 4."""
        final_archetype = timbre_archetype or archetype or "DEFAULT"
        final_quadrants = engine_quadrants or quadrants or {}
        self.bus_data["timbral_decisions"][str(track_index)] = {
            "archetype": final_archetype,
            "quadrants": final_quadrants,
            "timbre_dna": timbre_dna or {},
        }
        if str(track_index) in self.bus_data["track_roles"]:
            self.bus_data["track_roles"][str(track_index)]["timbre_archetype"] = final_archetype

    def get_timbre_decision(self, track_index: int) -> Optional[Dict[str, Any]]:
        return self.bus_data.get("timbral_decisions", {}).get(str(track_index))

    def get_timbre_decisions(self) -> Dict[str, Any]:
        """Returns all timbral decisions registered in the state bus."""
        return self.bus_data.get("timbral_decisions", {})

    # --------------------------------------------------------------------------
    # 4. Structural Contracts (Tacet, Overrides, Silences)
    # --------------------------------------------------------------------------
    def register_contract(self, contract: StructuralDecisionContract) -> None:
        """Registers an authorized structural decision contract."""
        self.bus_data["structural_contracts"][contract.contract_id] = contract.model_dump()
        # Also sync to session's root structural_contracts for legacy compatibility
        if "structural_contracts" not in self._data:
            self._data["structural_contracts"] = {}
        self._data["structural_contracts"][contract.contract_id] = contract.model_dump()

    def get_contracts(self, target: Optional[str] = None) -> List[StructuralDecisionContract]:
        raw_contracts = self.bus_data.get("structural_contracts", {})
        results = []
        for raw in raw_contracts.values():
            contract = StructuralDecisionContract.model_validate(raw)
            if target is None:
                results.append(contract)
            elif (
                (contract.target_track and contract.target_track.lower() == target.lower())
                or (contract.target_device and contract.target_device.lower() == target.lower())
            ):
                results.append(contract)
        return results

    def get_active_contracts(self) -> List[StructuralDecisionContract]:
        """Convenience accessor for all active structural contracts in the state bus."""
        return self.get_contracts()

    # --------------------------------------------------------------------------
    # 5. Phase Transition Integrity Audit
    # --------------------------------------------------------------------------
    def validate_phase_transition(
        self,
        from_phase: str,
        to_phase: str,
        session_data: Dict[str, Any],
    ) -> Tuple[bool, List[str]]:
        """
        Audits whether a proposed phase transition violates any registered bus anchors.
        Returns (is_valid, list_of_violations).
        """
        violations: List[str] = []

        context = self.get_musical_context()
        if context:
            # 1. Audit BPM anchor preservation
            proposed_bpm = session_data.get("bpm")
            if proposed_bpm is not None and abs(float(proposed_bpm) - context.bpm) > 0.01:
                violations.append(
                    f"StateBus Violation: BPM anchor drift detected! "
                    f"Bus locked to {context.bpm} BPM, proposed {proposed_bpm} BPM."
                )

            # 2. Audit Scale and Key anchor preservation
            proposed_key = session_data.get("musical_scale") or session_data.get("key")
            if proposed_key is not None:
                clean_pk = str(proposed_key).strip().lower()
                expected_k = f"{context.root_note} {context.scale}".lower()
                if clean_pk != expected_k and context.root_note.lower() not in clean_pk:
                    violations.append(
                        f"StateBus Violation: Musical scale drift! "
                        f"Bus locked to '{context.root_note} {context.scale}', proposed '{proposed_key}'."
                    )

        # 3. Audit track role preservation
        existing_roles = {r.track_index: r for r in self.get_all_track_roles()}
        if "tracks" in session_data and isinstance(session_data["tracks"], list):
            for trk in session_data["tracks"]:
                t_idx = trk.get("index")
                if t_idx in existing_roles:
                    registered_role = existing_roles[t_idx].role
                    proposed_role = str(trk.get("role", "")).upper()
                    if proposed_role and proposed_role != registered_role:
                        violations.append(
                            f"StateBus Violation: Track {t_idx} ('{trk.get('name')}') role mutated from "
                            f"{registered_role} to {proposed_role} without explicit override."
                        )

        # Record phase transition in history
        if not violations:
            self.bus_data["phase_history"].append({
                "from_phase": from_phase,
                "to_phase": to_phase,
            })

        return len(violations) == 0, violations

    # --------------------------------------------------------------------------
    # 6. Physical Live Transport & Song Scale Synchronization
    # --------------------------------------------------------------------------
    def sync_with_live(self, conn: Any) -> Dict[str, Any]:
        """
        Reads physical tempo and song scale from Live LOM and compares against bus anchors.
        """
        report = {"synced": True, "discrepancies": []}
        if conn is None or not hasattr(conn, "send_command"):
            return report

        context = self.get_musical_context()
        if not context:
            return report

        try:
            # Query song tempo
            tempo_info = conn.send_command("get_tempo", {})
            live_bpm = None
            if isinstance(tempo_info, dict):
                live_bpm = tempo_info.get("tempo", tempo_info.get("result", {}).get("tempo"))
            elif isinstance(tempo_info, (int, float)):
                live_bpm = float(tempo_info)

            if live_bpm is not None and abs(float(live_bpm) - context.bpm) > 0.05:
                report["synced"] = False
                report["discrepancies"].append(
                    f"Live physical tempo ({live_bpm} BPM) differs from StateBus anchor ({context.bpm} BPM)."
                )
                # Auto-align Live tempo to StateBus anchor
                conn.send_command("set_tempo", {"tempo": float(context.bpm)})
                report["remedy"] = f"Aligned Live tempo to {context.bpm} BPM."

        except Exception as ex:
            logger.debug(f"[StateBus] LOM sync notice: {ex}")

        return report

    # --------------------------------------------------------------------------
    # 7. Prompt Context Summary Generator
    # --------------------------------------------------------------------------
    def export_summary_for_prompt(self) -> str:
        """
        Generates a concise markdown summary of all inter-phase anchors
        for prompt injection so the AI never forgets the core musical foundation.
        """
        lines = ["### 🧭 ANCLAS DE PRODUCCIÓN (INTER-PHASE STATE BUS)"]
        ctx = self.get_musical_context()
        if ctx:
            lines.append(f"- **Tonalidad y Escala**: `{ctx.root_note} {ctx.scale.capitalize()}`")
            lines.append(f"- **Tempo & Compás**: `{ctx.bpm} BPM` ({ctx.time_signature})")
            lines.append(f"- **Género**: `{ctx.genre}`" + (f" / `{ctx.sub_genre}`" if ctx.sub_genre else ""))

        roles = self.get_all_track_roles()
        if roles:
            lines.append("- **Roles Acústicos & Slots de Frecuencia**:")
            for r in roles:
                slot_info = f" -> `{r.frequency_slot}`" if r.frequency_slot else ""
                lines.append(f"  • Pista {r.track_index} (`{r.track_name}`): **{r.role}**{slot_info}")

        contracts = self.get_contracts()
        if contracts:
            lines.append("- **Contratos Estructurales Activos**:")
            for c in contracts:
                lines.append(f"  • `{c.contract_id}`: **{c.decision.value}** ({c.target_track or 'global'})")

        return "\n".join(lines)

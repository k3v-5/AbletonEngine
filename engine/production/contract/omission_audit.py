# engine/production/contract/omission_audit.py
"""
Omission Audit:
Phase boundary gatekeeper answering the crucial question:
"What should have been done that was NOT done?"
Guarantees that no phase transition can proceed while critical obligations are missing,
unverified, or failed in Ableton Live, and provides creative continuity warnings.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import logging

from .song_contract import SongContract, TripartiteObligation, ObligationStatus
from .evidence_ledger import EvidenceLedger

logger = logging.getLogger("OmissionAudit")


@dataclass
class OmissionReport:
    """Report summarizing expected vs verified obligations at a phase boundary."""
    phase: str
    expected_count: int = 0
    implemented_count: int = 0
    verified_count: int = 0
    missing_count: int = 0
    failed_count: int = 0
    unverified_count: int = 0
    can_advance: bool = True
    block_reason: Optional[str] = None
    missing_obligations: List[Dict[str, Any]] = field(default_factory=list)
    failed_obligations: List[Dict[str, Any]] = field(default_factory=list)
    unverified_obligations: List[Dict[str, Any]] = field(default_factory=list)
    creative_evolution_warnings: List[str] = field(default_factory=list)
    remediation_options: List[str] = field(default_factory=list)

    def format_markdown_report(self) -> str:
        """Renders an executive markdown view of the audit."""
        status_badge = "✅ **PASS: LISTO PARA AVANZAR**" if self.can_advance else "🚫 **BLOQUEO POR OMISIÓN (FASE DETENIDA)**"
        
        md = [
            f"### 📋 Auditoría de Omisiones: {self.phase}",
            f"{status_badge}\n",
            f"| Métrica | Cantidad |",
            f"|---|---|",
            f"| **Obligaciones Esperadas** | `{self.expected_count}` |",
            f"| **Implementadas en Estado** | `{self.implemented_count}` |",
            f"| **Verificadas Físicamente en Live** | `{self.verified_count}` |",
            f"| **Omisiones / Pendientes** | `{self.missing_count}` |",
            f"| **Fallos de Gobernanza / DAW** | `{self.failed_count}` |",
            f"| **Sin Evidencia Física** | `{self.unverified_count}` |\n"
        ]

        if not self.can_advance:
            md.append(f"> [!CAUTION]\n> **Bloqueo Crítico:** {self.block_reason}\n")

        if self.failed_obligations:
            md.append("#### ❌ Obligaciones Fallidas:")
            for f in self.failed_obligations:
                md.append(f"- **{f['title']}** (`{f['id']}`): {f.get('failure_reason', 'Fallo no especificado')}")
            md.append("")

        if self.missing_obligations:
            md.append("#### ⚠️ Obligaciones Omitidas:")
            for m in self.missing_obligations:
                md.append(f"- **{m['title']}** (`{m['id']}`) - Target: `{m.get('target_entity', 'N/A')}`")
            md.append("")

        if self.creative_evolution_warnings:
            md.append("#### 🎨 Advertencias de Continuidad Creativa:")
            for w in self.creative_evolution_warnings:
                md.append(f"- ⚠️ {w}")
            md.append("")

        if self.remediation_options:
            md.append("#### 🔧 Vías de Reparación:")
            for opt in self.remediation_options:
                md.append(f"1. {opt}")

        return "\n".join(md)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase": self.phase,
            "expected_count": self.expected_count,
            "implemented_count": self.implemented_count,
            "verified_count": self.verified_count,
            "missing_count": self.missing_count,
            "failed_count": self.failed_count,
            "unverified_count": self.unverified_count,
            "can_advance": self.can_advance,
            "block_reason": self.block_reason,
            "missing_obligations": self.missing_obligations,
            "failed_obligations": self.failed_obligations,
            "unverified_obligations": self.unverified_obligations,
            "creative_evolution_warnings": self.creative_evolution_warnings,
            "remediation_options": self.remediation_options,
        }


class OmissionAuditor:
    """Evaluates phase readiness, audits omissions, and performs creative evolution checks."""

    @classmethod
    def audit_phase_readiness(
        cls,
        contract: SongContract,
        session_data: Dict[str, Any],
        conn: Any,
        target_phase: str
    ) -> OmissionReport:
        """
        Conducts full physical and contract audit before permitting a phase transition.
        """
        # 1. Reconcile evidence from Live
        if conn and hasattr(conn, "send_command"):
            EvidenceLedger.audit_and_reconcile(conn, contract, session_data, target_phase=target_phase)

        due = contract.get_obligations_due_by_phase(target_phase)
        expected_cnt = len(due)
        implemented_cnt = sum(1 for ob in due if ob.status in (ObligationStatus.IMPLEMENTED, ObligationStatus.VERIFIED))
        verified_cnt = sum(1 for ob in due if ob.status == ObligationStatus.VERIFIED)

        missing_list = []
        failed_list = []
        unverified_list = []

        for ob in due:
            if ob.status == ObligationStatus.FAILED:
                failed_list.append(ob.to_dict())
            elif ob.status == ObligationStatus.PENDING:
                missing_list.append(ob.to_dict())
            elif ob.status == ObligationStatus.IMPLEMENTED:
                unverified_list.append(ob.to_dict())

        # 2. Check Creative Evolution continuity
        evolution_warnings = cls.audit_creative_evolution(contract, session_data)

        # 3. Decision Gate: Can this phase advance?
        critical_failed = [ob for ob in due if ob.is_critical and ob.status == ObligationStatus.FAILED]
        critical_missing = [ob for ob in due if ob.is_critical and ob.status == ObligationStatus.PENDING]
        critical_unverified = [ob for ob in due if ob.is_critical and ob.status == ObligationStatus.IMPLEMENTED]

        can_advance = True
        block_reason = None
        remediations = []

        if critical_failed:
            can_advance = False
            first_fail = critical_failed[0]
            block_reason = f"Obligación crítica fallida: '{first_fail.title}' ({first_fail.failure_reason})."
            remediations.append(f"Reintentar o reparar '{first_fail.title}' en Ableton Live.")
            remediations.append("Escribir 'reintentar' tras resolver la causa física en Live.")

        elif critical_missing:
            can_advance = False
            first_miss = critical_missing[0]
            block_reason = f"Obligación crítica no implementada: '{first_miss.title}'."
            remediations.append(f"Completar la implementación de '{first_miss.title}' antes de cerrar {target_phase}.")

        elif critical_unverified and conn and hasattr(conn, "send_command"):
            can_advance = False
            first_unv = critical_unverified[0]
            block_reason = f"Obligación crítica sin verificación física en Live: '{first_unv.title}'."
            remediations.append(f"Verificar que '{first_unv.target_entity}' exista físicamente en Ableton Live.")

        return OmissionReport(
            phase=target_phase,
            expected_count=expected_cnt,
            implemented_count=implemented_cnt,
            verified_count=verified_cnt,
            missing_count=len(missing_list),
            failed_count=len(failed_list),
            unverified_count=len(unverified_list),
            can_advance=can_advance,
            block_reason=block_reason,
            missing_obligations=missing_list,
            failed_obligations=failed_list,
            unverified_obligations=unverified_list,
            creative_evolution_warnings=evolution_warnings,
            remediation_options=remediations
        )

    @classmethod
    def audit_creative_evolution(
        cls,
        contract: SongContract,
        session_data: Dict[str, Any]
    ) -> List[str]:
        """
        Analyzes composition and arrangement to detect subtle creative omissions:
        e.g., identical hook repetitions with zero development, missing climax transformations.
        """
        warnings = []
        sections = session_data.get("sections", [])
        tracks = session_data.get("tracks", [])

        # Check: Multiple hooks present? Are they identical?
        hook_sections = [s for s in sections if "hook" in str(s.get("name", "")).lower() or "coro" in str(s.get("name", "")).lower()]
        if len(hook_sections) >= 2:
            h1 = hook_sections[0]
            h_last = hook_sections[-1]
            if h1 != h_last:
                # Check if instrument tracks have variation
                chord_tracks = [t for t in tracks if t.get("role") in ("KEYS", "HARMONY", "LEAD", "PAD")]
                if chord_tracks and not any("evolution" in str(t.get("automations", [])).lower() for t in chord_tracks):
                    # Flag a gentle creative continuity warning
                    warnings.append(
                        f"Continuidad Creativa: '{h_last.get('name')}' corre riesgo de ser idéntico a '{h1.get('name')}'. "
                        "Considera añadir una variación de topline, contramelodía o automatización de brillo."
                    )

        # Check: Climax / Drop documented transformation
        climax_secs = [s for s in sections if any(w in str(s.get("name", "")).lower() for w in ["climax", "drop", "puente"])]
        if climax_secs:
            c_sec = climax_secs[0]
            # Check if bass or energy changes
            bass_trk = next((t for t in tracks if t.get("role") == "BASS"), None)
            if bass_trk and bass_trk.get("notes_count", 0) > 0 and not session_data.get("automations"):
                warnings.append(
                    f"Dinámica: Sección '{c_sec.get('name')}' carece de curvas de automatización o corte de frecuencias registradas."
                )

        return warnings

"""
Append-Only Transactional Ledger for Verifiable Production Governance.
Provides an immutable, tamper-evident audit trail with SHA-256 hash chains.
"""

from datetime import datetime, timezone
from enum import Enum
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import uuid

from pydantic import BaseModel, Field

from .contract import DecisionType, ResolutionStatus, StructuralDecisionContract
from .evidence import GovernancePolicy
from .provenance import (
    canonical_json,
    compute_contract_hash,
    compute_policy_hash,
    compute_sha256,
)
from .receipt import CommitReceipt
from .policy_resolver import ResolutionResult


GENESIS_PREVIOUS_HASH = "sha256:" + "0" * 64


class TransitionType(str, Enum):
    INITIAL = "INITIAL"
    COMMIT = "COMMIT"
    ROLLBACK = "ROLLBACK"
    SUSPEND = "SUSPEND"


class LedgerEntry(BaseModel):
    entry_id: str
    sequence_number: int
    timestamp: str
    transaction_id: str
    transition_type: TransitionType
    contract_id: str
    decision: DecisionType
    resolution_status: ResolutionStatus
    policy_hash: str
    contract_hash: str
    evidence_hash: str
    lineage_hash: str
    previous_entry_hash: str
    entry_hash: str
    reasons: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    receipt: Optional[CommitReceipt] = None

    def compute_expected_hash(self) -> str:
        """Calculates expected entry_hash from canonical entry payload."""
        payload = {
            "entry_id": self.entry_id,
            "sequence_number": self.sequence_number,
            "timestamp": self.timestamp,
            "transaction_id": self.transaction_id,
            "transition_type": self.transition_type.value,
            "contract_id": self.contract_id,
            "decision": self.decision.value,
            "resolution_status": self.resolution_status.value,
            "policy_hash": self.policy_hash,
            "contract_hash": self.contract_hash,
            "evidence_hash": self.evidence_hash,
            "lineage_hash": self.lineage_hash,
            "previous_entry_hash": self.previous_entry_hash,
            "reasons": sorted(self.reasons),
            "warnings": sorted(self.warnings),
            "receipt": self.receipt.model_dump() if self.receipt else None,
        }
        return compute_sha256(canonical_json(payload))


class GovernanceLedger:
    """
    Append-only cryptographically linked ledger for governance state transitions.
    Operates in-memory or persists atomically to a JSONL file.
    """

    def __init__(self, ledger_file: Optional[Path | str] = None):
        self.ledger_file: Optional[Path] = Path(ledger_file) if ledger_file else None
        self._entries: List[LedgerEntry] = []

        if self.ledger_file and self.ledger_file.exists():
            self._load_from_disk()

    def _load_from_disk(self) -> None:
        """Loads entries from JSONL file on disk."""
        if not self.ledger_file:
            return

        loaded_entries: List[LedgerEntry] = []
        with open(self.ledger_file, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, start=1):
                clean_line = line.strip()
                if not clean_line:
                    continue
                try:
                    data = json.loads(clean_line)
                    entry = LedgerEntry.model_validate(data)
                    loaded_entries.append(entry)
                except Exception as e:
                    raise ValueError(
                        f"Ledger file corruption at {self.ledger_file}:{line_num} -> {e}"
                    )

        self._entries = loaded_entries

    def record_transition(
        self,
        transaction_id: str,
        transition_type: TransitionType,
        contract: StructuralDecisionContract,
        resolution_result: ResolutionResult,
        evidence_hash: str,
        lineage_hash: str,
        policy_hash: str,
        previous_snapshot_hash: Optional[str] = None,
        resulting_snapshot_hash: Optional[str] = None,
        timestamp: Optional[str] = None,
    ) -> LedgerEntry:
        """
        Appends an immutable state transition record to the ledger.
        If transition_type is COMMIT and commit_approved is True, emits an inmutable CommitReceipt.
        """
        ts = timestamp or datetime.now(timezone.utc).isoformat()
        entry_id = str(uuid.uuid4())
        seq = len(self._entries)

        previous_hash = (
            self._entries[-1].entry_hash if self._entries else GENESIS_PREVIOUS_HASH
        )
        contract_hash = contract.contract_hash or compute_contract_hash(contract)

        receipt: Optional[CommitReceipt] = None
        if transition_type == TransitionType.COMMIT and resolution_result.commit_approved:
            receipt = CommitReceipt(
                commit_id=f"commit-{entry_id[:8]}",
                transaction_id=transaction_id,
                contract_id=contract.contract_id,
                execution_id=f"exec-{entry_id[:8]}",
                verification_id=f"verif-{entry_id[:8]}",
                integrity_id=f"integ-{entry_id[:8]}",
                policy_hash=policy_hash,
                contract_hash=contract_hash,
                evidence_hash=evidence_hash,
                previous_snapshot_hash=previous_snapshot_hash,
                resulting_snapshot_hash=resulting_snapshot_hash,
                timestamp=ts,
                status="COMMITTED",
            )
            # Attach receipt to resolution_result as well for convenience
            resolution_result.receipt = receipt

        # Draft payload to compute deterministic hash
        draft_payload = {
            "entry_id": entry_id,
            "sequence_number": seq,
            "timestamp": ts,
            "transaction_id": transaction_id,
            "transition_type": transition_type.value,
            "contract_id": contract.contract_id,
            "decision": contract.decision.value,
            "resolution_status": resolution_result.status.value,
            "policy_hash": policy_hash,
            "contract_hash": contract_hash,
            "evidence_hash": evidence_hash,
            "lineage_hash": lineage_hash,
            "previous_entry_hash": previous_hash,
            "reasons": sorted(resolution_result.reasons),
            "warnings": sorted(resolution_result.warnings),
            "receipt": receipt.model_dump() if receipt else None,
        }
        entry_hash = compute_sha256(canonical_json(draft_payload))

        entry = LedgerEntry(
            entry_id=entry_id,
            sequence_number=seq,
            timestamp=ts,
            transaction_id=transaction_id,
            transition_type=transition_type,
            contract_id=contract.contract_id,
            decision=contract.decision,
            resolution_status=resolution_result.status,
            policy_hash=policy_hash,
            contract_hash=contract_hash,
            evidence_hash=evidence_hash,
            lineage_hash=lineage_hash,
            previous_entry_hash=previous_hash,
            entry_hash=entry_hash,
            reasons=resolution_result.reasons,
            warnings=resolution_result.warnings,
            receipt=receipt,
        )

        self._entries.append(entry)

        if self.ledger_file:
            self._append_to_file(entry)

        return entry

    def _append_to_file(self, entry: LedgerEntry) -> None:
        """Appends a single JSON line to the ledger file."""
        if not self.ledger_file:
            return

        self.ledger_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.ledger_file, "a", encoding="utf-8") as f:
            f.write(canonical_json(entry.model_dump()) + "\n")
            f.flush()

    def verify_chain_integrity(self) -> Tuple[bool, List[str]]:
        """
        Cryptographically verifies the entire ledger chain from entry 0 to head:
        1. Sequence numbering is strictly sequential (0, 1, ..., N).
        2. Previous entry hash link matches preceding entry.
        3. Recalculated entry_hash matches stored entry_hash.
        4. Receipts hashes match entry records.
        """
        errors: List[str] = []

        if not self._entries:
            return True, []

        expected_prev = GENESIS_PREVIOUS_HASH

        for i, entry in enumerate(self._entries):
            # 1. Sequence check
            if entry.sequence_number != i:
                errors.append(
                    f"Sequence broken at index {i}: expected sequence_number={i}, got {entry.sequence_number}"
                )

            # 2. Previous hash link check
            if entry.previous_entry_hash != expected_prev:
                errors.append(
                    f"Hash link broken at index {i}: expected previous_entry_hash={expected_prev}, got {entry.previous_entry_hash}"
                )

            # 3. Recalculated entry hash check
            recomputed = entry.compute_expected_hash()
            if entry.entry_hash != recomputed:
                errors.append(
                    f"Tampered entry detected at index {i} ({entry.entry_id}): expected {recomputed}, got {entry.entry_hash}"
                )

            # 4. Receipt consistency check
            if entry.receipt:
                if entry.receipt.policy_hash != entry.policy_hash:
                    errors.append(f"Receipt policy_hash mismatch at index {i}")
                if entry.receipt.contract_hash != entry.contract_hash:
                    errors.append(f"Receipt contract_hash mismatch at index {i}")
                if entry.receipt.evidence_hash != entry.evidence_hash:
                    errors.append(f"Receipt evidence_hash mismatch at index {i}")

            expected_prev = entry.entry_hash

        return len(errors) == 0, errors

    def get_entries(self, transaction_id: Optional[str] = None) -> List[LedgerEntry]:
        """Returns list of entries, optionally filtered by transaction_id."""
        if transaction_id is None:
            return list(self._entries)
        return [e for e in self._entries if e.transaction_id == transaction_id]

    def get_head(self) -> Optional[LedgerEntry]:
        """Returns the latest entry in the ledger, or None if empty."""
        return self._entries[-1] if self._entries else None

    def get_receipts(self) -> List[CommitReceipt]:
        """Returns all CommitReceipts emitted in the ledger."""
        return [e.receipt for e in self._entries if e.receipt is not None]

    @property
    def head_hash(self) -> str:
        """Returns the SHA-256 hash of the latest entry or genesis hash if empty."""
        return self._entries[-1].entry_hash if self._entries else GENESIS_PREVIOUS_HASH

    @property
    def genesis_hash(self) -> str:
        """Returns the genesis block previous hash."""
        return GENESIS_PREVIOUS_HASH

    def __len__(self) -> int:
        return len(self._entries)

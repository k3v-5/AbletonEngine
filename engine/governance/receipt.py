"""
Cryptographic Commit Receipts for Audited Governance.
Provides immutable proof that a production change satisfied all architectural contracts.
"""

from typing import Optional
from pydantic import BaseModel


class CommitReceipt(BaseModel):
    commit_id: str
    transaction_id: str
    contract_id: str
    execution_id: str
    verification_id: str
    integrity_id: str
    policy_hash: str
    contract_hash: str
    evidence_hash: str
    previous_snapshot_hash: Optional[str] = None
    resulting_snapshot_hash: Optional[str] = None
    timestamp: str
    status: str = "COMMITTED"

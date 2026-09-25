"""
Cryptographic Provenance Engine for AbletonEngine Governance.
Computes deterministic SHA-256 hashes and verifies unbroken lineage chains.
"""

import hashlib
import json
from typing import Any, Dict, List, Optional

from .contract import (
    DecisionType,
    ExecutionStatus,
    MutationState,
    EvidenceStatus,
    StructuralDecisionContract,
)
from .evidence import (
    ExecutionResult,
    VerificationResult,
    IntegrityResult,
    ProvenanceCompleteness,
    ContextEvaluationResult,
    GovernancePolicy,
)


def _serialize_canonical(val: Any) -> Any:
    """Recursively converts structures to JSON-serializable primitives with sorted keys."""
    if isinstance(val, dict):
        return {str(k): _serialize_canonical(v) for k, v in sorted(val.items())}
    elif isinstance(val, (list, tuple)):
        return [_serialize_canonical(x) for x in val]
    elif hasattr(val, "model_dump"):
        return _serialize_canonical(val.model_dump())
    elif hasattr(val, "value"):  # Enum support
        return val.value
    elif val is None or isinstance(val, (int, float, str, bool)):
        return val
    else:
        return str(val)


def canonical_json(data: Any) -> str:
    """Serializes data deterministically: sorted keys, compact separators, UTF-8."""
    normalized = _serialize_canonical(data)
    return json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_sha256(content: str) -> str:
    """Returns SHA-256 digest prefixed with 'sha256:'."""
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def compute_contract_hash(contract: StructuralDecisionContract) -> str:
    """Computes deterministic hash for a structural decision contract."""
    payload = {
        "contract_id": contract.contract_id,
        "decision": contract.decision.value,
        "target_track": contract.target_track,
        "target_device": contract.target_device,
        "parameters": contract.parameters,
        "expected_state": contract.expected_state.model_dump() if contract.expected_state else None,
        "override_proposal": contract.override_proposal.model_dump() if contract.override_proposal else None,
        "is_valid": contract.is_valid,
        "intent": contract.intent,
        "justification": contract.justification,
        "exception_type": contract.exception_type,
        "metadata": contract.metadata,
    }
    return compute_sha256(canonical_json(payload))


def compute_policy_hash(policy: GovernancePolicy) -> str:
    """Computes deterministic hash for a governance policy."""
    payload = {
        "policy_id": policy.policy_id,
        "policy_version": policy.policy_version,
        "enabled": policy.enabled,
    }
    return compute_sha256(canonical_json(payload))


def compute_evidence_hash(
    execution_result: ExecutionResult,
    verification_result: VerificationResult,
    integrity_result: IntegrityResult,
    context_result: ContextEvaluationResult,
) -> str:
    """Computes composite hash for all observed facts and evidence."""
    payload = {
        "execution": {
            "execution_id": execution_result.execution_id,
            "status": execution_result.status.value,
            "mutation_state": execution_result.mutation_state.value,
            "error_message": execution_result.error_message,
        },
        "verification": {
            "verification_id": verification_result.verification_id,
            "status": verification_result.status.value,
            "mismatch_detail": verification_result.mismatch_detail,
            "observed_state": verification_result.observed_state,
            "override_passed": verification_result.override_passed,
        },
        "integrity": {
            "is_intact": integrity_result.is_intact,
            "violations": sorted(integrity_result.violations),
            "metrics": integrity_result.metrics,
        },
        "context": {
            "satisfied": context_result.satisfied,
            "unmet_constraints": sorted(context_result.unmet_constraints),
            "warnings": sorted(context_result.warnings),
        },
    }
    return compute_sha256(canonical_json(payload))


def compute_lineage_hash(
    parent_commit_hash: Optional[str],
    contract_hash: str,
    evidence_hash: str,
    policy_hash: str,
) -> str:
    """Computes lineage hash tying parent history to current decision and evidence."""
    payload = {
        "parent_commit_hash": parent_commit_hash or "genesis:00000000000000000000000000000000",
        "contract_hash": contract_hash,
        "evidence_hash": evidence_hash,
        "policy_hash": policy_hash,
    }
    return compute_sha256(canonical_json(payload))


def build_provenance(
    contract: StructuralDecisionContract,
    policy: GovernancePolicy,
    execution_result: ExecutionResult,
    verification_result: VerificationResult,
    integrity_result: IntegrityResult,
    context_result: ContextEvaluationResult,
    parent_commit_hash: Optional[str] = None,
    require_parent_if_non_genesis: bool = False,
    is_genesis: bool = False,
) -> ProvenanceCompleteness:
    """
    Constructs and verifies cryptographic provenance completeness.
    Audits the linkage between parent commit, contract, policy, and evidence.
    """
    missing_links: List[str] = []

    # 1. Contract hash audit
    computed_contract_hash = compute_contract_hash(contract)
    if contract.contract_hash and contract.contract_hash != computed_contract_hash:
        missing_links.append(
            f"Contract hash mismatch: expected {computed_contract_hash}, received {contract.contract_hash}"
        )

    # 2. Policy hash audit
    computed_policy_hash = compute_policy_hash(policy)
    if policy.policy_hash and policy.policy_hash != computed_policy_hash:
        missing_links.append(
            f"Policy hash mismatch: expected {computed_policy_hash}, received {policy.policy_hash}"
        )
    elif not policy.policy_hash:
        missing_links.append("Policy missing required policy_hash.")

    # 3. Lineage parent audit
    if require_parent_if_non_genesis and not is_genesis and not parent_commit_hash:
        missing_links.append("Missing parent commit hash in non-genesis transaction.")

    # 4. Compute composite evidence hash and lineage hash
    computed_evidence_hash = compute_evidence_hash(
        execution_result=execution_result,
        verification_result=verification_result,
        integrity_result=integrity_result,
        context_result=context_result,
    )

    lineage = compute_lineage_hash(
        parent_commit_hash=parent_commit_hash,
        contract_hash=computed_contract_hash,
        evidence_hash=computed_evidence_hash,
        policy_hash=computed_policy_hash,
    )

    is_complete = len(missing_links) == 0

    return ProvenanceCompleteness(
        complete=is_complete,
        missing_links=missing_links,
        lineage_hash=lineage if is_complete else None,
    )

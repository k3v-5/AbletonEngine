# PIE Production Governance Layer — First-Class Rollback Engine (Documento 12)

## 1. Overview & Architectural Principle

This document formalizes the architecture, contracts, and verification guarantees of the **First-Class Rollback Engine** in the Production Intelligence Engine (PIE) under `engine/production/rollback.py`.

### Fundamental Rule: Causal Non-Destruction
> **Una acción nunca desaparece.** Si se revierte, su reversión se convierte en un nuevo hecho causal dentro del `ProductionGraph`.

Rollback in PIE is fundamentally distinct from a mechanical "Undo":
- **Undo**: $\text{set\_volume}(-2\text{ dB}) \rightarrow \text{set\_volume}(+2\text{ dB})$. (Blind inversion, no verification, state amnesia).
- **Rollback PIE**: A causal, auditable, multivariably verified, and transactional transition:

```
Decision D1
   │
   ▼
Action A1
   │
   ▼
Result R1
   │
   ▼
Regression Detected (Acoustic / Policy / Socket)
   │
   ▼
Rollback Decision D2
   │
   ▼
Rollback Action A2
   │
   ▼
Verification V2 (Structural, Fingerprint, Acoustic)
   │
   ▼
Rollback Result R2 (COMMITTED)
```

---

## 2. Core Architectural Guarantees

1. **Atomicity (ACID Boundary)**:
   Rollback operations execute inside a dedicated transaction (`begin()` $\rightarrow$ `stage()` $\rightarrow$ `validate()` $\rightarrow$ `commit()`). If any operation fails, the transaction rolls back cleanly, leaving 0 partially applied operations.
2. **Idempotency**:
   Requesting rollback on an already reverted decision returns `RollbackStatus.ALREADY_REVERTED` without duplicating mutations or creating redundant nodes.
3. **Double Fingerprint Validation**:
   Validation is performed twice:
   - At `RollbackPlan` synthesis.
   - Immediately before physical transaction `commit()`.
   If a concurrent or manual mutation alters the relevant state between plan creation and commit, the rollback aborts with `StaleRollbackPlanError`.
4. **Anti-Loop Depth Guardrail**:
   Enforces `max_automatic_rollback_depth = 1` per incident. If a rollback attempt itself causes a regression, it terminates with `MAX_DEPTH_EXCEEDED` and requires manual intervention rather than entering infinite rollback loops.
5. **Inviolability of Locks**:
   If an entity is marked `locked = True`, `RollbackBlockedLockedObjectError` prevents any mutation, even if PIE originally caused the modification.
6. **Append-Only Journaling**:
   Every stage of rollback emits an immutable event to the rollback journal (`state/production/journal/`):
   - `ROLLBACK_REQUESTED`
   - `ROLLBACK_PLAN_CREATED`
   - `ROLLBACK_STARTED`
   - `ROLLBACK_OPERATION_STAGED`
   - `ROLLBACK_OPERATION_APPLIED`
   - `ROLLBACK_COMMITTED`
   - `ROLLBACK_VERIFICATION_PASSED` / `FAILED`
   - `ROLLBACK_COMPLETED`
7. **Crash Recovery & Incomplete Transactions**:
   Upon server reboot, `recover(transaction_id)` analyzes the journal and session state to classify transactions into `NOT_STARTED`, `PARTIALLY_APPLIED`, `FULLY_APPLIED`, or `UNKNOWN`, safely restoring the session state.

---

## 3. The 10 Canonical Rollback Policies

| Policy ID | Severity | Failure Code | Description |
| :--- | :---: | :--- | :--- |
| **1. ROLLBACK_TARGET_EXISTS** | `CRITICAL` | `TARGET_NOT_FOUND` | Target decision, transaction, or plan must exist in the graph or storage. |
| **2. ROLLBACK_TARGET_REVERSIBLE** | `CRITICAL` | `NON_REVERSIBLE_ACTION` | Target action must declare `reversible = True`. Non-reversible actions reject auto-rollback. |
| **3. ROLLBACK_FINGERPRINT_VALID** | `CRITICAL` | `STALE_ROLLBACK_PLAN` | Rejects rollback if relevant entity state shifted between plan conception and execution. |
| **4. ROLLBACK_NO_CONFLICT** | `CRITICAL` | `CONFLICTING_STATE` | Detects manual changes after original decision; refuses silent overwrite. |
| **5. ROLLBACK_DEPENDENCIES_SAFE**| `CRITICAL` | `DEPENDENCY_CONFLICT` | Rejects rollback if downstream decisions depend on target unless cascading scope is explicitly authorized. |
| **6. ROLLBACK_SNAPSHOT_VALID** | `CRITICAL` | `INVALID_SNAPSHOT` | Snapshot must exist, be complete, and match `project_id`. |
| **7. ROLLBACK_TRANSACTION_REQUIRED** | `CRITICAL` | `TRANSACTION_REQUIRED` | Rollback cannot mutate Ableton Live outside of a formal transaction. |
| **8. ROLLBACK_VERIFICATION_REQUIRED** | `ERROR` | `VERIFICATION_REQUIREMENT_MISSING` | Plan must define post-rollback verification requirements. |
| **9. ROLLBACK_MAX_DEPTH** | `CRITICAL` | `MAX_DEPTH_EXCEEDED` | Halts automatic rollback cascade when depth limit is reached. |
| **10. ROLLBACK_IDEMPOTENCY** | `CRITICAL` | `ALREADY_REVERTED` | Prevents re-executing already reverted decisions. |

---

## 4. Verification & Testing Matrix

The implementation is verified via **23 dedicated test cases** in `tests/test_production_rollback.py`:

- **Test 1 — Simple Rollback**: Action applied, rollback triggered, exact pre-state restored.
- **Test 2 — Idempotent Rollback**: Calling rollback twice returns `ALREADY_REVERTED` with zero mutations.
- **Test 3 — Invalid Snapshot**: Snapshot missing or corrupted rejected with `InvalidSnapshotError`.
- **Test 4 — Stale Fingerprint**: Altering relevant parameter before rollback triggers `StaleRollbackPlanError`.
- **Test 5 — Irrelevant Change**: Altering unrelated track preserves plan freshness and allows rollback.
- **Test 6 — Locked Object**: Target track locked rejected with `RollbackBlockedLockedObjectError`.
- **Test 7 — Dependency Conflict**: Descendant decision depending on target detected and blocked with `DependencyConflictError`.
- **Test 8 — Auto-Rollback on Regression**: Simulated acoustic regression triggers automatic rollback and verification.
- **Test 9 — Socket Failure**: Connection loss during rollback enters `RECOVERY_REQUIRED` state.
- **Test 10 — Crash Recovery**: Unfinished transaction journal analyzed and safely resolved.
- **Test 11 — Atomicity**: Partial failure in operation sequence rolls back 100% of staged changes.
- **Test 12 — No History Loss**: Original `ACTION` and `RESULT` nodes preserved alongside new `ROLLBACK_*` nodes.
- **Test 13 — Conflicting Rollback**: Manual parameter tweak post-action flagged as `CONFLICTING_STATE`.
- **Test 14 — Deleted Object Restore**: Track deletion cleanly restored from snapshot.
- **Test 15 — Created Object Rollback**: Created track cleanly removed on rollback.
- **Test 16 — No Rollback Loop**: Post-rollback regression halts cascade, preventing infinite loops.
- **Test 17 — Incorrect Project**: Snapshot from mismatched project ID rejected immediately.
- **Test 18 — Corrupted Persistence**: Hash mismatch in persisted JSON detected and rejected.
- **Test 19 — Determinism**: Identical inputs produce identical rollback plans and hashes.
- **Test 20 — Explainability**: `explain()` reconstructs the complete causal rollback narrative.
- **Failure Injection 1**: Non-reversible action injection blocks execution.
- **Failure Injection 2**: Pre-commit concurrent modification triggers stale plan detection.
- **Failure Injection 3**: Post-rollback regression properly marks status as `FAILED` and prevents loop.

# PIE Production Governance Layer — Failure Injection & Chaos Resilience

## 1. Overview & Objective

This document formalizes **Document 15 — Failure Injection & Chaos Testing** for the Production Intelligence Engine (PIE) Production Governance Layer (Hito 1).

The primary objective of Document 15 is to deliberately subject the system to severe catastrophic failure conditions and prove mathematically and empirically that PIE **always terminates in a consistent, recoverable state**:
- Zero orphan mutations in Ableton Live or the `SessionShadowGraph`.
- Zero dangling open transactions in `TransactionManager`.
- Zero unhandled tracebacks or naked panics leaking to the MCP transport.
- Zero corrupted JSON or partial disk writes during persistence.
- Zero loss of causal audit trail (`ProductionGraph` records all attempted actions, errors, and rollbacks non-destructively).
- Strict non-autonomous behavior for historical candidates retrieved from `DecisionMemory`.

---

## 2. Taxonomy of Injected Failures

### 2.1 The 5 Fundamental Catastrophic Failure Classes (Cases A through E)

| Class | Injected Failure Condition | Detection Layer | System Response | Invariant Preserved |
| :--- | :--- | :--- | :--- | :--- |
| **Case A** | Remote socket connection drops mid-dispatch | `ProductionExecutor` | Catches `ConnectionError`, triggers transaction auto-rollback, marks plan `FAILED` | No partial state applied; error node added to DAG |
| **Case B** | Target entity is locked (`locked=True`) | `ProductionPolicyEngine` | Pre-execution validation raises `LockedObjectError` | Zero mutations; transaction is never opened |
| **Case C** | Session state shifted after plan creation | `ProductionContext` / `SessionFingerprint` | Pre-execution validation raises `StalePlanError` | Scoped fingerprint protects against race conditions |
| **Case D** | Post-execution acoustic regression (True Peak > -0.3 dBTP, over-compression) | `VerificationMatrix` | Verification fails (`PASS=False`), raises `AcousticRegressionError`, auto-rolls back | Physical parameters restored; `ROLLBACK` node added to DAG |
| **Case E** | Low-end acoustic masking / mix defect | `ProductionPlanner` | Detects `MIX_PROBLEM`, rejects mastering action, redirects to Mix domain | Strict mix/master domain boundary enforced |

---

### 2.2 Explicit Failure Injection Specification (FAIL-001 through FAIL-017)

| Test ID | Scenario Description | Expected Trigger & Exception | System Invariant Guarantee |
| :--- | :--- | :--- | :--- |
| **FAIL-001** | Stale plan execution attempt | `StalePlanError` raised | `TransactionManager.begin()` is NEVER called |
| **FAIL-002** | Locked object mutation attempt | `LockedObjectError` raised | Modification blocked prior to execution |
| **FAIL-003** | Modifying action dispatch without active transaction | `TransactionRequiredError` raised | Direct un-governed mutation impossible |
| **FAIL-004** | Attempt to create circular dependency in DAG | `GraphIntegrityError` raised | `ProductionGraph` remains strictly a DAG |
| **FAIL-005** | Insertion of edge to non-existent node ID | `NodeNotFoundError` raised | Referential integrity of causal graph guaranteed |
| **FAIL-006** | Limiter gain reduction exceeding guardrail (2.5 dB) | Policy check returns `allowed=False` | Policy rejection recorded as `REJECTION` node |
| **FAIL-007** | Master True Peak exceeding ceiling (-0.3 dBTP) | Policy check returns `allowed=False` | Audio safety ceiling strictly enforced |
| **FAIL-008** | Master EQ modifying > 2 bands or > 1.0 dB gain | Policy check returns `allowed=False` | Principle of Minimum Intervention enforced |
| **FAIL-009** | Mix problem diagnosed during mastering intent | Policy check redirects to `mix` domain | Domain separation invariant preserved |
| **FAIL-010** | Inter-sample clipping detected post-execution | `AcousticRegressionError` raised | Automatic transaction rollback; snapshot restored |
| **FAIL-011** | Socket reset by peer during action write | `ExecutionError` raised | Physical rollback triggered; plan marked `FAILED` |
| **FAIL-012** | Corrupted JSON state file on disk | `SerializationError` raised | Disk corruption reported explicitly; never masked |
| **FAIL-013** | Process termination mid-execution (Crash) | `ProductionStorage.recover_startup_state()` | Plan marked `RECOVERY_REQUIRED` on restart |
| **FAIL-014** | Unhandled runtime panic inside executor | `ExecutionError` raised | No transactions left in `OPEN` state |
| **FAIL-015** | Atomic write failure (disk full / permission denied) | `PersistenceError` raised | Previous valid file remains 100% intact |
| **FAIL-016** | Attempting double commit on same transaction | `InvalidParameterError` raised | Transaction state remains `COMMITTED`; no duplicate actions |
| **FAIL-017** | Concurrent conflicting execution on same resource | Plan A commits; Plan B raises `StalePlanError` | Concurrency conflict safely rejected without race |

---

## 3. Atomic Persistence & Crash Recovery Guarantees

### 3.1 Two-Phase Atomic Disk Replace
All state updates (`ProductionGraph`, `DecisionMemory`, snapshots, execution records) follow the ACID storage protocol:
1. Data written to an isolated temporary file in the same directory (`tempfile.NamedTemporaryFile`).
2. Buffer flushed to OS kernel (`tf.flush()`).
3. File descriptor synced to physical media (`os.fsync(tf.fileno())`).
4. Atomic rename / replace onto target file (`os.replace()`).

**Failure Invariant**: If a power cut or process kill occurs at step 1, 2, or 3, the target file retains its previous valid state. Incomplete or corrupt JSON files are never created at the destination path.

### 3.2 Startup Recovery Protocol
Upon engine initialization, `ProductionStorage.recover_startup_state()` scans persisted plans:
- Identifies any plan left in `EXECUTING` state due to process termination.
- Safely transitions the plan status to `RECOVERY_REQUIRED`.
- Verifies `ProductionGraph` DAG integrity before enabling MCP command processing.

---

## 4. Test Suite Execution & Verification

The failure injection test suite is executed directly via pytest:
```bash
python -m pytest tests/test_failure_injection.py -v
```

All 22 failure injection test cases execute and pass deterministically:
```
tests/test_failure_injection.py::test_failure_case_a_socket_disconnect_triggers_rollback PASSED
tests/test_failure_injection.py::test_failure_case_b_locked_object_rejection PASSED
tests/test_failure_injection.py::test_failure_case_c_stale_plan_rejection PASSED
tests/test_failure_injection.py::test_failure_case_d_acoustic_regression_auto_rollback PASSED
tests/test_failure_injection.py::test_failure_case_e_mix_vs_master_boundary PASSED
tests/test_failure_injection.py::test_fail_001_stale_plan_execution PASSED
tests/test_failure_injection.py::test_fail_002_locked_object_mutation PASSED
tests/test_failure_injection.py::test_fail_003_transaction_required_violation PASSED
tests/test_failure_injection.py::test_fail_004_graph_cycle_detection PASSED
tests/test_failure_injection.py::test_fail_005_nonexistent_node_edge_insertion PASSED
tests/test_failure_injection.py::test_fail_006_master_limiter_gain_reduction_exceeded PASSED
tests/test_failure_injection.py::test_fail_007_master_true_peak_ceiling_exceeded PASSED
tests/test_failure_injection.py::test_fail_008_master_eq_excessive_bands_or_gain PASSED
tests/test_failure_injection.py::test_fail_009_mix_problem_separation_enforcement PASSED
tests/test_failure_injection.py::test_fail_010_post_execution_acoustic_regression_rollback PASSED
tests/test_failure_injection.py::test_fail_011_transport_socket_failure_mid_dispatch PASSED
tests/test_failure_injection.py::test_fail_012_corrupt_state_file_detection PASSED
tests/test_failure_injection.py::test_fail_013_interrupted_transaction_crash_recovery PASSED
tests/test_failure_injection.py::test_fail_014_unexpected_exception_leaves_no_open_transaction PASSED
tests/test_failure_injection.py::test_fail_015_persistence_atomic_write_failure_preserves_previous_state PASSED
tests/test_failure_injection.py::test_fail_016_double_commit_prevention PASSED
tests/test_failure_injection.py::test_fail_017_concurrent_conflicting_execution_invalidates_second_plan PASSED
============================= 22 passed in 17.53s =============================
```

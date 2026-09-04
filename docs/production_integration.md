# PIE Production Governance Layer — Integration Architecture & Verification Guarantees

## 1. Overview & Objective

This document formalizes the End-to-End (E2E) integration of the Production Intelligence Engine (PIE) Production Governance Layer (Hito 1).

The integration demonstrates conclusively that PIE does not operate as a direct unverified execution shortcut:
`LLM -> Direct Action -> Ableton`

Instead, every production action executes through a deterministic, auditable, and reversibility-guaranteed causal governance pipeline:

```
INTENT
  │
  ▼
CONTEXT (Snapshot & Scoped Fingerprint)
  │
  ▼
OBSERVATION (Pre-measurement: ITU-R BS.1770-5)
  │
  ▼
ANALYSIS (Diagnostic & Headroom Evaluation)
  │
  ▼
HYPOTHESIS
  │
  ▼
CANDIDATES (Multiple competing production strategies)
  │
  ▼
POLICY ENGINE (Critical Guardrails & Rule Check)
  ├── REJECTED ──► Recorded as REJECTION in ProductionGraph
  └── ALLOWED
        │
        ▼
PLAN (Deterministic, fingerprinted, immutable)
  │
  ▼
VALIDATION (Target existence, lock check, freshness)
  │
  ▼
TRANSACTION (Atomic boundary: begin_transaction)
  │
  ▼
EXECUTION (Physical DSP modification via adapter)
  │
  ▼
POST-MEASUREMENT (Acoustic measurement re-capture)
  │
  ▼
VERIFICATION MATRIX (Multivariable evaluation & regression check)
  ├── REGRESSION ──► Atomic Rollback, graph history preserved
  └── PASSED
        │
        ▼
COMMIT (Transaction commit & state version bump)
  │
  ▼
PRODUCTION GRAPH (Full causal DAG lineage)
  │
  ▼
DECISION MEMORY (Candidate-only historical record)
```

---

## 2. E2E Golden Integration Scenario

### User Intent
> *"Quiero que el master tenga más volumen"*

- **Target**: `Master`
- **Domain**: `MASTER`
- **Current State**: -14.8 LUFS (Integrated), -1.0 dBTP (True Peak)
- **Target Acoustic Target**: -14.0 LUFS
- **Required Delta**: +0.8 LUFS

### Step-by-Step Causal Verification
1. **Baseline Capture**:
   Deterministic baseline snapshot is computed with SHA-256 fingerprint scoped to the target (`Master`).
2. **Intent Ingestion**:
   Normalized into a typed `ProductionIntent` object and added as the root `INTENT` node in `ProductionGraph`.
3. **Context Validation**:
   Context verifies track existence (`Master`, `Kick`, `Bass`), sample rate (48 kHz), tempo (124 BPM), genre (`Melodic Techno`), and active loudness profile (`STREAMING`).
4. **Base Measurement**:
   Audited via BS.1770-5 compliant loudness analyzer (`integrated_lufs = -14.8`, `true_peak <= -1.0 dBTP`).
5. **Diagnosis & Analysis**:
   Identifies a +0.8 LUFS headroom gap without violating True Peak ceilings.
6. **Candidate Generation & Minimum Intervention Selection**:
   Generates multiple strategies:
   - Conservative Limiter (+0.8 dB)
   - Aggressive Limiter (+3.5 dB)
   - Master EQ Boost (+1.5 dB)
   - Mix Gain Adjustment
7. **Policy Engine Evaluation**:
   - Rejects Aggressive Limiter (`gain_reduction > 2.0 dB` violation).
   - Rejects Master EQ (`gain > 1.0 dB` violation).
   - Preserves all rejected candidates as `REJECTION` nodes in `ProductionGraph` with causal link to policy check.
   - Selects Conservative Limiter under the Principle of Minimum Intervention.
8. **Plan Fingerprinting & Scoped Freshness**:
   Plan receives deterministic SHA-256 session fingerprint. Validation succeeds because session state has not shifted.
9. **Transactional Execution**:
   Executes inside an isolated transaction (`tx_id`). Physical parameters are updated atomically.
10. **Post-Measurement & Acoustic Matrix Verification**:
    Post-execution measurement yields -14.0 LUFS, -0.4 dBTP. Verification confirms target met (+0.8 LUFS) with 0 regressions.
11. **Transaction Commit & Result**:
    Transaction commits atomically. `NodeType.RESULT` is appended to `ProductionGraph`.
12. **Lineage Explanation & Decision Memory**:
    Causal chain is verified via `graph.explain_decision()`. Decision is archived into `DecisionMemory` with `auto_executable=False` (Candidate-Only invariant).

---

## 3. Formal Verification Matrix Guarantees

| Scenario | Input | Policy | Plan | Execution | Verification | Rollback | Graph | Memory |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Master Loudness** | Intent: "+0.8 LUFS" | PASS (Conservative) | `PLANNED` | `COMMITTED` | `PASS` | No | Full DAG | Archived |
| **2. Compliant Master** | -14.1 LUFS (target -14.0) | N/A | `NO_OP` | Skipped | N/A | No | NO_OP Node | Not recorded |
| **3. Limiter GR Guardrail** | Candidate GR: 3.5 dB | REJECT (`max 2.0 dB`) | Alt selected | Valid plan | Standard | No | REJECTION node | Evidence only |
| **4. Master EQ Guardrail** | Candidate Gain: +1.5 dB | REJECT (`max 1.0 dB`) | Alt selected | Valid plan | Standard | No | REJECTION node | Evidence only |
| **5. Mix Problem** | Low-end masking | REJECT (Boundary) | Recommend Mix | Blocked | N/A | No | DIAGNOSTIC node| Not recorded |
| **6. Locked Track** | Target `Bass` (locked) | REJECT (`LOCKED`) | Blocked | Blocked | N/A | No | No change | Not recorded |
| **7. No Transaction** | Execution without tx | BLOCK (`TX_REQUIRED`) | N/A | Blocked | N/A | No | No mutation | Not recorded |
| **8. Stale Plan** | Master vol altered post-plan | PASS | `STALE` | `REJECTED` | N/A | No | No mutation | Not recorded |
| **9. Irrelevant Change** | Pad vol altered post-plan | PASS | `VALID` | `COMMITTED` | `PASS` | No | Valid DAG | Archived |
| **10. Acoustic Regression** | TP regresses to +1.5 dBTP | PASS | `PLANNED` | `ROLLED_BACK` | `FAIL` | **Auto Rollback** | ROLLBACK node | Marked failed |
| **11. Action Fault** | Adapter exception | PASS | `PLANNED` | `ROLLED_BACK` | N/A | **Auto Rollback** | Trans rolled back| Marked failed |
| **12. Socket Fault** | Socket disconnect | PASS | `PLANNED` | `ROLLED_BACK` | N/A | **Auto Rollback** | Error recorded | Marked failed |
| **13. Historical Match** | Previous decision in memory | PASS | Candidate only | Manual approval| Standard | No | Graph lineage | Candidate only |
| **14. Idempotent Execute** | Execute plan twice | N/A | `COMMITTED` | `NO_OP` | Cached | No | Preserved | Preserved |
| **15. Concurrency Lock** | 2 concurrent executes | N/A | Blocked 2nd | Mutex locked | N/A | No | Preserved | Preserved |

---

## 4. Invariant Checklist

- [x] **Zero Mocking Invariant**: In integration tests, `ProductionPlanner`, `ProductionPolicyEngine`, `ProductionGraph`, `DecisionMemory`, and `ProductionExecutor` run real application logic.
- [x] **Non-Destructive History Invariant**: Rollback never deletes prior nodes or decisions; it appends `NodeType.ROLLBACK` and links it causally to the failed verification.
- [x] **Candidate-Only Memory Invariant**: Historical decisions retrieved from memory cannot bypass current context observation, candidate generation, or policy evaluation.
- [x] **Scoped Fingerprint Invariant**: Unrelated changes (e.g. changing track "Pad") do not invalidate a plan scoped to "Master".
- [x] **Transactional Atomicity Invariant**: No modification persists if execution or verification fails; exact pre-execution session fingerprint is restored.

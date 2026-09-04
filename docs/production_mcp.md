# PIE Production Governance Layer — MCP Surface Integration (Documento 13)

## 1. Overview & Architectural Principle

This document specifies the Model Context Protocol (MCP) surface for the Production Governance Layer (Hito 1, Document 13).

### Separation of Concerns
- **`server.py`**: Acts strictly as a thin transport and serialization adapter. It performs input argument parsing, request-id propagation, and output formatting. **Zero DSP logic and zero governance decision-making** reside in `server.py`.
- **`engine/production/boundary.py` (`ProductionAPIBoundary`)**: Manages the singleton instance and coordinates between `ProductionPlanner`, `ProductionPolicyEngine`, `ProductionContext`, `ProductionGraph`, `DecisionMemory`, `ProductionExecutor`, and `RollbackEngine`.

```
                  MCP CLIENT / LLM
                         │
                         ▼
                ┌─────────────────┐
                │    server.py    │
                │   MCP Adapter   │
                └────────┬────────┘
                         │
                         ▼
                ┌─────────────────┐
                │ Production API  │
                │   Boundary      │
                └────────┬────────┘
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
      Planner         Policies       Executor
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                Production Context
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
       SessionShadowGraph      ProductionGraph
                                    │
                                    ▼
                              DecisionMemory
```

---

## 2. The 9 Canonical MCP Production Tools

All tools adhere to the standard envelope:
```json
{
  "success": true,
  "status": "COMMITTED",
  "data": {},
  "errors": [],
  "warnings": [],
  "trace": {
    "request_id": "req_...",
    "timestamp": "2026-09-04T...",
    "engine_version": "PIE-1.0"
  }
}
```

### Tool Reference

| Tool Name | Parameters | Mutates Live? | Description |
| :--- | :--- | :---: | :--- |
| **`production_status`** | None | **No** | Returns operational status of governance components, active transactions, pending plans, and last decision. |
| **`production_plan`** | `intent`, `domain`, `target` (opt), `profile` (opt) | **No** | Transforms musical intent into a structured candidate plan without physical execution (`execution_allowed=False`). |
| **`production_validate`** | `plan_id` | **No** | Full pre-execution validation: freshness check, object locks, transaction availability, and policy conformance. |
| **`production_execute`** | `plan_id`, `auto_rollback` (default=True) | **YES** | **The only tool that mutates Ableton Live.** Executes strictly inside an isolated transaction with post-measurement verification. |
| **`production_explain`** | `decision_id` | **No** | Reconstructs complete causal lineage, cleanly categorizing FACT, MEASUREMENT, INFERENCE, DECISION, ACTION, RESULT. |
| **`production_history`** | `limit` (default=20, max=100), `domain` (opt) | **No** | Chronological reverse history of committed decisions (`timestamp DESC, decision_id ASC`). |
| **`production_graph`** | `format` ("summary" \| "dag") | **No** | Inspects graph statistics (`summary`) or exports the acyclic causal DAG (`dag`). |
| **`production_rollback`** | `decision_id_or_transaction` | **YES** (via Tx) | Atomically reverts a past action/transaction without erasing history (appends new `ROLLBACK_*` nodes). |
| **`production_memory_search`**| `query`, `context` (`project_id` required) | **No** | Retrieves similar historical decisions as **evidence only**. Invariant: `evidence_only=True, execute=False`. |

---

## 3. Strict Safety Invariants

1. **Non-Mutating Planning**: `production_plan()` generates candidates and evaluates policies in a sandbox; it never alters Ableton Live parameters or track structures.
2. **Mandatory Pre-Validation**: `production_execute()` strictly rejects any plan that has not successfully passed `production_validate()` or whose session fingerprint has become stale.
3. **Transactional Boundary**: Even `production_execute()` and `production_rollback()` cannot touch Ableton Live directly; all physical mutations are mediated by `TransactionManager` inside an open transaction.
4. **Automatic Regression Rollback**: If post-execution verification detects an acoustic regression (e.g. True Peak > -0.3 dBTP), `auto_rollback=True` triggers an immediate atomic reversal, returning `status="ROLLED_BACK"`.
5. **Execution Idempotency & Concurrency Exclusion**: Re-executing a committed plan returns `ALREADY_EXECUTED` without duplicate operations. Concurrent execution attempts on the same plan are blocked with `CONCURRENT_EXECUTION`.
6. **Zero Traceback Leakage**: Internal Python exceptions are caught, logged internally, and transformed into structured error payloads with stable error codes (`INVALID_ARGUMENT`, `STALE_PLAN`, `POLICY_REJECTED`, `PLAN_NOT_FOUND`, etc.).

---

## 4. Verification Suite

Tested comprehensively in `tests/test_production_mcp.py` (20 / 20 PASS):
- **Test 1 & 2**: Exact 9 tool existence on `server.py` FastMCP registry and `ProductionAPIBoundary`.
- **Test 3**: `production_status()` zero-mutation verification.
- **Test 4**: `production_plan()` creation without execution.
- **Test 5**: Domain validation (rejects invalid domains with `INVALID_ARGUMENT`).
- **Test 6**: `production_validate()` rejects non-existent plans (`PLAN_NOT_FOUND`).
- **Test 7**: Stale plan detection on relevant track modifications (`STALE_PLAN`).
- **Test 8**: `production_execute()` enforces pre-validation requirement.
- **Test 9 & 10**: Transactional execution and idempotency (`ALREADY_EXECUTED`).
- **Test 11**: Critical policy guardrail blocks execution (`POLICY_REJECTED`).
- **Test 12**: True Peak regression triggers auto-rollback (`status="ROLLED_BACK"`).
- **Test 13**: `production_explain()` causal chain and evidence typing.
- **Test 14**: `production_history()` limit, ordering, and domain filtering.
- **Test 15 & 16**: `production_graph()` summary vs DAG export.
- **Test 17**: Non-destructive `production_rollback()`.
- **Test 18**: `production_memory_search()` evidence-only invariant (`execute=False`).
- **Test 19 & 20**: Structured error mapping without traceback leakage.
- **Test 21**: Plan isolation does not alter session state.
- **Test 22**: Irrelevant session changes preserve plan validity.
- **Test 23**: Server restart reload recovery from `state/production/`.
- **Test 24**: 10-iteration determinism check.

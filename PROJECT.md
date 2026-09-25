# Project: Universal Genre-Family FX Catalog & Phase 5 Per-Device Gate

## Architecture
- **Genre-Family Aware FX Catalog (`engine/fx/`):**
  - Defines `GenreFamily(str, Enum)` with 4 families:
    1. `URBANA_MODERNA`: Trap, Drill, Boom Bap, Reggaeton (sharp transients, Drum Buss crunch, Glue compression, mono 808 sub, hard saturation).
    2. `ELECTRONICA_CLUB`: House, Techno, EDM, Drum & Bass (sidechain ducking, steep cut filters, synchronized delays, OTT, bright halls).
    3. `ORGANICA_ACUSTICA`: Neo-Soul, R&B, Flamenco, Indie/Pop (transparent optical compression, analog Chow Tape warmth, warm BBD chorus, broad non-invasive EQ, no OTT).
    4. `ESPACIAL_CINEMATICA`: Ambient, Drone, Downtempo (deep stereo diffusion with ValhallaSupermassive across 22 modes, infinite reverb clouds, slow modulation, granular Nimbus).
  - `resolve_genre_family(genre, bpm)`: Robust normalization and classification of any genre string or tempo into the canonical sound family.
  - Reusable device factories: `make_eq_eight`, `make_glue_compressor`, `make_saturator`, `make_drum_buss`, `make_compressor`, `make_utility`, `make_ott`, `make_valhalla_supermassive`, `make_valhalla_vintage_verb`, `make_surge_xt_effects`, `make_chorus_ensemble`, `make_delay`.
  - `UniversalGenreFamilyFXCatalog`: Maps each `GenreFamily` to its full role-specific device chains and parameter blueprints.
  - `ROLE_INSERT_EFFECTS`: Kept backward-compatible as the default dictionary aliasing `UniversalGenreFamilyFXCatalog.CATALOG[GenreFamily.URBANA_MODERNA]`.

- **Physical LOM Device Execution Verifier (`engine/core/device_execution_verifier.py`):**
  - `resolve_lom_parameter_name`: Canonical mapping and aliases for:
    - `ValhallaSupermassive`: `Mix`, `Mode`, `Delay Sync`, `Delay Note`, `Delay (ms)`, `Delay Warp`, `Feedback`, `Density`, `Width`, `Low Cut`, `High Cut`, `Mod Rate`, `Mod Depth`.
    - `ValhallaVintageVerb`: `Mix`, `Decay`, `Pre-delay`, `Mode`, `Color Mode`, `Size`, `Attack`, `Bass Multiply`, `Low Cut`, `High Cut`, `Mod Rate`, `Mod Depth`.
    - `Surge XT Effects`: Canonical slot mapping (`A Insert FX 1 Type`, `A Insert FX 1 Param 1..12`).
    - Live 12 stock devices: `Drum Buss` (Drive, Crunch, Transients, Boom, Output), `Compressor` (Threshold, Ratio, Attack, Release), `Chorus-Ensemble`, `Delay`, `Utility` (Gain, Stereo Width, Bass Mono, Bass Freq), and bugfix for `Saturator` (`base` kept as `Base`).

- **Phase 5 Mandatory Per-Device Gate (`engine/production/copilot/phases/phase_5_insert_effects.py`):**
  - Removal of all bulk approval shortcuts: `"cadena express"`, `"lote"`, `"toda la pista"`, and whole-track bypass `"cadena:"`.
  - Sequential pointer progression: `current_fx_dev_ptr` and `current_fx_track_ptr`.
  - Deliberate parameter calibration requirement: explicit key-value parameters or device-specific valid input required. Uncalibrated generic advances (`"siguiente"`, `"aprobar todo"`, empty input) rejected with `STATUS: EFFECT_CALIBRATION_REQUIRED`.
  - Controlled track transition: `current_fx_track_ptr` only increments when `dev_ptr == len(fx_list) - 1`. Exactly $N$ turns for $N$ insert effects across each track.
  - Session data recording: chosen parameters registered in `track["insert_effects"]` and `session.data["insert_effects"]`.

- **Opaque-Box E2E Testing Track (`tests/test_phase_5_insert_effects.py`):**
  - Systematic 4-tier test suite verifying requirement satisfaction, boundary cases, cross-family differentiation, per-device pointer navigation, and zero regressions.

---

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | `GenreFamily` Enum & Resolver | 4 sound families (Urbana, Club, Orgánica, Espacial) with `resolve_genre_family` | M1 | R1 |
| 2 | Device Parameter Factories | Deduplicated modular helpers creating device dicts with Live 12 parameters | M1 | R1 |
| 3 | Universal Genre-Family FX Catalog | Role chains specialized across all 4 families with acoustic justification | M1 | R1 |
| 4 | Backward-Compatible Catalog API | `ROLE_INSERT_EFFECTS` alias ensuring legacy tests continue to pass | M1 | R1 |
| 5 | LOM Mapping: ValhallaSupermassive | Canonical aliases for all 13 Supermassive parameters in Live 12 LOM | M2 | R3 |
| 6 | LOM Mapping: ValhallaVintageVerb & Surge XT | Canonical aliases for VintageVerb & Surge XT slot parameters | M2 | R3 |
| 7 | LOM Mapping: Live 12 Stock Devices & Saturator Fix | Mappings for Drum Buss, Compressor, Chorus, Delay, Utility, fix Saturator Base | M2 | R3 |
| 8 | Bulk Approval Shortcut Elimination | Remove Cadena Express and batch custom chain shortcuts in Phase 5 | M3 | R2 |
| 9 | Per-Device Pointer Navigation | Sequential `current_fx_dev_ptr` step-by-step traversal across `fx_list` | M3 | R2 |
| 10 | Deliberate Parameter Validation & Lock | Reject uncalibrated input with `STATUS: EFFECT_CALIBRATION_REQUIRED` | M3 | R2 |
| 11 | Controlled Track Transition | Advance `current_fx_track_ptr` only after final device; exactly $N$ turns per track | M3 | R2 |
| 12 | Session State Serialization | Record calibrated parameters per device in `track["insert_effects"]` | M3 | R2 |
| 13 | E2E Testing Infra & Suite | Category-partition test suite in `tests/test_phase_5_insert_effects.py` | M4 | AC |
| 14 | Legacy Test Hardening | Update `test_anti_token_shortcut_guards.py` to assert Cadena Express rejection | M4 | AC |
| 15 | Full Regression Verification | 100% pass across all pytest suites with adversarial review & forensic audit | M5 | AC |

---

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Universal Genre-Family FX Catalog | `engine/fx/role_fx_catalog.py`, `GenreFamily`, `resolve_genre_family`, `UniversalGenreFamilyFXCatalog` | none | DONE |
| M2 | LOM Device Execution Verifier | `engine/core/device_execution_verifier.py`, mappings for Supermassive, VintageVerb, Surge, Stock devices, Saturator bugfix | none | DONE |
| M3 | Phase 5 Mandatory Per-Device Gate | `engine/production/copilot/phases/phase_5_insert_effects.py`, eliminate shortcuts, enforce per-device calibration, `STATUS: EFFECT_CALIBRATION_REQUIRED` | M1, M2 | DONE |
| M4 | E2E Testing Suite & Legacy Adaptation | `tests/test_phase_5_insert_effects.py` (Tiers 1-4), update `tests/test_anti_token_shortcut_guards.py` | M1, M2, M3 | DONE |
| M5 | Final E2E Verification & Forensic Audit | Run full pytest suite, adversarial coverage audit, forensic integrity validation | M4 | DONE |

---

## Interface Contracts
### `UniversalGenreFamilyFXCatalog` ↔ `Phase5InsertEffectsHandler`
- `UniversalGenreFamilyFXCatalog.get_fx_chain_for_role(role: str, genre: Optional[str] = None) -> List[Dict[str, Any]]`:
  - Returns list of effect dictionaries with keys: `"name"`, `"type"`, `"acoustic_purpose"`, `"params"`.
  - When `genre` is omitted or unrecognized, defaults gracefully to `GenreFamily.URBANA_MODERNA`.
- `ROLE_INSERT_EFFECTS`:
  - Retained as `Dict[str, List[Dict[str, Any]]]` pointing to `UniversalGenreFamilyFXCatalog.CATALOG[GenreFamily.URBANA_MODERNA]`.

### `DeviceExecutionVerifier` ↔ Live 12 Socket / LOM
- `resolve_lom_parameter_name(device_name: str, param_identifier: str, available_params: Optional[Dict[str, Any]] = None) -> str`:
  - Case-insensitive, punctuation-tolerant mapping of plugin & stock parameters to exact Live Object Model names.
  - Zero unmapped critical parameters for `ValhallaSupermassive`, `Surge XT Effects`, `ValhallaVintageVerb`, `Drum Buss`, `Compressor`, `Saturator`, `Utility`.

### `Phase5InsertEffectsHandler` State Transitions
- State variables in `session.data`:
  - `current_fx_track_ptr`: integer index in `session.data["tracks"]`.
  - `current_fx_dev_ptr`: integer index in `fx_list` for active track.
  - `tracks[t_ptr]["insert_effects"]`: List of dicts `{"name": str, "device_index": int, "bypass": bool, "parameters": dict}`.
- Interaction protocol:
  - Input with missing/generic parameters $\rightarrow$ returns `STATUS: EFFECT_CALIBRATION_REQUIRED`, pointers unchanged.
  - Valid calibration input $\rightarrow$ applies parameters, increments `current_fx_dev_ptr += 1`.
  - When `current_fx_dev_ptr >= len(fx_list)` $\rightarrow$ resets `current_fx_dev_ptr = 0`, increments `current_fx_track_ptr += 1`.
  - When `current_fx_track_ptr >= len(tracks)` $\rightarrow$ transitions to `PHASE_6_COMPOSITION`.

---

## Code Layout
- `engine/fx/role_fx_catalog.py`: `GenreFamily`, `resolve_genre_family`, device factories, `UniversalGenreFamilyFXCatalog`, `ROLE_INSERT_EFFECTS`.
- `engine/core/device_execution_verifier.py`: `DeviceExecutionVerifier` LOM parameter resolvers.
- `engine/production/copilot/phases/phase_5_insert_effects.py`: `Phase5InsertEffectsHandler` per-device gate.
- `tests/test_phase_5_insert_effects.py`: Dedicated E2E tests for R1, R2, and R3.
- `tests/test_anti_token_shortcut_guards.py`: Adapted legacy test ensuring Cadena Express rejection.

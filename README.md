# Ableton Production Intelligence Engine (PIE)

> **Autonomous AI-Assisted Music Production, Mixing, and Mastering Middleware for Ableton Live 12 Suite.**
> Powered by Model Context Protocol (FastMCP) with 165 specialized tools and 80 automated unit tests (100% pass rate).

---

## Core Philosophy & Design Axioms

- **"The LLM decides musical intent; the Engine decides how to execute it; Ableton Live executes."**
- **"The Arrangement Engine does not copy clips; it reasons about energy, roles, phrases, transitions, and narrative evolution."**
- **"Separation of Mix vs. Master: Low-end mud, kick/bass masking, and headroom defects must be resolved in the mix, NEVER patched in mastering."**
- **"Principle of Minimum Intervention: DO NOTHING is a valid and preferred outcome if the session already meets target acoustic standards."**
- **"No Fake DSP and No Fake Success: All spectral and perceptual measurements use real DSP algorithms (ITU-R BS.1770-4 LUFS, True Peak 4x oversampling, FFT energy integration). Never invent metrics or report successful device creation when slots are empty."**

---

## Architecture Overview (Fases 1 to 6)

```
                       ┌─────────────────────────────────────┐
                       │        LLM Cognitive Client         │
                       │    (Antigravity / Claude Desktop)   │
                       └──────────────────┬──────────────────┘
                                          │ FastMCP (165 Tools)
                                          ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │                 Production Intelligence Engine (PIE)                  │
  ├───────────────────┬───────────────────┬────────────────────────────────┤
  │ Fase 1: Foundation│ Fase 2: Music     │ Fase 2.5: Instruments          │
  │ • Shadow Graph    │ • Roman Numerals  │ • Sound Profiles               │
  │ • ACID Transact.  │ • Voice Leading   │ • Drum Rack Pad Populator      │
  │ • State Snapshots │ • Grooves/Motifs  │ • Native Browser Resolution    │
  ├───────────────────┼───────────────────┼────────────────────────────────┤
  │ Fase 3: Arrange   │ Fase 4: Sound     │ Fase 5: Digital Ear / Mix      │
  │ • Energy Curves   │ • Macro Controls  │ • LUFS / True Peak / Masking   │
  │ • Transitions     │ • Chain Templates │ • Frequency Conflict Graph     │
  │ • Drop Differ.    │ • Native Racks    │ • Closed-Loop Corrections      │
  ├───────────────────┴───────────────────┴────────────────────────────────┤
  │ Fase 6: Mastering Engine + Reference Matching + Final QC              │
  │ • Delivery Targets: STREAMING (-14 LUFS), CLUB (-7.5), DIGITAL, VIDEO  │
  │ • True Peak Brickwall Limiting (Max GR <= 2.5 dB)                     │
  │ • Conservative Master EQ (Max +-1.0 dB across top 2 bands)            │
  │ • Master Glue Compressor & Subtle Analog Warmth                       │
  │ • 6-Condition Translation Matrix (Mono, Phone, 40 phon, 90 phon)       │
  │ • Commercial Reference Matcher with Flawed Reference Protection        │
  │ • Final QC: DC Offset, Digital Dropouts, Clipping, Imbalance           │
  │ • Versioned WAV Export (v001, v002) with Deterministic SHA-256         │
  │ • Autonomous Unified Pipeline: master_project()                       │
  └──────────────────────────────────┬─────────────────────────────────────┘
                                     │ TCP Socket (Port 9877)
                                     ▼
                       ┌─────────────────────────────────────┐
                       │     Ableton Live 12 Suite Engine    │
                       │     (MIDI Remote Script: AbletonMCP)│
                       └─────────────────────────────────────┘
```

---

## Tool Catalog Summary (165 FastMCP Tools)

| Category | Tool Count | Core Capabilities |
| :--- | :---: | :--- |
| **Foundation (Fase 1)** | 29 | Session graph, inspect, resolve, diff, transactions, WAL commit/rollback, snapshots |
| **Music Engine (Fase 2)** | 12 | Harmony, roman numeral parsing, voice leading, rhythm grids, swing, humanize, motifs |
| **Instrument Engine (Fase 2.5)**| 10 | Instrument inspect, resolve, sound profile mapping, drum rack populate, verify |
| **Arrangement (Fase 3)** | 13 | Energy curves, section structures, transitions, risers, drop differentiation, linter |
| **Sound Design (Fase 4)** | 17 | Tonal sound intent, device chain presets, macro mapping, drum bus, sound profiles |
| **Digital Ear / Mix (Fase 5)** | 21 | Audio capture, ITU-R LUFS, True Peak, masking detector, conflict graph, linter, corrections |
| **Mastering & QC (Fase 6)** | 14 | Master readiness, chain builder, preview, apply, evaluate, rollback, reference match, translation test, QC, export, report |
| **Ableton Native / Legacy** | 49 | Clips, tracks, notes, devices, mixer faders, arrangement timeline, browser navigation |
| **TOTAL** | **165** | **Complete end-to-end music production, mix, and master capability** |

---

## Verification & Test Suite

All 80 comprehensive unit and acceptance tests execute offline with **100% pass rate**:

```bash
python -m unittest discover tests
# Ran 80 tests in 38.070s — OK
```

- **Fase 1:** Transaction atomicity, rollback, state shadow resolution
- **Fase 2:** Voice leading distance minimization, polyphony constraints, motif transformations
- **Fase 3:** Energy continuity, drop differentiation, transition generation
- **Fase 4:** Preset resolution, device chain building, macro assignment
- **Fase 5:** Kick/sub conflict detection, mono collapse, causal diagnostics, regression rollback
- **Fase 6:** DO_NOTHING principle, low-end rejection as MIX_PROBLEM, limiter guardrails (<=2.5 dB), clipping QC fail, 6-condition translation simulation, SHA-256 versioned export, autonomous master pipeline

---

## Setup & Quickstart

1. **Install Remote Script:**
   Ensure `AbletonMCP` is installed in:
   `D:\Programs\Ableton\Live 12 Suite\Resources\MIDI Remote Scripts\AbletonMCP`
   In Ableton Live: `Preferences > Link, Tempo & MIDI > Control Surface = AbletonMCP`.

2. **Configure MCP Server (`mcp_config.json`):**
   ```json
   {
     "mcpServers": {
       "AbletonMCP": {
         "command": "C:/Python314/python.exe",
         "args": ["-u", "-m", "MCP_Server.server"]
       }
     }
   }
   ```

3. **Autonomous Mastering Command:**
   ```json
   {
     "tool": "master_project",
     "args": {
       "delivery_target": "STREAMING",
       "mode": "BALANCED",
       "auto_apply": true
     }
   }
   ```

# Ableton Production Intelligence Engine (PIE) — API & Capabilities Matrix

> **Author**: Ableton Production Intelligence Engine Team  
> **Architecture**: FastMCP + Python 3.14 + Ableton Live 12 Suite Remote Script (Port 9877)  
> **Status**: Verified & Consolidated on Drive `F:\` (`F:\Dev\AbletonEngine`)

---

## 1. FastMCP Tool Capabilities Matrix

| Domain / Category | Tool Name | Primary Parameters | Mode / Permissions | Verification Status |
|---|---|---|---|---|
| **Session & Tracks** | `get_session_info` | *none* | Read-Only | Verified Live |
| | `get_track_info` | `track_index` | Read-Only | Verified Live |
| | `create_midi_track` | `index` | Read/Write | Verified Live |
| | `set_track_name` | `track_index`, `name` | Read/Write | Verified Live |
| | `set_tempo` | `tempo` | Read/Write | Verified Live |
| | `set_track_volume` | `track_index`, `volume` | Read/Write | Verified Live |
| | `set_track_panning` | `track_index`, `panning` | Read/Write | Verified Live |
| | `set_track_mute` | `track_index`, `mute` | Read/Write | Verified Live |
| | `set_track_solo` | `track_index`, `solo` | Read/Write | Verified Live |
| **Arrangement** | `switch_to_arrangement_view` | *none* | Read/Write | Verified Live |
| | `duplicate_to_arrangement` | `track_index`, `clip_index`, `destination_time_beats` | Read/Write | Verified Live |
| | `create_cue_point` | `name`, `time_beats` | Read/Write | Verified Live |
| | `get_cue_points` | *none* | Read-Only | Verified Live |
| | `arrangement_generate` | `genre`, `target_bars`, `tempo` | Preview/Write | Verified Live |
| | `arrangement_apply_transition` | `track_index_or_id`, `transition_type`, `start_bar`, `duration_bars`, `min_val`, `max_val` | Preview/Write | Verified Live |
| | `arrangement_add_energy_curve` | `track_index_or_id`, `target_parameter`, `min_val`, `max_val` | Preview/Write | Verified Live |
| **Composition & MIDI** | `music_generate_harmony` | `key`, `scale`, `genre`, `bars`, `complexity` | Pure DSP/MIDI | Verified Live |
| | `music_generate_bass` | `key`, `scale`, `genre`, `bars`, `follow_kick` | Pure DSP/MIDI | Verified Live |
| | `music_generate_drums` | `genre`, `bars`, `swing`, `complexity` | Pure DSP/MIDI | Verified Live |
| | `music_generate_melody` | `key`, `scale`, `genre`, `bars` | Pure DSP/MIDI | Verified Live |
| | `add_notes_to_clip` | `track_index`, `clip_index`, `notes`, `mode` | Read/Write | Verified Live |
| **Instruments & Presets**| `preset_list_available` | `role`, `genre`, `query` | Read-Only | Verified Live |
| | `instrument_load_preset` | `track_index_or_id`, `preset_name_or_role`, `genre`, `preview` | Preview/Write | Verified Live |
| | `instrument_resolve` | `role`, `sound_profile` | Pure Resolver | Verified Live |
| | `load_instrument_or_effect` | `track_index`, `uri` | Read/Write | Verified Live |
| **Drum Racks** | `drum_rack_inspect` | `track_index_or_id` | Read-Only | Verified Live |
| | `drum_rack_populate` | `track_index`, `style`, `kit`, `preview`, `seed` | Preview/Write | Verified Live |
| | `drum_rack_verify` | `track_index_or_id` | Read-Only | Verified Live |
| | `get_drum_rack_pads` | `track_index`, `device_index` | Read-Only | Verified Live |
| | `set_drum_pad_parameter` | `track_index`, `pad_note`, `device_index`, `parameter`, `value` | Read/Write | Verified Live |
| **Mix & Forensics** | `mix_analyze` | `file_path_or_target`, `section`, `genre` | Pure DSP | Verified Live |
| | `mix_lint` | `track_index_or_id` | Read-Only | Verified Live |
| | `mix_check_headroom` | *none* | Read-Only | Verified Live |
| | `mix_check_mono` | *none* | Read-Only | Verified Live |
| | `audio_listen_live` | `duration_seconds`, `port`, `simulate_if_silent` | Real-time Acoustic | Verified Live |
| **Mastering** | `master_readiness` | *none* | Read-Only | Verified Live |
| | `master_create_chain` | `target`, `ceiling_dbtp`, `target_lufs` | Preview/Write | Verified Live |
| | `master_apply` | `preset_name` | Read/Write | Verified Live |
| | `master_evaluate` | *none* | Read-Only | Verified Live |

---

## 2. Safety & Verification Guarantees

1. **Deterministic Resolution**: All preset and sound resolvers map musical intent to immutable, verified Native Live 12 URIs without hallucination.
2. **Transaction Rollback**: High-level commands support staging and rollback (`transaction_begin`, `transaction_commit`, `transaction_rollback`).
3. **Strict Range Validation**: Parameter modifications check parameter boundaries (`[min, max]`) before sending to Ableton to prevent clamping errors or crashes.
4. **Read-After-Write Verification**: When writing clips, notes, or parameters, the engine automatically verifies the modification via Live's API.

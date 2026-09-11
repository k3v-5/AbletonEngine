# Documentación Técnica Detallada del Proyecto (PIE)

Este documento contiene un índice profundo y documentación a nivel de código de todos los módulos Python en el proyecto.

## Módulo: `engine/config.py`

### Clases

#### `EngineConfig`
- **Métodos:**
  - `ensure_directories`: Sin documentación

---

## Módulo: `engine/errors.py`

### Clases

#### `ErrorCode`

#### `EngineError`
Base exception class for all Engine operations with structured error payload

- **Métodos:**
  - `__init__`: Sin documentación
  - `to_dict`: Sin documentación
  - `__str__`: Sin documentación

#### `ObjectNotFoundError`
- **Métodos:**
  - `__init__`: Sin documentación

#### `AmbiguousObjectError`
- **Métodos:**
  - `__init__`: Sin documentación

#### `ObjectLockedError`
- **Métodos:**
  - `__init__`: Sin documentación

#### `SessionDesynchronizedError`
- **Métodos:**
  - `__init__`: Sin documentación

#### `TransactionConflictError`
- **Métodos:**
  - `__init__`: Sin documentación

#### `TransactionFailedError`
- **Métodos:**
  - `__init__`: Sin documentación

#### `RollbackFailedError`
- **Métodos:**
  - `__init__`: Sin documentación

#### `InvalidParameterError`
- **Métodos:**
  - `__init__`: Sin documentación

#### `InvalidRelationshipError`
- **Métodos:**
  - `__init__`: Sin documentación

#### `SnapshotNotFoundError`
- **Métodos:**
  - `__init__`: Sin documentación

#### `UnsupportedOperationError`
- **Métodos:**
  - `__init__`: Sin documentación

#### `AbletonConnectionError`
- **Métodos:**
  - `__init__`: Sin documentación

#### `RemoteScriptError`
- **Métodos:**
  - `__init__`: Sin documentación

#### `TransactionLimitExceededError`
- **Métodos:**
  - `__init__`: Sin documentación

---

## Módulo: `engine/music/song_state.py`

**Descripción del Módulo:**
```text
engine/music/song_state.py
Authoritative Intermediate Musical Representation (Musical OS Layer).

Provides the unified schema that decouples high-level creative AI intent
from low-level Ableton DAW implementation:
- Nivel 1: Estado Técnico (Pistas, Plugins, Racks, Automatizaciones en Live).
- Nivel 2: Estado Musical (SongState: Tempo, Armonía, Rango Melódico, Densidad, Energía).
- Nivel 3: Estado Narrativo & Prosódico (Mood, Tensión, LyricBlueprint, Acentuación).
```

### Clases

#### `ProsodicConstraint`
Constraints imposed by a melodic line onto prospective lyric text.

- **Métodos:**
  - `to_dict`: Sin documentación

#### `LyricBlueprint`
Complete lyric generation specification for a musical section.

- **Métodos:**
  - `to_dict`: Sin documentación

#### `MelodicState`
Melodic characteristics of a musical section.

- **Métodos:**
  - `to_dict`: Sin documentación

#### `MusicalSection`
High-level semantic definition of a song section.

- **Métodos:**
  - `to_dict`: Sin documentación

#### `SongState`
Authoritative Intermediate Representation of the Complete Song.
Acts as the source of truth between LLM and Ableton Live.

- **Métodos:**
  - `to_dict`: Sin documentación
  - `to_llm_prompt_summary`: Formats a clean, token-efficient summary for LLM context injection.

---

## Módulo: `engine/music/mutation_engine.py`

**Descripción del Módulo:**
```text
Engine Music Mutation Engine:
Transforms barebone library seeds into unique, expressive, and humanized patterns.
Enforces non-linear micro-timing, velocity contours, and bar turnaround variations.
```

### Clases

#### `MusicMutationEngine`
Applies musical mutations to raw library seeds to guarantee organic uniqueness.

- **Métodos:**
  - `mutate_drum_pattern`: Mutates a drum pattern: shifts micro-timing, modulates velocity curves,
  - `mutate_bass_or_melody_pattern`: Mutates a melodic or bassline seed: velocity contours, legato articulation adjustments,

---

## Módulo: `engine/music/analyzer.py`

**Descripción del Módulo:**
```text
engine/music/analyzer.py
MusicAnalyzer: Analyzes Live session tracks, cue points, and MIDI clips
to abstract a complete intermediate SongState representation.
```

### Clases

#### `MusicAnalyzer`
Extracts high-level musical abstractions from Ableton Live project data.

- **Métodos:**
  - `analyze_melody_clip`: Analyzes a list of MIDI notes to extract range, contour, and density.
  - `extract_prosodic_constraints`: Groups melodic notes into musical phrases separated by rests (> 0.75 beats)
  - `analyze_session`: Builds a full SongState by querying session tempo, locators, and tracks from Live.

### Funciones Globales

- `pitch_to_name`: Converts MIDI pitch number (e.g. 60) to scientific pitch name (e.g. 'C4').

---

## Módulo: `engine/music/generators.py`

### Funciones Globales

- `generate_bassline`: Generates a genre-appropriate bassline (rolling, offbeat, acid, sustained)
- `generate_chords`: Generates fully voiced chords with smooth voice leading and rhythmic humanization.
- `generate_melody`: Generates a melodic lead motif with phrasing, contour shaping, and rhythmic syncopation.

---

## Módulo: `engine/music/models.py`

### Clases

#### `NoteEvent`
Internal high-fidelity representation of a musical note event

- **Métodos:**
  - `__post_init__`: Sin documentación
  - `to_dict`: Sin documentación
  - `from_pitch_and_time`: Sin documentación

#### `Chord`
Harmonic chord representation with root, quality, extensions, and bass inversion

- **Métodos:**
  - `to_dict`: Sin documentación

#### `RhythmPattern`
Rhythmic pattern grid representation


#### `Motif`
Structural invariant melodic motif

- **Métodos:**
  - `to_dict`: Sin documentación

#### `PartFingerprint`
Musical statistical fingerprint for similarity comparison


---

## Módulo: `engine/music/intent.py`

### Clases

#### `MusicalIntent`
High-level semantic musical intent requested by the LLM / Creative Director

- **Métodos:**
  - `to_dict`: Sin documentación
  - `from_dict`: Sin documentación

---

## Módulo: `engine/music/bass/intelligent_808.py`

**Descripción del Módulo:**
```text
Intelligent 808 Bass Engine:
Composes interlocking, section-dynamic 808 sub-basslines.
Features kick-groove interlocking, chromatic leading-tone approaches,
octave leaps, authentic portamento slide envelopes, and pre-drop vacuums.
```

### Clases

#### `Intelligent808BassEngine`
Composes performance-grade 808 basslines across 96 bars.

- **Métodos:**
  - `get_bass_pitch_for_root`: Calculates root MIDI pitch clamped strictly in sub-bass range (MIDI 24 - 44).
  - `generate_808_bassline`: Generates complete 96-bar 808 bassline aligned with chords and section energy.

---

## Módulo: `engine/music/bass/glide.py`

**Descripción del Módulo:**
```text
Bass Glide & 808 Pitch-Bend Engine:
Generates authentic drill/trap 808 slides, octave glides, pitch drop-offs,
and legato overlap articulations for monophonic sub-bass synths and samplers.
```

### Clases

#### `SlideMode`

#### `BassGlideEngine`
Computes pitch bend curves and legato slide notes for 808 and sub-bass tracks.

- **Métodos:**
  - `generate_808_slides`: Takes bass notes and generates:

---

## Módulo: `engine/music/humanizer/engine.py`

### Funciones Globales

- `humanize_notes`: Applies correlated physiological humanization to NoteEvents:
- `apply_velocity_curve`: Applies musical velocity contours (linear, exponential, accented, wave, phrase)

---

## Módulo: `engine/music/theory/notes.py`

### Funciones Globales

- `parse_note_string`: Parse a note string like 'F3', 'C#4', 'Bb2' into (pitch_class, octave)
- `note_to_midi`: Convert a note string like 'C4', 'A0', 'F#2', 'Bb3' into a standard MIDI integer (0-127)
- `midi_to_note`: Convert a MIDI integer (0-127) to note name with octave, e.g. 60 -> 'C4', 42 -> 'F#2'
- `normalize_pitch_class`: Normalize any root string like 'F', 'Eb', 'c#' into pitch class 0-11
- `pitch_class_to_name`: Convert a pitch class 0-11 to note name string
- `get_enharmonic`: Return common enharmonic equivalent, e.g. C# -> Db, Eb -> D#

---

## Módulo: `engine/music/theory/scales.py`

### Funciones Globales

- `normalize_scale_name`: Sin documentación
- `get_scale_intervals`: Sin documentación
- `get_scale_pitch_classes`: Returns the list of pitch classes (0-11) belonging to the key and scale
- `get_scale_notes`: Returns note names of the scale, e.g. 'F', 'G', 'Ab', 'Bb', 'C', 'Db', 'Eb'
- `scale_degree_to_midi`: Convert a 1-based scale degree (e.g. 1=tonic, 3=third, 5=fifth) to a MIDI pitch.
- `midi_to_scale_degree`: Finds the 1-based scale degree of a MIDI pitch, or returns None if outside scale
- `is_in_scale`: Sin documentación
- `snap_to_scale`: Diatonic pitch quantizer: snaps a chromatic MIDI pitch to the closest note in the scale

---

## Módulo: `engine/music/validation/repair.py`

### Funciones Globales

- `repair_notes`: Deterministically repairs musical constraint violations:

---

## Módulo: `engine/music/validation/constraints.py`

### Funciones Globales

- `validate_notes`: Validates NoteEvents against fundamental musical and physical production constraints.

---

## Módulo: `engine/music/melody/vocal_hook.py`

**Descripción del Módulo:**
```text
Vocal Hook Chop Engine:
Generates infectious, syncopated vocal chop hook motifs.
Aligned with active harmonic degrees and positioned dynamically across
Intro, Chorus, and Final Climax sections.
```

### Clases

#### `VocalHookChopEngine`
Composes rhythmic vocal chop hooks across 96 bars.

- **Métodos:**
  - `generate_2bar_hook_motif`: Generates a 2-bar (8 beats) infectious syncopated vocal chop motif.
  - `generate_full_song_vocal_hook`: Deploys the vocal chop hook into:

---

## Módulo: `engine/music/melody/topline.py`

**Descripción del Módulo:**
```text
Top-Line Melodic Engine:
Composes human-like Call-and-Response melodies with vocal respiration,
emotional melodic contours (arch, climax, cascade), and scale color degree emphasis.
```

### Clases

#### `TopLineMelodyEngine`
Composes conversational, singable top-line lead melodies across sections.

- **Métodos:**
  - `generate_8bar_phrase`: Generates an 8-bar (32 beats) structured Call-and-Response melodic statement:
  - `generate_full_song_melody`: Generates full-song melodic arrangement across active sections:

---

## Módulo: `engine/music/melody/counterpoint.py`

**Descripción del Módulo:**
```text
Counter-Melody & Polyphonic Modal Arpeggiator Engine:
Generates guide-tone counter-melodies in upper registers (C5-C7) on syncopated off-beats,
and mathematical polyphonic arpeggios (Up, Down, Converge, Ping-Pong) with dynamic humanization.
```

### Clases

#### `ArpMode`

#### `CounterpointEngine`
Intelligent guide-tone counter-melody and arpeggio composer.

- **Métodos:**
  - `extract_chord_pitches`: Calculates MIDI pitches for a chord.
  - `generate_guide_tone_counter_melody`: Generates soaring counter-melody notes focusing on 3rds and 7ths of chords,
  - `generate_modal_arpeggio`: Arpeggiates chord tones across the bar using the specified directional mode.
  - `apply_counterpoint`: Generates counter-melody or arpeggio and writes to Live clip.

---

## Módulo: `engine/music/voicing/profiles.py`

### Funciones Globales

- `apply_voicing_profile`: Transforms a Chord's raw pitches into a specific voicing style and register.

---

## Módulo: `engine/music/voicing/voice_leading.py`

### Funciones Globales

- `voice_leading_cost`: Cost function evaluating voice leading quality:
- `optimize_voice_leading`: Smooths a progression of Chords using a Voice Leading Solver that minimizes intervallic leaps.

---

## Módulo: `engine/music/variation/phrase_evolver.py`

**Descripción del Módulo:**
```text
Phrase Evolver Engine:
Implements formal musical phrase evolution (A -> A' -> B -> A'') across 16-bar and 32-bar sections.
Prevents static 4-bar looping by generating organic variations, tension departures, and climactic returns.
```

### Clases

#### `PhraseFunction`

#### `PhraseEvolver`
Evolves 4-bar clips across multi-phrase arrangement sections.

- **Métodos:**
  - `evolve_phrase`: Evolves a 4-bar motif based on its phrase function in the section.
  - `_apply_a_prime`: Subtle ornament: 1/32 rolls on hats, ghost note on snare, octave jump in bar 4.
  - `_apply_departure_b`: Departure B: Contrast, density reduction, syncopation shifts.
  - `_apply_climax_a_double_prime`: Climax A'': Full return with peak energy and pre-transition fill.

---

## Módulo: `engine/music/variation/engine.py`

### Funciones Globales

- `apply_variation`: Applies musical variation to avoid static looping while preserving motif identity:

---

## Módulo: `engine/music/expression/mpe.py`

**Descripción del Módulo:**
```text
MIDI Polyphonic Expression (MPE) & Continuous Pitch Bend Engine:
Generates vocal scoops, organic vibrato curves, and aftertouch dynamics for expressive lead instruments.
```

### Clases

#### `PitchBendPoint`

#### `ExpressiveNoteModifier`
- **Métodos:**
  - `to_dict`: Sin documentación

#### `MPEExpressionEngine`
Calculates attack scoops, delayed vibrato oscillations, and MPE note specifications.

- **Métodos:**
  - `generate_pitch_bend_envelope_for_note`: Generates dense pitch bend curve points across a single sustained note:
  - `add_expression_to_melody`: Processes melodic line notes and attaches MPE specifications and global pitch bend timeline points.

---

## Módulo: `engine/music/motifs/memory.py`

### Clases

#### `MotifMemory`
Stores and catalogs musical motifs linked with roles, tracks, and sections

- **Métodos:**
  - `__init__`: Sin documentación
  - `store_motif`: Sin documentación
  - `get_motif`: Sin documentación
  - `list_motifs`: Sin documentación
  - `find_by_role`: Sin documentación
  - `find_by_section`: Sin documentación

---

## Módulo: `engine/music/motifs/motif.py`

### Funciones Globales

- `create_motif_from_notes`: Extracts invariant structural intervals, rhythmic durations and accents from a list of NoteEvents.

---

## Módulo: `engine/music/motifs/transformations.py`

### Funciones Globales

- `transform_motif`: Applies musical motif transformations:
- `realize_motif_as_notes`: Converts a relative Motif into concrete, scale-quantized NoteEvents

---

## Módulo: `engine/music/groove/profiles.py`

### Funciones Globales

- `apply_groove_to_notes`: Applies musical swing and timing offsets (push/pull) to a list of NoteEvents.

---

## Módulo: `engine/music/groove/humanizer.py`

**Descripción del Módulo:**
```text
Dynamic Groove Humanizer:
Orchestrates micro-timing displacement, MPC 60 / Dilla hardware swing, and Gaussian velocity shaping
across MIDI notes and Ableton Live clips.
```

### Clases

#### `DynamicGrooveHumanizer`
Master humanization engine unifying micro-timing, hardware swing, and expressive velocity.

- **Métodos:**
  - `humanize_notes`: Applies genre-specific micro-timing, MPC hardware swing, and velocity dynamics to NoteEvents.
  - `humanize_clip_dict_notes`: Helper to process standard Live dictionary notes format directly.

---

## Módulo: `engine/music/groove/pool.py`

**Descripción del Módulo:**
```text
Groove Pool & Micro-Timing Matcher.
- Subphase 4.1: Iconic hardware groove templates (Akai MPC 60, E-mu SP-1200, J Dilla Quintuplet, UKG 2-Step).
- Subphase 4.2: Groove DNA Extractor (measures delta offsets and velocity profile from existing clips).
- Subphase 4.3: Multitrack Pocket Locking (synchronizes bass and melodic tracks to the rhythmic pocket).
```

### Clases

#### `GroovePreset`

#### `GrooveDNA`
- **Métodos:**
  - `to_dict`: Sin documentación

#### `GroovePoolEngine`
Engine for hardware groove templates, groove DNA extraction, and cross-track pocket locking.

- **Métodos:**
  - `get_preset_dna`: Subphase 4.1: Returns iconic mathematical groove templates.
  - `extract_groove_dna_from_notes`: Subphase 4.2: Analyzes raw MIDI notes, computes timing deviations and velocity profile across a 1-bar cycle.
  - `apply_groove_to_notes`: Subphase 4.3: Transforms note timing and velocity using GrooveDNA offsets.
  - `apply_groove_to_live_clip`: Dispatches multitrack pocket locking or groove template application to Live.

---

## Módulo: `engine/music/groove/pocket.py`

**Descripción del Módulo:**
```text
Groove Pocket Engine:
Advanced genre-specific micro-timing, swing, humanization budgets, and chord strumming.
Replaces robotic 100% quantization with authentic physiological and genre-defined pockets.
```

### Clases

#### `PocketStyle`

#### `GroovePocketEngine`
Orchestrates musical micro-timing, genre swing, and chord humanization.

- **Métodos:**
  - `producer_to_pocket_style`: Maps a producer name or stylistic prompt to a canonical PocketStyle.
  - `apply_pocket_to_notes`: Applies role-specific micro-timing displacement, velocity variance,
  - `apply_chord_strum`: Groups simultaneous notes into chords and spreads note start times

---

## Módulo: `engine/music/harmony/reharmonizer.py`

**Descripción del Módulo:**
```text
Modal Reharmonization Engine:
Enriches simple harmonic progressions with secondary dominants (V7/X), tritone substitutions,
diminished passing chords, and modal borrowing for modern neo-soul, jazz-rap, and R&B sophistication.
```

### Clases

#### `ReharmStyle`

#### `ModalReharmonizer`
Calculates advanced harmonic substitutions and passing chord insertions.

- **Métodos:**
  - `_normalize_root`: Sin documentación
  - `get_secondary_dominant_root`: Returns the root note a perfect 5th above target root (or 4th down).
  - `get_tritone_sub_root`: Returns the root note a half-step (1 semitone) above target root.
  - `reharmonize_progression`: Takes an input list of 4-bar or 8-bar chords and injects harmonic tension
  - `render_chords_to_notes`: Converts Chord objects into concrete NoteEvent voices with smooth voice leading.

---

## Módulo: `engine/music/harmony/roman.py`

### Funciones Globales

- `parse_roman_numeral`: Parse Roman numeral token like 'VI', 'i7', 'IIImaj7', 'ii°', 'V7'.
- `roman_progression_to_chords`: Convert a list or string of Roman numeral tokens into concrete Chord objects.
- `parse_progression_string`: Splits 'i - VI - III - VII' or 'i, VI, III, VII' into clean token list

---

## Módulo: `engine/music/harmony/full_song.py`

**Descripción del Módulo:**
```text
Full-Song Harmonic Progression Engine:
Composes section-aware, progressive harmony across the full 96-bar arrangement.
Generates Drop-2/4 voicings, modal tension modulation, and smooth voice leading
without static loops.
```

### Clases

#### `FullSongHarmonyEngine`
Composes macro-level harmony and Drop-2 voice-led chords across 96 bars.

- **Métodos:**
  - `get_chord_intervals`: Returns semitone interval offsets for chord qualities.
  - `build_drop2_voicing`: Creates an open Drop-2 voicing centered around middle C (MIDI 60).
  - `optimize_voice_leading`: Inverts and octave-shifts next_voicing so that the sum of distances
  - `generate_full_song_progression`: Generates the continuous list of Chord objects across 96 bars.
  - `generate_harmony_notes`: Generates the full 96-bar sequence of NoteEvents with smooth voice leading,

---

## Módulo: `engine/music/harmony/chords.py`

### Funciones Globales

- `get_chord_intervals`: Get relative semitone intervals for a chord quality and optional extensions
- `get_chord_pitches`: Returns raw MIDI pitches for a Chord in basic closed position at base_octave

---

## Módulo: `engine/music/harmony/generator.py`

### Funciones Globales

- `generate_harmonic_structure`: Generates a structured timeline of Chord objects filling the specified number of bars.

---

## Módulo: `engine/music/harmony/strum.py`

**Descripción del Módulo:**
```text
Physical Chord Strummer:
Applies natural keyboard finger-roll staggering (8-18 ms) and physiological velocity tilt
to polyphonic chord voicings, eliminating synthetic simultaneous key-strikes.
```

### Clases

#### `PhysicalChordStrummer`
Master keyboard chord strummer with alternating strum directions and velocity tilt.

- **Métodos:**
  - `strum_notes`: Staggers simultaneous notes into realistic human chord finger-rolls.
  - `strum_dict_notes`: Helper to process dict notes from Live's get_clip_notes directly.

---

## Módulo: `engine/music/rhythm/generator.py`

### Funciones Globales

- `generate_drums`: Generates a full multi-element drum arrangement across bars with dynamic velocity, fills, and accents.

---

## Módulo: `engine/music/rhythm/templates.py`

---

## Módulo: `engine/music/rhythm/grid.py`

### Funciones Globales

- `get_subdivision_duration`: Sin documentación
- `generate_grid_offsets`: Generate all rhythmic grid beat offsets across total_bars

---

## Módulo: `engine/music/drums/ghost_notes.py`

**Descripción del Módulo:**
```text
Drum Ghost Note & Hi-Hat Dynamics Injector:
Enriches drum patterns with authentic ghost snares, turnaround fills, and 16th-note dynamic velocity waves.
```

### Clases

#### `DrumGhostNoteInjector`
Injects subtle ghost snare notes and shapes hi-hat dynamics with velocity waves.

- **Métodos:**
  - `inject_ghost_notes`: Detects turnaround bars (bars 4, 8, 12, 16...) and injects realistic low-velocity ghost snares.
  - `shape_hihat_velocities`: Applies a dynamic 4-step velocity wave pattern across 16th-note hi-hat events.
  - `process_drum_track_notes`: Applies both ghost snare injection and hi-hat velocity shaping in a single pass.

---

## Módulo: `engine/music/drums/multitrack.py`

**Descripción del Módulo:**
```text
Multi-Track Drum Layering & Sample Kit Loader.
- Decomposes drum sequences into distinct physical tracks (Kick, Snare, Clap, Hats, Perc, Crash).
- Loads verified native Drum Kits (.adg) with real analog and acoustic samples into Drum Racks.
- Eliminates single-track drum clutter, allowing granular mixing, independent processing, and surgical arrangement mutes.
```

### Clases

#### `DrumLayerRole`

#### `DrumLayerConfig`

#### `MultiTrackDrumEngine`
Coordinates multi-track drum decomposition and physical sample kit loading.

- **Métodos:**
  - `split_drum_notes_by_layer`: Partitions an aggregated drum note list into separated role layers.
  - `distribute_drum_pattern`: Distributes notes across standard drum layer names (Kick, Snare, Clap, Hi-Hats, Crash).
  - `load_verified_drum_kit`: Physically loads an authentic .adg drum kit preset into the track's Drum Rack.
  - `scaffold_drum_tracks`: Scaffolds multi-track drum architecture and loads verified sample kit.
  - `setup_multitrack_session`: Decomposes notes and creates dedicated clips on each physical drum track.

---

## Módulo: `engine/music/drums/evolver.py`

**Descripción del Módulo:**
```text
Drum Pattern Evolver & Micro-Turnaround Engine:
Eliminates loop monotony by procedurally evolving drum sequences:
- Injects Bar 4 micro-turnarounds (ghost snares & triplet hi-hat rolls)
- Injects Bar 8 fills (cascading toms & syncopated flams)
- Injects section crashes and impact layers on arrivals.
```

### Clases

#### `DrumFillType`

#### `DrumPatternEvolver`
Procedural micro-variation and fill generator for drum loops.

- **Métodos:**
  - `inject_bar_4_turnaround`: Inserts ghost notes and a triplet hat roll in the final beat of Bar 4 (beats 14.0 to 16.0).
  - `inject_bar_8_fill`: Inserts a dynamic tom and snare fill across the last 2 beats of Bar 8 (beats 30.0 to 32.0).
  - `inject_section_crash`: Inserts a crash cymbal on section arrival beat.
  - `evolve_drum_sequence`: Extends a 4-bar drum motif across total_bars with procedurally varied fills,
  - `apply_drum_evolution`: Reads or creates drum notes, evolves them with fills, and writes to Live.

---

## Módulo: `engine/music/drums/genre_grooves.py`

**Descripción del Módulo:**
```text
Genre Rhythm & Groove Articulation Engine:
Generates authentic, highly articulated drum patterns tailored to specific genres
(Trap, House, Neo-Soul, Reggaeton, Synthwave, Boom-Bap), replacing generic loops
with professional groove-pool micro-timing, ghost notes, and hi-hat roll dynamics.
```

### Clases

#### `GenreDrumStyle`

#### `GenreRhythmGrooveEngine`
Procedural rhythm generator with genre-authentic pocket and groove templates.
FEATURE STATUS: EXPERIMENTAL (OFF BY DEFAULT).
This engine is dormant and strictly optional. The standard/custom workflow is preserved.

- **Métodos:**
  - `get_supported_genres`: Sin documentación
  - `generate_rhythm_pattern`: Generates a complete multi-layered drum pattern for the requested genre and length.
  - `_generate_trap`: Trap pattern:
  - `_generate_house`: House pattern:
  - `_generate_neo_soul`: Neo-Soul pattern:
  - `_generate_reggaeton`: Reggaeton / Latin Dembow:
  - `_generate_synthwave`: Synthwave 80s pattern:
  - `_generate_boom_bap`: Boom-Bap classic hip hop pattern.
  - `_generate_techno`: Techno driving industrial pattern.
  - `_generate_cumbia`: Cumbia Latina / Sonidera / Electrocumbia pattern:
  - `_generate_rock`: Modern / Indie / Alternative Rock pattern:
  - `_generate_afrobeat`: Afrobeat / Afropop / Urban Dancehall pattern:
  - `_generate_edm`: EDM / Festival Big Room pattern:
  - `_generate_drum_and_bass`: Drum & Bass 2-step breakbeat pattern (170-175 BPM):
  - `_generate_pop`: Commercial / Latin Pop pattern:
  - `apply_mpc_swing`: Shifts every second 16th note (odd sixteenths: 0.25, 0.75, 1.25, etc.) forward
  - `apply_micro_timing_humanization`: Applies deterministic organic humanization (+/- ms) and subtle velocity fluctuations
  - `offer_genre_options`: Offers structured production options grouped by genre categories:
  - `get_genre_descriptor`: Returns the specific production profile descriptor for a genre.

---

## Módulo: `engine/music/midi/compiler.py`

### Funciones Globales

- `compile_notes_to_ableton_format`: Compiles internal NoteEvent models into the exact dict format expected by AbletonMCP:
- `compute_part_fingerprint`: Computes a statistical fingerprint for similarity measurement and duplicate detection
- `compare_fingerprints`: Calculates multidimensional similarity metrics between two musical parts

---

## Módulo: `engine/adapters/mock_adapter.py`

### Clases

#### `MockAbletonAdapter`
In-memory simulation of Ableton Live for offline execution and automated tests

- **Métodos:**
  - `__init__`: Sin documentación
  - `is_connected`: Sin documentación
  - `set_connected`: Sin documentación
  - `get_session_info`: Sin documentación
  - `get_track_info`: Sin documentación
  - `create_midi_track`: Sin documentación
  - `set_track_name`: Sin documentación
  - `delete_track`: Sin documentación
  - `create_clip`: Sin documentación
  - `delete_clip`: Sin documentación
  - `set_track_volume`: Sin documentación
  - `set_track_panning`: Sin documentación
  - `set_track_mute`: Sin documentación
  - `set_track_solo`: Sin documentación
  - `set_tempo`: Sin documentación
  - `add_notes_to_clip`: Sin documentación
  - `get_clip_notes`: Sin documentación
  - `_reindex_tracks`: Sin documentación
  - `load_instrument_or_effect`: Sin documentación
  - `get_drum_rack_pads`: Sin documentación
  - `get_drum_pad_devices`: Sin documentación
  - `load_drum_pad_item`: Sin documentación
  - `get_arrangement_clips`: Sin documentación
  - `duplicate_to_arrangement`: Sin documentación
  - `send_command`: Sin documentación
  - `_send`: Sin documentación

---

## Módulo: `engine/adapters/ableton_adapter.py`

### Clases

#### `LiveAbletonAdapter`
Production adapter that communicates with Ableton Live Remote Script via TCP socket

- **Métodos:**
  - `__init__`: Sin documentación
  - `_get_connection`: Sin documentación
  - `is_connected`: Sin documentación
  - `_send`: Sin documentación
  - `get_session_info`: Sin documentación
  - `get_track_info`: Sin documentación
  - `create_midi_track`: Sin documentación
  - `set_track_name`: Sin documentación
  - `delete_track`: Sin documentación
  - `create_clip`: Sin documentación
  - `delete_clip`: Sin documentación
  - `set_track_volume`: Sin documentación
  - `set_track_panning`: Sin documentación
  - `set_track_mute`: Sin documentación
  - `set_track_solo`: Sin documentación
  - `set_tempo`: Sin documentación
  - `add_notes_to_clip`: Sin documentación
  - `get_clip_notes`: Sin documentación
  - `fire_clip`: Sin documentación
  - `stop_clip`: Sin documentación
  - `start_playback`: Sin documentación
  - `stop_playback`: Sin documentación
  - `load_instrument_or_effect`: Sin documentación
  - `load_drum_pad_item`: Sin documentación
  - `send_command`: Sin documentación
  - `get_cue_points`: Sin documentación
  - `get_arrangement_clips`: Sin documentación

---

## Módulo: `engine/adapters/base.py`

### Clases

#### `BaseAbletonAdapter`
Abstract interface for communicating with Ableton Live

- **Métodos:**
  - `is_connected`: Sin documentación
  - `get_session_info`: Sin documentación
  - `get_track_info`: Sin documentación
  - `create_midi_track`: Sin documentación
  - `set_track_name`: Sin documentación
  - `delete_track`: Sin documentación
  - `create_clip`: Sin documentación
  - `delete_clip`: Sin documentación
  - `set_track_volume`: Sin documentación
  - `set_track_panning`: Sin documentación
  - `set_track_mute`: Sin documentación
  - `set_track_solo`: Sin documentación
  - `set_tempo`: Sin documentación
  - `add_notes_to_clip`: Sin documentación
  - `get_clip_notes`: Sin documentación
  - `fire_clip`: Sin documentación
  - `stop_clip`: Sin documentación
  - `start_playback`: Sin documentación
  - `stop_playback`: Sin documentación

---

## Módulo: `engine/events/event_logger.py`

### Clases

#### `EventLogger`
- **Métodos:**
  - `__init__`: Sin documentación
  - `log_event`: Sin documentación
  - `get_events_for_transaction`: Sin documentación
  - `get_recent_events`: Sin documentación

---

## Módulo: `engine/supervisor/anti_cliche_guard.py`

**Descripción del Módulo:**
```text
Engine Supervisor: Anti-Cliché & Mandatory Variation Gatekeeper.
Enforces INV-ANTI-CLICHE-01 and INV-ANTI-CLICHE-02 across clips, patterns, and sound design.
Prevents unmutated copies, flat velocities, and static loops.
```

### Clases

#### `AntiClicheGuard`
Quality gatekeeper that intercepts MIDI note buffers and synthesis parameters,
rejecting raw un-sculpted presets and repetitive, un-humanized loops.

- **Métodos:**
  - `audit_midi_clip`: Audits a MIDI clip's notes before placement on timeline:
  - `audit_preset_sculpting`: Audits whether a preset from the knowledge base was modified.

---

## Módulo: `engine/supervisor/governance.py`

**Descripción del Módulo:**
```text
Engine Governance Supervisor & Production Contract Enforcer.
Enforces strict DAW-level rules for AI music production:
1. Mandatory preset selection prior to production (where applicable).
2. Mandatory parameter sculpting immediately after preset selection.
3. Strict effect stacking discipline: blocks adding subsequent effects until the current effect is configured.
4. Clean plugin and effect replacement support.
5. Permissive effect expansion respecting active configuration rules.
6. Channel signal integrity audit (device presence, clip content, live meter activity).
7. Final song master LUFS compliance (-14.0 to -11.0 LUFS) and True Peak ceiling (<= -1.0 dBTP).
```

### Clases

#### `GovernanceViolationError`
Raised when an AI production action violates the engine governance contract.


#### `UnconfiguredEffectStackingError`
Raised when attempting to add an effect while the previous effect remains unconfigured.


#### `PresetSelectionRequiredError`
Raised when producing without selecting a preset on an instrument requiring presets.


#### `ParameterSculptingRequiredError`
Raised when an instrument or effect is left in un-sculpted default/init state.


#### `UnconfiguredDeviceViolationError`
Raised when an AI attempts to proceed or produce while a device is unconfigured or in default/init state.


#### `ChannelSilenceError`
Raised when a track has no audio output during playback audit.


#### `MasterLoudnessNonCompliantError`
Raised when the master output fails LUFS or True Peak thresholds.


#### `DeviceState`

#### `TrackState`

#### `EngineGovernanceSupervisor`
Authoritative production supervisor enforcing AbletonEngine governance rules.

- **Métodos:**
  - `resolve_category_for_role`: Sin documentación
  - `audit_track_category`: Sin documentación
  - `__init__`: Sin documentación
  - `reset`: Resets the supervisor state for a fresh production session.
  - `register_track`: Sin documentación
  - `get_track_state`: Sin documentación
  - `notify_instrument_loaded`: Sin documentación
  - `record_preset_selected`: Sin documentación
  - `assert_preset_selection_valid`: Sin documentación
  - `assert_instrument_sculpted`: Enforces that the track's instrument has been actively sculpted.
  - `request_add_effect`: Request permission to append an effect to a track.
  - `record_device_sculpted`: Marks an instrument or effect as consciously tuned and sculpted.
  - `record_effect_sculpted`: Backward-compatible alias for record_device_sculpted.
  - `assert_device_sculpted`: Checks that a specific device on a track has been actively configured.
  - `assert_track_fully_sculpted`: Enforces that EVERY device (both instruments and serial effects) on the track
  - `assert_session_fully_sculpted`: Enforces that all tracks in the current production session have every device configured.
  - `get_unconfigured_devices`: Returns a list of all devices across all tracks currently in un-sculpted state.
  - `get_mandatory_sculpting_requirements`: Provides the dictionary of parameters and semantic controls that must be configured for a device.
  - `replace_device`: Cleanly replaces a device on a track. Resets sculpting state for that slot.
  - `audit_channel_integrity`: Audits all active tracks in the session snapshot:
  - `audit_and_enforce_master_lufs`: Verifies and calibrates master output against commercial broadcast standards.

---

## Módulo: `engine/supervisor/gatekeeper.py`

**Descripción del Módulo:**
```text
Supervisor Gatekeeper & Hard Quality Gates Engine:
Enforces a strict 7-phase state machine where the engine is the authoritative supervisor.
Execution cannot progress to subsequent phases if any physical, structural,
or acoustic gate criteria are violated.
```

### Clases

#### `ProductionPhase`

#### `GateValidationError`
Raised when a quality gate fails physical, acoustic, or structural validation.

- **Métodos:**
  - `__init__`: Sin documentación
  - `to_dict`: Sin documentación

#### `GateResult`
- **Métodos:**
  - `to_dict`: Sin documentación

#### `Gatekeeper`
Supervises the production lifecycle across 7 hard quality gates.

- **Métodos:**
  - `__init__`: Sin documentación
  - `validate_gate_1_dna`: Gate 1: DNA (Tempo, Cue Points, Musical Scale).
  - `validate_gate_2_composition`: Gate 2: Composition (MIDI Notes, Density, Scale).
  - `validate_gate_3_instrumentation`: Gate 3: Instrumentation (VST Guard, Drum Rack Pad audit, Vital presets).
  - `validate_gate_4_groove`: Gate 4: Arrangement & Timeline Structure (Clips placed on Arrangement timeline).
  - `validate_gate_5_transitions`: Gate 5: Transitions & Energy (Risers, Downlifters, Silence Gaps).
  - `validate_gate_6_mix`: Gate 6: Mix & Gain Staging (-6.0 dBFS pre-master headroom, HPF on tracks, zero duplicate plugins).
  - `validate_gate_7_mastering`: Gate 7: Mastering (Guided 7-Point Chain, Physical Convergence to Target LUFS).
  - `_finalize_gate`: Sin documentación

---

## Módulo: `engine/supervisor/acoustic_probe.py`

**Descripción del Módulo:**
```text
Acoustic Probe & Physical Signal Supervisor:
Monitors and audits playback liveness, track signal paths, transport state,
and mixer conditions in Ableton Live to guarantee that audio actually reaches the Master bus.
- Starts transport and jumps to Drop (beat 80) where all musical parts are active.
- Multi-sample physical meter measurement across all tracks.
- Enforces strict audibility (every track must produce physical meter energy > 0.001).
```

### Clases

#### `AcousticSilenceError`
Raised when the session or specific tracks are acoustically silent or structurally blocked.

- **Métodos:**
  - `__init__`: Sin documentación

#### `AcousticProbe`
Probes physical track liveness, routing, and transport status in Ableton Live.

- **Métodos:**
  - `audit_track_liveness`: Deep physical audit of a single track in Ableton Live:
  - `audit_all_tracks_signal`: Audits physical signal output across all tracks during real playback at the Drop:
  - `probe_main_liveness`: Probes main track liveness across session or target tracks, checking for blocking silence.
  - `ensure_audible_playback`: Forces Ableton Live into an audible state.

---

## Módulo: `engine/supervisor/failure_diagnostics.py`

**Descripción del Módulo:**
```text
Failure Diagnostics & Root Cause Analyzer:
Performs deep physical and structural diagnostics when quality gates or acoustic probes fail,
providing clear actionable remediation options rather than vague error messages.
```

### Clases

#### `FailureCategory`

#### `DiagnosticSeverity`

#### `DiagnosticFinding`
- **Métodos:**
  - `to_dict`: Sin documentación

#### `FailureDiagnostics`
Performs structured diagnosis of playback, plugin, mixing, and mastering anomalies.

- **Métodos:**
  - `diagnose_silence`: Diagnoses why a specific track is silent during playback.
  - `format_diagnostic_report`: Generates a markdown diagnostic report from findings.

---

## Módulo: `engine/sound/evolution.py`

**Descripción del Módulo:**
```text
Sound Evolution & Patch Identity:
Maintains sonic identity while modulating timbre across song sections.
```

### Clases

#### `PatchIdentity`

#### `SoundEvolutionManager`
Manages section-specific macro states while keeping instrument identity constant.

- **Métodos:**
  - `derive_section_macros`: Calculates macro adjustments based on section energy.

---

## Módulo: `engine/sound/context.py`

**Descripción del Módulo:**
```text
Mix Context, Frequency Role Mapping & Adaptive Sound Advisor.
Prevents frequency collision between Kick, Sub-bass, Bass, Leads, and Pads.
```

### Clases

#### `FrequencyBand`

#### `FrequencyRoleMap`
Defines acoustic spectrum frequency domains.


#### `MixContext`
Current musical context across active session tracks.


#### `AdaptiveAdvisor`
Analyzes MixContext to diagnose frequency clashes and produce sound design recommendations.

- **Métodos:**
  - `evaluate_clashes`: Sin documentación
  - `check_low_end_phase`: Validates that low-end roles (SUB_BASS, KICK) are strictly mono/centered.

---

## Módulo: `engine/sound/engine.py`

**Descripción del Módulo:**
```text
Master Sound Design & Production Engine:
High-level production coordinator uniting Capability Discovery, Sound Profiles,
Chains, Drum Rack Engine, Semantic Macros, Snapshots, and Linter.
```

### Clases

#### `SoundEngine`
Master Production Intelligence Sound Engine.

- **Métodos:**
  - `__init__`: Sin documentación
  - `set_adapter`: Sin documentación
  - `build_sound_role`: Builds a complete, production-grade sound chain for a musical role.
  - `build_drum_rack`: Builds a complete, verified Drum Rack with all required samples.
  - `create_sound`: Creates an instrument/sound chain based on musical intent parameters.
  - `update_sound`: Updates macro parameters or character on an existing track.
  - `inspect_track`: Inspects sound chain, devices, macro parameters, and frequency profile for a track.
  - `verify_track`: Verifies physical sound device state (checks for empty chains, missing plugins).
  - `compare_tracks`: Compares two tracks for frequency clash, stereo balance, and dynamic headroom.
  - `apply_profile`: Applies a curated sound profile directly to a track.
  - `set_macro`: Sin documentación
  - `get_macro`: Sin documentación
  - `get_all_macros`: Sin documentación
  - `lint_session`: Audits all tracks in the session for sound design issues.
  - `_infer_role`: Sin documentación
  - `_resolve_track_index`: Sin documentación
  - `_get_track_info`: Sin documentación

---

## Módulo: `engine/sound/linter.py`

**Descripción del Módulo:**
```text
Sound Design Linter:
Audits track production chains for issues:
- Missing primary instrument
- Empty drum racks
- Stereo sub-bass
- Excessive gain (> +6.0 dB)
- Excessive reverb on bass/kick
```

### Clases

#### `SoundLintIssue`

#### `SoundLinter`
Audits production sound design quality.

- **Métodos:**
  - `lint_track`: Sin documentación

---

## Módulo: `engine/sound/intent.py`

**Descripción del Módulo:**
```text
Sound Intent & Sidechain Intent Models:
High-level musical declarations from the LLM or Creative Director.
```

### Clases

#### `SoundIntent`
Declaration of desired sound character without referencing physical plugins.

- **Métodos:**
  - `__post_init__`: Sin documentación
  - `to_dict`: Sin documentación

#### `SidechainIntent`
Sidechain ducking relationship between two musical roles.

- **Métodos:**
  - `to_dict`: Sin documentación

---

## Módulo: `engine/sound/vital/builder.py`

**Descripción del Módulo:**
```text
Procedural Patch Synthesis Builder for Vital (.vital)
Produces fully articulated VitalPresetSpec instances for Bass, 808, Keys, Leads, Pads, and Custom.
```

### Clases

#### `VitalPatchBuilder`
Procedural sound designer creating tailored Vital synthesizers patches.

- **Métodos:**
  - `build_reese_bass`: Builds a modern heavy Reese Bass with stereo detuned saw saws,
  - `build_hard_808`: Builds an aggressive modern 808 with transient punch pitch envelope,
  - `build_neo_soul_keys`: Builds a lush warm electric piano / neo soul keys patch
  - `build_lead_hook`: Builds a cutting synth lead with 7-voice unison spread,
  - `build_custom`: Builds a custom Vital patch from a dictionary specification or prompt synthesis.

---

## Módulo: `engine/sound/vital/file_manager.py`

**Descripción del Módulo:**
```text
Vital Preset Manager
Handles saving, serialization, verification, and cataloging of .vital JSON preset files
both inside the engine repository and into the user's local Vital directory.
```

### Clases

#### `VitalPresetManager`
Manages serialization and deployment of .vital patches.

- **Métodos:**
  - `__init__`: Sin documentación
  - `_load_base_template`: Loads clean base template with initialized Vital parameters and wavetables.
  - `serialize_spec_to_dict`: Transforms a VitalPresetSpec into a valid Vital preset JSON object.
  - `save_preset`: Saves a synthesized preset to both engine library and user Vital folder.
  - `list_presets`: Scans engine and user directories for .vital presets and extracts metadata.

---

## Módulo: `engine/sound/vital/models.py`

### Clases

#### `VitalPresetStyle`

#### `VitalOscillatorSpec`

#### `VitalFilterSpec`

#### `VitalEnvelopeSpec`

#### `VitalLfoSpec`

#### `VitalEffectsSpec`

#### `VitalModulationRouting`

#### `VitalPresetSpec`

---

## Módulo: `engine/sound/parameters/curves.py`

**Descripción del Módulo:**
```text
Parameter Curves:
Transfer functions translating [0.0, 1.0] semantic values to physical parameter units (Hz, dB, ms, %).
```

### Clases

#### `ParameterCurve`
- **Métodos:**
  - `linear`: Sin documentación
  - `exponential`: Sin documentación
  - `logarithmic`: Logarithmic curve (ideal for frequency in Hz).
  - `inverse`: Sin documentación

---

## Módulo: `engine/sound/parameters/semantic.py`

**Descripción del Módulo:**
```text
Semantic Sound Parameters:
Defines the universal acoustic descriptors and normalization scales.
```

### Clases

#### `SemanticParameter`
- **Métodos:**
  - `__post_init__`: Sin documentación

---

## Módulo: `engine/sound/parameters/mapper.py`

**Descripción del Módulo:**
```text
Parameter Translation Layer:
Maps high-level semantic sound parameters to concrete physical device parameters
across multiple target devices (EQ, Filter, Saturation, Reverb, Delay, Utility).
```

### Clases

#### `ParameterMapper`
Translates semantic parameters into multi-device parameter assignments.

- **Métodos:**
  - `map_semantic_to_devices`: Returns a list of device target bindings for a semantic parameter.

---

## Módulo: `engine/sound/macros/mappings.py`

**Descripción del Módulo:**
```text
Universal 8-Macro Architecture:
Defines standard macro controls and their multi-parameter bindings.
```

---

## Módulo: `engine/sound/macros/semantic_morph.py`

**Descripción del Módulo:**
```text
Semantic Timbre Morph Engine:
Bridges high-level musical descriptors (Brightness, Warmth, Sub Weight, Space, Attack Snap)
to physical device parameters in Ableton Live 12 and generates dynamic section-by-section
automation envelopes across the 96-bar song timeline.
```

### Clases

#### `TimbreMacroState`
- **Métodos:**
  - `to_dict`: Sin documentación

#### `SectionMorphPoint`

#### `SemanticTimbreMorphEngine`
Calculates dynamic timbre states and generates parameter automation across sections.

- **Métodos:**
  - `get_section_morph_plan`: Returns the 8-section timbre roadmap with bar and beat coordinates.
  - `frequency_to_normalized`: Logarithmic frequency to Live 12 normalized 0.0-1.0 parameter value.
  - `brightness_to_filter_hz`: Maps brightness 0.0-1.0 to LPF cutoff from 300 Hz to 20000 Hz.
  - `warmth_to_saturator_drive`: Maps warmth 0.0-1.0 to Saturator drive in dB (0.0 to 6.0 dB).
  - `generate_brightness_envelope`: Generates a list of (beat, normalized_value) automation breakpoints across 96 bars (384 beats).
  - `generate_full_automation_manifest`: Returns the complete multi-parameter automation roadmap for the project.

---

## Módulo: `engine/sound/macros/system.py`

**Descripción del Módulo:**
```text
Macro System:
Controls multi-parameter macro values across physical Ableton devices.
```

### Clases

#### `MacroSystem`
Manages multi-parameter macro controls with transfer functions.

- **Métodos:**
  - `__init__`: Sin documentación
  - `set_macro`: Sets a semantic macro and updates all linked physical device parameters.
  - `get_macro`: Sin documentación

---

## Módulo: `engine/sound/chains/builder.py`

**Descripción del Módulo:**
```text
Chain Builder:
Builds, resolves, and loads device chains into Ableton Live tracks with fallback support.
```

### Clases

#### `ChainBuilder`
Instantiates and configures physical Ableton Live devices matching a semantic chain.

- **Métodos:**
  - `__init__`: Sin documentación
  - `build_chain_for_track`: Sin documentación

---

## Módulo: `engine/sound/chains/templates.py`

**Descripción del Módulo:**
```text
Production Chain Templates:
Contextual, parameterized signal chains for every musical role.
```

### Funciones Globales

- `get_chain_template`: Retrieves standard production chain for a role.

---

## Módulo: `engine/sound/chains/models.py`

**Descripción del Módulo:**
```text
Device Chain Models:
Defines semantic device identifiers and parameterized device chains.
```

### Clases

#### `SemanticDevice`
- **Métodos:**
  - `to_dict`: Sin documentación

#### `DeviceChain`
- **Métodos:**
  - `to_dict`: Sin documentación

---

## Módulo: `engine/sound/snapshots/snapshots.py`

**Descripción del Módulo:**
```text
Sound Snapshots & Rollback:
Captures track devices, parameters, and macro states before operations.
Enforces atomic safety during sound building.
```

### Clases

#### `SoundSnapshot`

#### `SoundSnapshotManager`
Captures and restores track sound states.

- **Métodos:**
  - `__init__`: Sin documentación
  - `capture`: Sin documentación
  - `rollback`: Sin documentación

---

## Módulo: `engine/sound/foley/texture.py`

**Descripción del Módulo:**
```text
Organic Foley & Atmospheric Texture Generator:
Generates evolving, tempo-synced background textures (vinyl, tape hiss, rain, room tone)
with parametric band-pass safety filters, rhythmic breathing LFO envelopes,
and automated kick/snare sidechain ducking so organic textures sit seamlessly in the mix.
```

### Clases

#### `TextureType`

#### `OrganicTextureProfile`

#### `OrganicTextureGenerator`
Calculates parameters, rhythmic breathing envelopes, and Live device chains for foley beds.

- **Métodos:**
  - `get_profile`: Sin documentación
  - `calculate_breathing_envelope`: Generates a smooth sinusoidal breathing envelope synchronized to musical divisions.
  - `calculate_rhythmic_ducking`: Generates ducking envelope points under kicks and snares to glue texture into the groove.
  - `build_live_device_chain`: Constructs the native Ableton Live 12 Suite processing chain for the foley bed:
  - `configure_foley_bed`: Configures an organic foley track in Ableton Live:

---

## Módulo: `engine/sound/curator/auto_curate.py`

**Descripción del Módulo:**
```text
Session Auto-Curate & Empty Track Rescuer:
Proactively audits all session tracks in Ableton Live 12 Suite,
detects unassigned, empty, or un-instrumented tracks,
and automatically loads suitable instruments, Vital/Drum Rack presets,
and essential safety channel strips (EQ Eight + Utility Mono Bass).
```

### Clases

#### `TrackCurateAction`

#### `SessionAutoCuratorEngine`
Intelligent diagnostic and 1-click self-healing engine for session tracks.

- **Métodos:**
  - `classify_track_role`: Classifies musical role based on track name heuristics.
  - `diagnose_tracks`: Scans tracks metadata and generates curation actions for empty tracks.
  - `auto_curate_session`: Executes automatic curation across all empty or unassigned tracks in Live.

---

## Módulo: `engine/sound/capabilities/discovery.py`

**Descripción del Módulo:**
```text
Capability Discovery:
Inspects active Ableton Live instance to verify presence of devices and plugins.
```

### Clases

#### `CapabilityDiscovery`
Discovers host capabilities from Ableton Live session.

- **Métodos:**
  - `discover_capabilities`: Sin documentación

---

## Módulo: `engine/sound/capabilities/cache.py`

**Descripción del Módulo:**
```text
Device Capability Cache:
Caches inspected device parameters to minimize TCP socket queries.
```

### Clases

#### `DeviceCapabilityCache`
Caches parameter schema per device class to speed up parameter mapping.

- **Métodos:**
  - `get`: Sin documentación
  - `set`: Sin documentación
  - `clear`: Sin documentación

---

## Módulo: `engine/sound/capabilities/registry.py`

**Descripción del Módulo:**
```text
Capability Registry:
Maintains the single source of truth of available Ableton devices, formats, and libraries.
Enforces Native-First policy: Ableton Native > Max for Live > Third-Party > Fallback.
```

### Clases

#### `CapabilityRegistry`
- **Métodos:**
  - `is_instrument_available`: Sin documentación
  - `is_effect_available`: Sin documentación
  - `select_instrument`: Native-first instrument selection.

---

## Módulo: `engine/sound/profiles/profiles.py`

**Descripción del Módulo:**
```text
Pre-defined Production Sound Profiles across genres and characters.
```

### Funciones Globales

- `get_sound_profile`: Retrieves or builds a matching SoundProfile.

---

## Módulo: `engine/sound/profiles/models.py`

**Descripción del Módulo:**
```text
Sound Profile Models:
Normalized [0.0, 1.0] timbre representations defining character, weight, brightness, and space.
```

### Clases

#### `SoundProfile`
Comprehensive timbre descriptor for a musical role.

- **Métodos:**
  - `__post_init__`: Sin documentación
  - `punch`: Sin documentación
  - `to_dict`: Sin documentación

---

## Módulo: `engine/sound/drum_rack/resolver.py`

**Descripción del Módulo:**
```text
Drum Sound Resolver & Sample Validation:
Locates authentic samples from user libraries and validates audio integrity.
```

### Clases

#### `DrumSoundResolver`
Resolves samples for drum roles with format and audio integrity validation.

- **Métodos:**
  - `validate_sample`: Validates that a sample exists, is readable, and is a supported audio format.
  - `resolve_drum_sound`: Resolves an authentic local audio sample path for a drum role.

---

## Módulo: `engine/sound/drum_rack/verifier.py`

**Descripción del Módulo:**
```text
Drum Rack Verifier:
Enforces the strict 'No Fake Success' invariant.
Audits physical Drum Rack pads in Ableton Live.
```

### Clases

#### `DrumRackVerifier`
Strictly audits that a Drum Rack has real physical devices and samples in its pads.

- **Métodos:**
  - `verify_drum_rack`: Verifies that the Drum Rack exists and is populated.

---

## Módulo: `engine/sound/drum_rack/engine.py`

**Descripción del Módulo:**
```text
Drum Rack Engine v2:
Idempotent batch construction, pad configuration, and strict verification.
```

### Clases

#### `DrumRackEngine`
Master production engine for Drum Racks in Ableton Live.

- **Métodos:**
  - `__init__`: Sin documentación
  - `build_drum_rack`: Builds and populates a complete Drum Rack in an atomic batch operation.
  - `add_pad`: Adds or updates a single pad in an existing Drum Rack.
  - `load_sample`: Loads a specific audio sample onto a drum pad.
  - `set_pad_params`: Modifies volume, pitch, filter, decay, pan, mute, or solo of a drum pad.
  - `inspect_drum_rack`: Inspects all loaded pads, samples, and chains in a Drum Rack.
  - `rebuild_unverified_pads`: Rebuilds missing or unverified pads using fallback sample library.

---

## Módulo: `engine/sound/drum_rack/models.py`

**Descripción del Módulo:**
```text
Drum Rack Models:
Declarative specifications for Drum Racks and Pad configurations.
```

### Clases

#### `SampleMetadata`

#### `DrumPadSpec`

#### `DrumRackSpec`
- **Métodos:**
  - `to_dict`: Sin documentación

---

## Módulo: `engine/sound/drum_rack/authentic_builder.py`

**Descripción del Módulo:**
```text
Authentic Sample Drum Rack Engine:
Scans the user's authentic local sample libraries (FL Studio libraries, ASAN Essentials, Cymatics, Drums)
and constructs verified, fully populated Drum Racks with real, punchy audio samples.
```

### Clases

#### `AuthenticDrumPad`
- **Métodos:**
  - `to_dict`: Sin documentación

#### `AuthenticDrumKitSpec`
- **Métodos:**
  - `to_dict`: Sin documentación

#### `AuthenticSampleDrumRackEngine`
Resolves, validates, and loads real local drum samples into Ableton Drum Racks.

- **Métodos:**
  - `__init__`: Sin documentación
  - `build_sample_index`: Indexes available audio files in the user's sample libraries.
  - `find_best_sample`: Finds the optimal audio file matching the requested keywords.
  - `build_kit_spec`: Constructs a complete 8-pad authentic drum kit specification.
  - `load_kit_into_live`: Loads the authentic drum kit into the Ableton Live track.

---

## Módulo: `engine/persistence/storage.py`

### Clases

#### `StorageManager`
- **Métodos:**
  - `__init__`: Sin documentación
  - `_ensure_dirs`: Sin documentación
  - `save_graph`: Sin documentación
  - `load_graph`: Sin documentación
  - `save_snapshot`: Sin documentación
  - `load_snapshot`: Sin documentación
  - `list_snapshots`: Sin documentación
  - `save_transaction`: Sin documentación
  - `load_transaction`: Sin documentación
  - `list_transactions`: Sin documentación

---

## Módulo: `engine/mix/channel_strip.py`

**Descripción del Módulo:**
```text
Channel Strip & Bus Frequency Processing Engine:
Inserts and configures physical EQ Eight, Channel EQ, Drum Buss, and Glue Compressor
devices on individual tracks and group busses to enforce professional frequency separation,
high-pass filtering, surgical resonance dips, air boosts, and bus glue.
```

### Clases

#### `ChannelStripEngine`
Architect for individual channel strips and group bus processing chains in Ableton Live.

- **Métodos:**
  - `freq_to_normalized`: Converts frequency in Hz (10 to 22000) to EQ Eight's exact normalized float [0.0..1.0].
  - `get_role_eq_settings`: Returns surgical EQ Eight parameter profiles tailored for specific instrument roles:
  - `apply_channel_strip`: Inserts EQ Eight on track_index and calibrates surgical HPF and curve for its role.
  - `apply_bus_processing`: Applies group/bus processing to tie stems together:

---

## Módulo: `engine/mix/sidechain_manager.py`

**Descripción del Módulo:**
```text
Physical Sidechain Compression Manager.
Inspects, loads, and configures native Ableton Compressor devices on target tracks
(such as 808 Bass or Synth Pads) with S/C enabled, fast transient clamp, and tight release.
```

### Clases

#### `SidechainManager`
Manages physical sidechain routing and compressor device setup in Ableton Live.

- **Métodos:**
  - `find_or_load_compressor`: Inspects track devices. If Compressor is not present, attempts to load native Compressor.
  - `configure_sidechain`: Configures physical sidechain parameters on the target track's Compressor.
  - `setup_sidechain`: Convenience wrapper mapping source and destination to configure_sidechain.

---

## Módulo: `engine/mix/multitrack_sidechain.py`

**Descripción del Módulo:**
```text
Multi-Track Sidechain Ducking Coordinator:
Coordinates physical sidechain compression routing and envelope ducking
across Kick-to-Bass, Vocal-to-Chords, and Kick-to-Reverb buses.
```

### Clases

#### `MultiTrackSidechainCoordinator`
Master architect for multitrack sidechain compression routing.

- **Métodos:**
  - `get_multitrack_sidechain_matrix`: Returns the complete sidechain routing blueprint with compressor calibrations.
  - `generate_compressor_device_parameters`: Calculates normalized device parameter values for Ableton Live's native Compressor:

---

## Módulo: `engine/mix/diagnostic_engine.py`

**Descripción del Módulo:**
```text
Diagnostic Engine: evidence-based causal diagnosis and explanation.
Answers: What is wrong, why, with what physical evidence, and what are the best musical fixes.
```

### Clases

#### `DiagnosticEngine`
Synthesizes physical DSP evidence into actionable causal diagnoses.

- **Métodos:**
  - `diagnose`: Sin documentación

---

## Módulo: `engine/mix/conflict_graph.py`

**Descripción del Módulo:**
```text
Frequency Collision Graph and Spectral Occupancy Map.
Represents multi-role mixing as an interconnected spectral network.
```

### Clases

#### `ConflictEdge`
- **Métodos:**
  - `to_dict`: Sin documentación

#### `FrequencyConflictGraph`
Graph network tracking multi-role spectral and temporal clashes.

- **Métodos:**
  - `__init__`: Sin documentación
  - `add_role_node`: Sin documentación
  - `add_conflict`: Sin documentación
  - `get_conflicts_for_role`: Sin documentación
  - `to_dict`: Sin documentación

#### `SpectralOccupancyMap`
Maps spectral bands to occupying roles and energy distributions.

- **Métodos:**
  - `get_occupancy_map`: Returns band -> list of active occupying roles.

---

## Módulo: `engine/mix/feature_extractor.py`

**Descripción del Módulo:**
```text
Unified Audio Feature Extractor.
Extracts complete AudioFeatures using Loudness, Frequency, Dynamics, Stereo, and Transient analyzers.
```

### Clases

#### `FeatureExtractor`
Pipelines DSP analyzers to produce a comprehensive AudioFeatures object.

- **Métodos:**
  - `extract_all`: Sin documentación

---

## Módulo: `engine/mix/balance_analyzer.py`

**Descripción del Módulo:**
```text
Role Balance and Energy Distribution Analyzer.
Examines multi-track stems across the arrangement.
```

### Clases

#### `RoleBalanceAnalyzer`
Estimates energy occupation, priority, and frequency allocation per role.

- **Métodos:**
  - `evaluate_role_balances`: Sin documentación

---

## Módulo: `engine/mix/mix_linter.py`

**Descripción del Módulo:**
```text
Mix Linter: automated rule-based production mix auditing.
Checks headroom, low-end stereo, mono compatibility, masking, and spectral balance.
```

### Clases

#### `MixLinter`
Audits audio features against professional production standards.

- **Métodos:**
  - `lint_mix`: Sin documentación

---

## Módulo: `engine/mix/masking_detector.py`

**Descripción del Módulo:**
```text
Low-End Masking and Collision Detector (Kick vs Bass / Sub).
Evaluates frequency overlap, temporal coincidence, energy distribution, and phase correlation.
```

### Clases

#### `MaskingDetector`
Detects and scores spectral/temporal masking between rhythmic and melodic low-end roles.

- **Métodos:**
  - `detect_low_end_conflict`: Sin documentación

---

## Módulo: `engine/mix/psychoacoustic_masking.py`

**Descripción del Módulo:**
```text
Full-Spectrum Psychoacoustic Masking Auditor.
Implements Zwicker's 24 Critical Bark Bands and Auditory Spreading Functions
to evaluate real perceptual masking conflicts across all frequency ranges:
- Low-End (20-150 Hz): Kick vs Sub/Bass
- Low-Mids (200-600 Hz): Bass harmonics vs Keys/Guitars/Mud
- Mids & High-Mids (1-5 kHz): Vocals vs Lead Synths (Intelligibility)
- Air (8-16 kHz): Hi-hats vs Cymbals / Sibilance
Calculates exact Signal-to-Mask Ratio (SMR) and surgical dynamic EQ carving parameters.
```

### Clases

#### `PsychoacousticMaskingReport`
Comprehensive auditory masking analysis between two tracks.

- **Métodos:**
  - `to_dict`: Sin documentación

#### `PsychoacousticMaskingAuditor`
Audits full-spectrum auditory masking using 24 Bark critical bands and spreading models.

- **Métodos:**
  - `compute_bark_energy_distribution`: Calculates total energy in dB in each of the 24 Bark critical bands.
  - `apply_auditory_spreading_function`: Applies Zwicker psychoacoustic spreading function across adjacent Bark bands:
  - `audit_masking_conflict`: Audits spectral masking exerted by masker_audio onto target_audio.

---

## Módulo: `engine/mix/sidechain.py`

**Descripción del Módulo:**
```text
Auto-Sidechain Ducker:
Mathematically models and applies surgical sub-bass ducking keyed to Kick strikes.
Eliminates low-end phase cancellation and prevents master bus headroom clipping.
```

### Clases

#### `AutoSidechainDucker`
Computes exact volume ducking envelopes for 808/Sub Bass keyed to Kick transients.

- **Métodos:**
  - `calculate_ducking_envelope`: Generates volume breakpoint automation points synchronized to kick strikes.
  - `apply_sidechain_to_track`: Calculates and applies sidechain ducking curve directly to Ableton Live track.

---

## Módulo: `engine/mix/bridge.py`

**Descripción del Módulo:**
```text
AudioBridge abstraction for Level 3 / real-time / M4L integration.
Allows Mix Engine to interface with either rendered audio files or real-time Max for Live bridges.
```

### Clases

#### `AudioBridge`
Abstract interface for audio capture bridges.

- **Métodos:**
  - `connect`: Establishes connection with the audio bridge.
  - `disconnect`: Disconnects the audio bridge.
  - `is_connected`: Returns connection status.
  - `get_audio_data`: Returns audio data as (channels, samples) array in float32 and sample_rate.
  - `get_rms`: Returns overall RMS in dBFS.
  - `get_peak`: Returns peak in dBFS.

#### `RenderedFileAudioBridge`
Bridge that loads audio from rendered wav/aiff files on disk.

- **Métodos:**
  - `__init__`: Sin documentación
  - `connect`: Sin documentación
  - `disconnect`: Sin documentación
  - `is_connected`: Sin documentación
  - `get_audio_data`: Sin documentación
  - `get_rms`: Sin documentación
  - `get_peak`: Sin documentación

#### `M4LAudioBridge`
Max for Live bridge stub ready for UDP/OSC or socket streaming.
Returns status: UNAVAILABLE until M4L device is inserted in Live session.

- **Métodos:**
  - `__init__`: Sin documentación
  - `connect`: Sin documentación
  - `disconnect`: Sin documentación
  - `is_connected`: Sin documentación
  - `get_audio_data`: Sin documentación
  - `get_rms`: Sin documentación
  - `get_peak`: Sin documentación

---

## Módulo: `engine/mix/lufs_validation_gate.py`

**Descripción del Módulo:**
```text
ITU-R BS.1770-5 LUFS & True Peak End-of-Chain Validation Gate:
Audits integrated loudness, short-term dynamic range, and inter-sample True Peak.
Enforces broadcast and streaming compliance (e.g. Spotify/Apple -14.0 LUFS / -1.0 dBTP),
and calculates automatic trim compensation to prevent digital summing overload and clipping.
```

### Clases

#### `LoudnessAuditResult`
- **Métodos:**
  - `to_dict`: Sin documentación

#### `LUFSValidationGate`
End-of-chain automated loudness and inter-sample peak compliance validator.

- **Métodos:**
  - `__init__`: Sin documentación
  - `audit`: Runs complete ITU-R BS.1770-5 and Annex 2 True Peak analysis on audio array.
  - `apply_loudness_compensation`: Audits the audio signal, and if non-compliant, applies exact linear gain trim

---

## Módulo: `engine/mix/correction_engine.py`

**Descripción del Módulo:**
```text
Correction Engine: Musical hierarchy, guardrails, and closed-loop ACID corrections.
Modes: SAFE (recommend), ASSISTED (low-risk auto), AUTONOMOUS (full closed-loop).
Rolls back immediately if regressions occur on secondary musical metrics.
```

### Clases

#### `CorrectionEngine`
Orchestrates musical corrections with strict parameter guardrails and rollback safety.

- **Métodos:**
  - `__init__`: Sin documentación
  - `create_correction_plan`: Creates a conservative correction plan respecting the musical hierarchy.
  - `apply_plan`: Applies correction actions to live Ableton tracks if in ASSISTED or AUTONOMOUS mode.
  - `evaluate_correction`: Multiobjective verification:

---

## Módulo: `engine/mix/frequency_analyzer.py`

**Descripción del Módulo:**
```text
DSP Frequency and Spectral Profile Analyzer.
Computes STFT across 12 standard frequency bands and derives acoustic features.
```

### Clases

#### `FrequencyAnalyzer`
Performs FFT/STFT analysis across 12 frequency bands and derives spectral features.

- **Métodos:**
  - `analyze_bands`: Calculates power spectrum and energy metrics across 12 frequency bands.
  - `get_spectral_profile`: Computes centroid, rolloff, flatness, zero crossing rate, and classification.

---

## Módulo: `engine/mix/loudness_standards.py`

**Descripción del Módulo:**
```text
Formal DSP Measurement & Loudness Compliance Contract.
Complies with ITU-R BS.1770-5 and EBU R 128 (2023).

Architectural Principle:
Strict separation of four distinct concepts:
1. AUDIO SIGNAL: Discrete PCM time-domain samples.
2. MEASUREMENT: What did the audio physically measure? (LoudnessMeasurement)
3. PROFILE: What delivery targets/guardrails are we evaluating against? (LoudnessProfile)
4. COMPLIANCE: Does the measurement meet the selected profile? (ProfileCompliance)

No mixing of concerns: LoudnessAnalyzer only measures; LoudnessProfile evaluates.
```

### Clases

#### `MeasurementStatus`
Execution status and diagnostic result of a DSP loudness measurement.


#### `ProfileType`
Classification of delivery target authority.


#### `MeasurementWindow`
Closed set of normative measurement integration windows.


#### `ChannelLayout`
Explicit speaker and channel configurations.


#### `UnknownLoudnessProfileError`
Raised when an unrecognized loudness profile name is requested from the registry.


#### `MeasurementMetadata`
Provenance, algorithmic context, and format parameters for a loudness measurement.
Immutable to guarantee historical audit integrity.

- **Métodos:**
  - `__post_init__`: Sin documentación
  - `to_dict`: Deterministic dictionary serialization.

#### `LoudnessMeasurement`
Acoustic loudness measurement strictly describing objective audio characteristics.
Does not dictate whether the audio is acceptable, compliant, or 'too loud'.
Immutable (frozen=True) to prevent post-measurement state tampering.

- **Métodos:**
  - `__init__`: Sin documentación
  - `to_dict`: Deterministic dictionary serialization.
  - `lra`: Sin documentación
  - `true_peak`: Sin documentación
  - `sample_peak`: Sin documentación
  - `crest_factor`: Sin documentación

#### `ProfileCompliance`
Formal, immutable compliance evaluation of a LoudnessMeasurement against a LoudnessProfile.
Deterministic, side-effect free result object (Section 15).

- **Métodos:**
  - `profile_compliant`: Sin documentación
  - `target_met`: Sin documentación
  - `true_peak_safe`: Sin documentación
  - `lra_compliant`: Sin documentación
  - `measurement_valid`: Sin documentación
  - `loudness_error_lu`: Sin documentación
  - `lufs_delta`: Sin documentación
  - `true_peak_margin_db`: Sin documentación
  - `true_peak_headroom_db`: Sin documentación
  - `violations`: Sin documentación
  - `warnings`: Sin documentación
  - `to_dict`: Deterministic serialization in stable order.

#### `LoudnessProfile`
Delivery specification against which a LoudnessMeasurement is evaluated.
Centralizes acoustic targets, tolerances, and ceiling guardrails.
Immutable to guarantee safety across pipeline stages.

- **Métodos:**
  - `integrated_target`: Sin documentación
  - `max_true_peak`: Sin documentación
  - `integrated_tolerance`: Sin documentación
  - `__post_init__`: Sin documentación
  - `evaluate`: Pure, deterministic, side-effect free evaluation of a LoudnessMeasurement.
  - `to_dict`: Deterministic serialization in stable order.

#### `ProfileRegistry`
Registry accessor class maintaining backward compatibility with legacy calls.

- **Métodos:**
  - `get`: Sin documentación
  - `list_profiles`: Sin documentación

### Funciones Globales

- `get_loudness_profile`: Retrieves a loudness profile from the central registry.
- `list_loudness_profiles`: Returns the list of registered profile names in deterministic, sorted order.

---

## Módulo: `engine/mix/stereo_analyzer.py`

**Descripción del Módulo:**
```text
DSP Stereo and Mono Compatibility Analyzer.
Measures Pearson correlation, Mid/Side energy, low-frequency stereo energy, and mono loss.
```

### Clases

#### `StereoAnalyzer`
Analyzes stereo imaging and checks mono compatibility.

- **Métodos:**
  - `analyze_stereo`: Sin documentación

---

## Módulo: `engine/mix/reference_engine.py`

**Descripción del Módulo:**
```text
Reference Engine: Compares current production mix against commercial reference audio files.
Produces delta profiles for loudness, frequency balance, dynamic range, and stereo width.
```

### Clases

#### `ReferenceEngine`
Analyzes reference tracks and extracts acoustic deltas without blind copying.

- **Métodos:**
  - `compare_to_reference`: Sin documentación

---

## Módulo: `engine/mix/reports.py`

**Descripción del Módulo:**
```text
Mix Report generator: formats dual machine-readable (JSON) and human-readable (Markdown) reports.
```

### Clases

#### `MixReportGenerator`
Generates comprehensive mix analysis reports.

- **Métodos:**
  - `generate_report`: Produces machine JSON and formatted Markdown representation.

---

## Módulo: `engine/mix/transient_analyzer.py`

**Descripción del Módulo:**
```text
DSP Transient, Kick, and Bass Analyzers.
Extracts attack time, decay time, sub-frequency fundamentals, and punch.
```

### Clases

#### `TransientAnalyzer`
Analyzes envelope, attack times, decay times, and onset events.

- **Métodos:**
  - `analyze_transients`: Sin documentación
  - `analyze_kick`: Isolates kick drum characteristics: fundamental frequency, click, sub energy, decay.
  - `analyze_bass`: Analyzes bassline fundamental, harmonic saturation, low-end stereo width.

---

## Módulo: `engine/mix/vocal_analyzer.py`

**Descripción del Módulo:**
```text
Vocal role acoustic feature and balance analyzer.
```

### Clases

#### `VocalAnalyzer`
Analyzes presence, boxiness, sibilance, and stereo placement of vocal tracks.

- **Métodos:**
  - `analyze_vocal`: Sin documentación

---

## Módulo: `engine/mix/phase_alignment.py`

**Descripción del Módulo:**
```text
Phase Correlation & Mono Compatibility Auditing Engine:
Computes inter-stem phase correlation coefficients, enforces sub-bass mono collapse (<120Hz),
detects destructive phase cancellation, and calculates micro-delay transient alignment.
```

### Clases

#### `PhaseAlignmentEngine`
Audits and aligns phase relationships across multitrack stems and sub-frequencies.

- **Métodos:**
  - `calculate_phase_correlation`: Calculates Pearson correlation coefficient rho in [-1.0, 1.0].
  - `audit_sub_bass_mono`: Audits stereo energy in the sub-bass band (< 120 Hz).
  - `evaluate_phase_coherence`: Analyzes correlation score between two interacting tracks (e.g. Kick and 808 Bass).
  - `calculate_micro_delay_offset`: Calculates millisecond delay to nudge bass transient into constructive alignment with kick.
  - `generate_phase_audit_report`: Generates a complete pre-master phase correlation audit manifest.

---

## Módulo: `engine/mix/loudness_analyzer.py`

**Descripción del Módulo:**
```text
DSP Loudness and Headroom Analyzer.
Complies with ITU-R BS.1770-5 (LUFS Integrated, Short-term, Momentary, True Peak, RMS, and LRA).
Provides strict separation between acoustic measurement and profile compliance.
```

### Clases

#### `LoudnessAnalyzer`
Analyzes perceptual loudness, peak, and True Peak per ITU-R BS.1770-5 and EBU R 128.

- **Métodos:**
  - `__init__`: Sin documentación
  - `_apply_k_weighting`: Applies ITU-R BS.1770-5 K-weighting pre-filter (Stage 1 High-Shelf + Stage 2 RLB High-Pass).
  - `calculate_lufs_with_blocks`: Calculates ITU-R BS.1770-5 LUFS and returns internal block powers and short-term values.
  - `calculate_lufs`: Backwards-compatible wrapper returning (Integrated, Short-term, Momentary).
  - `calculate_lra`: Calculates Loudness Range (LRA) according to EBU Tech 3342 / ITU-R BS.1770-5.
  - `calculate_true_peak`: Calculates True Peak per ITU-R BS.1770-5 Annex 2 using a 4x oversampling
  - `calculate_headroom`: Classifies headroom status according to standard thresholds.
  - `measure`: Normative ITU-R BS.1770-5 measurement generating a full LoudnessMeasurement.

---

## Módulo: `engine/mix/models.py`

**Descripción del Módulo:**
```text
Domain models and dataclasses for Mix Intelligence Engine (Digital Ear).
```

### Clases

#### `Severity`

#### `HeadroomClassification`

#### `DynamicClassification`

#### `FrequencyBandData`
- **Métodos:**
  - `to_dict`: Sin documentación

#### `SpectralProfile`
- **Métodos:**
  - `to_dict`: Sin documentación

#### `StereoFeatures`
- **Métodos:**
  - `to_dict`: Sin documentación

#### `TransientFeatures`
- **Métodos:**
  - `to_dict`: Sin documentación

#### `KickAnalysis`
- **Métodos:**
  - `to_dict`: Sin documentación

#### `BassAnalysis`
- **Métodos:**
  - `to_dict`: Sin documentación

#### `VocalAnalysis`
- **Métodos:**
  - `to_dict`: Sin documentación

#### `AudioFeatures`
- **Métodos:**
  - `to_dict`: Sin documentación

#### `MaskingResult`
- **Métodos:**
  - `to_dict`: Sin documentación

#### `GenreProfile`

#### `MixContext`
- **Métodos:**
  - `__post_init__`: Sin documentación

#### `MixIssue`
- **Métodos:**
  - `to_dict`: Sin documentación

#### `CorrectionAction`
- **Métodos:**
  - `to_dict`: Sin documentación

#### `CorrectionPlan`
- **Métodos:**
  - `to_dict`: Sin documentación

#### `CorrectionEvaluation`
- **Métodos:**
  - `to_dict`: Sin documentación

### Funciones Globales

- `severity_from_score`: Sin documentación

---

## Módulo: `engine/mix/render_manager.py`

**Descripción del Módulo:**
```text
Temporary Render Manager and Cache for Mix Intelligence Engine.
Stores temporary renders in .mcp_analysis/ isolated from user session files.
Caches analysis results to avoid redundant renders.
```

### Clases

#### `RenderCache`
In-memory and file-backed cache for audio analysis results.

- **Métodos:**
  - `__init__`: Sin documentación
  - `make_cache_key`: Sin documentación
  - `get`: Sin documentación
  - `set`: Sin documentación
  - `clear`: Sin documentación

#### `RenderManager`
Manages temporary audio renders for offline analysis.

- **Métodos:**
  - `__init__`: Sin documentación
  - `create_temp_path`: Sin documentación
  - `validate_file`: Sin documentación
  - `render_analysis_target`: Creates a temporary render target.
  - `cleanup`: Removes temporary files older than max_age_seconds.

---

## Módulo: `engine/mix/static_auditor.py`

**Descripción del Módulo:**
```text
AbletonEngine Static Mix Auditor:
Analyzes DAW track layout, device chains, fader staging, and routing
prior to playback or mastering, flagging risks and generating actionable advice.
```

### Clases

#### `StaticMixAuditor`
Evaluates session layout without requiring playback or audio capture.

- **Métodos:**
  - `audit_session`: Takes session info dictionary (tracks, master volume, etc.) and returns structured report.
  - `format_report_es`: Formats audit report into concise Spanish markdown.

---

## Módulo: `engine/mix/fader_rider.py`

**Descripción del Módulo:**
```text
Vocal & Lead Fader Riding Automation Engine:
Computes section-aware dynamic fader riding curves across 96 bars,
maintaining constant vocal intelligibility and emotional climax presence without over-compression.
```

### Clases

#### `VocalLeadFaderRider`
Generates continuous fader rides across 96 bars for vocal hooks and lead melodies.

- **Métodos:**
  - `db_to_fader_val`: Converts dB fader adjustment into Ableton Live normalized volume fader value.
  - `generate_fader_automation_envelope`: Generates continuous volume breakpoint automation points across all 96 bars (384 beats).
  - `get_fader_riding_manifest`: Returns the complete 96-bar fader riding manifest with section descriptions.

---

## Módulo: `engine/mix/confidence.py`

**Descripción del Módulo:**
```text
Confidence and statistical reliability estimation for audio measurements.
Enforces rule: never perform automatic modifications on low-confidence data.
```

### Clases

#### `ConfidenceEvaluator`
Calculates statistical confidence [0.0, 1.0] for various DSP measurements.

- **Métodos:**
  - `estimate_fundamental_confidence`: Estimates confidence of fundamental frequency detection based on:
  - `estimate_transient_confidence`: Estimates confidence of transient detection based on duration and onset count.
  - `estimate_stereo_confidence`: Estimates confidence of stereo metrics based on channel count and audio energy.
  - `is_safe_for_auto_correction`: Checks if confidence meets strict guardrail for automatic modification.

---

## Módulo: `engine/mix/audio_capture.py`

**Descripción del Módulo:**
```text
Audio capture abstraction and engine.
Decouples audio source acquisition from DSP analysis.
Supports RenderedFileSource, StemSource, M4LSource, and ExternalCaptureSource.
```

### Clases

#### `AudioSource`
Abstract base class for audio sources.

- **Métodos:**
  - `get_audio_data`: Returns audio as float32 ndarray with shape (channels, samples) and sample rate.
  - `get_duration`: Returns duration in seconds.

#### `RenderedFileSource`
Source that reads an audio file (.wav, .aiff, .flac) from disk.

- **Métodos:**
  - `__init__`: Sin documentación
  - `get_audio_data`: Sin documentación
  - `get_duration`: Sin documentación

#### `StemSource`
Source containing multiple role-specific stem audio files.

- **Métodos:**
  - `__init__`: Sin documentación
  - `get_audio_data`: Sin documentación
  - `get_stem`: Sin documentación
  - `get_duration`: Sin documentación

#### `M4LSource`
Source connected to a Max for Live streaming device bridge.

- **Métodos:**
  - `__init__`: Sin documentación
  - `get_audio_data`: Sin documentación
  - `get_duration`: Sin documentación

#### `ExternalCaptureSource`
Source recorded or captured from an external soundcard or interface.


#### `AudioCaptureEngine`
Orchestrates audio capture in different operational modes.

- **Métodos:**
  - `__init__`: Sin documentación
  - `capture`: Captures audio according to specified mode:

---

## Módulo: `engine/mix/dynamics_analyzer.py`

**Descripción del Módulo:**
```text
DSP Dynamics and Crest Factor Analyzer.
Measures dynamic range, crest factor, and variations.
```

### Clases

#### `DynamicsAnalyzer`
Analyzes dynamic range and transient-to-body ratios.

- **Métodos:**
  - `analyze_dynamics`: Returns:

---

## Módulo: `engine/mix/frequency_slotting.py`

**Descripción del Módulo:**
```text
Frequency Slotting & Complementary EQ Carving Engine:
Calculates surgical notch, bell, and shelf cuts to interlock conflicting stems,
carves out acoustic pockets, and enforces strict High-Pass Filtering across all 8 session tracks.
```

### Clases

#### `FrequencySlottingEngine`
Calculates complementary EQ curves to eliminate frequency collisions between stems.

- **Métodos:**
  - `freq_to_normalized`: Converts frequency in Hz (10 to 22000) to EQ Eight's normalized float [0.0..1.0].
  - `get_multitrack_hpf_scaffold`: Returns surgical High-Pass Filter cutoff frequencies and Q values
  - `calculate_complementary_carving`: Calculates interlocking EQ Eight curves between two competing elements:
  - `generate_full_session_slotting_plan`: Generates the master surgical frequency slotting blueprint for the entire 8-track session.

---

## Módulo: `engine/mix/spatial/depth.py`

**Descripción del Módulo:**
```text
3D Depth & Spatial Staging Engine:
Calculates tempo-synced acoustic depth planes (Foreground, Midground, Background)
and dynamic ducked reverb envelopes to achieve massive clarity and separation.
```

### Clases

#### `DepthPlane`

#### `SpatialProfile`
- **Métodos:**
  - `to_dict`: Sin documentación

#### `DepthStagingEngine`
Orchestrates acoustic depth placement and dynamic space automation.

- **Métodos:**
  - `calculate_plane_parameters`: Calculates tempo-synchronized pre-delay, acoustic absorption filters,
  - `calculate_ducked_reverb_envelope`: Computes reverb send gain automation points that duck when instrument notes are playing,

---

## Módulo: `engine/mix/eq/dynamic_eq.py`

**Descripción del Módulo:**
```text
Dynamic EQ & Adaptive De-Esser Engine:
Implements frequency-selective dynamic compression and de-essing in Ableton Live.
Selectively suppresses harsh sibilance (5.5kHz - 8.5kHz) and cleans frequency masking collisions
only when energy exceeds perceptual thresholds, preserving full brightness and warmth.
```

### Clases

#### `DynamicEQBand`
- **Métodos:**
  - `calculate_gain_reduction`: Computes dynamic cut in dB when signal exceeds threshold.

#### `DynamicEQEngine`
Intelligent dynamic equalizer and de-esser configurator for Ableton Live tracks.

- **Métodos:**
  - `freq_to_normalized`: Sin documentación
  - `calculate_sibilance_profile`: Analyzes audio buffer to detect sibilance/harshness energy ratio:
  - `apply_adaptive_deesser`: Deploys and calibrates an authentic surgical De-Esser in Ableton Live:
  - `apply_frequency_unmasking`: Dynamically carves space in target_track_index whenever masking_track_index produces energy

---

## Módulo: `engine/mix/eq/resonance.py`

**Descripción del Módulo:**
```text
Resonance Hunter & Surgical Dynamic EQ Engine:
Scans audio signals with high-resolution FFT spectral decomposition, detects narrow
ear-fatiguing parasitic resonances (Q >= 6.0), and generates precise EQ Eight notch cuts.
```

### Clases

#### `ResonantPeak`
- **Métodos:**
  - `to_dict`: Sin documentación

#### `ResonanceHunter`
Detects parasitic spectral resonances and configures surgical EQ Eight cuts.

- **Métodos:**
  - `detect_resonances`: Analyzes audio samples via FFT to find sharp spectral anomalies exceeding
  - `generate_eq_eight_parameters`: Translates detected resonant peaks into Ableton EQ Eight band parameters.

---

## Módulo: `engine/mix/gain_staging/auto_stager.py`

**Descripción del Módulo:**
```text
Full Session Auto Gain Staging & Master Headroom Engine:
Recalibrates individual track faders across the entire session to enforce
strict studio gain staging hierarchy (Kick anchor, Bass, Snare, Leads, Harmony, Foley),
guaranteeing a clean -6.0 dBFS headroom margin on the Master bus before mastering.
```

### Clases

#### `TrackGainCalibration`

#### `AutoGainStagingEngine`
Calculates and applies mathematically coherent gain staging across all session tracks.

- **Métodos:**
  - `classify_role`: Sin documentación
  - `db_to_linear`: Converts dB to Live 12 fader linear gain using audio-tapered calibration (0 dB ≈ 0.85).
  - `calculate_session_calibration`: Calculates optimal fader positions for all session tracks.
  - `apply_gain_staging`: Calculates and applies fader volumes across all session tracks in Live.

---

## Módulo: `engine/production/rollback.py`

**Descripción del Módulo:**
```text
Rollback Engine for the Production Intelligence Engine (PIE).
Documento 12 — ROLLBACK DE PRIMERA CLASE, RECUPERACIÓN Y CONSISTENCIA CAUSAL.

Architectural Invariants:
1. Atomicity: Whole operation reverts or none does (ACID transactional boundary).
2. Idempotency: Multiple rollback requests for same target return ALREADY_REVERTED without re-mutating.
3. Traceability & Causal Non-Destruction: Original nodes (INTENT, DECISION, ACTION, RESULT) are NEVER deleted.
   Rollback creates new causal nodes:
   ROLLBACK_DECISION -> ROLLBACK_ACTION -> ROLLBACK_VERIFICATION -> ROLLBACK_RESULT.
4. Double Fingerprint Validation: Verified at plan creation and immediately before commit.
5. Inviolability of Locks: Locked objects cannot be modified by rollback.
6. 10 Canonical Rollback Policies enforced deterministically.
7. Anti-loop Guardrail: Enforces max_automatic_rollback_depth to prevent infinite rollback loops.
```

### Clases

#### `RollbackEngine`
First-Class Rollback Engine for PIE Governance Layer.
Orchestrates atomic rollbacks, dependency chain checks, crash recovery,
and verified non-destructive causal tracking.

- **Métodos:**
  - `__init__`: Sin documentación
  - `create_plan`: Synthesizes an immutable RollbackPlan for the requested decision or transaction.
  - `validate`: Validates a RollbackPlan against the 10 canonical rollback policies (Doc 12 Sec 35).
  - `execute`: Executes a validated RollbackPlan inside an atomic transaction.
  - `verify`: Explicit post-rollback verification comparing acoustic measurements
  - `recover`: Recovers an interrupted or incomplete transaction based on journal state
  - `status`: Returns the current RollbackStatus of a rollback.
  - `explain`: Reconstructs the complete causal explanation of a rollback (Doc 12 Sec 34).
  - `_is_already_reverted`: Determines if target_decision_id was already reverted previously (Idempotency Invariant).
  - `_synthesize_inverse_operation`: Synthesizes inverse operation based on action type and snapshot data (Doc 12 Sec 9 & 54, 55).
  - `_apply_operation_to_context`: Applies inverse operation to the active ProductionContext and ShadowGraph.
  - `_record_rollback_in_graph`: Appends first-class causal rollback nodes into ProductionGraph (Doc 12 Sec 31, 32, 33).

---

## Módulo: `engine/production/memory.py`

**Descripción del Módulo:**
```text
Decision Memory for the Production Intelligence Engine (PIE).
Structured, contextual memory for decision lineage, historical comparison, and traceable reuse.
Explicitly non-ML; enforces the absolute invariant that historical matches never auto-execute.
```

### Clases

#### `MemoryStatus`

#### `DecisionMemory`
Context-aware memory of prior decisions, verified actions, and acoustic outcomes.
Serves as an evidence engine: produces candidates for current validation, never executes blindly.

- **Métodos:**
  - `__init__`: Sin documentación
  - `records`: Sin documentación
  - `record`: Stores a decision with required musical, technical, and acoustic context.
  - `get`: Sin documentación
  - `search`: Contextual search for historically verified actions matching current scenario.
  - `invalidate`: Invalidates a memory record when subsequent findings disprove it.
  - `validate`: Re-validates a memory record.
  - `supersede`: Marks a prior decision as superseded by a newer, higher-confidence decision.
  - `link`: Links two decisions that informed each other.
  - `get_related`: Retrieves related memory records linked to a specific decision.
  - `to_dict`: Sin documentación
  - `from_dict`: Sin documentación

---

## Módulo: `engine/production/verification.py`

**Descripción del Módulo:**
```text
engine/production/verification.py

Verification Engine for the Production Intelligence Engine (PIE).
Fase 11 de 18 — VERIFICATION ENGINE: Verificación Multivariable,
Regresión Acústica y Criterio Formal de Éxito.

Contractual Invariants:
- BEFORE -> ACTION -> AFTER -> EXPECTED DELTA -> ACTUAL DELTA -> REGRESSION CHECK -> POLICY CHECK -> VERDICT.
- Multivariable evaluation: never rely on a single metric to evaluate production changes.
- Strict verdict priority: INVALID -> ROLLBACK_REQUIRED -> FAILED -> VERIFIED_WITH_WARNING -> VERIFIED.
- Snapshot immutability: VerificationSnapshot and MetricSnapshot are frozen dataclasses.
- Complete float precision: full float precision in decision logic; rounding allowed only for display.
- NaN / Inf detection: immediately invalidates evaluation (verdict = INVALID).
- Missing metrics: marked as UNAVAILABLE, never defaulted to 0.0.
- Verified Rollback: post-rollback state verified against baseline.
- Deterministic cryptographic hash (SHA-256) for auditability.
```

### Clases

#### `VerificationVerdict`
Deterministic verdict of post-execution verification.


#### `MetricSnapshot`
Immutable measurement point for a specific acoustic or structural metric.

- **Métodos:**
  - `__post_init__`: Sin documentación
  - `to_dict`: Sin documentación
  - `from_dict`: Sin documentación

#### `VerificationSnapshot`
Immutable collection of acoustic metrics captured at a discrete point in time.

- **Métodos:**
  - `__post_init__`: Sin documentación
  - `get_metric`: Sin documentación
  - `get_value`: Sin documentación
  - `to_dict`: Sin documentación
  - `from_dict`: Sin documentación

#### `MetricExpectation`
Formal expected change for a specific metric resulting from an action or plan.

- **Métodos:**
  - `__post_init__`: Sin documentación
  - `to_dict`: Sin documentación
  - `from_dict`: Sin documentación

#### `RegressionRule`
Guardrail rule specifying permissible limits or bounds for a metric.

- **Métodos:**
  - `__post_init__`: Sin documentación
  - `to_dict`: Sin documentación
  - `from_dict`: Sin documentación

#### `MetricDelta`
Quantified differential between baseline and post-execution measurements.

- **Métodos:**
  - `to_dict`: Sin documentación
  - `from_dict`: Sin documentación

#### `RegressionResult`
Record of a detected acoustic regression or boundary violation.

- **Métodos:**
  - `to_dict`: Sin documentación
  - `from_dict`: Sin documentación

#### `VerificationReport`
Comprehensive, cryptographically auditable verification outcome.
Distinguishes RESULT (what happened) from VERIFICATION (whether it met criteria).

- **Métodos:**
  - `__post_init__`: Sin documentación
  - `compute_hash`: Sin documentación
  - `passed`: Sin documentación
  - `status`: Sin documentación
  - `actual_delta`: Sin documentación
  - `expected_delta`: Sin documentación
  - `regression_messages`: Sin documentación
  - `to_dict`: Sin documentación
  - `from_dict`: Sin documentación

#### `VerificationResult`
Outcome of comparing pre- and post-execution acoustic measurements.

- **Métodos:**
  - `metrics_evaluated`: Sin documentación
  - `to_dict`: Sin documentación

#### `VerificationEngine`
Deterministic Verification Engine for PIE.
Performs multi-variable comparison between expected and actual acoustic deltas.
Evaluates acoustic regressions, profile guardrails, and rollback verification.

- **Métodos:**
  - `__init__`: Sin documentación
  - `capture_snapshot`: Converts measurements dictionary into an immutable VerificationSnapshot.
  - `capture_before`: Captures pre-execution baseline snapshot.
  - `capture_after`: Captures post-execution snapshot.
  - `compare`: Deterministic multi-variable comparison between before and after snapshots.
  - `verify`: High-level verification of a plan against before/after measurements or snapshots.
  - `verify_rollback`: Verifies that an atomic rollback accurately restored the session to baseline.

#### `VerificationMatrix`
Evaluates multi-variable success criteria and checks for secondary regressions.
Maintains 100% backward compatibility for Document 10 and existing test suites,
delegating to the deterministic VerificationEngine.

- **Métodos:**
  - `__init__`: Sin documentación
  - `evaluate`: Compares before and after measurements against expected deltas and guardrails.

### Funciones Globales

- `_lookup_metric`: Helper to lookup metric values handling standard aliases.

---

## Módulo: `engine/production/completeness.py`

**Descripción del Módulo:**
```text
Production Completeness Gate & Invariant Auto-Resolver.

Ensures that no production is left incomplete, silent, or structurally deficient:
1. INV-SOUND-01: No MIDI track with clips may have 0 devices (No Silent Tracks).
2. INV-STRUCT-02: Minimum core structural roles (Drums, Bass, Harmony, Lead) must be represented.
3. INV-TIMELINE-03: Arrangement timeline must be populated across song structure (>= 16 bars).
4. INV-NAV-04: Cue points / Section locators must define major narrative boundaries.
5. INV-MASTER-05: Master bus must possess dynamics/limiting control.
6. INV-GAP-06: No dead air gaps (>= 2 bars) allowed in the arrangement timeline.
7. Auto-Remediation:
   - Automatically resolves and loads verified native Live 12 or Vital presets onto silent tracks.
   - Automatically bridges timeline dead air gaps with appropriate harmonic/rhythmic material.
```

### Clases

#### `CompletenessViolationType`

#### `ViolationSeverity`

#### `CompletenessViolation`
- **Métodos:**
  - `to_dict`: Sin documentación

#### `RemediationResult`
- **Métodos:**
  - `to_dict`: Sin documentación

#### `CompletenessReport`
- **Métodos:**
  - `to_dict`: Sin documentación

#### `ProductionCompletenessGate`
Formal Quality Gate enforcing complete, sounding, gapless productions.

- **Métodos:**
  - `deduce_role_from_track`: Heuristically deduce musical role from track name and clip names.
  - `map_role_to_core_category`: Sin documentación
  - `audit_session`: Audits an Ableton session via an adapter, reporting defects and auto-healing.
  - `_remediate_gap`: Auto-bridges dead air by duplicating an active harmonic clip into the gap.
  - `_remediate_track`: Finds preset and loads it into the track to fix the silent track violation.

---

## Módulo: `engine/production/boundary.py`

**Descripción del Módulo:**
```text
Production API Boundary for MCP Layer (Documento 13).
Encapsulates all 9 canonical MCP production tools with deterministic validation,
error mapping, concurrency protection, idempotency, and audit logging.
Prevents business logic leakage into server.py while enforcing strict safety invariants.
```

### Clases

#### `ProductionAPIBoundary`
Singleton-capable boundary providing the 9 canonical MCP production tools.

- **Métodos:**
  - `__init__`: Sin documentación
  - `_get_plan_lock`: Sin documentación
  - `_success_response`: Sin documentación
  - `_error_response`: Sin documentación
  - `production_status`: Returns the current state of Production Governance infrastructure.
  - `production_plan`: Transforms a musical intent into a candidate plan without executing any mutations.
  - `production_validate`: Validates a previously created plan against current session state,
  - `production_execute`: Executes a validated production plan atomically through the ProductionExecutor.
  - `production_explain`: Reconstructs the full causal explanation for a decision or node.
  - `production_history`: Queries historical decisions ordered by timestamp DESC, decision_id ASC.
  - `production_graph`: Queries ProductionGraph statistics ('summary') or DAG structure ('dag').
  - `production_rollback`: Reverts a decision or transaction atomically, non-destructively,
  - `production_memory_search`: Searches historical decision memory.

### Funciones Globales

- `get_production_boundary`: Returns the managed singleton instance of ProductionAPIBoundary.
- `reset_production_boundary`: Resets singleton instance for testing isolation.
- `production_status`: Sin documentación
- `production_plan`: Sin documentación
- `production_validate`: Sin documentación
- `production_execute`: Sin documentación
- `production_explain`: Sin documentación
- `production_history`: Sin documentación
- `production_graph`: Sin documentación
- `production_rollback`: Sin documentación
- `production_memory_search`: Sin documentación

---

## Módulo: `engine/production/serializer.py`

**Descripción del Módulo:**
```text
Atomic persistence for PIE ProductionGraph, DecisionMemory, and Plans.
Uses atomic file writes (write to temp file in target dir then atomic os.replace)
to guarantee persistence safety against crashes and power failures.
```

### Clases

#### `ProductionStorage`
Manages disk persistence for production state.
Guarantees atomic writes (flush + fsync + os.replace) and explicit corruption detection.

- **Métodos:**
  - `__init__`: Sin documentación
  - `_atomic_write`: Writes content to a temp file in target directory, flushes, fsyncs, then atomically replaces.
  - `save_graph`: Sin documentación
  - `load_graph`: Sin documentación
  - `save_memory`: Sin documentación
  - `load_memory`: Sin documentación
  - `save_decisions`: Sin documentación
  - `load_decisions`: Sin documentación
  - `save_metadata`: Sin documentación
  - `load_metadata`: Sin documentación
  - `save_plan`: Sin documentación
  - `load_plan`: Sin documentación
  - `save_execution`: Sin documentación
  - `load_execution`: Sin documentación
  - `save_snapshot`: Sin documentación
  - `load_snapshot`: Sin documentación
  - `save_fingerprint`: Sin documentación
  - `load_fingerprint`: Sin documentación
  - `save_verification`: Sin documentación
  - `load_verification`: Sin documentación
  - `save_rollback_plan`: Sin documentación
  - `load_rollback_plan`: Sin documentación
  - `save_rollback_result`: Sin documentación
  - `load_rollback_result`: Sin documentación
  - `append_rollback_journal`: Sin documentación
  - `read_rollback_journal`: Sin documentación
  - `create_backup`: Creates a timestamped backup before modifying critical state (Doc 12 Sec 30).
  - `save_with_integrity_hash`: Saves document with schema version and canonical SHA-256 content hash (Doc 12 Sec 29).
  - `load_with_integrity_hash`: Loads document and cryptographically validates content hash against payload (Doc 12 Sec 29).
  - `recover_startup_state`: Validates state on startup (Section 71):

---

## Módulo: `engine/production/graph.py`

**Descripción del Módulo:**
```text
Production Causal Graph (DAG).
Maintains the directed acyclic graph of production decisions, observations, actions, and results.
Guarantees aciclicity, deterministic serialization, and causal explainability.
```

### Clases

#### `ProductionGraph`
Directed Acyclic Graph (DAG) representing the causal lineage of music production.
Separates WHAT EXISTS (SessionShadowGraph) from WHY IT EXISTS (ProductionGraph).

- **Métodos:**
  - `__init__`: Sin documentación
  - `increment_version`: Sin documentación
  - `has_node`: Returns True if node_id exists in the graph.
  - `add_node`: Adds a node to the graph. Node IDs must be unique.
  - `remove_node`: Removes a node and all incident edges from the graph.
  - `add_edge`: Adds a directed causal edge from source to target.
  - `remove_edge`: Removes an edge between two nodes.
  - `_is_reachable`: BFS search to determine if target_id is reachable from start_id.
  - `get_node`: Sin documentación
  - `get_parents`: Returns direct predecessor nodes.
  - `get_children`: Returns direct successor nodes.
  - `get_outgoing_edges`: Returns outgoing edges from node_id.
  - `get_incoming_edges`: Returns incoming edges to node_id.
  - `edges`: Sin documentación
  - `get_ancestors`: Returns all transitive predecessors in topological order.
  - `get_descendants`: Returns all transitive successors.
  - `explain_decision`: Reconstructs the full causal explanation for a decision or node.
  - `topological_sort`: Computes a deterministic topological sort of the DAG.
  - `validate_integrity`: Validates graph structural integrity:
  - `to_dict`: Full serializable dictionary representation.
  - `serialize_deterministic`: Serializes graph deterministically byte-for-byte for hashing and verification.
  - `from_dict`: Sin documentación

---

## Módulo: `engine/production/recipe_engine.py`

**Descripción del Módulo:**
```text
Production Recipe Engine & Authoritative Skeleton Generator.
Inverted Control Architecture:
- The Engine owns the Recipe and defines the Skeleton Questionnaire.
- The Engine asks the necessary parameters to construct the musical skeleton.
- The AI communicates with the Engine, supplying the creative intent.
- The Engine physically loads VSTs/instruments, verifies device presence,
  sculpts parameters, arranges clips, and performs real acoustic meter & LUFS audits.
- Absolutely zero fake passes: if signal is 0.0000 or devices are missing, it strictly fails.
```

### Clases

#### `DeviceLoadFailureError`
Raised when an instrument or effect fails to physically load into Live.


#### `PhysicalAcousticSilenceError`
Raised when a track produces zero audible signal (meter < 0.001) during playback.


#### `MasterLoudnessComplianceError`
Raised when master audio fails integrated LUFS or True Peak criteria.


#### `ArrangementMissingClipsError`
Raised when one or more tracks have zero clips in the Arrangement view timeline.


#### `DrumRackEmptyError`
Raised when a Drum Rack device contains zero playable sample pads.


#### `GenreProductionProfile`

#### `RecipeSection`

#### `TrackBlueprint`

#### `ProductionRecipe`

#### `ProductionRecipeEngine`
Authoritative Engine that imposes the recipe questionnaire and executes song creation.

- **Métodos:**
  - `get_skeleton_questionnaire`: The Engine presents the complete structural questionnaire to construct a song skeleton.
  - `resolve_uri`: Resolves device name to exact Live browser URI.
  - `audit_incremental_addition`: Audita de manera incremental la sonoridad acústica (medidores de nivel y LUFS estimado)
  - `execute_ai_loudness_decision`: Ejecuta de forma determinista la decisión correctiva seleccionada por la IA a partir
  - `offer_genre_production_menu`: Offers structured production skeletons, musical scales, recommended instruments,
  - `resolve_audio_sample`: Resolves the authentic studio audio sample for an audio track blueprint.
  - `get_section_automation_menu`: Analiza las secciones del Arrangement y genera un menú estructurado de curvas de automatización
  - `apply_section_automations`: Aplica físicamente las curvas de automatización seleccionadas en el Arrangement de Ableton Live.
  - `execute_physical_recipe`: Physically executes the recipe inside Ableton Live:
  - `build_zomboy_brostep_recipe`: Constructs the authoritative Zomboy-style Heavy Brostep / Tearout Dubstep recipe.
  - `produce_zomboy_full_song_0_to_100`: Executes the entire 0-to-100 Zomboy Heavy Brostep beat through the authoritative engine.

---

## Módulo: `engine/production/planner.py`

**Descripción del Módulo:**
```text
ProductionPlanner for the Production Intelligence Engine (PIE).
Formulates causal, policy-compliant production plans.
Generates multi-candidate interventions, records policy rejections in the graph,
and selects the optimal plan following the Principle of Minimum Intervention.
```

### Clases

#### `ProductionPlanner`
Deterministic production planner.
Explores candidate interventions, checks policy compliance, logs rejections,
and returns a minimal-intervention plan bound by session fingerprint.

- **Métodos:**
  - `__init__`: Sin documentación
  - `plan`: Plans intervention based on musical intent, acoustic measurements, and policies.
  - `_generate_candidates`: Generates a spectrum of candidates: minimal, aggressive, and alternative.

---

## Módulo: `engine/production/context.py`

**Descripción del Módulo:**
```text
ProductionContext for the Production Intelligence Engine (PIE).
Bridges the Live SessionShadowGraph, TransactionManager, and DSP analyzers.
Calculates deterministic session fingerprints (global and scoped) to detect stale plans.
```

### Clases

#### `ProductionContext`
Unified context representing current project and audio session state.
Provides scoped fingerprinting to distinguish relevant vs irrelevant state changes.

- **Métodos:**
  - `__init__`: Sin documentación
  - `get_project_id`: Sin documentación
  - `get_session_state`: Sin documentación
  - `get_track`: Sin documentación
  - `get_device`: Sin documentación
  - `get_locked_state`: Sin documentación
  - `get_locks`: Sin documentación
  - `lock`: Sin documentación
  - `unlock`: Sin documentación
  - `get_track_ref`: Sin documentación
  - `get_device_ref`: Sin documentación
  - `capture`: Sin documentación
  - `get_fingerprint`: Sin documentación
  - `get_session_fingerprint`: Sin documentación
  - `compute_session_fingerprint`: Computes deterministic SHA-256 hash of session state.
  - `is_stale_for_plan`: Checks if relevant state has shifted since plan creation.
  - `record_measurement`: Stores a pre-recorded measurement for a target track.
  - `get_measurements`: Sin documentación
  - `capture_measurements`: Captures acoustic measurements using ITU-R BS.1770-5.

---

## Módulo: `engine/production/full_song_producer.py`

**Descripción del Módulo:**
```text
Complete End-to-End Song Generator (Phases 1-7, 0 to 100).
- Song Identity: Inspired by 'Bodies' by JID (142 BPM, F minor, Atlanta bounce, sliding 808s, Rhodes keys, call/response lead, vocal chops).
- Instrumentation: Real host VST3 plugins (Arturia Stage-73 V2, Arturia Analog Lab V, Vital Audio Vital)
  and fully populated 808 Core Kit (.adg) Drum Rack (16 pads).
- Physical Effects: Real VST & native chains (FabFilter Pro-Q 4, ValhallaVintageVerb, ValhallaDelay, Cradle The God Particle, EQ Eight, Saturator, Drum Buss).
- 96 bars / 384 beats in Live Arrangement timeline with playback initiated.
```

### Clases

#### `AbletonLiveConnection`
Direct TCP connection to Ableton Live Remote Script on port 9877.

- **Métodos:**
  - `__init__`: Sin documentación
  - `connect`: Sin documentación
  - `send_command`: Sin documentación
  - `close`: Sin documentación

### Funciones Globales

- `note_to_live_dict`: Converts a NoteEvent or dict to Ableton Live's exact note format.
- `produce_song_0_to_100`: Sin documentación

---

## Módulo: `engine/production/models.py`

**Descripción del Módulo:**
```text
Canonical Data Models for the Production Intelligence Engine (PIE) Governance Layer.
Documento 5 — PRODUCTION MODELS & GOVERNANCE CONTRACT (PIE-H1-D05).

ARCHITECTURAL INVARIANTS:
1. Production Models son contratos de dominio, no motores de ejecución.
2. Ningún modelo de producción puede ejecutar una acción por sí mismo.
3. Toda mutación futura deberá pasar por:
   Policy -> Plan -> Validation -> Transaction -> Execution -> Verification.
4. Los modelos existen y se validan completamente sin Ableton Live, MCP, red,
   filesystem ni bibliotecas de grafos externas.
```

### Clases

#### `NodeType`
The 15 canonical node classifications representing production causality.


#### `EdgeType`
Causal relationship between nodes in the Production DAG (Section 7 & Test 2).


#### `EvidenceType`
Classification of causal evidence in the production lineage (Section 8).


#### `DecisionStatus`
Lifecycle state of a production decision (Section 9).


#### `PolicyDecision`
Policy evaluation outcome decision (Document 9 Section 6).


#### `PolicySeverity`
Enforcement severity of a production policy (Section 11).


#### `ProductionReference`
Reference to a real object in the Ableton Live project (Section 12 & 13).
Purely declarative: does not verify whether the object currently exists.

- **Métodos:**
  - `__post_init__`: Sin documentación
  - `to_dict`: Sin documentación

#### `Evidence`
Verifiable piece of acoustic, structural, or user evidence (Section 14 & 15).

- **Métodos:**
  - `__post_init__`: Sin documentación
  - `to_dict`: Sin documentación

#### `ProductionIntent`
High-level user musical or technical objective (Section 16 & 17).
Describes WHAT the user wants to achieve, NOT how to do it.

- **Métodos:**
  - `__post_init__`: Sin documentación
  - `to_dict`: Sin documentación

#### `ProductionAction`
Specific physical parameter mutation or structural operation (Section 24 & 25).
Defaults to transaction_required=True.

- **Métodos:**
  - `__post_init__`: Sin documentación
  - `to_dict`: Sin documentación

#### `PolicyViolation`
Specific violation record explaining why a policy declined an action (Document 9 Section 7).

- **Métodos:**
  - `__post_init__`: Sin documentación
  - `__contains__`: Enables pythonic substring checking: 'gain reduction' in violation.
  - `__str__`: Sin documentación
  - `to_dict`: Sin documentación
  - `from_dict`: Sin documentación

#### `PolicyEvaluation`
Outcome emitted by the ProductionPolicyEngine (Document 9 Section 8).
Strict Precedence: CRITICAL -> ERROR -> WARNING -> INFO.
Inviolable Invariant: CRITICAL violation CAN NEVER be ALLOW or ALLOW_WITH_WARNING.

- **Métodos:**
  - `__post_init__`: Sin documentación
  - `allowed`: Sin documentación
  - `status`: Sin documentación
  - `to_dict`: Sin documentación
  - `to_json`: Serializes the PolicyEvaluation to a JSON string.
  - `from_dict`: Reconstructs PolicyEvaluation from a dictionary without loss of types, enums, or floats.
  - `from_json`: Reconstructs PolicyEvaluation from a JSON string.

#### `ProductionPolicy`
Metadata representation of a production policy rule (Document 9 Section 9).

- **Métodos:**
  - `__post_init__`: Sin documentación
  - `to_dict`: Sin documentación

#### `MeasurementReference`
Lightweight pointer to an external DSP LoudnessMeasurement (Section 29).
Prevents duplicating heavy signal arrays or DSP logic in the production layer.

- **Métodos:**
  - `__post_init__`: Sin documentación
  - `to_dict`: Sin documentación

#### `VerificationResult`
Comparison record: expected acoustic delta vs actual delta (Sections 30 & 31).
Distinguishes RESULT (what occurred) from VERIFICATION (whether it met specs).

- **Métodos:**
  - `__post_init__`: Sin documentación
  - `to_dict`: Sin documentación

#### `RollbackReference`
Explicit pointer linking a rollback action to the original decision (Sections 32 & 33).
Preserves audit history: decisions are never physically deleted.

- **Métodos:**
  - `__post_init__`: Sin documentación
  - `to_dict`: Sin documentación

#### `ParameterRef`
- **Métodos:**
  - `to_dict`: Sin documentación
  - `from_dict`: Sin documentación

#### `DeviceRef`
- **Métodos:**
  - `__post_init__`: Sin documentación
  - `to_dict`: Sin documentación
  - `from_dict`: Sin documentación

#### `ClipRef`
- **Métodos:**
  - `to_dict`: Sin documentación
  - `from_dict`: Sin documentación

#### `TrackRef`
- **Métodos:**
  - `__post_init__`: Sin documentación
  - `to_dict`: Sin documentación
  - `from_dict`: Sin documentación

#### `ProductionContextSnapshot`
Immutable context snapshot under which a decision or plan was conceived (Sections 34 & 35, Doc 10 Sec 43).
Stores session_fingerprint without computing it.

- **Métodos:**
  - `__post_init__`: Sin documentación
  - `timestamp`: Sin documentación
  - `to_dict`: Sin documentación
  - `from_dict`: Sin documentación

#### `ProductionCandidate`
Purely declarative candidate strategy (Sections 36, 37, 38).
Strictly normalized scores: 0.0 to 1.0. No side effects or global references.

- **Métodos:**
  - `__post_init__`: Sin documentación
  - `to_dict`: Sin documentación

#### `ProductionNode`
Verifiable node in the Production Causal DAG (Sections 18, 19, 20).
Represents WHY an action occurred or WHAT state justified it.
Deeply immutable: defensive copying prevents external mutation contamination (Section 51).

- **Métodos:**
  - `__post_init__`: Sin documentación
  - `_infer_evidence_type`: Sin documentación
  - `parent_ids`: Sin documentación
  - `to_dict`: Sin documentación
  - `from_dict`: Sin documentación

#### `ProductionDecision`
Complete causal record of a music production decision (Sections 21, 22, 23).
Validates COMMITTED invariant: requires candidate, evidence, hypothesis, and rationale
unless classified as NO_OP.

- **Métodos:**
  - `__post_init__`: Sin documentación
  - `transition_to`: Transitions decision status validating lifecycle rules.
  - `to_dict`: Sin documentación
  - `from_dict`: Sin documentación

#### `ProductionPlan`
Declarative production plan (Sections 39 & 40).
Pure data + decisions + references + validations.
Never includes sockets, live objects, callbacks, or execution threads.

- **Métodos:**
  - `__post_init__`: Sin documentación
  - `transition_to`: Transitions plan status.
  - `to_dict`: Sin documentación
  - `from_dict`: Sin documentación

#### `ProductionResult`
Final execution result model (Sections 41 & 42).
Requires error_code when success=False.

- **Métodos:**
  - `__post_init__`: Sin documentación
  - `to_dict`: Sin documentación

#### `SessionFingerprint`
Cryptographic SHA-256 fingerprint of Live session state (Document 10 Sections 8-13).
Ensures safe commit and stale plan rejection.

- **Métodos:**
  - `__post_init__`: Sin documentación
  - `to_dict`: Sin documentación
  - `from_dict`: Sin documentación

#### `PlanValidationResult`
Result of validating a ProductionPlan before execution (Document 10 Sections 15 & 38).

- **Métodos:**
  - `__post_init__`: Sin documentación
  - `to_dict`: Sin documentación
  - `from_dict`: Sin documentación

#### `ExecutionResult`
Detailed result of executing a ProductionPlan through ProductionExecutor (Document 10 Section 38).

- **Métodos:**
  - `__post_init__`: Sin documentación
  - `to_dict`: Sin documentación
  - `__getitem__`: Sin documentación
  - `__contains__`: Sin documentación
  - `get`: Sin documentación
  - `keys`: Sin documentación
  - `values`: Sin documentación
  - `items`: Sin documentación
  - `from_dict`: Sin documentación

#### `RollbackStatus`
Lifecycle status for a first-class rollback operation (Doc 12 Sec 4.1).


#### `RollbackType`
Taxonomy of rollback triggers (Doc 12 Sec 5).


#### `RollbackScope`
Scope of rollback execution (Doc 12 Sec 15).


#### `RecoveryStatus`
Crash recovery and transaction journal states (Doc 12 Sec 23).


#### `IncompleteTransactionState`
Evaluation of incomplete transaction state on crash recovery (Doc 12 Sec 25).


#### `VerificationTolerance`
Centralized tolerances for post-rollback verification (Doc 12 Sec 19).

- **Métodos:**
  - `to_dict`: Sin documentación
  - `from_dict`: Sin documentación

#### `RollbackRequest`
Formal request to revert a prior production decision or transaction (Doc 12 Sec 6).

- **Métodos:**
  - `__post_init__`: Sin documentación
  - `to_dict`: Sin documentación
  - `from_dict`: Sin documentación

#### `RollbackPlan`
Immutable specification of atomic operations needed to restore session state (Doc 12 Sec 7).

- **Métodos:**
  - `__post_init__`: Sin documentación
  - `to_dict`: Sin documentación
  - `from_dict`: Sin documentación

#### `RollbackResult`
Final verified outcome of executing a RollbackPlan (Doc 12 Sec 63).

- **Métodos:**
  - `to_dict`: Sin documentación
  - `from_dict`: Sin documentación

#### `RecoveryResult`
Outcome of an automated or requested transaction recovery (Doc 12 Sec 24 & 25).

- **Métodos:**
  - `to_dict`: Sin documentación
  - `from_dict`: Sin documentación

#### `RollbackJournalEvent`
Append-only journal entry tracking granular rollback steps (Doc 12 Sec 26).

- **Métodos:**
  - `to_dict`: Sin documentación
  - `from_dict`: Sin documentación

### Funciones Globales

- `generate_node_id`: Generates a stable, unique node identifier conforming to prd_<type>_<uuid>.

---

## Módulo: `engine/production/exceptions.py`

**Descripción del Módulo:**
```text
Exception hierarchy for the Production Intelligence Engine (PIE) Governance Layer.
All errors provide structured error details for auditable diagnosis.
```

### Clases

#### `ProductionError`
Base exception for all production governance, causal graph, and policy errors.

- **Métodos:**
  - `__init__`: Sin documentación
  - `to_dict`: Sin documentación

#### `ModelValidationError`
Raised when a production model violates its contract.


#### `InvalidNodeTypeError`
Raised when an invalid or unknown node type is specified.


#### `InvalidEdgeTypeError`
Raised when an invalid or unknown edge type is specified.


#### `InvalidDecisionStateError`
Raised when a decision status or transition violates lifecycle rules.


#### `InvalidEvidenceError`
Raised when evidence records are malformed or invalid.


#### `GraphIntegrityError`
Raised when an operation would violate graph integrity (e.g. cycle formation).


#### `DuplicateNodeError`
Raised when attempting to add a node with an ID that already exists with conflicting data.


#### `NodeNotFoundError`
Raised when referencing a node that does not exist in the graph.


#### `EdgeNotFoundError`
Raised when referencing an edge that does not exist in the graph.


#### `PolicyViolationError`
Raised when an action or plan violates an unbypassable production policy.

- **Métodos:**
  - `__init__`: Sin documentación

#### `TransactionRequiredError`
Raised when a state-mutating operation is executed without an active transaction.


#### `LockedObjectError`
Raised when attempting to mutate an entity that is locked by user or engine.


#### `ProductionExecutionError`
Base exception for all production execution failures.


#### `StalePlanError`
Raised when attempting to execute a plan whose relevant dependencies have changed.


#### `PlanAlreadyExecutedError`
Raised when attempting to re-execute a plan that has already been committed.


#### `TargetNotFoundError`
Raised when a target track, device, parameter, or clip does not exist.


#### `ExecutionStateUnknownError`
Raised when execution state is ambiguous (e.g. connection drops during mutate call).


#### `ConcurrentExecutionError`
Raised when an execution cannot acquire the session or target execution lock.


#### `CriticalRecoveryRequiredError`
Raised when the session is in an unverified/inconsistent state requiring manual recovery.


#### `PlanNotFoundError`
Raised when a specified production plan cannot be found in memory or storage.


#### `DecisionNotFoundError`
Raised when a specified production decision cannot be found in graph or memory.


#### `InvalidPlanError`
Raised when a plan definition is malformed or internally contradictory.


#### `ExecutionError`
Raised when staging or committing a planned transaction fails.


#### `VerificationError`
Base exception for all verification failures.


#### `VerificationFailedError`
Raised when post-execution verification detects an unhandled acoustic regression or failure.


#### `AcousticRegressionError`
Raised when post-execution verification detects an acoustic regression (e.g. true peak clipping, phase collapse).


#### `InvalidMeasurementError`
Raised when an acoustic measurement is missing, corrupt, or mathematically invalid.


#### `VerificationDataMismatchError`
Raised when algorithm versions or context data between before and after snapshots mismatch.


#### `RollbackVerificationError`
Raised when verifying a rollback reveals the rollback is incomplete or divergent.


#### `RollbackRequiredError`
Raised when an automated rollback is triggered and required.


#### `RollbackFailureError`
Raised when an atomic rollback operation fails or restored fingerprint does not match.


#### `RollbackTargetNotFoundError`
Raised when the target decision, action, or transaction to roll back does not exist.


#### `NonReversibleActionError`
Raised when attempting to roll back an action declared as irreversible.


#### `ConflictingStateError`
Raised when the session was modified externally/manually after the target action.


#### `DependencyConflictError`
Raised when subsequent decisions depend on the target decision and scope is SINGLE_DECISION.


#### `InvalidSnapshotError`
Raised when snapshot is missing, corrupted, from another project, or incomplete.


#### `StaleRollbackPlanError`
Raised when the session fingerprint changed in a way that invalidates the rollback plan.


#### `RollbackExecutionInterruptedError`
Raised when socket disconnect or crash occurs during rollback execution, requiring recovery.


#### `MaxRollbackDepthExceededError`
Raised when automatic rollback depth limit is exceeded to prevent infinite loops.


#### `RollbackBlockedLockedObjectError`
Raised when an entity affected by rollback is locked by user or engine.


#### `PersistenceError`
Raised when loading or saving production state to disk fails.


#### `SerializationError`
Raised when graph, memory, or plan serialization/deserialization fails or encounters corruption.


#### `ProductionStateCorruptionError`
Raised when persisted state (e.g. graph.json) is corrupted on disk.


---

## Módulo: `engine/production/executor.py`

**Descripción del Módulo:**
```text
ProductionExecutor for the Production Intelligence Engine (PIE).
Documento 10 — EXECUTION INTEGRATION, SESSION FINGERPRINT & SAFE COMMIT.

Executes production plans through atomic transactions with strict safety invariants:
1. Double validation: Planner Policy Check + Executor Policy Check.
2. session_fingerprint recalculated immediately before transaction initiation.
3. Strict ACID transactions through TransactionManager.
4. Idempotency detection (NO_OP).
5. Post-execution acoustic verification.
6. Verified automatic rollback: verifies state restoration against pre-fingerprint.
7. Concurrency exclusion lock.
8. Non-blocking simulation (dry-run).
```

### Clases

#### `ProductionExecutor`
Executes production plans safely, reversibly, and traceably.
Guarantees double validation, concurrency exclusion, and verified rollback.

- **Métodos:**
  - `__init__`: Sin documentación
  - `validate_plan`: Performs dry-run validation of a plan against the current session context (Doc 10 Sec 15).
  - `simulate`: Dry-run simulation of plan execution (Doc 10 Sec 15).
  - `verify`: Evaluates acoustic verification between before and after measurements (Doc 10 Sec 15).
  - `execute`: Executes a ProductionPlan through the 10-step transactional pipeline (Doc 10 Sec 20).
  - `_execute_internal`: Sin documentación
  - `rollback`: Rolls back a transaction or decision via the RollbackEngine (Doc 12 Sec 42).
  - `rollback_decision`: Manually rolls back a previously committed decision (Backward compatibility).
  - `recover_execution`: Reconstructs execution state to diagnose and recover from interruptions (Doc 10 Sec 38).

---

## Módulo: `engine/production/policies.py`

**Descripción del Módulo:**
```text
Production Policy Engine for PIE (Hito 1 — Documento 9).
Enforces acoustic guardrails, domain separation axioms, transaction safety,
stale plan detection, and post-execution regression prevention.

ARCHITECTURAL INVARIANTS:
1. Double Policy Validation:
   Planner validation -> Policy check -> Execution -> Policy validation AGAIN -> Commit.
2. Inviolability of CRITICAL severity:
   CRITICAL violations CAN NEVER be bypassed, forced (no force=True, bypass=True),
   nor converted into warnings.
3. Strict Determinism:
   Same context + same action + same policy versions = same evaluation and same SHA-256 fingerprint.
4. Non-Execution:
   Purely diagnostic evaluation; never mutates Live session or executes transactions.
```

### Clases

#### `BasePolicyEvaluator`
Abstract base evaluator for deterministically testing an action against a policy.

- **Métodos:**
  - `__init__`: Sin documentación
  - `policy_id`: Sin documentación
  - `name`: Sin documentación
  - `version`: Sin documentación
  - `severity`: Sin documentación
  - `description`: Sin documentación
  - `evaluate_rule`: Evaluates the specific policy rule.
  - `evaluate`: Evaluates compliance and produces a PolicyEvaluation.

#### `MasterLimitPolicy`
CRITICAL: Controls limiter gain reduction (<= 2.5 dB) and True Peak ceiling.
Prevents destructive over-limiting and patching mix problems via master limiting.

- **Métodos:**
  - `__init__`: Sin documentación
  - `evaluate_rule`: Sin documentación

#### `MasterEQPolicy`
CRITICAL: Restricts mastering EQ moves to conservative adjustments
(maximum 2 bands, maximum ±1.0 dB per band).

- **Métodos:**
  - `__init__`: Sin documentación
  - `evaluate_rule`: Sin documentación

#### `MixMasterBoundaryPolicy`
CRITICAL: Separation of Mix vs Master Axiom.
If an issue is diagnosed as a MIX_PROBLEM (kick/bass masking, mud, resonance, etc.),
mastering processing MUST be rejected and redirected to mix intervention.

- **Métodos:**
  - `__init__`: Sin documentación
  - `evaluate_rule`: Sin documentación

#### `LockedObjectPolicy`
CRITICAL: Protects tracks, clips, and devices marked locked from modification or deletion.

- **Métodos:**
  - `__init__`: Sin documentación
  - `evaluate_rule`: Sin documentación

#### `TransactionRequiredPolicy`
CRITICAL: Enforces that state-mutating operations must have an active transaction ID.

- **Métodos:**
  - `__init__`: Sin documentación
  - `evaluate_rule`: Sin documentación

#### `StalePlanPolicy`
CRITICAL: Rejects execution if session dependencies have changed since plan creation.

- **Métodos:**
  - `__init__`: Sin documentación
  - `evaluate_rule`: Sin documentación

#### `RegressionPolicy`
CRITICAL: Requires rollback if post-execution acoustic verification exhibits secondary regressions.

- **Métodos:**
  - `__init__`: Sin documentación
  - `evaluate_rule`: Sin documentación

#### `ProductionPolicyEngine`
Deterministic governance engine evaluating actions, plans, and candidates.
Coordinates the 7 canonical policies, guarantees CRITICAL inviolability,
and calculates deterministic SHA-256 evaluation fingerprints.

- **Métodos:**
  - `__init__`: Sin documentación
  - `_register_default_policies`: Sin documentación
  - `register_policy`: Sin documentación
  - `get_policy`: Sin documentación
  - `list_policies`: Sin documentación
  - `policies`: Sin documentación
  - `_compute_sha256`: Calculates canonical sorted-key JSON SHA-256 fingerprint.
  - `evaluate`: Evaluates an action/candidate against applicable production policies.
  - `validate`: Validates action against policies and raises PolicyViolationError (preserving evaluation)
  - `evaluate_result`: Evaluates post-execution acoustic results against regression policies (Section 35).

---

## Módulo: `engine/production/copilot/recipes.py`

**Descripción del Módulo:**
```text
Macro Production Recipes:
High-level orchestrators that package the entire best-practice chain of commands
into single atomic operations, guaranteeing zero omitted steps by default.
```

### Clases

#### `MacroProductionRecipes`
End-to-end intelligent macro pipelines for rhythm, harmony, and finalization.

- **Métodos:**
  - `produce_complete_rhythm_section`: Produces an entire rhythm section end-to-end:
  - `produce_complete_harmony_and_lead`: Produces harmony and lead layers:
  - `finalize_mix_and_master`: All-in-one macro recipe finalizing the song:
  - `orchestrate_complete_song`: All-in-one grand orchestrator:

---

## Módulo: `engine/production/copilot/role_orchestrator.py`

**Descripción del Módulo:**
```text
Atomic Role Orchestrator (Capa 3: Operaciones Atómicas de Rol):
Indivisible ACID orchestrator that bundles:
1. Instrument loading from verified catalog / installed plugins.
2. Physical LOM verification (device presence check).
3. Sound parameter sculpting (Delta >= 1 rule applied from blueprints).
4. Multi-section musical composition (notes tailored by role, key, and scale).
5. Arrangement timeline clip deployment (covers all song sections).
6. Track renaming and graph metadata synchronization.

Guarantees zero silent tracks, zero unconfigured plugins, and zero omitted clips.
```

### Clases

#### `RoleTrackOrchestrator`
- **Métodos:**
  - `normalize_role`: Normalizes user role string to standard uppercase role with strict lexical precedence.
  - `resolve_instrument`: Resolves instrument URI and display name from installed plugins or curated catalog.
  - `verify_instrument_loaded`: Physically queries Live LOM to ensure an authentic instrument is loaded.
  - `generate_musical_notes`: Composes complete multi-section NoteEvents tailored to role and arrangement length.
  - `orchestrate_role_track`: Executes complete Atomic Role Orchestration:

---

## Módulo: `engine/production/copilot/stepper.py`

**Descripción del Módulo:**
```text
Executive Copilot Stepper Engine:
Actively inspects the Ableton Live session state, detects acoustic and musical gaps,
and enforces an interactive decision checklist so the AI never forgets critical production steps.
```

### Clases

#### `ExecutiveCopilotEngine`
The proactive executive producer that inspects, guides, and enforces session quality.

- **Métodos:**
  - `__init__`: Sin documentación
  - `reset`: Resets copilot state for a fresh song production session.
  - `inspect_session`: Inspects session tracks, clips, and parameters to discover pending decisions.
  - `_register_pending`: Sin documentación
  - `_build_state`: Sin documentación
  - `execute_decision`: Executes an interactive decision:
  - `preflight_check`: Validates that zero neglected decisions remain before final mastering export.
  - `run_autonomous_pipeline`: Runs the complete Copilot pipeline autonomously from DNA to Master Delivery in a single command.

---

## Módulo: `engine/production/copilot/guided_session.py`

**Descripción del Módulo:**
```text
Copilot Guided Session Engine (Asistente Conversacional por Estados):
Single-tool state machine wizard for interactive music production.

Replaces disjointed tool calling with a structured 7-phase conversational interview
between Copilot (the Technical Director) and the Producer (AI/User).

Workflow Phases:
1. PHASE_1_TRACKS: Channels, names & acoustic role reservation.
2. PHASE_2_SECTIONS: Song structure, section names & arrangement cue points.
3. PHASE_3_INSTRUMENTS: Track-by-track verified VST/Kit selection (Strict LOM verification, Drum Pad population check, zero silent swallow).
4. PHASE_4_PARAM_SCULPTING: Track-by-track synthesis sculpting across 4 engine quadrants (Oscillators, Filter, ADSR, Macros) with track gain staging.
5. PHASE_5_INSERT_EFFECTS: Effect-by-effect, parameter-by-parameter insert FX tuning (Drum Buss, Glue, Saturator, Valhalla, Delay, OTT) with continuous loudness feedback.
6. PHASE_6_COMPOSITION: Modular 7-section composition across slots 0..6 with structural silences and arrangement timeline deployment.
7. PHASE_7_MIX_MASTER: Strict ITU-R BS.1770-5 Real Audio Gatekeeper (start_playback, zero synthetic estimations, blocks progression until compliant).
8. PHASE_8_COMPLETED: Production certified compliant, Copilot stays active listening for adjustments.
```

### Clases

#### `CopilotGuidedSession`
State machine wizard orchestrating the entire music production via conversational dialogue.

- **Métodos:**
  - `__init__`: Sin documentación
  - `_default_state`: Sin documentación
  - `_load_state`: Sin documentación
  - `_save_state`: Sin documentación
  - `reset`: Resets the state machine back to step 1.
  - `step`: Sin documentación
  - `_prompt_phase_1`: Sin documentación
  - `_handle_phase_1`: Sin documentación
  - `_prompt_phase_2`: Sin documentación
  - `_handle_phase_2`: Sin documentación
  - `_prompt_current_track_instrument`: Sin documentación
  - `_handle_phase_3`: Sin documentación
  - `_prompt_current_track_params`: Sin documentación
  - `_handle_phase_4`: Sin documentación
  - `_prompt_current_fx_device`: Sin documentación
  - `_handle_phase_5`: Sin documentación
  - `_prompt_phase_6`: Sin documentación
  - `_handle_phase_6`: Sin documentación
  - `_build_recipe_from_session`: Sin documentación
  - `_prompt_phase_7`: Sin documentación
  - `_handle_phase_7`: Sin documentación
  - `_prompt_phase_8`: Sin documentación
  - `_handle_phase_8`: Sin documentación
  - `_handle_phase_9`: Sin documentación
  - `_audit_and_prepare_stems`: Audits the entire arrangement, verifies sub-bass phase cross-correlation (rho >= +0.30),

### Funciones Globales

- `_normalize_text`: Sin documentación
- `resolve_genre_style`: Resolves genre name or bpm into canonical GenreDrumStyle enum.
- `generate_modular_section_notes`: Sin documentación

---

## Módulo: `engine/production/copilot/models.py`

**Descripción del Módulo:**
```text
Executive Copilot Data Models:
Defines the 7 formal production phases, decision status lifecycles,
and state snapshots that prevent selective amnesia and tool sprawl in LLMs.
```

### Clases

#### `ProductionPhase`

#### `DecisionStatus`

#### `ProductionDecision`
- **Métodos:**
  - `to_dict`: Sin documentación

#### `CopilotState`
- **Métodos:**
  - `to_dict`: Sin documentación

---

## Módulo: `engine/mastering/rollback.py`

**Descripción del Módulo:**
```text
Mastering Rollback Manager.
Restores master track to a previous snapshot upon regression.
```

### Clases

#### `MasterRollbackManager`
Executes atomic reversion of master chain parameters.

- **Métodos:**
  - `__init__`: Sin documentación
  - `rollback`: Sin documentación

---

## Módulo: `engine/mastering/reference_match.py`

**Descripción del Módulo:**
```text
Reference Gap Analyzer.
Compares master with commercial reference tracks without blind imitation.
Protects against copying flawed references (clipping, extreme compression, phase inversion).
```

### Clases

#### `ReferenceGapAnalyzer`
Extracts reference deltas while guarding against reference production flaws.

- **Métodos:**
  - `calculate_gap_map`: Sin documentación
  - `generate_matching_guidance`: Sin documentación
  - `analyze_reference`: Sin documentación

---

## Módulo: `engine/mastering/release_package.py`

**Descripción del Módulo:**
```text
Commercial Release Packager:
Constructs, renders, hashes, and validates the complete professional distribution package
ready for digital service providers (Spotify, Apple Music, Tidal), sync licensing,
and physical CD pressing:
1. 24-bit / 48 kHz Lossless Master WAV
2. 16-bit / 44.1 kHz Red Book CD Master WAV (TPDF triangular dithered)
3. 320 kbps Commercial Promo MP3
4. Clean Instrumental Master WAV
5. Acapella / Vocal Master WAV
6. Full 5-Group Commercial Stem Archive (Drums, Bass, Music, Vocals, FX)
7. Complete release_manifest.json with ISRC, UPC, BS.1770-5 metrics, and SHA-256 checksums.
```

### Clases

#### `CommercialReleasePackager`
End-to-end commercial release bundler and distribution manifest generator.

- **Métodos:**
  - `generate_isrc`: Generates standard ISO 3901 ISRC code: CC-XXX-YY-NNNNN.
  - `generate_upc_barcode`: Generates 12-digit universal product code (UPC-A) with Mod-10 checksum.
  - `apply_tpdf_dither`: Applies Triangular Probability Density Function (TPDF) dither.
  - `compute_sha256`: Sin documentación
  - `create_release_package`: Builds the entire market-ready commercial delivery package.

---

## Módulo: `engine/mastering/saturation.py`

**Descripción del Módulo:**
```text
Master Saturation and Harmonic Exciter Engine.
Conservative analog tape/tube warmth; automatically bypassed if distortion is detected.
```

### Clases

#### `MasterSaturationEngine`
Generates subtle analog saturation if spectral profile is thin.

- **Métodos:**
  - `plan_saturation`: Sin documentación
  - `calculate_settings`: Sin documentación

---

## Módulo: `engine/mastering/dynamics.py`

**Descripción del Módulo:**
```text
Dynamic Preservation Engine.
Monitors crest factor, dynamic range, and transient health to prevent squashing.
```

### Clases

#### `DynamicPreservationEngine`
Calculates dynamic preservation score and loudness efficiency.

- **Métodos:**
  - `evaluate_dynamics`: Sin documentación

---

## Módulo: `engine/mastering/mastering_analyzer.py`

**Descripción del Módulo:**
```text
Mastering Acoustic Inspector.
Extracts acoustic mastering indicators from audio buffers, rendered files, or live sessions.
Complies with ITU-R BS.1770-5 and EBU R 128 through LoudnessAnalyzer.
```

### Clases

#### `MasteringAnalyzer`
Performs comprehensive acoustic analysis for pre-master and post-master evaluation.

- **Métodos:**
  - `__init__`: Sin documentación
  - `analyze_audio_data`: Sin documentación
  - `analyze_file`: Sin documentación
  - `analyze_session`: Sin documentación

---

## Módulo: `engine/mastering/quality_control.py`

**Descripción del Módulo:**
```text
Final Quality Control (QC) Engine.
Audits DC offset, digital silence/dropouts, true peak clipping, channel imbalance, and mono collapse.
```

### Clases

#### `FinalQualityControlEngine`
Audits mastered audio for all critical technical and acoustic requirements.

- **Métodos:**
  - `check_features`: Sin documentación
  - `check_audio`: Sin documentación
  - `execute_qc`: Sin documentación

---

## Módulo: `engine/mastering/loudness_target.py`

**Descripción del Módulo:**
```text
Loudness Target Calculator for delivery standards.
Consolidates delivery targets by consuming canonical profiles directly from engine.mix.loudness_standards.
```

### Clases

#### `LoudnessTargetCalculator`
Calculates delivery targets and loudness specs from the unified standards registry.

- **Métodos:**
  - `get_target_specs`: Sin documentación
  - `get_target_lufs`: Sin documentación

### Funciones Globales

- `_build_delivery_specs`: Builds delivery specifications dynamically from the single canonical source of truth.

---

## Módulo: `engine/mastering/compressor.py`

**Descripción del Módulo:**
```text
Master Bus Glue Compressor Engine.
Focuses on dynamic stabilization, groove cohesion, and glue, NOT volume maximization.
```

### Clases

#### `MasterCompressorEngine`
Evaluates need for gentle bus compression glue.

- **Métodos:**
  - `plan_compression`: Sin documentación
  - `calculate_settings`: Sin documentación

---

## Módulo: `engine/mastering/guided_mastering.py`

**Descripción del Módulo:**
```text
Guided Step-by-Step Mastering Engine:
Executes the physical 7-point native mastering process in Ableton Live:
Point 1: Headroom Audit Pre-Master (-8.0 to -6.0 dBFS)
Point 2: Master EQ Eight (HPF 25Hz, Mud Dip 250Hz, Air 12kHz)
Point 3: Master Glue Compressor (2:1 Ratio, 30ms Attack, Auto Release, 1.5-2.0dB GR)
Point 4: Master Saturator (Analog Clip curve, +1.5dB Drive for harmonic density)
Point 5: Master Utility (Bass Mono <120Hz, Stereo Width 100%)
Point 6: Master Brickwall Limiter (Ceiling -0.3 dBTP for club, Lookahead 5ms)
Point 7: Iterative Physical LUFS Calibration Loop with REAL METER MEASUREMENT in Ableton Live.
```

### Clases

#### `DeliveryProfile`

#### `MasteringStepResult`

#### `GuidedMasteringEngine`
Guided step-by-step master chain builder with physical calibration.

- **Métodos:**
  - `execute_guided_mastering`: Executes each mastering point sequentially, validating each point before proceeding.

---

## Módulo: `engine/mastering/limiter.py`

**Descripción del Módulo:**
```text
Master True Peak Limiter Engine.
Controls inter-sample peaks with strict maximum gain reduction guardrails (<= 2.5 dB).
```

### Clases

#### `MasterLimiterEngine`
Manages true peak brickwall limiting with gain reduction safety.

- **Métodos:**
  - `plan_limiter`: Sin documentación
  - `calculate_settings`: Sin documentación

---

## Módulo: `engine/mastering/eq.py`

**Descripción del Módulo:**
```text
Conservative Mastering EQ Engine.
Restricted to subtle surgical adjustments (typically ±0.5 dB to ±1.0 dB, top 2 bands).
```

### Clases

#### `MasterEQEngine`
Generates conservative mastering EQ moves.

- **Métodos:**
  - `plan_eq_actions`: Sin documentación
  - `calculate_eq`: Sin documentación

---

## Módulo: `engine/mastering/snapshot.py`

**Descripción del Módulo:**
```text
Master Snapshot Manager.
Captures master track parameters and effects state before modification.
```

### Clases

#### `MasterSnapshotManager`
Stores master track device state snapshots for rollback.

- **Métodos:**
  - `__init__`: Sin documentación
  - `create_snapshot`: Sin documentación
  - `capture_snapshot`: Sin documentación
  - `get_snapshot`: Sin documentación
  - `get_latest_snapshot`: Sin documentación
  - `list_snapshots`: Sin documentación
  - `delete_snapshot`: Sin documentación

---

## Módulo: `engine/mastering/true_peak.py`

**Descripción del Módulo:**
```text
True Peak Protection Engine.
Defines platform true peak ceilings and verifies inter-sample peak compliance.
Consolidates ceiling limits from engine.mix.loudness_standards.
```

### Clases

#### `TruePeakEngine`
Platform True Peak limit definitions and verification.

- **Métodos:**
  - `get_ceiling`: Sin documentación
  - `get_target`: Sin documentación

---

## Módulo: `engine/mastering/reports.py`

**Descripción del Módulo:**
```text
Mastering Report Generator.
Produces structured JSON and human-readable executive Markdown report.
```

### Clases

#### `MasteringReportGenerator`
Formats mastering summaries, QC gates, and history.

- **Métodos:**
  - `generate_master_report`: Sin documentación
  - `generate_report`: Sin documentación

---

## Módulo: `engine/mastering/tonal_balance.py`

**Descripción del Módulo:**
```text
Tonal Balance Analyzer across 7 standard mastering frequency bands.
```

### Clases

#### `TonalBalanceAnalyzer`
Extracts energy across 7 mastering bands and computes spectral difference maps.

- **Métodos:**
  - `analyze_tonal_balance`: Sin documentación
  - `compute_difference_map`: Sin documentación

---

## Módulo: `engine/mastering/mastering_chain.py`

**Descripción del Módulo:**
```text
Native Ableton Mastering Chain Builder.
Constructs and configures the standard mastering chain on the Master track
using Live 12 Suite native devices with [MCP] prefix and logical ownership tags.

Chain Order:
1. [MCP] Master EQ (EQ Eight)
2. [MCP] Master Glue (Glue Compressor)
3. [MCP] Master Saturation (Saturator)
4. [MCP] Master Stereo (Utility)
5. [MCP] Master Limiter (Limiter)
```

### Clases

#### `MasterChainBuilder`
Manages the lifecycle and parameter configuration of the native master track chain.

- **Métodos:**
  - `__init__`: Sin documentación
  - `adapter`: Sin documentación
  - `build_master_chain`: Sin documentación
  - `configure_chain`: Sin documentación
  - `get_chain_status`: Sin documentación
  - `remove_master_chain`: Sin documentación

---

## Módulo: `engine/mastering/optimizer.py`

**Descripción del Módulo:**
```text
Multi-Objective Pareto Optimizer.
Weighs competing mastering dimensions (loudness vs dynamic damage vs translation).
```

### Clases

#### `MasteringOptimizer`
Evaluates multi-objective tradeoffs and determines whether a master is superior.

- **Métodos:**
  - `evaluate_pareto`: Sin documentación
  - `optimize_plan`: Sin documentación

---

## Módulo: `engine/mastering/models.py`

**Descripción del Módulo:**
```text
Domain models and dataclasses for Mastering Engine, Reference Matching, and Final QC.
```

### Clases

#### `DeliveryTarget`

#### `MasteringMode`

#### `QualityGate`

#### `MasterReadiness`
- **Métodos:**
  - `to_dict`: Sin documentación

#### `TonalDifferenceMap`
- **Métodos:**
  - `to_dict`: Sin documentación

#### `FinalQualityScore`
- **Métodos:**
  - `overall_score`: Sin documentación
  - `tonal_balance_score`: Sin documentación
  - `dynamic_preservation_score`: Sin documentación
  - `loudness_compliance_score`: Sin documentación
  - `stereo_integrity_score`: Sin documentación
  - `translation_score`: Sin documentación
  - `gate`: Sin documentación
  - `to_dict`: Sin documentación

#### `MasteringProfile`
- **Métodos:**
  - `to_dict`: Sin documentación

#### `MasterAction`
- **Métodos:**
  - `__post_init__`: Sin documentación
  - `target_device`: Sin documentación
  - `to_dict`: Sin documentación

#### `MasterPlan`
- **Métodos:**
  - `target`: Sin documentación
  - `to_dict`: Sin documentación

#### `MasterHistoryEntry`
- **Métodos:**
  - `to_dict`: Sin documentación

---

## Módulo: `engine/mastering/export_manager.py`

**Descripción del Módulo:**
```text
Export Manager with SHA256 Hashing and Versioning.
Saves versioned masters (v001, v002) without destructive overwriting.
```

### Clases

#### `MasterExportManager`
Manages audio file export, version numbering, and sample integrity hashing.

- **Métodos:**
  - `__init__`: Sin documentación
  - `compute_audio_hash`: Computes deterministic SHA256 hash of float32 sample data.
  - `get_next_version`: Sin documentación
  - `export_master`: Sin documentación
  - `export`: Sin documentación

---

## Módulo: `engine/mastering/translation_test.py`

**Descripción del Módulo:**
```text
Translation Simulation Engine.
Simulates listening conditions across 6 acoustic environments:
Full Stereo, Mono Collapse, Low Volume (40 phon), High Volume (90 phon), Bass Reduced, High Cut.
```

### Clases

#### `TranslationTestEngine`
Tests how well the master translates to various consumer playback systems.

- **Métodos:**
  - `test_audio_features`: Sin documentación
  - `test_translation`: Sin documentación
  - `test_audio_buffer`: Sin documentación

---

## Módulo: `engine/mastering/stereo.py`

**Descripción del Módulo:**
```text
Master Stereo and Low-End Mono Protection Engine.
```

### Clases

#### `MasterStereoEngine`
Ensures solid mono sub-bass (<100 Hz) and healthy correlation.

- **Métodos:**
  - `evaluate_stereo`: Sin documentación
  - `suggest_stereo_action`: Sin documentación
  - `calculate_settings`: Sin documentación

---

## Módulo: `engine/mastering/mastering_engine.py`

**Descripción del Módulo:**
```text
Mastering Intelligence Engine — Master Facade.
Coordinates all mastering components: loudness target calibration, true peak protection,
dynamic preservation, conservative tonal EQ, glue compression, subtle warmth,
stereo correction, multi-objective Pareto optimization, translation testing,
reference matching, final quality control, snapshot rollback, and versioned export.
```

### Clases

#### `MasteringEngine`
Complete Mastering Intelligence Engine Facade.

- **Métodos:**
  - `__init__`: Sin documentación
  - `check_readiness`: Sin documentación
  - `generate_plan`: Sin documentación
  - `create_chain`: Sin documentación
  - `preview_master`: Sin documentación
  - `apply_master`: Sin documentación
  - `rollback`: Sin documentación
  - `evaluate_master`: Sin documentación
  - `compare_reference`: Sin documentación
  - `test_translation`: Sin documentación
  - `run_quality_control`: Sin documentación
  - `export_master`: Sin documentación
  - `get_report`: Sin documentación
  - `master_project`: Sin documentación

---

## Módulo: `engine/mastering/live_master_chain.py`

**Descripción del Módulo:**
```text
Live Master Chain Engine:
Constructs, inserts, and calibrates the physical 5-device native mastering chain
in Ableton Live (EQ Eight, Glue Compressor, Saturator, Utility [Bass Mono <120Hz], Limiter)
strictly compliant with ITU-R BS.1770-5 and international streaming/club delivery targets.
```

### Clases

#### `LiveMasterChainEngine`
Orchestrator for the physical 5-device mastering chain in Ableton Live.

- **Métodos:**
  - `freq_to_normalized`: Converts frequency in Hz to EQ Eight normalized float [0.0..1.0].
  - `get_target_specs`: Returns acoustic targets (LUFS, True Peak, Limiter Gain) per delivery profile.
  - `setup_live_mastering_chain`: Loads and parameterizes the 5 mastering devices in sequence on track_index:
  - `deploy_master_chain`: Convenience alias for setup_live_mastering_chain.

---

## Módulo: `engine/fx/track_fx_rack.py`

**Descripción del Módulo:**
```text
Track FX Rack & Channel Strip Supervisor:
Enforces mandatory audio effect selection, insertion, and parameterization per track role.
Strictly prevents plugin duplication and stacking:
- Audits existing devices on the track before loading.
- Reuses existing devices if already present on the track.
- Deploys verified parameter tuning to every plugin (VST3 and native).
```

### Clases

#### `TrackFXRack`
Manages role-based channel strip construction and parameter tuning.

- **Métodos:**
  - `get_role_fx_spec`: Returns the mandatory FX chain specification for each track role.
  - `apply_track_channel_strip`: Loads and tunes the mandatory channel strip on track_index based on role.

---

## Módulo: `engine/fx/device_parameter_supervisor.py`

**Descripción del Módulo:**
```text
Device Parameter Supervisor & Multi-Section Semantic Engine:
Comprehensive parameter abstraction for professional music production in Ableton Live.
Organizes all exposed parameters across Vital, Analog Lab V, Pigments, FabFilter Pro-Q 4,
The God Particle, OTT, ValhallaVintageVerb, Efx REFRACT, 808 Core Kit, and Native Live devices
into 8 production-grade functional sections:

Section 1: MACROS & MASTER (Quick sound character & overall gain)
Section 2: OSCILLATORS & ENGINES (Wavetable position, pitch, unison, morph)
Section 3: FILTERS & SPECTRAL CUTOFF (Filter cutoff, resonance, drive, filter modes)
Section 4: SURGICAL & DYNAMIC EQ (Pro-Q 4 bands 1-13: HPF, Sub bump, Mud cut, Air shelf, Thresholds)
Section 5: ENVELOPES & TIME DYNAMICS (Attack, decay, sustain, release, glide/portamento)
Section 6: DYNAMICS & COMPRESSION (OTT depth/bands, Glue threshold, Limiter drive)
Section 7: HARMONIC SATURATION & COLOR (Analog drive, distortion, character, bitcrusher)
Section 8: SPACE & MODULATION FX (Reverb mix/decay, delay feedback, chorus, flanger, phaser)

Guarantees:
- Dynamic live inspection of what parameters are actually present on each device.
- The AI never needs to guess obscure DAW names or parameter indices.
- Zero crashes: safely skips unmapped parameters without error.
```

### Clases

#### `DeviceParameterSupervisor`
Intelligent semantic and sectional parameter controller for Ableton Live devices.

- **Métodos:**
  - `introspect_device_parameters`: Queries Live for all exposed parameters on a specific device.
  - `inspect_device_catalog`: Deep structural cataloging: Inspects the live device and categorizes every detected
  - `inspect_semantic_capabilities`: Standard high-level semantic capability query with detailed AI descriptions.
  - `inspect_for_ai`: AI-Oriented Parameter Introspection & Guide:
  - `get_semantic_guide`: Returns the full catalog guide with descriptions and usage hints for all roles.
  - `_calculate_musical_parameter_value`: Calculates safe musical physical values.
  - `_configure_eq_band_shape`: Configures proper musical band shapes on FabFilter Pro-Q.
  - `_activate_shaperbox_modules`: Ensures ShaperBox 3 modules are visibly and audibly active.
  - `apply_semantic_tuning`: Tunes device parameters using high-level semantic roles.
  - `apply_sectional_tuning`: Tunes specific functional sections (e.g. FILTERS, SURGICAL_EQ, SPACE_MODULATION).
  - `tune_vital_macros`: Modulates Vital's 4 macros directly.
  - `tune_device_parameters`: Unified tuning router supporting semantic roles, sections, or literal keys.
  - `audit_device_sculpting`: Audits whether a device on a track has been sculpted/configured
  - `enforce_mandatory_sculpting`: Enforces that a device is configured and sculpted.
  - `apply_sound_blueprint`: Applies a concrete parameter blueprint to an instrument or device on track_index.

---

## Módulo: `engine/models/roles.py`

### Clases

#### `RoleEnum`

#### `TrackMetadata`
- **Métodos:**
  - `to_dict`: Sin documentación
  - `from_dict`: Sin documentación

### Funciones Globales

- `validate_role`: Validate and normalize a role string. Returns normalized name or raises ValueError if invalid.

---

## Módulo: `engine/models/ids.py`

### Funciones Globales

- `generate_id`: Generate a short, collision-resistant identifier with a semantic prefix.

---

## Módulo: `engine/models/session.py`

### Clases

#### `SyncStatus`

#### `SectionType`

#### `ClipNode`
- **Métodos:**
  - `to_dict`: Sin documentación
  - `from_dict`: Sin documentación

#### `DeviceNode`
- **Métodos:**
  - `to_dict`: Sin documentación
  - `from_dict`: Sin documentación

#### `TrackNode`
- **Métodos:**
  - `to_dict`: Sin documentación
  - `from_dict`: Sin documentación

#### `SectionNode`
- **Métodos:**
  - `to_dict`: Sin documentación
  - `from_dict`: Sin documentación

#### `ProjectState`
- **Métodos:**
  - `to_dict`: Sin documentación
  - `from_dict`: Sin documentación

---

## Módulo: `engine/models/transactions.py`

### Clases

#### `TransactionStatus`

#### `Operation`
- **Métodos:**
  - `to_dict`: Sin documentación
  - `from_dict`: Sin documentación

#### `Transaction`
- **Métodos:**
  - `to_dict`: Sin documentación
  - `from_dict`: Sin documentación

#### `DiffReport`
- **Métodos:**
  - `is_empty`: Sin documentación
  - `to_dict`: Sin documentación

#### `Snapshot`
- **Métodos:**
  - `to_dict`: Sin documentación
  - `from_dict`: Sin documentación

---

## Módulo: `engine/transactions/rollback.py`

### Clases

#### `RollbackEngine`
Executes atomic rollbacks via WAL inverse operations (Level 1) or snapshot restoration (Level 2)

- **Métodos:**
  - `execute_rollback`: Sin documentación

---

## Módulo: `engine/transactions/manager.py`

### Clases

#### `TransactionManager`
Manages transactional units of work with optimistic concurrency and atomic rollback

- **Métodos:**
  - `__init__`: Sin documentación
  - `begin`: Start a new transaction, take an automatic baseline snapshot and record base_version
  - `get_transaction`: Sin documentación
  - `stage_create_track`: Sin documentación
  - `stage_set_volume`: Sin documentación
  - `stage_set_panning`: Sin documentación
  - `stage_set_mute`: Sin documentación
  - `stage_set_role`: Sin documentación
  - `stage_set_tempo`: Sin documentación
  - `stage_add_notes`: Sin documentación
  - `preview`: Dry-run preview calculating impacts without modifying Ableton Live
  - `validate`: Sin documentación
  - `commit`: Atomically commit the transaction. Validates, checks optimistic concurrency, executes, or auto-rolls back
  - `rollback`: Manually trigger rollback for an open or failed transaction
  - `status`: Sin documentación
  - `history`: Sin documentación
  - `_execute_single_op`: Dispatches an operation to both Ableton Live (via adapter) and the Shadow Graph

---

## Módulo: `engine/transactions/validator.py`

### Clases

#### `TransactionValidator`
Pre-commit validation engine enforcing graph consistency, locks, parameter bounds and limits

- **Métodos:**
  - `validate`: Sin documentación

---

## Módulo: `engine/indexer/keywords.py`

**Descripción del Módulo:**
```text
Keyword dictionaries for filename-based sample classification.

All keyword lists are lowercase. The parser normalizes input filenames
before matching. Keywords are matched against tokens (split on `_-. /\`),
not substrings — this avoids "kick" matching inside "kickback" or "sticking".
```

---

## Módulo: `engine/indexer/storage.py`

**Descripción del Módulo:**
```text
Parquet storage for the sample manifest.

Manifest is stored as a single parquet file. For 40k rows the file is
~10 MB and loads in <100ms. Schema is defined explicitly so we catch
mismatches early when adding new fields.
```

### Funciones Globales

- `empty_manifest`: Sin documentación
- `save_manifest`: Sin documentación
- `load_manifest`: Sin documentación

---

## Módulo: `engine/indexer/manifest.py`

**Descripción del Módulo:**
```text
High-level indexer API: build, search, stats.
```

### Funciones Globales

- `build_manifest`: Walk the packs root and build/update the manifest incrementally.
- `search_samples`: Search the manifest with AND-combined filters.
- `library_stats`: Compute aggregate statistics over the manifest.

---

## Módulo: `engine/indexer/fileinfo.py`

**Descripción del Módulo:**
```text
File stat and content hashing for incremental indexing.
```

### Funciones Globales

- `compute_content_hash`: sha1(filename + first 64KB).
- `stat_file`: Sin documentación

---

## Módulo: `engine/indexer/walker.py`

**Descripción del Módulo:**
```text
Filesystem walker for sample libraries.

Yields `pathlib.Path` objects for audio files under a root. Skips:
  - Hidden directories (those whose names start with .)
  - Files with non-audio extensions
```

### Funciones Globales

- `walk_audio_files`: Yield Path to every audio file under `root`, recursively.

---

## Módulo: `engine/indexer/parser.py`

**Descripción del Módulo:**
```text
Filename and folder parser.

Converts file paths into structured tags by:
1. Tokenizing the filename (and optionally the folder path)
2. Matching tokens against keyword dictionaries
3. Extracting numeric metadata (BPM, key) with regex

camelCase splitting is applied only when the stem contains no explicit
separator characters (_, -, space, /, \). This avoids mangling filenames
like "Kick-BoomBap" which would otherwise yield spurious extra tokens.
```

### Funciones Globales

- `tokenize`: Normalize a filename or folder name into lowercase tokens.
- `extract_bpm`: Extract BPM from a filename or path.
- `extract_key`: Extract musical key from a filename, e.g. 'F#min', 'Cmaj'.
- `parse_filename`: Parse a single filename into structured tags.
- `parse_folder_context`: Parse a folder path (relative to packs root, or absolute) into the
- `parse_path`: High-level: parse filename + use folder context as fallback.
- `match_keywords`: Return the list of categories from `dictionary` whose keywords match

---

## Módulo: `engine/indexer/paths.py`

### Funciones Globales

- `default_samples_root`: Sin documentación
- `default_manifest_path`: Sin documentación

---

## Módulo: `engine/forensics/report.py`

**Descripción del Módulo:**
```text
Forensic Report Generation & Fingerprinting Engine (PIE Phase 7).
Compiles ForensicReport instances with deterministic SHA-256 provenance hashes
and human-readable diagnostic summaries.
```

### Clases

#### `ForensicReportGenerator`
Assembles comprehensive ForensicReport data structures and calculates
deterministic cryptographic provenance signatures.

- **Métodos:**
  - `compute_deterministic_hash`: Calculates SHA-256 checksum over a normalized, alphabetically sorted JSON
  - `create_report`: Constructs and seals a complete ForensicReport with verifiable deterministic hash.
  - `generate_markdown_summary`: Produces human-readable markdown summary of the forensic report.

---

## Módulo: `engine/forensics/clipping.py`

**Descripción del Módulo:**
```text
Temporal and Inter-Sample Clipping Detection Engine (PIE Phase 7).
Implements deterministic sample clipping clustering and ITU-R BS.1770-5
4x sinc-interpolated True Peak oversampling detection.
```

### Clases

#### `ClippingEngine`
Deterministic detection of digital full-scale sample clipping and
inter-sample reconstructed True Peak overshoots.

- **Métodos:**
  - `_validate_audio`: Sin documentación
  - `detect_sample_clipping`: Detects digital full-scale sample clipping and clusters adjacent clipped
  - `detect_true_peak_clipping`: Calculates 4x oversampled True Peak continuous signal according to
  - `analyze`: Runs comprehensive clipping and True Peak analysis using provided or default config.

---

## Módulo: `engine/forensics/serializer.py`

**Descripción del Módulo:**
```text
Atomic Persistence & Serialization for Audio Forensics Engine (PIE Phase 7).
Ensures safe disk operations (flush + fsync + os.replace) and cryptographic
integrity verification upon deserialization.
```

### Clases

#### `ForensicsStorage`
Handles atomic serialization, disk storage, and integrity-verified loading
of ForensicReports and acoustic diagnostic evidence.

- **Métodos:**
  - `__init__`: Sin documentación
  - `_atomic_write`: Atomically writes data using temp file, flush, fsync, and replace.
  - `serialize_report`: Serializes a ForensicReport to deterministic canonical JSON.
  - `deserialize_report`: Deserializes a JSON string into a validated, typed ForensicReport instance.
  - `save_report`: Atomically saves a ForensicReport to disk in reports directory.
  - `load_report`: Loads and verifies a ForensicReport by ID or path.
  - `list_reports`: Lists all stored report IDs.

---

## Módulo: `engine/forensics/spectral.py`

**Descripción del Módulo:**
```text
Spectral Feature & Dynamic Resonance Analysis Engine (PIE Phase 7).
Extracts centroid, flux, rolloff, band energies across 14 standard bands,
and identifies localized persistent dynamic resonances.
```

### Clases

#### `SpectralEngine`
Analyzes STFT representation to compute spectral features and detect localized resonances.

- **Métodos:**
  - `calculate_spectral_centroid`: Calculates spectral centroid in Hz for a 1D magnitude spectrum.
  - `calculate_spectral_rolloff`: Calculates rolloff frequency below which percentile of energy lies.
  - `calculate_spectral_flux`: Calculates spectral flux between two consecutive magnitude frames.
  - `calculate_band_energies`: Calculates energy in dBFS across the 14 standard frequency bands.
  - `detect_resonances`: Detects dynamic resonances that exceed the baseline energy by > resonance_threshold_db,

---

## Módulo: `engine/forensics/analyzer.py`

**Descripción del Módulo:**
```text
Audio Forensics Master Engine Facade (PIE Phase 7).
Coordinates temporal, spectral, dynamic, and causal forensic diagnostics
for single audio streams and multitrack stems.
GUARANTEES: Deterministic, strictly READ-ONLY ($State_{before} \equiv State_{after}$),
zero ML dependencies.
```

### Clases

#### `AudioForensicsEngine`
Comprehensive Audio Forensics Engine.
Transitions PIE from global static metrics to exact time-frequency diagnostic localization.

- **Métodos:**
  - `__init__`: Sin documentación
  - `_validate_audio`: Sin documentación
  - `analyze_track`: Performs full forensic audit on a single audio track or mixbus.
  - `analyze_multitrack`: Performs multitrack forensic audit across stems, detecting pairwise masking

---

## Módulo: `engine/forensics/correlation.py`

**Descripción del Módulo:**
```text
Cross-Track Envelope & Spectral Correlation Engine (PIE Phase 7).
Computes deterministic Pearson correlation, lag alignment, and
source-attribution correlation across multitrack stems.
```

### Clases

#### `CorrelationEngine`
Deterministic correlation analysis across tracks for causal source attribution
and phase/bleed diagnostic checks.

- **Métodos:**
  - `_validate_signal`: Sin documentación
  - `compute_envelope`: Computes moving RMS envelope of a 1D audio signal.
  - `calculate_pearson_correlation`: Calculates normalized Pearson correlation coefficient between two 1D series.
  - `calculate_lag_correlation`: Calculates maximum correlation and optimal lag in milliseconds within +/- max_lag_ms.
  - `attribute_event_to_sources`: Attributes an event (e.g. Master clipping or resonance) to the candidate stems

---

## Módulo: `engine/forensics/config.py`

**Descripción del Módulo:**
```text
Centralized Configuration & Standard Spectral Bands for Audio Forensics Engine.
```

---

## Módulo: `engine/forensics/stft.py`

**Descripción del Módulo:**
```text
Deterministic Short-Time Fourier Transform (STFT) Engine for Audio Forensics (PIE Phase 7).
Operates strictly on real-valued signals with explicit frequency and time resolutions.
```

### Clases

#### `STFTEngine`
Computes deterministic time-frequency representations (STFT) for audio analysis.
Guarantees mathematical reproducibility and explicit resolution tracking.

- **Métodos:**
  - `get_window`: Generates window array, raising UnsupportedWindowError if unknown.
  - `validate_audio`: Validates numerical integrity of audio array and sample rate.
  - `compute_stft`: Computes STFT magnitude, power, frequency bins, and time frames.

---

## Módulo: `engine/forensics/temporal.py`

**Descripción del Módulo:**
```text
Temporal Feature Analysis Engine for Audio Forensics (PIE Phase 7).
Computes frame-level RMS, peaks, crest factors, attack/decay profiles, and constructs AudioFrame objects.
```

### Clases

#### `TemporalEngine`
Extracts time-domain envelope, dynamics, and builds AudioFrame sequences.

- **Métodos:**
  - `calculate_frame_rms`: Calculates RMS level in dBFS for a 1D slice of audio.
  - `calculate_frame_peak`: Calculates peak level in dBFS for a 1D slice of audio.
  - `calculate_crest_factor`: Calculates crest factor in dB (peak_dbfs - rms_dbfs).
  - `analyze_frames`: Builds AudioFrame objects for all frames in the STFT representation.

---

## Módulo: `engine/forensics/baseline.py`

**Descripción del Módulo:**
```text
Track Baseline Statistical Profile Engine (PIE Phase 7).
Computes track-specific distributions (mean, median, std, p10, p50, p90)
to establish dynamic acoustic reference baselines.
```

### Clases

#### `BaselineEngine`
Computes statistical baseline distributions for RMS, peaks, centroids, and the 14 frequency bands.

- **Métodos:**
  - `compute_distribution_stats`: Calculates standard percentile and summary statistics for a 1D array.
  - `compute_baseline`: Flexible extractor of TrackBaseline supporting:

---

## Módulo: `engine/forensics/masking.py`

**Descripción del Módulo:**
```text
Dynamic Spectral Masking Engine (PIE Phase 7).
Detects time-localized frequency masking and spectral collision between
audio stems (e.g., Kick vs Bass, Vocal vs Instruments).
```

### Clases

#### `MaskingEngine`
Deterministic detector of time-frequency spectral collision and acoustic masking
between multi-track stems.

- **Métodos:**
  - `_validate_stem`: Sin documentación
  - `detect_masking`: Detects time-frequency masking between two stems across standard spectral bands.
  - `analyze_multitrack`: Analyzes pairwise spectral masking across a multitrack dictionary of stems.

---

## Módulo: `engine/forensics/models.py`

**Descripción del Módulo:**
```text
Canonical Domain Models for Audio Forensics Engine (PIE Phase 7).
Defines strictly typed, immutable contracts for temporal, spectral, dynamic,
and causal audio forensic diagnostics.
```

### Clases

#### `ForensicEventType`
Canonical classification of forensic audio anomalies and acoustic phenomena.


#### `Severity`
Hierarchical severity levels for forensic events.


#### `AnalysisConfig`
Configuration parameters for forensic temporal/spectral audio analysis.
Guarantees deterministic, reproducible analysis runs.

- **Métodos:**
  - `__post_init__`: Sin documentación
  - `to_dict`: Sin documentación

#### `AudioFrame`
Represents a single time-windowed slice of analysis.

- **Métodos:**
  - `__post_init__`: Sin documentación
  - `to_dict`: Sin documentación

#### `SpectralMeasurement`
Localized point measurement on the time-frequency plane.

- **Métodos:**
  - `__post_init__`: Sin documentación
  - `to_dict`: Sin documentación

#### `ForensicEvent`
Principal record of a detected forensic acoustic event or anomaly.
Correlates exact time span, affected frequencies, severity, and evidence pointers.

- **Métodos:**
  - `__post_init__`: Sin documentación
  - `to_dict`: Sin documentación

#### `CausalHypothesis`
Hypothesis explaining the likely origin or source of a forensic phenomenon.
Includes supporting evidence, competing alternative explanations, and confidence.

- **Métodos:**
  - `__post_init__`: Sin documentación
  - `to_dict`: Sin documentación

#### `TrackBaseline`
Statistical distribution profile representing the baseline behavior of a specific signal.
Prevents relying on arbitrary static thresholds by establishing dynamic context.

- **Métodos:**
  - `__post_init__`: Sin documentación
  - `to_dict`: Sin documentación

#### `ForensicReport`
Complete deterministic forensic audit report for an audio stream or stem.
Provides verifiable SHA-256 fingerprint for forensic provenance.

- **Métodos:**
  - `__post_init__`: Sin documentación
  - `to_dict`: Sin documentación

---

## Módulo: `engine/forensics/exceptions.py`

**Descripción del Módulo:**
```text
Exception hierarchy for the Audio Forensics Engine (PIE Phase 7).
Provides structured, auditable error types for deterministic DSP forensic analysis.
```

### Clases

#### `ForensicsError`
Base exception for all Audio Forensics Engine errors.

- **Métodos:**
  - `__init__`: Sin documentación
  - `to_dict`: Sin documentación

#### `InvalidAudioError`
Raised when audio array is empty, non-float, incorrect shape, or contains NaN/Infinity.


#### `InvalidAnalysisConfigError`
Raised when analysis configuration parameters violate numerical invariants.


#### `UnsupportedSampleRateError`
Raised when sample rate is <= 0 or outside supported boundaries (8000 Hz to 192000 Hz).


#### `UnsupportedChannelLayoutError`
Raised when channel count is not 1 (mono) or 2 (stereo).


#### `UnsupportedWindowError`
Raised when an unsupported STFT window function is requested.


#### `InsufficientAudioError`
Raised when audio length is shorter than the minimum FFT window size.


#### `ForensicsPersistenceError`
Raised when persistence or atomic report writing fails.


#### `ForensicsIntegrityError`
Raised when report structure, hashes, or causal assertions are corrupted.


---

## Módulo: `engine/forensics/causality.py`

**Descripción del Módulo:**
```text
Forensic Causal Inference & Lineage Engine (PIE Phase 7).
Infers causal hypotheses from acoustic observations and injects
deterministic lineage into ProductionGraph (Measurement -> Observation -> Hypothesis).
GUARANTEE: Purely diagnostic / READ-ONLY; never creates Decision or Action nodes.
```

### Clases

#### `CausalityEngine`
Deterministic causal inference engine correlating acoustic forensic events
with probable physical/production causes, supporting evidence, and competing explanations.

- **Métodos:**
  - `generate_hypotheses_for_events`: Generates structured causal hypotheses for a list of forensic events.
  - `inject_into_production_graph`: Injects forensic measurements, observations, and causal hypotheses into the

---

## Módulo: `engine/forensics/anomalies.py`

**Descripción del Módulo:**
```text
Acoustic Anomaly Detection Engine (PIE Phase 7).
Implements deterministic detection of DC offset, clicks, pops,
dropouts, channel loss, and stereo phase cancellation anomalies.
```

### Clases

#### `AnomalyEngine`
Deterministic detector for acoustic defects: DC offset, transient impulses
(clicks/pops), dropouts, channel asymmetry/loss, and negative phase correlation.

- **Métodos:**
  - `_validate_audio`: Sin documentación
  - `detect_dc_offset`: Detects continuous DC offset across audio channels.
  - `detect_clicks_and_pops`: Detects localized transient impulse anomalies (clicks < 3ms, pops 3-25ms)
  - `detect_dropouts`: Detects dropouts: sudden unexpected collapse of audio energy (> drop_threshold_db)
  - `detect_channel_loss`: Detects channel loss: one stereo channel drops > imbalance_threshold_db
  - `detect_phase_anomalies`: Detects sustained negative phase correlation across stereo channels.
  - `analyze`: Runs complete battery of acoustic anomaly detections.

---

## Módulo: `engine/creative/dna_engine.py`

**Descripción del Módulo:**
```text
Creative Direction Engine (Phase 1):
Orchestrates aesthetic world-building, reference acoustic profiling,
harmonic DNA selection, frequency-slot track scaffolding, and arrangement energy blueprints.
Directly translates creative intent into physical Ableton Live session architecture.
```

### Clases

#### `CreativeDirectionEngine`
The master creative architect for Phase 1 of musical production.

- **Métodos:**
  - `get_available_reference_profiles`: Returns metadata for all built-in acoustic reference profiles.
  - `build_default_track_scaffold`: Creates the standard 8-track acoustic scaffolding, reserving distinct
  - `build_default_arrangement_blueprint`: Builds the 96-bar dynamic energy arrangement blueprint.
  - `formulate_creative_brief`: Formulates the complete creative and sonic direction brief.
  - `scaffold_live_project`: Physically instantiates the creative DNA in Ableton Live:

---

## Módulo: `engine/creative/models.py`

**Descripción del Módulo:**
```text
Data models for Phase 1: DNA & Creative Direction.
Defines strong contracts for sonic world-building, reference acoustic profiles,
harmonic/modal DNA, instrumentation scaffolding, and arrangement energy blueprints.
```

### Clases

#### `AestheticMood`

#### `ModalFlavor`

#### `SonicWorld`
Aesthetic, textural and acoustic spatial identity of the song.


#### `SpectralTargetBand`
Target acoustic energy balance for a specific frequency band.


#### `ReferenceProfile`
Acoustic DNA and fingerprint extracted from top-tier reference productions.


#### `HarmonicDNA`
Harmonic vocabulary, modal structure, and voicing rules.


#### `TrackRoleAllocation`
Acoustic role reservation and slot allocation per track.


#### `ArrangementSectionBlueprint`
Structural blueprint for an individual song section.


#### `ArrangementBlueprint`
Macro structural arrangement and dynamic energy trajectory of the whole song.


#### `SongCreativeDNA`
Master contract representing the complete Phase 1 Creative Direction.

- **Métodos:**
  - `to_dict`: Serializes the entire creative brief into a clean JSON-ready dictionary.

---

## Módulo: `engine/snapshots/manager.py`

### Clases

#### `SnapshotManager`
Manages creation, listing, persistence, and restoration of session snapshots

- **Métodos:**
  - `__init__`: Sin documentación
  - `create_snapshot`: Sin documentación
  - `get_snapshot`: Sin documentación
  - `restore_snapshot`: Sin documentación
  - `list_snapshots`: Sin documentación

---

## Módulo: `engine/snapshots/serializer.py`

### Clases

#### `SnapshotSerializer`
Serializes and deserializes the full state of a SessionShadowGraph

- **Métodos:**
  - `serialize`: Sin documentación
  - `apply_to_graph`: Sin documentación

---

## Módulo: `engine/vocal/pipeline.py`

### Clases

#### `VocalStyle`

#### `VocalChainStage`

#### `VocalProductionProfile`

#### `VocalProductionEngine`
Intelligent vocal production engine for track scaffolding, DSP chain design,
and automatic instrumental ducking matrix around vocal phrasing.

- **Métodos:**
  - `get_vocal_profile`: Sin documentación
  - `calculate_ducking_envelope`: Calculates a continuous volume automation envelope that transparently ducks
  - `identify_ducking_targets`: Scans track names to find high-priority musical elements to duck (Keys, Chords, Leads, Pads, Guitars, Synths)

---

## Módulo: `engine/vocal/chopper.py`

**Descripción del Módulo:**
```text
Vocal Chopper & Hook Pitch-Shift Engine:
Generates in-key, scale-quantized rhythmic vocal chop phrases, call-and-response hooks,
stutter fills, and spatial stereo ping-pong / delay throw automations for Ableton Live.
```

### Clases

#### `VocalChopStyle`

#### `VocalChopNote`

#### `VocalChopperEngine`
Produces musically coherent vocal chop motifs aligned with session key, scale, and tempo.

- **Métodos:**
  - `get_scale_pitches`: Calculates MIDI pitches for the diatonic scale across two octaves.
  - `generate_hook_chops`: Generates scale-quantized vocal chop patterns with panning and velocity dynamics.
  - `calculate_pan_automation`: Generates stereo panning automation points based on vocal chop note coordinates.
  - `calculate_delay_send_automation`: Generates dynamic send automation throws opening up during key turnaround phrases.
  - `generate_and_apply_vocal_chops`: Calculates and injects vocal chop clips and stereo panning automation into Ableton Live.

---

## Módulo: `engine/vocal/vocal_staging_supervisor.py`

**Descripción del Módulo:**
```text
Vocal Lead Staging & Multitrack Ducking Supervisor:
Orchestrates spectral slotting (-3 dB dip in harmonic accompaniment at 2.5-3.0 kHz),
dynamic sidechain ducking of instrumental beds when vocal or lead is active,
and stage gain-riding to maintain vocal primacy in commercial mixes.
```

### Clases

#### `VocalStagingSupervisor`
Supervises vocal presence carving, dynamic ducking, and staging matrix.

- **Métodos:**
  - `calculate_vocal_staging_plan`: Builds complete staging blueprint:
  - `apply_staging_to_session`: Applies live parametric carving or volume trim to accompaniment tracks in Live.

---

## Módulo: `engine/vocal/lyric_engine.py`

**Descripción del Módulo:**
```text
engine/vocal/lyric_engine.py
Lyric & Prosody Engine: Closed-Loop Metric, Stress, and Vowel Resonance Validator.

Enforces musical prosody so generated lyrics fit melodic contours naturally:
1. Syllable count matching (1:1 note-to-syllable correspondence).
2. Metric stress alignment: strong beats (1 and 3) must carry tonic accents.
3. Vowel resonance on vocal peaks (favors open vowels /a/, /o/, /e/ on notes >= E4).
4. Rhyme scheme validation.
5. Actionable feedback generation for LLM self-correction.
```

### Clases

#### `LyricEngine`
Validates lyric prosody against melodic constraints in closed-loop cycles.

- **Métodos:**
  - `count_syllables_word`: Counts syllables in a single word and identifies the tonic/stressed syllable index (1-indexed).
  - `analyze_line`: Splits a text line into words and syllables, tracking absolute stressed syllable indices.
  - `validate_line_against_constraint`: Validates whether a candidate lyric line satisfies the musical constraints of the melody.

---

## Módulo: `engine/session/diff.py`

### Clases

#### `SessionDiff`
Calculates granular differences between the Engine's SHADOW_STATE and Live's REAL_STATE

- **Métodos:**
  - `compute_diff`: Sin documentación
  - `_check_properties`: Sin documentación

---

## Módulo: `engine/session/resolver.py`

### Clases

#### `SessionResolver`
Semantic resolver for locating objects in the Session Shadow Graph with ambiguity detection

- **Métodos:**
  - `__init__`: Sin documentación
  - `resolve`: Resolve a track using flexible semantic criteria.

---

## Módulo: `engine/session/graph.py`

### Clases

#### `SessionShadowGraph`
The in-memory semantic representation and state mirror of an Ableton Live session

- **Métodos:**
  - `__init__`: Sin documentación
  - `increment_version`: Sin documentación
  - `add_track`: Sin documentación
  - `get_track`: Sin documentación
  - `remove_track`: Sin documentación
  - `set_track_role`: Sin documentación
  - `set_track_tags`: Sin documentación
  - `lock_object`: Sin documentación
  - `unlock_object`: Sin documentación
  - `add_section`: Sin documentación
  - `get_section`: Sin documentación
  - `remove_section`: Sin documentación
  - `to_dict`: Sin documentación
  - `from_dict`: Sin documentación
  - `clear`: Sin documentación

---

## Módulo: `engine/session/synchronizer.py`

### Clases

#### `SessionSynchronizer`
Manages synchronization, refresh, diffing and reconciliation between Live and Shadow Graph

- **Métodos:**
  - `__init__`: Sin documentación
  - `refresh`: Query Ableton, detect all differences, update the Shadow Graph and ensure consistency
  - `reconcile`: Reconcile persisted state with live Ableton session without losing semantic IDs or roles

---

## Módulo: `engine/knowledge/constants.py`

**Descripción del Módulo:**
```text
Foundation constants for FL Studio MCP knowledge base.
```

### Clases

#### `Genre`

#### `DrumPiece`

### Funciones Globales

- `note_to_midi`: Convert note name + octave to MIDI number. C4 = 60.
- `midi_to_note`: Convert MIDI number to note name with octave. 60 -> 'C4'.
- `transpose`: Transpose a MIDI note by a number of semitones.

---

## Módulo: `engine/knowledge/plugins/cymatics.py`

**Descripción del Módulo:**
```text
Cymatics plugins knowledge - Diablo, Pluto, Space, Quake, Vortex.

Guia completa de plugins Cymatics instalados con presets por contexto,
cadenas por genero y parametros detallados.
```

### Funciones Globales

- `get_cymatics_chain`: Devuelve la cadena de plugins Cymatics recomendada para un elemento en un genero.
- `get_plugin_guide`: Devuelve guia completa de un plugin Cymatics.
- `list_cymatics_presets`: Lista todos los presets Cymatics disponibles con sus configuraciones.

---

## Módulo: `engine/knowledge/plugins/fabfilter.py`

**Descripción del Módulo:**
```text
Conocimiento de FabFilter Suite completa para FL Studio MCP.

Pro-Q 4, Pro-C 3, Pro-L 2, Pro-R 2, Saturn 2, Pro-DS, Pro-G, Pro-MB,
Timeless 3, Volcano 3, Twin 3, Simplon, Micro.
EQ presets, compressor presets, limiter, saturación y mixing chains.
```

### Funciones Globales

- `get_eq_preset`: Devuelve preset de EQ (Pro-Q 4) para un elemento.
- `get_compressor_preset`: Devuelve preset de compresor (Pro-C 3).
- `get_fabfilter_chain`: Devuelve cadena de mezcla completa usando solo FabFilter.
- `get_saturn_guide`: Devuelve guía de Saturn 2 con todos los presets de saturación.
- `format_plugin_info`: Devuelve info detallada de un plugin FabFilter.

---

## Módulo: `engine/knowledge/plugins/rx11.py`

**Descripción del Módulo:**
```text
iZotope RX 11 knowledge - módulos de reparación y limpieza de audio.

Guía completa de módulos RX 11 instalados, workflows de limpieza por tipo
de fuente, presets de intensidad, y funciones helper.
```

### Funciones Globales

- `get_cleanup_chain`: Devuelve el workflow de limpieza recomendado para un tipo de fuente.
- `get_module_guide`: Devuelve guía detallada de un módulo RX 11.
- `get_repair_workflow`: Devuelve una visión general de todos los workflows de reparación disponibles.
- `list_rx_modules`: Lista todos los módulos RX 11 disponibles con descripción breve.

---

## Módulo: `engine/knowledge/plugins/autotune.py`

**Descripción del Módulo:**
```text
Antares Auto-Tune Pro + Auto-Key knowledge para produccion vocal.

Guia completa de estilos de tuning, deteccion de tonalidad con Auto-Key,
workflow de grabacion a vocal tuneada, y errores comunes.
```

### Funciones Globales

- `get_autotune_settings`: Devuelve la configuracion de Auto-Tune para un estilo dado.
- `get_vocal_tuning_workflow`: Devuelve el workflow completo de grabacion a vocal tuneada.
- `get_key_detection_guide`: Devuelve guia de deteccion de tonalidad con Auto-Key.

---

## Módulo: `engine/knowledge/plugins/vocal_chains.py`

**Descripción del Módulo:**
```text
Vocal processing chains with exact settings from plugins_voz_fl_studio.txt.

Encodes the complete professional vocal chain (10-slot order), style-specific
recipes, advanced tricks, recording tips, mix levels, checklist, free plugin
alternatives, and investment tiers.
```

### Funciones Globales

- `get_vocal_chain`: Return a formatted string describing the vocal chain for a given style.
- `get_vocal_tricks`: Return a formatted string listing all advanced vocal tricks.
- `get_vocal_checklist`: Return the formatted 17-point final verification checklist.

---

## Módulo: `engine/knowledge/plugins/plugin_chains.py`

**Descripción del Módulo:**
```text
Complete mixing and mastering knowledge for FL Studio MCP.

Encodes all plugin chains, EQ guides, mix levels, gain staging,
mastering chains, send configurations, and LUFS targets from the
comprehensive boom bap / trap mixing guide.

Plugins referenced: iZotope Ozone 12, iZotope RX, FabFilter Pro-Q 3,
Soundtoys (full bundle), Antares Auto-Tune, FL Studio native plugins.
```

### Funciones Globales

- `get_chain`: Return a formatted string describing the plugin chain for an element/genre.
- `get_mix_levels`: Return a formatted string with relative mix levels for the given genre.
- `get_mastering_chain`: Return a formatted string with the complete mastering chain for the genre.
- `get_eq_guide`: Return a formatted EQ frequency guide for the given element.
- `get_send_config`: Return a formatted string with the send effect configuration for the genre.
- `get_gain_staging_guide`: Return the complete gain staging guide as a formatted string.
- `get_mixer_template`: Return the recommended FL Studio mixer layout as a formatted string.
- `get_lufs_targets`: Return LUFS targets per platform as a formatted string.
- `get_workflow`: Return the complete mixing/mastering workflow as a formatted string.
- `get_soundtoys_guide`: Return a formatted guide of which Soundtoys plugin to use where.

---

## Módulo: `engine/knowledge/plugins/serum2.py`

**Descripción del Módulo:**
```text
Conocimiento de sound design con Serum 2 para FL Studio MCP.

Recetas de patches, técnicas de síntesis, wavetables y FX chains
organizados por tipo de sonido y género.
```

### Funciones Globales

- `get_patch_recipe`: Devuelve receta paso a paso para crear un patch.
- `get_genre_sounds`: Lista sonidos recomendados para un género.
- `get_fx_chain`: Devuelve cadena de FX interna de Serum.
- `get_sound_design_tips`: Devuelve todas las técnicas de sound design.
- `get_wavetable_guide`: Guía de selección de wavetables.
- `list_patches`: Lista todos los patches disponibles.

---

## Módulo: `engine/knowledge/plugins/mixing_advanced.py`

**Descripción del Módulo:**
```text
Advanced mixing and mastering knowledge for FL Studio.

Covers gain staging, mixer layout, mixing order, genre differences,
parallel processing, bus processing, referencing, common mistakes,
and complete mixing checklists.
Extracted from GUIA_MEZCLA_MASTER_COMPLETA.txt.
```

### Funciones Globales

- `get_mixing_workflow`: Workflow completo de mezcla para un genero especifico.
- `get_gain_staging_guide`: Guia completa de gain staging.
- `get_bus_setup`: Guia de configuracion de buses para un genero.
- `get_mixing_checklist`: Checklist completo de mezcla y mastering.

---

## Módulo: `engine/knowledge/plugins/ozone12.py`

**Descripción del Módulo:**
```text
Conocimiento de iZotope Ozone 12 para mastering en FL Studio MCP.

Cadenas de mastering por género, módulos con parámetros detallados,
LUFS targets por plataforma y quick chains simplificadas.
```

### Funciones Globales

- `get_mastering_chain`: Devuelve cadena de mastering completa para un género.
- `get_module_guide`: Devuelve guía detallada de un módulo Ozone.
- `get_quick_master`: Devuelve cadena simplificada de 3-4 módulos.
- `get_lufs_targets`: Devuelve targets de LUFS por plataforma y género.
- `list_ozone_modules`: Lista todos los módulos Ozone 12.

---

## Módulo: `engine/knowledge/producers/producers.py`

**Descripción del Módulo:**
```text
Producer style profiles and replication guides from GUIA_BOOM_BAP_90s_COMPLETA.txt.
```

### Funciones Globales

- `get_producer_profile`: Format a producer profile as a readable string.
- `list_producers`: List all available producer profiles.

---

## Módulo: `engine/knowledge/arrangement/song_structures.py`

**Descripción del Módulo:**
```text
Song structure templates and arrangement guides.
```

### Funciones Globales

- `get_structure`: Get song structure template for a genre.
- `get_quick_start`: Get the 10-step quick start guide.

---

## Módulo: `engine/knowledge/sampling/sampling.py`

**Descripción del Módulo:**
```text
Sampling knowledge for boom bap production in FL Studio.

Covers sampling sources, chopping techniques, pitch/time manipulation,
layering, sample processing, drum machine emulation, and legal tips.
Extracted from GUIA_BOOM_BAP_90s_COMPLETA.txt.
```

### Funciones Globales

- `get_chopping_guide`: Guia de chopping. Si no se especifica metodo, muestra todos.
- `get_sampling_workflow`: Workflow completo de sampling segun el tipo de fuente.
- `get_drum_machine_emulation`: Guia para emular drum machines clasicas en FL Studio.
- `get_sample_processing_chain`: Cadena de procesamiento para samples segun el estilo.

---

## Módulo: `engine/knowledge/composition/chords.py`

**Descripción del Módulo:**
```text
Chord progressions, voicings, and generation helpers for FL Studio MCP.
```

### Funciones Globales

- `build_chord`: Build a chord from root note, quality and octave.
- `get_progression_chords`: Get chord voicings for a progression in a specific key.
- `progression_to_midi_notes`: Convert a chord progression to send_melody() compatible note data string.
- `format_progression_info`: Format progression information as a readable string.
- `list_progressions`: List all available progressions, optionally filtered by genre.

---

## Módulo: `engine/knowledge/composition/basslines.py`

**Descripción del Módulo:**
```text
Bass production knowledge, processing chains, and bassline generation for FL Studio MCP.

Encodes all bass production knowledge from plugins_bajos_fl_studio.txt including
bass types per genre, processing chains, growl techniques, distortion plugin
comparisons, multiband techniques, golden rules, and production tricks.
```

### Funciones Globales

- `_nearest_scale_tone`: Find the nearest note that belongs to the scale.
- `_get_bpm_style_recommendation`: Get bassline style recommendation based on BPM.
- `generate_bassline_notes`: Generate a bassline as note data compatible with send_melody().
- `format_bass_type_info`: Format bass type information for a given genre as a readable string.
- `format_processing_chain`: Format the bass processing chain as a readable string.
- `format_growl_guide`: Format the complete bass growl technique as a readable string.
- `format_golden_rules`: Format golden rules as a readable string.
- `list_distortion_plugins`: List distortion plugins with their settings, optionally filtered.

---

## Módulo: `engine/knowledge/composition/scales.py`

**Descripción del Módulo:**
```text
Scale definitions, descriptions, and helper functions for FL Studio MCP.
```

### Funciones Globales

- `get_scale_notes`: Return MIDI note numbers for one octave of a scale.
- `get_scale_notes_range`: Return all MIDI notes in a scale across multiple octaves.
- `format_scale_info`: Format scale information as a readable string.

---

## Módulo: `engine/knowledge/composition/drum_patterns.py`

**Descripción del Módulo:**
```text
Drum patterns with exact step/velocity data from GUIA_BOOM_BAP_90s_COMPLETA.txt.
```

### Funciones Globales

- `_step_to_beat_position`: Convert 1-indexed step number to beat position.
- `get_patterns_for_bpm`: Get drum patterns that match a specific BPM.
- `check_bpm_compatibility`: Check if a BPM is compatible with a pattern and return a warning if not.
- `pattern_to_midi_notes`: Convert a drum pattern to send_melody() compatible note data string.
- `list_patterns`: List all available patterns, optionally filtered by genre.
- `format_velocity_guide`: Format velocity reference as readable string.

---

## Módulo: `engine/memory/user_learning.py`

**Descripción del Módulo:**
```text
AbletonEngine User Learning & Persistent Memory Engine.
Stores favorite patterns (with 1-5 star ratings), user production preferences,
and session decision history in state/learned/ for continuous cross-session improvement.
```

### Funciones Globales

- `_load_json`: Sin documentación
- `_save_json`: Sin documentación
- `save_favorite_pattern`: Saves a pattern approved or rated by the user into persistent memory.
- `get_favorite_patterns`: Retrieves saved favorite patterns filtered by type, genre, and minimum star rating.
- `save_user_preference`: Stores a durable user preference (e.g., favorite scale, default master target, preferred VSTs).
- `get_user_preferences`: Retrieves stored preferences by category and optional key.
- `log_decision_feedback`: Logs whether a proposed decision/recipe was approved by the user.
- `get_learned_context_summary`: Generates a concise markdown summary of learned user preferences for Copilot context injection.

---

## Módulo: `engine/arrangement/density.py`

**Descripción del Módulo:**
```text
Arrangement Density Controller:
Calculates and controls notes per beat/bar across sections and roles.
Guarantees climactic energy matches density targets without frequency mud.
```

### Clases

#### `DensityController`
Calculates, verifies, and modulates musical density across sections.

- **Métodos:**
  - `calculate_section_density`: Computes notes per bar.
  - `evaluate_density_curve`: Validates that density curve aligns with energy arc.

---

## Módulo: `engine/arrangement/scoring.py`

**Descripción del Módulo:**
```text
Arrangement Quality Scorer:
Scores tension dynamics, contrast, pacing, and overall flow.
```

### Clases

#### `ArrangementScorer`
Evaluates comprehensive musical arrangement quality.

- **Métodos:**
  - `score_arrangement`: Sin documentación

---

## Módulo: `engine/arrangement/generator.py`

**Descripción del Módulo:**
```text
Arrangement Generator:
High-level director of song composition and structure generation.
Coordinates Energy Curves, Role Matrix, Multi-Drop Differentiation,
Variation Planning, Repetition Linting, and Compilation.
```

### Clases

#### `ArrangementGenerator`
Master Arrangement Generator for complete song workflows.

- **Métodos:**
  - `__init__`: Sin documentación
  - `create_song_arrangement`: Constructs an intelligent, fully linted and scored Song arrangement.
  - `preview`: Generates full preview report without mutating Ableton Live.
  - `build`: Builds and executes full song into Ableton Live.

---

## Módulo: `engine/arrangement/locking.py`

**Descripción del Módulo:**
```text
Arrangement Locking Manager:
Allows specific sections or roles to be locked, preserving them completely
during selective regeneration operations.
```

### Clases

#### `ArrangementLockManager`
Manages locks on sections and musical roles.

- **Métodos:**
  - `__init__`: Sin documentación
  - `lock_section`: Sin documentación
  - `unlock_section`: Sin documentación
  - `lock_role`: Sin documentación
  - `unlock_role`: Sin documentación
  - `is_section_locked`: Sin documentación
  - `is_role_locked`: Sin documentación
  - `to_dict`: Sin documentación

---

## Módulo: `engine/arrangement/compiler.py`

**Descripción del Módulo:**
```text
Arrangement Compiler:
Translates logical Song model into Ableton Session clips & Arrangement timeline.
Enforces ACID transaction safety, dry-run preview invariant, and phrase alignment.
```

### Clases

#### `ArrangementCompiler`
Compiles Song data structure into concrete Ableton Live clips and notes.

- **Métodos:**
  - `__init__`: Sin documentación
  - `compile`: Compiles the entire song arrangement.
  - `_map_roles_to_tracks`: Maps standard roles to active session tracks.

---

## Módulo: `engine/arrangement/arrangement_composer.py`

**Descripción del Módulo:**
```text
Arrangement Composer & Multi-Section Timeline Orchestrator:
Orchestrates a complete 5-section musical song directly onto Ableton Live's Arrangement timeline.
Enforces structural progression: Intro -> Verse -> Pre-Drop (with 1-bar vacuum drop) -> Drop / Chorus -> Outro.
Creates cue points, generates unique musical patterns per section and role, duplicates clips to their
exact beat locations, and switches Live to Arrangement view.
```

### Clases

#### `ArrangementSection`
Specification of an arrangement section.

- **Métodos:**
  - `__init__`: Sin documentación

#### `ArrangementComposer`
Builds and deploys complete multi-section arrangements to Ableton Live.

- **Métodos:**
  - `compose_and_deploy`: Executes full arrangement composition:
  - `_generate_section_notes`: Generates tailored musical notes for a role in a specific section.
  - `_drums_pattern`: Generates dynamic drum patterns for 808 Kit (Kick=36, Snare=38, Clap=39, Hat=42, OpenHat=46).
  - `_sub_bass_pattern`: Generates 808 Sub Bass notes (C#1=37, A0=33, B0=35, G#0=32).
  - `_chords_pattern`: Generates chord progressions (C#m - A - B - G#m).
  - `_lead_pattern`: Generates cutting Lead Hook melodies (C# Minor).
  - `_vocals_pattern`: Generates rhythmic vocal chop triggers.
  - `_pad_pattern`: Generates ethereal atmospheric pad layers.
  - `_fx_pattern`: Generates FX triggers (Pitch 60=Riser, 62=Impact, 64=Downlifter).

---

## Módulo: `engine/arrangement/automation/live_automation.py`

**Descripción del Módulo:**
```text
Live Physical Automation Engine:
Manages real-time and arrangement automation envelopes in Ableton Live.
Applies physical filter sweeps, pre-drop vacuum cuts, and tension washouts.
```

### Clases

#### `LiveAutomationEngine`
Orchestrates physical automation curves and envelopes directly on Ableton Live tracks.

- **Métodos:**
  - `detect_device_parameter`: Scans devices on a track to find a matching parameter name from candidates.
  - `apply_filter_sweep`: Calculates and applies a filter sweep build-up or breakdown on the specified track.
  - `apply_pre_drop_vacuum`: Creates dramatic vacuum silence / energy cut right before the drop.
  - `apply_reverb_washout`: Calculates and applies a dramatic reverb build-up that snaps to dry on the downbeat of the drop.

---

## Módulo: `engine/arrangement/automation/clip_suggester.py`

**Descripción del Módulo:**
```text
Clip Automation Suggester:
Proactively generates and offers tangible, contextual vector automation recipes
whenever a clip is created or added to Ableton Live.
```

### Clases

#### `ClipAutomationRecipe`
Represents a specific, tangible automation curve recipe.

- **Métodos:**
  - `__init__`: Sin documentación
  - `to_dict`: Sin documentación

#### `ClipAutomationSuggester`
Analyzes track instruments, devices, and musical context to offer
and stamp vector automation curves on clips.

- **Métodos:**
  - `get_recipe`: Sin documentación
  - `suggest_for_track`: Inspects track devices and name to return the top 3-4 contextual automation recipes.
  - `generate_points`: Generates mathematically precise normalized breakpoint points across the clip duration.
  - `apply_recipe_to_clip`: Bakes an automation recipe into a Session clip's envelope and optionally duplicates it

---

## Módulo: `engine/arrangement/automation/recorder.py`

**Descripción del Módulo:**
```text
engine/arrangement/automation/recorder.py
High-Precision Live Arrangement Automation Recorder for Ableton Live.

Executes real-time arrangement automation overdubbing:
- Moves playhead to precise start_bar / start_beat.
- Arms arrangement recording (song.record_mode = True, arrangement_overdub = True).
- Smoothly sweeps parameters across mathematical curves (linear, exponential, sigmoid, drop vacuum).
- Disengages record mode, re-enables automation lanes, and returns verification status.
- Guarantees tangible red curves with editable vector breakpoints when pressing 'A' in Ableton Live.
```

### Clases

#### `ArrangementAutomationRecorder`
Orchestrates physical recording of tangible arrangement automation curves
onto Ableton Live track lanes.

- **Métodos:**
  - `bars_to_beats`: Converts musical bars (4/4 time) to beats.
  - `beats_to_seconds`: Converts musical beats to real-time seconds at a given tempo.
  - `record_curve`: Records a tangible arrangement automation curve onto the track lane in Ableton Live.
  - `record_multi_pass`: Records multiple automation curves across multiple tracks/devices simultaneously

---

## Módulo: `engine/arrangement/automation/weaver.py`

**Descripción del Módulo:**
```text
Arrangement Automation Weaver:
Translates high-level energy curves and transition directives into continuous,
mathematically precise parameter breakpoint envelopes in Ableton Live.
Weaves filter sweeps, reverb washouts, sub-bass cutoffs, and gain staging.
```

### Clases

#### `TransitionAutomationType`

#### `ArrangementAutomationWeaver`
Computes and injects multi-parameter arrangement automation breakpoint curves.

- **Métodos:**
  - `_interpolate`: Interpolates normalized t in [0.0, 1.0] across start_val and end_val.
  - `generate_filter_sweep`: Generates continuous filter cutoff sweep envelope.
  - `generate_reverb_washout`: Generates dramatic reverb washout: rises exponentially to max_wet during build,
  - `generate_sub_cleanup`: Pre-drop sub cleanup: ramps volume down or filter up right before drop impact.
  - `apply_transition_automation`: Injects calculated transition automation curves into Live.

---

## Módulo: `engine/arrangement/templates/structures.py`

### Clases

#### `StructureLibrary`
- **Métodos:**
  - `get_template`: Sin documentación

### Funciones Globales

- `get_structure_template`: Sin documentación

---

## Módulo: `engine/arrangement/templates/genres.py`

### Clases

#### `GenreArrangementProfile`

#### `GenreTemplates`
- **Métodos:**
  - `get_genre_template`: Sin documentación

### Funciones Globales

- `get_genre_profile`: Sin documentación

---

## Módulo: `engine/arrangement/narrative/arc.py`

**Descripción del Módulo:**
```text
Narrative Arc:
Models song progression as a 5-stage dramatic narrative arc:
1. Exposition (Intro/Verse)
2. Rising Action (Build)
3. Climax I (Drop 1)
4. Falling Action / Reflection (Breakdown)
5. Climax II (Drop 2 - Main Peak)
6. Resolution (Outro)
```

### Clases

#### `NarrativeStage`

#### `NarrativeArc`
Evaluates narrative tension and pacing throughout the song.

- **Métodos:**
  - `evaluate_narrative`: Scores how well the section sequence conforms to a compelling narrative arc.

---

## Módulo: `engine/arrangement/energy/curve.py`

### Clases

#### `EnergyCurve`
Piecewise multi-point energy curve with continuous interpolation across song bars.

- **Métodos:**
  - `__init__`: Sin documentación
  - `add_keypoint`: Sin documentación
  - `get_at_bar`: Returns interpolated EnergyDimensions at any arbitrary bar.
  - `find_climaxes`: Detect primary and secondary energy peaks in the curve.
  - `to_dict`: Sin documentación

#### `EnergyCurveGenerator`
Generates continuous energy curves for arrangements and synchronizes section values.

- **Métodos:**
  - `generate_curve`: Sin documentación

---

## Módulo: `engine/arrangement/energy/dimensions.py`

### Clases

#### `EnergyDimensions`
Multi-dimensional representation of musical energy in an arrangement.

- **Métodos:**
  - `to_dict`: Sin documentación
  - `from_dict`: Sin documentación

---

## Módulo: `engine/arrangement/fx/ear_candy_transitions.py`

**Descripción del Módulo:**
```text
Ear Candy Transition Engine:
Unifies analog tape stops, reverse vocal swells, and freeze wash FX across transition boundaries.
```

### Clases

#### `EarCandyTransitionEngine`
Generates micro-transitional FX and automation curves across 96 bars.

- **Métodos:**
  - `generate_tape_stop_transition`: Generates analog tape slowdown curve preceding target_bar (default bar 33 -> Drop 1).
  - `generate_reverse_vocal_swell`: Calculates coordinates and parameters for a reverse vocal sweep leading into the drop.
  - `generate_reverb_freeze_wash`: Freezes the reverb decay tail at the end of the verse / pre-chorus boundary.
  - `get_full_ear_candy_manifest`: Returns the complete micro-production FX transition roadmap.

---

## Módulo: `engine/arrangement/fx/ear_candy.py`

**Descripción del Módulo:**
```text
Ear Candy & Micro-FX Engine:
Injects unexpected transitional ear candy: vinyl tape-stops, glitch stutter rolls,
accelerating subdivisions, and pre-drop vacuum silences.
```

### Clases

#### `EarCandyType`

#### `EarCandyEngine`
Generates micro-production ear candy automation and MIDI events.

- **Métodos:**
  - `generate_tape_stop`: Calculates pitch bend and volume automation points simulating analog tape slowdown.
  - `generate_glitch_stutter`: Subdivides a single note into an explosive rhythmic stutter (e.g. 1/8 -> 1/16 -> 1/32 -> 1/64).
  - `generate_pre_drop_vacuum`: Creates a dead-air vacuum immediately before a transition or drop

---

## Módulo: `engine/arrangement/drops/engine.py`

**Descripción del Módulo:**
```text
Multi-Drop Differentiation Engine:
Guarantees Drop 2 > Drop 1 in energy, density, harmonic/melodic variation, and climax satisfaction.
```

### Clases

#### `DropDifferentiationEngine`
Enforces the core rule: Drop 2 must never be a mere copy of Drop 1.
Drop 2 must have greater dynamic energy, new counter-melodies, fuller rhythm, or harmonic extension.

- **Métodos:**
  - `differentiate_drops`: Adjust Drop 2 (and Drop 3 if any) to ensure progressive escalation.
  - `compute_drop_contrast`: Calculates quantitative contrast between two drops.

---

## Módulo: `engine/arrangement/models/section.py`

### Clases

#### `SectionType`
- **Métodos:**
  - `from_str`: Sin documentación

#### `RoleState`
- **Métodos:**
  - `from_str`: Sin documentación

#### `Section`
Represents a discrete musical section within a song arrangement.

- **Métodos:**
  - `__init__`: Sin documentación
  - `bars`: Sin documentación
  - `bars`: Sin documentación
  - `section_type`: Sin documentación
  - `section_type`: Sin documentación
  - `variation_type`: Sin documentación
  - `variation_type`: Sin documentación
  - `to_dict`: Sin documentación
  - `from_dict`: Sin documentación

---

## Módulo: `engine/arrangement/models/song.py`

### Clases

#### `SongArrangement`
Represents a complete musical arrangement model.

- **Métodos:**
  - `__init__`: Sin documentación
  - `name`: Sin documentación
  - `name`: Sin documentación
  - `total_bars`: Sin documentación
  - `duration_seconds`: Sin documentación
  - `get_section`: Sin documentación
  - `to_dict`: Sin documentación
  - `summary`: Sin documentación

---

## Módulo: `engine/arrangement/impacts/downlifters.py`

**Descripción del Módulo:**
```text
Impacts, Downlifters & Sub-Boom Engine.
Generates dynamic transitional releases:
- Subphase 2.1: White noise & tonal downlifters with exponential filter decay (20 kHz -> 150 Hz).
- Subphase 2.2: Sub-boom impacts with downward pitch modulation (140 Hz -> 32 Hz / 808 pitch drop).
- Subphase 2.3: Reverse cymbal swells with surgical pre-impact silence gap (~0.05 beats).
```

### Clases

#### `ImpactType`

#### `DownlifterCurve`

#### `ImpactEnvelope`
- **Métodos:**
  - `to_dict`: Sin documentación

#### `ImpactEngine`
Procedural impact and downlifter generator for post-drop and section transitions.

- **Métodos:**
  - `generate_downlifter_sweep`: Subphase 2.1: Downlifter sweep with descending filter cutoff and decaying volume.
  - `generate_sub_boom`: Subphase 2.2: Sub-boom drop with analog sine pitch sweep (140 Hz -> 32 Hz).
  - `generate_reverse_cymbal_swell`: Subphase 2.3: Reverse cymbal swell with pre-impact silence vacuum.
  - `apply_impact_to_live`: Dispatches impact generation to Ableton Live via connection adapter.

---

## Módulo: `engine/arrangement/transitions/pre_drop.py`

**Descripción del Módulo:**
```text
Pre-Drop Tension & Acoustic Vacuum Generator:
Creates surgical silence gaps, low-end mutes, and tension windows right before drops hit.
```

### Clases

#### `PreDropGenerator`
Specialized tension builder for sections transitioning into a DROP.

- **Métodos:**
  - `create_pre_drop`: Creates a pre-drop transition descriptor that cuts off low-end and creates

#### `PreDropVacuumEngine`
Calculates exact silence windows and low-end cut automation envelopes for drops.

- **Métodos:**
  - `get_vacuum_windows`: Returns the acoustic vacuum silence coordinates for Drop 1 and Final Chorus.
  - `generate_vacuum_mute_envelope`: Generates volume automation breakpoints:

---

## Módulo: `engine/arrangement/transitions/automation.py`

**Descripción del Módulo:**
```text
Transition & Energy Automation Engine:
Generates continuous, mathematically precise automation breakpoint curves for
filter sweeps, reverb washouts, volume swells, sidechain simulation, and arrangement energy.
```

### Clases

#### `AutomationCurveType`

#### `TransitionAutomationEngine`
Computes exact automation breakpoint envelopes for musical arrangement transitions.

- **Métodos:**
  - `_interpolate`: Interpolate normalized t in [0.0, 1.0] to [start_val, end_val] according to curve.
  - `generate_filter_sweep`: Generate filter frequency sweep envelope.
  - `generate_reverb_washout`: Generate classic washout reverb automation:
  - `generate_volume_swell`: Generate volume swell / riser automation.
  - `generate_sidechain_pump`: Simulate 4-on-the-floor / 8th-note sidechain pumping automation.
  - `generate_energy_curve_automation`: Generate continuous macro automation envelope mapping arrangement section

---

## Módulo: `engine/arrangement/transitions/engine.py`

**Descripción del Módulo:**
```text
Transition Engine:
Computes and injects transition descriptors between sections across the arrangement.
```

### Clases

#### `TransitionEngine`
Plans and applies seamless musical transitions based on section energy delta.

- **Métodos:**
  - `plan_transitions`: Sin documentación

---

## Módulo: `engine/arrangement/transitions/models.py`

**Descripción del Módulo:**
```text
Transition Models:
Data classes for transition descriptors, types, and automated FX fills.
```

### Clases

#### `TransitionType`

#### `TransitionDescriptor`
Defines how the song transitions between two adjacent sections.

- **Métodos:**
  - `to_dict`: Sin documentación

---

## Módulo: `engine/arrangement/transitions/risers.py`

**Descripción del Módulo:**
```text
Transition Risers & Continuous Sweeps Engine:
Generates Auto Filter frequency sweeps, white noise/synth pitch risers,
and procedural accelerating snare rolls to bridge energy gaps before drops.
```

### Clases

#### `SweepFilterType`

#### `TransitionRisersEngine`
Architect for automated filter risers, noise sweeps, and procedural build fills.

- **Métodos:**
  - `generate_filter_sweep`: Calculates exponential frequency automation points for Ableton Auto Filter.
  - `generate_noise_pitch_riser`: Calculates pitch bend (+24 semitones) and volume crescendo automation curves.
  - `generate_procedural_snare_roll`: Generates an accelerating build-up snare roll (1/8 -> 1/16 -> 1/24 -> 1/32 -> flam).
  - `apply_transition_riser`: Dispatches automated risers and fills into Ableton Live.

---

## Módulo: `engine/arrangement/transitions/impacts.py`

**Descripción del Módulo:**
```text
Section Impact & Downlifter Engine:
Deploys sub-booms, crashes, and exponential downlifters at section arrivals across 96 bars.
```

### Clases

#### `SectionImpactEvent`
- **Métodos:**
  - `to_dict`: Sin documentación

#### `SectionImpactEngine`
Orchestrates arrival impacts and downlifters at section boundaries across 96 bars.

- **Métodos:**
  - `get_section_impact_manifest`: Returns the complete 8-section impact plan with metadata.
  - `generate_impact_notes`: Generates physical MIDI NoteEvents for crashes and sub-booms on the Foley/FX track.

---

## Módulo: `engine/arrangement/variation/planner.py`

**Descripción del Módulo:**
```text
Variation Planner:
Assigns transformational strategies to musical motifs across song sections.
Prevents monotony by scheduling musical operations: inversion, retrograde, rhythmic augmentation/diminution.
```

### Clases

#### `VariationDirective`

#### `VariationPlanner`
Plans how musical motifs evolve across the song sections.

- **Métodos:**
  - `plan_variations`: Assigns variation directives per section to maintain progressive interest.

---

## Módulo: `engine/arrangement/variation/motifs.py`

**Descripción del Módulo:**
```text
Motif Evolution Manager:
Interfaces with Fase 2 Motif Memory to apply algebraic transformations.
```

### Clases

#### `MotifEvolutionManager`
Manages transformed variations of musical motifs for arrangement.

- **Métodos:**
  - `apply_transformation`: Applies algorithmic transformations to a list of note dicts.

---

## Módulo: `engine/arrangement/blueprints/song_arranger.py`

**Descripción del Módulo:**
```text
Full Song Blueprint & Dynamic Section Arranger Engine:
Orchestrates an entire radio/streaming commercial song structure across 96 bars (~3 minutes)
in Ableton Live 12 Suite's Arrangement View with dynamic role matrix distribution,
pre-drop micro-vacuums, section cue points, and multi-track clip placements.
```

### Clases

#### `SectionSpec`
- **Métodos:**
  - `start_beat`: Sin documentación
  - `end_beat`: Sin documentación
  - `end_bar`: Sin documentación

#### `FullSongBlueprint`
- **Métodos:**
  - `duration_seconds`: Sin documentación

#### `FullSongArrangerEngine`
End-to-end architect for full-length song arrangement and dynamic layer orchestration.

- **Métodos:**
  - `generate_96bar_blueprint`: Generates the golden standard 96-bar (~3 minute) commercial structure:
  - `calculate_clip_placements`: Calculates all Session-to-Arrangement clip duplications based on the section role matrix.
  - `calculate_pre_drop_vacuums`: Calculates ear candy pre-drop silence vacuum automation points.
  - `orchestrate_full_song`: Executes end-to-end full song arrangement orchestration in Ableton Live:

---

## Módulo: `engine/arrangement/structure/beat_switch.py`

**Descripción del Módulo:**
```text
Beat Switch Orchestrator:
Coordinates dramatic mid-song beat switches (tempo jumps, mood transitions,
track group muting/activation, and metric handoffs).
```

### Clases

#### `BeatSwitchOrchestrator`
Orchestrates seamless and dramatic multi-movement beat switches.

- **Métodos:**
  - `plan_beat_switch`: Generates tempo automation envelopes and arrangement markers for a multi-part beat switch.

---

## Módulo: `engine/arrangement/roles/matrix.py`

**Descripción del Módulo:**
```text
Role Activation Matrix & Energy-to-Role Mapping.
Defines which musical roles are active, muted, or featured per section and energy tier.
```

### Clases

#### `RoleSlot`

#### `SectionRoleMap`
- **Métodos:**
  - `is_active`: Sin documentación
  - `active_roles`: Sin documentación
  - `activate`: Sin documentación
  - `deactivate`: Sin documentación

#### `RoleMatrix`
Manages role activation across all sections of a song.

- **Métodos:**
  - `__init__`: Sin documentación
  - `initialize_for_sections`: Populate initial role activations based on section type and energy.
  - `get_section_roles`: Sin documentación
  - `to_dict`: Sin documentación

---

## Módulo: `engine/arrangement/roles/orchestrator.py`

**Descripción del Módulo:**
```text
Role Orchestrator:
Controls role entry/exit staging, frequency collision avoidance, and role density.
```

### Clases

#### `RoleOrchestrator`
Ensures roles enter and exit musically without sudden jarring transitions,
and detects frequency band competition.

- **Métodos:**
  - `__init__`: Sin documentación
  - `validate_arrangements`: Verify frequency balance and smooth role staging across all sections.
  - `apply_staggered_entrances`: Stagger role entries across phrases (e.g. 0-4 bars, 4-8 bars, etc.).

---

## Módulo: `engine/arrangement/linter/comparison.py`

**Descripción del Módulo:**
```text
Section Comparison Engine:
Computes structural, harmonic, and rhythmic similarity between sections.
Calculates repetition index (0.0 = completely unique, 1.0 = duplicate copy).
```

### Clases

#### `SectionComparator`
Computes similarity index between sections to prevent copy-paste arrangements.

- **Métodos:**
  - `compare_sections`: Calculates similarity metrics between two sections.

---

## Módulo: `engine/arrangement/linter/linter.py`

**Descripción del Módulo:**
```text
Arrangement Repetition & Flow Linter:
Enforces production-grade structural rules:
1. Anti-copy-paste invariant (no duplicate drops or back-to-back clone sections)
2. Climax superiority (Drop 2 > Drop 1 in energy/intensity)
3. Energy monotonicity penalty (no long flat stretches)
4. Narrative completeness (exposition, tension, climax, resolution)
```

### Clases

#### `LintIssue`

#### `ArrangementLinter`
Audits arrangement quality and reports actionable lint issues.

- **Métodos:**
  - `lint`: Sin documentación

---

## Módulo: `engine/instruments/roles.py`

### Clases

#### `InstrumentRole`
- **Métodos:**
  - `from_str`: Sin documentación

#### `SoundProfile`
Sonic profile specification describing how a role should sound

- **Métodos:**
  - `to_dict`: Sin documentación

---

## Módulo: `engine/instruments/vst_guard.py`

**Descripción del Módulo:**
```text
VST Guard & Instrument Parameter Supervisor:
Enforces strict parameter exposure rules (INV-VST-PARAMS).
Guarantees that no instrument is left as an unconfigured blind init patch with only 1 parameter (Device On).
Automatically wraps plugins into Instrument Racks with 8 mapped Macros, or swaps to native synths
(Wavetable, Drift, Operator, Analog) with 50-90 fully sculpted sound design parameters.
```

### Clases

#### `VSTComplianceError`
Raised when an instrument fails parameter exposure or remains an unconfigured init patch.


#### `VSTGuard`
Supervisor for DAW instrument parameter exposure and sound design verification.

- **Métodos:**
  - `audit_track_instrument`: Audits the track's primary instrument for parameter exposure and compliance.
  - `enforce_instrument`: Enforces instrument compliance on a track:
  - `_apply_parameters`: Applies sound design parameter values to Wavetable or Instrument Rack.
  - `ensure_all_tracks_compliant`: Iterates across all production tracks and guarantees 100% compliance with INV-VST-PARAMS.

---

## Módulo: `engine/instruments/installed_scanner.py`

**Descripción del Módulo:**
```text
Installed Plugin Scanner & Semantic Role Classifier.
Scans standard Windows VST3 and VST directories, indexes available instruments and effects,
and classifies them into musical roles (KEYS, BASS, LEAD, DRUMS, VOCALS, FX, MASTER)
so the Copilot and AI agent make authentic sound design decisions based on the user's real setup.
```

### Clases

#### `PluginCategory`

#### `ScannedPlugin`
- **Métodos:**
  - `to_dict`: Sin documentación

#### `InstalledPluginScanner`
Scans local disk for installed VST3/VST plugins and classifies them by semantic musical role.

- **Métodos:**
  - `__init__`: Sin documentación
  - `scan`: Scans the configured plugin directories and builds the index.
  - `_process_plugin_file`: Sin documentación
  - `scan_live_session`: Queries the live connected Ableton instance to discover and register all installed VST3s.
  - `_get_relevance_score`: Sin documentación
  - `get_plugins_for_role`: Returns all plugins suitable for a specific musical role sorted by acoustic excellence and relevance.
  - `get_catalog_summary`: Returns structured overview of all discovered plugins grouped by role.
  - `recommend_top_for_role`: Returns the top 5 curated instrument/effect options for a role,
  - `recommend_for_role`: Returns the optimal instrument recommendation for a given role and style.
  - `verify_and_fallback`: Verifies that a loaded instrument is active and healthy in Live.

---

## Módulo: `engine/instruments/browser_catalog.py`

**Descripción del Módulo:**
```text
Live Browser Catalog & VST3 / Native Preset Discovery Engine.
- Scans and catalogs available VST3 instruments (Arturia, Spectrasonics, Native Instruments, Vital, Serum) and native Live presets.
- Presents structured sound choices categorized by musical role (KEYS, BASS, LEAD, DRUMS, FX).
- Enables the Copilot and AI agent to select concrete, authentic sound sources rather than defaulting blindly to empty devices.
```

### Clases

#### `InstrumentSourceCategory`

#### `SoundSourceOption`
- **Métodos:**
  - `to_dict`: Sin documentación

#### `LiveBrowserCatalogEngine`
Catalog inspection and dynamic instrument loader.

- **Métodos:**
  - `get_available_sources_for_role`: Returns sound options for a musical role (KEYS, BASS, LEAD, PAD, DRUMS, VOCALS, FX, MASTER, GUITAR, PERCUSSION).
  - `get_role_suggestions`: Returns top recommended instruments/sources for a role (default 5),
  - `list_all_available_instruments`: Lists all available instruments organized by role or filtered by a specific role.

---

## Módulo: `engine/instruments/models.py`

### Clases

#### `InstrumentSource`

#### `InstrumentDescriptor`
- **Métodos:**
  - `to_dict`: Sin documentación

#### `PadAssignment`
- **Métodos:**
  - `to_dict`: Sin documentación

#### `InstrumentExecutionPlan`
- **Métodos:**
  - `to_dict`: Sin documentación

#### `RackInspectionReport`
- **Métodos:**
  - `to_dict`: Sin documentación

---

## Módulo: `engine/instruments/drum_rack_guard.py`

**Descripción del Módulo:**
```text
Drum Rack Guard & Pad Population Supervisor:
Audits drum racks in Ableton Live to guarantee that pads are physically populated
with devices/samples, preventing silent drum tracks ("Suelte aquí un instrumento o muestra").
```

### Clases

#### `DrumRackEmptyError`
Raised when a Drum Rack in Ableton Live has 0 populated pads or missing devices.

- **Métodos:**
  - `__init__`: Sin documentación

#### `DrumRackGuard`
Supervises Drum Rack integrity, pad devices, and sound readiness.

- **Métodos:**
  - `audit_drum_rack`: Audits a Drum Rack on track_index:
  - `enforce_populated_drum_kit`: Audits the Drum Rack and if empty, automatically remediates by loading
  - `audit_drum_clip_octaves`: Audits MIDI clip notes on a drum track against Drum Rack physical pad quadrant layout.
  - `remediate_drum_clip_octaves`: Transposes all notes in the drum clip by semitone_shift (default -24 semitones / 2 octaves)

---

## Módulo: `engine/instruments/drum_map.py`

### Clases

#### `DrumMap`
Canonical single source of truth mapping between MIDI note pitches and drum roles.

Ensures absolute mathematical consistency:
Music Engine DrumMap == Ableton Drum Rack DrumMap

- **Métodos:**
  - `get_note_for_role`: Sin documentación
  - `get_role_for_note`: Sin documentación
  - `get_display_name_for_note`: Sin documentación
  - `get_display_name`: Sin documentación

---

## Módulo: `engine/instruments/plugins/registry.py`

### Clases

#### `PluginRegistry`
Central registry of plugin parameter maps for native Ableton devices
and 3rd party VST3s (Vital, Omnisphere, Analog Lab, Kontakt, Thermal, etc.).
Extensible and non-limiting: Unknown devices fall back to generic semantic matching.

- **Métodos:**
  - `__init__`: Sin documentación
  - `register_profile`: Sin documentación
  - `get_profile`: Sin documentación
  - `list_registered_plugins`: Sin documentación
  - `_normalize_key`: Sin documentación
  - `_init_default_profiles`: Sin documentación

---

## Módulo: `engine/instruments/plugins/models.py`

### Clases

#### `PluginSemanticRole`

#### `ParameterSpec`
- **Métodos:**
  - `to_dict`: Sin documentación

#### `PluginProfile`
- **Métodos:**
  - `to_dict`: Sin documentación

#### `NormalizedParameterResult`
- **Métodos:**
  - `to_dict`: Sin documentación

---

## Módulo: `engine/instruments/plugins/normalizer.py`

### Clases

#### `VSTParameterNormalizer`
Intelligent parameter normalizer and semantic mapper for VST3 plugins and native devices.
Bridges musical intent (e.g. CUTOFF, DRIVE, MACRO_1) to real device parameter names and normalized [0.0, 1.0] ranges.

- **Métodos:**
  - `__init__`: Sin documentación
  - `resolve_parameter`: Resolves a semantic role to a real device parameter from the given device parameters list.
  - `normalize_value`: Normalizes a raw parameter value to [0.0, 1.0] range
  - `denormalize_value`: Denormalizes a [0.0, 1.0] value into the device's native [min_val, max_val] range
  - `_parse_role`: Sin documentación
  - `_find_param_by_name`: Sin documentación
  - `_clean_token`: Sin documentación
  - `_build_result`: Sin documentación

---

## Módulo: `engine/instruments/rack/builder.py`

### Clases

#### `DrumRackBuilder`
Orchestrates building, populating, and verifying Drum Racks with strict idempotency.

- **Métodos:**
  - `__init__`: Sin documentación
  - `plan_population`: Inspects existing track state and builds an execution plan for empty pads.
  - `execute_plan`: Executes the operations in an execution plan against Ableton Live.

---

## Módulo: `engine/instruments/rack/verifier.py`

### Clases

#### `DrumRackVerifier`
Verifies that each populated pad in a Drum Rack contains real chains, devices and samples.

- **Métodos:**
  - `__init__`: Sin documentación
  - `verify`: Sin documentación

---

## Módulo: `engine/instruments/rack/inspector.py`

### Clases

#### `DrumRackInspector`
Inspects tracks and Drum Racks in Live to detect empty racks and pad population state.

- **Métodos:**
  - `__init__`: Sin documentación
  - `inspect`: Sin documentación

---

## Módulo: `engine/instruments/library/resolver.py`

### Clases

#### `SampleCandidate`
- **Métodos:**
  - `to_dict`: Sin documentación

#### `SampleLibraryResolver`
Intelligent scanner, semantic indexer and sample resolver for local sample libraries.

- **Métodos:**
  - `__init__`: Sin documentación
  - `ensure_index`: Scans sample roots and indexes available audio files quickly
  - `find_samples`: Search and rank samples for a given role, style and character without loading anything
  - `_generate_fallback`: Provides a safe, explicit fallback sample if preferred match is unavailable

---

## Módulo: `engine/instruments/library/preset_catalog.py`

**Descripción del Módulo:**
```text
Curated Catalog of Verified Native Instrument and Drum Presets for Ableton Live 12 Suite.

Provides instant resolution from high-level musical roles, genres, and timbral intents
to production-ready, authentic .adv and .adg presets without loading empty 'init' patches.
```

### Clases

#### `PresetEntry`
- **Métodos:**
  - `to_dict`: Sin documentación

#### `PresetCatalog`
Fast resolver and index for curated native Live 12 presets.

- **Métodos:**
  - `resolve_preset`: Find the best matching preset for a musical role, genre, and timbral character.
  - `list_presets`: Sin documentación
  - `search`: Sin documentación

---

## Módulo: `engine/instruments/library/crawler.py`

### Clases

#### `LibraryCrawler`
Automated crawler and indexer for Ableton Live 12 library and VST3 plugins.
Indexes presets, instruments, audio effects, and 3rd party plugins into a searchable cache.

- **Métodos:**
  - `__init__`: Sin documentación
  - `load_cache`: Loads cached index from disk if present
  - `save_cache`: Saves current index to disk atomically
  - `crawl_category`: Crawls a browser category path recursively using the provided query function.
  - `search`: Searches indexed items by name or URI.
  - `get_summary`: Returns statistics of the crawler index

---

## Módulo: `engine/instruments/library/search.py`

### Funciones Globales

- `get_sample_resolver`: Sin documentación
- `search_samples`: MCP & Engine interface to search for samples without modifying Ableton.
- `select_sample`: Deterministically select the best sample candidate using seed.

---

## Módulo: `engine/instruments/execution/planner.py`

### Clases

#### `InstrumentPlanner`
Resolves and plans instrumentation for both melodic instruments and drum kits.

- **Métodos:**
  - `resolve_instrument`: Sin documentación

---

## Módulo: `engine/instruments/profiles/sound_profiles.py`

### Funciones Globales

- `get_sound_profile`: Sin documentación

---

## Módulo: `engine/instruments/profiles/drum_kits.py`

### Clases

#### `DrumKitPadConfig`

#### `DrumKitProfile`
- **Métodos:**
  - `to_dict`: Sin documentación

### Funciones Globales

- `get_drum_kit_profile`: Sin documentación

---

## Módulo: `engine/audio/stem_audit.py`

**Descripción del Módulo:**
```text
Multi-Stem Bouncer & Deep Phase Forensics.
- Subphase 3.1: Orchestrates stem export partition into standard commercial groups.
- Subphase 3.2: Audits inter-stem phase cross-correlation in sub-bass (20-150 Hz) and flags destructive cancellations (rho < -0.30).
- Subphase 3.3: Computes stem integrated LUFS, True Peak, Crest Factor, and LRA headroom compliance.
```

### Clases

#### `PhaseCorrelationStatus`

#### `StemMetric`
- **Métodos:**
  - `to_dict`: Sin documentación

#### `StemPhaseAuditResult`
- **Métodos:**
  - `to_dict`: Sin documentación

#### `StemAuditor`
Forensic analysis and export auditing for audio stems.

- **Métodos:**
  - `calculate_pearson_correlation`: Computes the Pearson correlation coefficient between two audio sample buffers:
  - `audit_stem_phase`: Subphase 3.2: Analyzes phase correlation between two stems (e.g. Drums vs Bass).
  - `audit_stem_loudness`: Subphase 3.3: Computes stem-level loudness and True Peak metrics.
  - `orchestrate_stem_export_and_audit`: Full orchestration of stem export plan, audio buffers inspection, and phase forensics.
  - `apply_stem_audit_adapter`: Dispatches stem export plan and phase audit via Live connection adapter.

---

## Módulo: `engine/audio/sample_generator.py`

**Descripción del Módulo:**
```text
Procedural Audio Sample Generator:
Generates studio-grade 44.1kHz 16-bit PCM WAV audio samples in memory or disk:
- Vocal vowel chants / hooks (synthesized formant filtering with human vibrato).
- Organic foley beds (band-limited pink/brown noise texture with subtle atmospheric resonance).
- Transition risers & sweeps (exponential frequency sweep + high-pass filtered noise).
- Transition impacts / sub drops (transient attack punch + exponential sub decay).
```

### Clases

#### `ProceduralSampleGenerator`
Generates standalone standard PCM WAV audio files for Ableton Live audio tracks.

- **Métodos:**
  - `get_cache_dir`: Returns the default directory for caching generated samples.
  - `generate_sample`: Generates a 16-bit Mono WAV audio file based on sample_type.

---

## Módulo: `engine/audio/semantic_sample_matcher.py`

**Descripción del Módulo:**
```text
Semantic Sample Matcher and Acoustic Feature Extractor.
Extracts 6D physical acoustic signatures from audio samples and matches
natural language intent (e.g. 'punchy kick', 'dark boomy 808', 'crisp snappy snare')
using normalized acoustic vector space and cosine similarity.
Zero external network calls, 100% deterministic, high-speed DSP.
```

### Clases

#### `AcousticSignature`
Normalized physical acoustic representation of an audio sample.

- **Métodos:**
  - `to_dict`: Sin documentación

#### `AcousticFeatureExtractor`
Extracts physical timbre, envelope, and frequency metrics from audio signals.

- **Métodos:**
  - `extract`: Computes 6D physical acoustic signature from raw audio.
  - `extract_from_file`: Reads audio file from disk and returns acoustic signature.

#### `SemanticSampleMatcher`
Matches text descriptions to audio samples based on acoustic vectors.

- **Métodos:**
  - `parse_intent_to_target_vector`: Parses words from text query and constructs normalized target acoustic vector.
  - `compute_similarity`: Computes hybrid similarity (80% Cosine Similarity + 20% Euclidean Proximity).
  - `rank_candidates`: Ranks candidates by semantic similarity to prompt.

---

## Módulo: `engine/audio/live_listener.py`

**Descripción del Módulo:**
```text
Live Audio Ear Bridge:
Captures real-time audio from Ableton Live via WASAPI Loopback, UDP/TCP socket stream,
or synthetic buffer, and pipes it into ITU-R BS.1770-5 Loudness and Audio Forensics STFT
for instant acoustic feedback without requiring offline stem exports.
```

### Clases

#### `LiveAudioListener`
Real-time acoustic listener and forensic ear bridge.

- **Métodos:**
  - `__init__`: Sin documentación
  - `capture_socket_stream`: Attempt to capture raw PCM float32/int16 chunks streamed over UDP socket from Ableton.
  - `generate_synthetic_stream`: Generate realistic dual-channel audio buffer for simulation, testing, and CI verification.
  - `analyze_audio_stream`: Perform deep acoustic audit on raw audio stream:
  - `listen`: Master listening command:

---

## Módulo: `engine/audio/stem_bouncer.py`

### Clases

#### `StemDefinition`

#### `StemExportPlan`
- **Métodos:**
  - `to_dict`: Sin documentación

#### `StemBouncer`
Automated stems export coordinator for arrangement sessions in Ableton Live.
Groups musical roles into clean stems (Drums, Bass, Keys, Leads, Vocals, FX, Master)
and prepares safe bounce workflows and metadata manifests.

- **Métodos:**
  - `__init__`: Sin documentación
  - `create_export_plan`: Analyzes session tracks and automatically partitions them into standard musical stem groups.
  - `generate_manifest`: Generates and saves the stem manifest JSON in the export directory.
  - `execute_stem_isolation_pass`: Orchestrates solo/mute state for rendering a single stem group cleanly in Live.
  - `reset_session_mutes`: Unmutes all tracks after stem isolation passes are finished.

---

## Módulo: `engine/audio/chopper/transient.py`

**Descripción del Módulo:**
```text
Drum Stem Demuxer & Transient Break Chopper:
Detects rhythmic slice points and transient boundaries in drum breaks and loops,
resequences them into classic break patterns (Amen Shuffle, Half-Time, Jungle/DnB, Lofi),
and exports mapped MIDI trigger sequences for Ableton Live Drum Racks and Simplers.
```

### Clases

#### `BreakPatternStyle`

#### `TransientSlice`

#### `TransientBreakChopper`
Intelligent slicer and resequencer for drum breaks and acoustic loops.

- **Métodos:**
  - `generate_slices`: Generates standard transient slice boundaries across the break length.
  - `resequence_break`: Algoritmically resequences chopped slices into target breakbeat patterns.
  - `chop_and_resequence`: Executes end-to-end break chopping, pattern resequencing, and Live clip writing.

---

## Módulo: `engine/audio/deconstruction/expressive_transcriber.py`

**Descripción del Módulo:**
```text
Expressive Audio-to-MIDI Transcriber.
Transcribes monophonic audio signals (vocals, humming, whistling, solo guitars, synth leads)
into quantized MIDI NoteEvents with velocity dynamics and continuous pitch bend detection.
Powered by PyTorch/torchaudio F0 detection with deterministic DSP autocorrelation fallback.
```

### Clases

#### `ExpressiveNoteEvent`
NoteEvent enriched with microtonal pitch bends and dynamic velocity.

- **Métodos:**
  - `to_note_event`: Sin documentación
  - `to_dict`: Sin documentación

#### `ExpressiveAudioTranscriber`
Converts audio recordings into expressive MIDI note events.

- **Métodos:**
  - `__init__`: Sin documentación
  - `_check_torchaudio`: Sin documentación
  - `hz_to_midi_pitch`: Converts frequency in Hz to closest MIDI note number and microtonal deviation in cents.
  - `extract_f0_curve`: Extracts fundamental frequency curve (F0 in Hz) frame by frame.
  - `transcribe`: Transcribes continuous F0 curve and energy novelty into discrete ExpressiveNoteEvents.
  - `transcribe_file`: Transcribes an audio file on disk to ExpressiveNoteEvents.

---

## Módulo: `engine/audio/deconstruction/neural_separator.py`

**Descripción del Módulo:**
```text
Hybrid Neural Stem Separator and Reference Energy Profiler.
Attempts to use Meta Demucs (HTDemucs) when available for state-of-the-art 4-stem separation.
Guarantees seamless fallback to pure DSP Multi-Band Crossover & Mid-Side decomposition
(AudioStemSeparator) if Demucs is not installed, out of memory, or timed out.
Also extracts multi-stem arrangement energy profiles across timeline bars.
```

### Clases

#### `HybridStemSeparator`
Hybrid AI/DSP Stem Separator with graceful fallback and arrangement profiling.

- **Métodos:**
  - `__init__`: Sin documentación
  - `_check_demucs`: Checks if demucs is installed and importable.
  - `separate`: Separates reference track into drums, bass, vocals, and other stems.
  - `_separate_demucs`: Executes separation using Meta HTDemucs.
  - `profile_arrangement_energy`: Profiles the dynamic energy and role activity per bar window.

---

## Módulo: `engine/audio/deconstruction/reconstructor.py`

**Descripción del Módulo:**
```text
Reference Reconstructor: Injects transcribed reference parts and separated stems
directly into an Ableton Live session or arrangement.
```

### Clases

#### `ReferenceReconstructor`
Orchestrates the reconstruction of transcribed stems and MIDI notes inside Ableton Live.

- **Métodos:**
  - `__init__`: Sin documentación
  - `format_notes_for_live`: Converts TranscribedNoteEvent list into the format accepted by Ableton Live MCP tools.
  - `build_reconstruction_plan`: Creates a structured plan for recreating the reference inside Ableton Live.
  - `reconstruct`: Executes reconstruction commands against Ableton Live if a client is connected,

---

## Módulo: `engine/audio/deconstruction/transcriber.py`

**Descripción del Módulo:**
```text
Reference Audio Transcriber: Audio-to-MIDI Transcription Engine.
Performs:
1. Tempo estimation (Autocorrelation on onset energy envelope).
2. Key / Tonality detection (Krumhansl-Schmuckler chroma correlation).
3. Drum multi-band transcription (Kick 36, Snare 38, Closed Hat 42).
4. Bass pitch tracking (Autocorrelation F0 tracking in 35-260 Hz range).
5. Chord / Harmony chromagram transcription.
```

### Clases

#### `ReferenceTranscriber`
Extracts musical structures, stems, and MIDI notes from audio references.

- **Métodos:**
  - `__init__`: Sin documentación
  - `detect_tempo`: Estimates BPM using autocorrelation of onset energy envelope.
  - `detect_key`: Estimates musical key using 12-semitone chromagram correlation
  - `transcribe_drums`: Transcribes rhythmic drum events into Kick (36), Snare (38), and Hat (42) notes.
  - `transcribe_bass`: Tracks bass fundamental frequency (35Hz - 260Hz) frame by frame
  - `transcribe_chords`: Estimates musical chords from the harmonic audio stem.
  - `transcribe`: Executes full reference deconstruction:

---

## Módulo: `engine/audio/deconstruction/models.py`

**Descripción del Módulo:**
```text
Data models for audio reference deconstruction, stem separation, and MIDI transcription.
```

### Clases

#### `StemCategory`

#### `DeconstructedStem`

#### `TranscribedNoteEvent`

#### `AudioTranscriptionResult`

---

## Módulo: `engine/audio/deconstruction/separator.py`

**Descripción del Módulo:**
```text
Audio Stem Separator using Pure DSP Multi-Band Crossover & Mid-Side Decomposition.
Produces 4 stems: drums, bass, vocals, other.
Zero heavy dependencies, fully deterministic, fast and robust.
```

### Clases

#### `AudioStemSeparator`
Separates a mixed audio track into Drums, Bass, Vocals, and Other stems.

- **Métodos:**
  - `__init__`: Sin documentación
  - `_compute_rms_db`: Calculates RMS level in decibels.
  - `_compute_peak_db`: Calculates peak level in decibels.
  - `_stft_mask`: Applies a smooth frequency bandpass and mid-side weighting mask via STFT.
  - `_extract_transients`: Extracts sharp transient rhythmic energy (kick onsets, snare cracks, hats)
  - `separate`: Separates audio into drums, bass, vocals, and other stems.

---

## Módulo: `engine/midi/program_change.py`

**Descripción del Módulo:**
```text
engine/midi/program_change.py - MIDI Program Change & Bank Dispatcher.

Handles MIDI Program Change (0-127) and Bank Select (CC0 MSB / CC32 LSB) configuration for:
- Arturia Analog Lab V (Playlists & Stage Mode)
- Spectrasonics Omnisphere (Live Mode slots)
- Native Instruments Massive (Program List)
- Roland Cloud ZENOLOGY (Roland Tone Banks)
```

### Clases

#### `MIDIProgramChangeDispatcher`
Manages Program Change and Bank parameters for VST synthesizers.

- **Métodos:**
  - `resolve_program_change`: Translates a preset request into standard MIDI Program Change and Bank parameters.
  - `send_program_change`: Dispatches MIDI Program Change and Bank parameters to Ableton Live.

---

## Módulo: `generate_comprehensive_docs.py`

### Funciones Globales

- `parse_file`: Sin documentación
- `build_docs`: Sin documentación

---

## Módulo: `generate_mermaid.py`

### Funciones Globales

- `extract_imports`: Sin documentación
- `generate_mermaid`: Sin documentación

---

## Módulo: `telemetry.py`

**Descripción del Módulo:**
```text
Privacy-focused, anonymous telemetry for Ableton MCP
Tracks tool usage, DAU/MAU, and performance metrics

Two-tier consent system:
- Without consent: Only anonymous session/platform info, tool names, success/failure, duration
- With consent: Also collects prompts, MIDI data, instrument/sound URIs, and other metadata
```

### Clases

#### `EventType`
Types of telemetry events


#### `TelemetryEvent`
Structure for telemetry events


#### `TelemetryCollector`
Main telemetry collection class

- **Métodos:**
  - `__init__`: Initialize telemetry collector
  - `_is_disabled`: Check if telemetry is disabled via environment variables
  - `_get_data_directory`: Get directory for storing telemetry data
  - `_get_or_create_uuid`: Get or create anonymous customer UUID
  - `_check_user_consent`: Check if user has consented to detailed data collection
  - `record_event`: Record a telemetry event (non-blocking)
  - `_worker_loop`: Background worker that sends telemetry
  - `_send_event`: Send event to Supabase

### Funciones Globales

- `get_package_version`: Get version from pyproject.toml
- `set_telemetry_consent`: Set the user's telemetry consent status
- `get_telemetry_consent`: Get the current telemetry consent status
- `get_telemetry`: Get the global telemetry collector instance
- `record_tool_usage`: Convenience function to record tool usage
- `record_startup`: Record server startup event
- `is_telemetry_enabled`: Check if telemetry is enabled

---

## Módulo: `server.py`

### Clases

#### `AbletonConnection`
- **Métodos:**
  - `connect`: Connect to the Ableton Remote Script socket server
  - `disconnect`: Disconnect from the Ableton Remote Script
  - `is_connected`: Check if connection socket is active
  - `receive_full_response`: Receive the complete response, potentially in multiple chunks
  - `_send_raw`: Low-level raw socket dispatch without governance interception for internal queries.
  - `_enforce_immutable_governance`: ==============================================================================
  - `send_command`: Send a command to Ableton and return the response

### Funciones Globales

- `get_ableton_connection`: Get or create a persistent Ableton connection
- `get_session_info`: Get detailed information about the current Ableton session
- `get_track_info`: Get detailed information about a specific track in Ableton.
- `create_midi_track`: Create a new MIDI track in the Ableton session.
- `set_track_name`: Set the name of a track.
- `create_clip`: Create a new MIDI clip in the specified track and clip slot.
- `create_audio_clip`: Create a new audio clip in an audio track's clip slot by importing a file.
- `add_notes_to_clip`: Add MIDI notes to a clip.
- `set_clip_name`: Set the name of a clip.
- `set_tempo`: Set the tempo of the Ableton session.
- `load_instrument_or_effect`: Load an instrument or effect onto a track using its URI.
- `fire_clip`: Start playing a clip.
- `stop_clip`: Stop playing a clip.
- `start_playback`: Start playing the Ableton session.
- `stop_playback`: Stop playing the Ableton session.
- `get_browser_tree`: Get a hierarchical tree of browser categories from Ableton.
- `get_browser_items_at_path`: Get browser items at a specific path in Ableton's browser.
- `load_drum_kit`: Load a drum rack and then load a specific drum kit into it.
- `switch_to_arrangement_view`: Switch Ableton's main window to the Arrangement view.
- `set_arrangement_time`: Move the arrangement playhead to a specific position.
- `get_arrangement_clips`: List all clips placed in the Arrangement timeline for a track.
- `duplicate_to_arrangement`: Copy a Session-view clip into the Arrangement timeline.
- `get_device_parameters`: Get all controllable parameters (knobs, sliders, toggles) for a device on a track.
- `set_device_parameter`: Set the value of a specific parameter (knob/slider) on a device.
- `get_clip_notes`: Get all MIDI notes currently stored in a clip.
- `delete_clip`: Delete/clear a clip from a specific track clip slot.
- `set_track_mute`: Mute or unmute a track.
- `set_track_solo`: Set solo state for a track.
- `set_track_volume`: Set track mixer volume fader (0.0 to 1.0, where ~0.85 represents 0 dB).
- `set_track_panning`: Set track mixer stereo panning (-1.0 for hard left, 0.0 for center, +1.0 for hard right).
- `set_track_send`: Set track send level to return tracks (0.0 to 1.0).
- `set_loop_region`: Set arrangement song loop region bracket and state.
- `set_clip_pitch`: Set pitch transpose (semitones) and fine detune (cents) on an audio clip.
- `set_clip_warp_mode`: Set warp state and mode (Beats, Tones, Texture, Re-Pitch, Complex, Complex Pro) on an audio clip.
- `set_clip_gain`: Set sample gain on an audio clip.
- `get_audio_clip_info`: Get full properties and metadata of an audio clip (pitch, warp mode, gain, length).
- `create_cue_point`: Create or update an arrangement section locator (Cue Point) at a given beat time with a name.
- `get_cue_points`: Get all cue points / section locators in the arrangement timeline.
- `delete_cue_point`: Delete an arrangement section locator by time or index.
- `jump_to_cue_point`: Jump the arrangement playhead to a named section locator or beat time.
- `add_expressive_notes_to_clip`: Add expressive MIDI notes to a clip with probability (generative triggers), velocity deviation (humanization), and release velocity.
- `clear_clip_envelopes`: Clear all modulation and automation envelopes from a clip.
- `get_drum_rack_pads`: List all active drum pads with loaded chains, pitch numbers, and devices inside a Drum Rack.
- `get_drum_pad_devices`: Get detailed device list and all parameters for an individual Drum Rack pad (e.g. note 36 Kick, note 38 Snare).
- `set_drum_pad_parameter`: Set a parameter on a device loaded inside a specific drum pad (e.g. adjust Simpler filter/envelope or pad effect).
- `set_drum_pad_mute_solo`: Mute or solo an individual drum pad inside a Drum Rack.
- `run_automation_sweep`: Execute a smooth real-time parameter automation sweep (e.g. filter opening build-up, reverb bloom, bitcrush descent).
- `analyze_audio_file`: Digital Ear Audio & Mix Analyzer: Analyzes any WAV audio file/render for Peak dBFS, RMS, Crest Factor (dynamics), Stereo Phase Correlation, and 5-Band Spectral Energy Distribution with mixing recommendations.
- `search_sample_library`: Search and index the local Sample & Preset Library (e.g. 'D:\Documentos\Librerias FL Studio') for WAV samples, vocal chops, breakbeats, drum hits, Serum/Vital presets (.fxp/.vital), and Kontakt instruments (.nki).
- `get_sample_library_summary`: Get a complete overview of all installed sample packs, total WAV audio files, synth presets, and Kontakt instruments in the library.
- `_server_parse_res`: Sin documentación
- `_server_gen_curve`: Sin documentación
- `_server_resolve_track_and_device`: Sin documentación
- `get_device_parameter`: Get detailed metadata, range (min/max), unit, and automation state of a specific device parameter or track mixer control in Ableton Live.
- `create_automation`: Create a real, continuous parameter automation curve envelope in Ableton Live.
- `re_enable_automation`: Re-enable all overridden automation lanes across the entire Live set.
- `record_arrangement_automation`: Record tangible, vector-editable arrangement automation directly onto the track lane in Live.
- `record_multi_automation_pass`: Record multiple automation curves across multiple tracks/devices concurrently in a single playback pass.
- `add_automation_points`: Inject an explicit list of timestamped automation breakpoint values into an Ableton Live envelope.
- `get_automation`: Read back real existing automation envelope breakpoints for a parameter in Ableton Live.
- `clear_automation`: Clear all automation or clear within a specified range [start, end] for a parameter in Ableton Live.
- `_async_bootstrap_engine`: Sin documentación
- `session_inspect`: Inspect the project's semantic session state.
- `session_refresh`: Refresh the Session Shadow Graph by querying current live Ableton state.
- `session_diff`: Calculate and report differences between the Engine's SHADOW_STATE and Ableton's CURRENT_REAL_STATE.
- `session_resolve`: Semantically locate a track by role (e.g. SUB_BASS, KICK, LEAD), name, ID, or tag.
- `transaction_begin`: Start a new atomic transaction. Creates a baseline snapshot and records base_version for optimistic concurrency.
- `transaction_stage_track`: Stage track creation within an open transaction with automatic inverse delete operation registered for WAL rollback.
- `transaction_stage_volume`: Stage volume change on a track within an open transaction.
- `transaction_stage_mute`: Stage mute change on a track within an open transaction.
- `transaction_stage_tempo`: Stage project tempo change within an open transaction.
- `transaction_preview`: Dry-run preview calculating impacts and warnings without modifying Ableton Live.
- `transaction_validate`: Validate an open transaction against graph invariants, locks, and safety limits.
- `transaction_commit`: Atomically commit an open transaction to Ableton Live.
- `transaction_rollback`: Manually rollback a transaction, reverting all executed changes in reverse order.
- `transaction_status`: Get detailed status, operations, and metadata for a specific transaction.
- `transaction_history`: Get list of recent transactions and their outcomes.
- `snapshot_create`: Create and persist a logical state snapshot of the session.
- `snapshot_restore`: Restore the session graph state from a previously saved snapshot.
- `snapshot_list`: List all available snapshots in persistent storage.
- `graph_get`: Get the complete Session Shadow Graph including tracks, clips, devices, and sections.
- `graph_find`: Find all tracks matching a search term across names, roles, and tags.
- `graph_set_role`: Assign a semantic role (e.g. KICK, SUB_BASS, LEAD, PAD, FX) to a track.
- `graph_set_tags`: Assign comma-separated semantic tags (e.g. 'low_end,mono,analog') to a track.
- `graph_lock`: Lock a track or object against automated modifications or deletions.
- `graph_unlock`: Unlock a previously locked track or object.
- `_server_resolve_track`: Resolve track by stable ID, numeric Ableton index, role, or fuzzy name
- `_server_get_clip_notes_as_events`: Fetch existing clip notes via adapter and convert into NoteEvent models
- `music_generate_part`: Generate an entire musical part (Drums, Bass, Chords, Melody/Lead) based on high-level intent.
- `music_generate_harmony`: Generate a harmonic chord progression with smooth voice-leading and voicing style.
- `music_generate_bass`: Generate a bassline (rolling 16ths, offbeat pumping, sustained root, syncopated) with sub-bass monophony.
- `music_generate_drums`: Generate a full drum groove (Kick, Snare/Clap, Hihats, Percussion) with phrase-boundary fills.
- `music_generate_melody`: Generate a melodic lead or hook with musical contour (arch, ascending, descending, wave).
- `music_create_motif`: Extract and catalog a relative melodic motif from clip notes or provided JSON note events.
- `music_transform_motif`: Apply a musical transformation (transpose, invert, retrograde, augmentation, diminution, displacement, fragment)
- `music_apply_groove`: Apply a groove template (swing_16th_light, swing_16th_heavy, swing_8th, laid_back, pushing) to clip notes.
- `music_humanize`: Apply correlated stochastic timing and velocity jitter to clip notes with role-based variance.
- `music_compare_parts`: Calculate statistical fingerprint similarity (pitch class distribution, rhythm histogram, density) between two clips.
- `music_validate`: Validate clip notes against musical constraints (monophony for sub-bass, register bounds, scale degrees).
- `music_compile`: Pure algorithmic compilation of high-level MusicalIntent into compiled Ableton note events and quality metrics.
- `instrument_inspect`: Inspect devices and instrument configuration on a track.
- `instrument_search_samples`: Search for available audio samples across user sample libraries for a specific role and style without modifying Ableton.
- `instrument_resolve`: Resolve an instrument descriptor detailing how to build or load a sound profile.
- `instrument_preview`: Preview sound assignments and execution plan without modifying Ableton Live.
- `instrument_load`: Load a resolved instrument or specific device onto a track.
- `preset_list_available`: List or search curated native Live 12 presets (.adv/.adg) by role, genre, or keyword.
- `instrument_load_preset`: Load a verified curated native Ableton Live 12 preset directly onto a track.
- `drum_rack_inspect`: Inspect a Drum Rack in Ableton Live to detect empty pads, active pads and missing roles.
- `drum_rack_populate`: Populate empty pads of a Drum Rack with resolved samples according to kit style (strictly idempotent).
- `drum_rack_rebuild`: Rebuild and re-populate the Drum Rack on a track with a fresh kit profile.
- `drum_rack_verify`: Verify that populated pads have actual devices, chains and samples loaded in Live.
- `prepare_track_sound`: High-level semantic tool: inspect -> resolve -> plan -> populate -> verify track instrumentation.
- `arrangement_generate`: Generates a complete song arrangement structure (sections, energy curves, role matrix, transitions, variations).
- `arrangement_preview`: Generates a full arrangement dry-run preview report without altering Ableton Live.
- `arrangement_validate`: Validates song arrangement structure, energy flow, and phrase boundaries.
- `arrangement_lint`: Audits arrangement with the Repetition & Flow Linter (detects copy-pasting, flat energy, missing drops).
- `arrangement_apply`: Applies and compiles the arrangement to Ableton Live via atomic ACID transaction.
- `arrangement_regenerate_section`: Selectively regenerates a specific section while preserving locked sections.
- `arrangement_regenerate_role`: Selectively regenerates a specific musical role across unlocked sections.
- `arrangement_compare_sections`: Compares two sections for energy, duration, variation, and repetition index.
- `arrangement_lock`: Locks a section or role so subsequent regenerations will not modify it.
- `arrangement_unlock`: Unlocks a section or role.
- `arrangement_get_energy_curve`: Calculates and returns the multi-dimensional energy curve and climax locations.
- `arrangement_get_structure`: Returns the high-level structural outline of sections, phrase boundaries, and timings.
- `arrangement_apply_transition`: Apply an automated musical transition (filter sweep, reverb washout, volume swell, or sidechain pump) to a track.
- `arrangement_add_energy_curve`: Apply continuous macro energy automation across arrangement sections.
- `build_song`: High-level master command: plans, lints, and builds a complete song in Ableton Live.
- `build_sound_role`: Orchestrates end-to-end sound design for a musical role:
- `build_drum_rack`: Builds and populates a complete, production-grade Drum Rack with validated samples,
- `sound_create`: Creates an instrument and sound chain on a track based on high-level musical intent parameters.
- `sound_update`: Updates macro parameters or sound character on an existing track.
- `sound_inspect`: Inspects sound chain, devices, active macro values, and frequency profile for a track.
- `sound_verify`: Strictly verifies physical sound devices on a track (detects empty chains, missing plugins, unpopulated racks).
- `sound_rebuild`: Rebuilds an instrument chain from scratch with alternative devices and presets.
- `sound_compare`: Compares two tracks for low-end frequency clashes, stereo panning balance, and dynamic headroom.
- `sound_apply_profile`: Applies a curated sound profile (e.g. dark_club, acid_resonant, atmospheric, punchy) to a track.
- `sound_set_macro`: Sets a semantic macro control (brightness, warmth, weight, punch, space, width, movement, pressure)
- `sound_get_macro`: Gets the current value of a semantic macro for a track.
- `sound_preview`: Previews sound chain configuration and preset choices without mutating Ableton Live (dry-run).
- `sound_lint`: Audits the current session for sound design defects:
- `drum_rack_create`: Creates a new Drum Rack on a track populated with a genre-specific kit layout.
- `drum_rack_add_pad`: Adds or updates a single pad in an existing Drum Rack.
- `drum_rack_load_sample`: Loads a specific sample file or browser URI onto an individual drum pad.
- `drum_rack_set_pad`: Modifies volume, pitch, filter, decay, pan, mute, or solo of a drum pad.
- `audio_listen_live`: Real-time acoustic listener bridge: captures live audio stream and returns instant ITU-R BS.1770-5 LUFS, True Peak, phase correlation, and spectral balance without offline bounce.
- `audio_capture`: Captures or extracts audio for DSP analysis.
- `audio_analyze`: Extracts comprehensive DSP features (LUFS BS.1770-4, True Peak, STFT 12 bands, Mid/Side stereo, Transients).
- `audio_analyze_track`: Analyzes the acoustic properties of an individual track in Ableton Live.
- `audio_analyze_section`: Performs section-aware acoustic analysis and generates prioritized diagnostics.
- `audio_analyze_stem`: Analyzes an isolated stem file for a specific musical role.
- `mix_analyze`: High-level mix analysis with automatic context and genre profile resolution.
- `mix_lint`: Audits the current mix against professional production standards (clipping, sub stereo, masking, dynamics).
- `mix_diagnose`: Generates evidence-based causal diagnoses for detected mix problems.
- `mix_compare`: A/B compares acoustic features of two audio files or mix renders.
- `mix_get_report`: Generates a full human-readable and machine-readable mix report.
- `mix_get_conflicts`: Returns the Frequency Collision Graph detailing clashing roles and severities.
- `mix_get_frequency_map`: Returns the Spectral Occupancy Map across standard frequency bands.
- `mix_check_mono`: Verifies mono compatibility, phase correlation, and sub-bass stereo width (<120Hz).
- `mix_check_headroom`: Evaluates True Peak (4x oversampling), peak margin, and clipping risk.
- `mix_reference_compare`: Compares the current production mix against a commercial reference audio track.
- `mix_suggest_correction`: Suggests a conservative correction plan respecting musical hierarchy (SAFE mode).
- `mix_apply_correction`: Applies a correction plan in SAFE, ASSISTED, or AUTONOMOUS mode with parameter guardrails.
- `mix_preview_correction`: Previews the expected acoustic delta and parameter changes of a proposed correction.
- `mix_rollback_correction`: Reverts an applied correction plan if regressions occurred.
- `mix_evaluate_correction`: Multiobjective evaluation of a correction: ensures primary issue improved without secondary regression.
- `production_audit`: Executes a complete end-to-end audit across 12 production categories:
- `validate_production_completeness`: Formal Quality Gate: audits the Ableton session to ensure no production is left
- `master_analyze`: Analyzes audio on the Master track or an audio file on disk.
- `master_readiness`: Evaluates whether the current mix is ready for mastering.
- `master_create_chain`: Creates or verifies the 5-device native mastering chain on the Master track:
- `master_apply`: Generates and optionally applies a conservative mastering plan.
- `master_preview`: Pre-configures the mastering chain temporarily for audition without committing.
- `master_evaluate`: Evaluates post-master vs pre-master quality score across 6 perceptual dimensions:
- `master_rollback`: Rolls back the master chain device parameters to a previous snapshot state.
- `master_compare_reference`: Compares the current track against a commercial reference track.
- `master_translation_test`: Simulates playback across 6 consumer environments:
- `master_quality_control`: Runs comprehensive technical Quality Control:
- `master_export`: Exports the finalized master with SHA-256 integrity hash, versioning (v001, v002),
- `master_get_report`: Generates human-readable Markdown and structured JSON executive mastering report.
- `master_get_history`: Retrieves full versioned mastering history and commit logs.
- `master_project`: Executes the entire end-to-end intelligent mastering pipeline:
- `production_status`: Returns the operational status of the Production Intelligence Engine (PIE):
- `production_plan`: Formulates a causal ProductionPlan for a musical intent (e.g. 'Quiero que el master tenga más volumen').
- `production_validate`: Validates a proposed plan or raw action candidate against the ProductionPolicyEngine.
- `production_execute`: Executes a previously formulated ProductionPlan through atomic transactions.
- `production_explain`: Reconstructs the full causal explanation for a production decision.
- `production_history`: Retrieves recent production decisions, actions, and verification outcomes from the causal graph.
- `production_graph`: Exports the Production Causal DAG in deterministic JSON or Mermaid format.
- `production_rollback`: Executes an atomic rollback of a previously committed production decision.
- `production_memory_search`: Searches DecisionMemory for historically verified decisions matching the scenario.
- `forensics_analyze`: Executes deep time-frequency forensic audit on an audio file or track buffer.
- `forensics_report`: Retrieves a cryptographically sealed forensic audit report by ID.
- `forensics_events`: Queries and filters acoustic forensic events within an existing report.
- `forensics_explain`: Explains the causal hypothesis, acoustic evidence, and competing explanations
- `production_status`: Devuelve el estado actual de la infraestructura de Production Governance.
- `production_plan`: Transforma una intención musical en un plan candidato determinista y seguro.
- `production_validate`: Realiza la validación completa de un plan antes de su ejecución.
- `production_execute`: Ejecuta un plan previamente validado dentro de una transacción atómica segura.
- `production_explain`: Reconstruye la causalidad completa de una decisión de producción.
- `production_history`: Consulta el historial determinista de decisiones de producción.
- `production_graph`: Consulta la estructura o estadísticas del Production Graph en modo solo lectura.
- `production_rollback`: Revierte de forma atómica y no destructiva una decisión o transacción de producción.
- `production_memory_search`: Busca precedentes históricos en la memoria de producción para evidencia contextual.
- `plugin_inspect_parameters`: Inspecciona y clasifica semánticamente los parámetros de un dispositivo VST3 o nativo.
- `plugin_set_semantic_parameter`: Ajusta un parámetro de un plugin VST3 o dispositivo nativo usando un rol semántico ('cutoff', 'drive', 'fatness', etc.).
- `browser_crawl_library`: Rastrea e indexa de forma asíncrona una categoría de la librería o plugins de Ableton Live.
- `browser_search_library`: Busca presets, sintetizadores, efectos y librerías en el catálogo indexado de Ableton Live.
- `arrangement_inject_automation_envelope`: Inyecta una envolvente de automatización en la pista y clips del Arrangement de Ableton Live (LOM).
- `vocal_get_profile`: Devuelve la especificación de cadena DSP y parámetros de compresión, ecualización y ducking
- `vocal_calculate_ducking`: Calcula la curva de atenuación (ducking) instrumental ante la presencia de frases vocales.
- `stem_create_export_plan`: Agrupa automáticamente las pistas del proyecto en grupos de stems estándar
- `stem_generate_manifest`: Genera y guarda el manifiesto técnico de exportación de stems en exports/stems/manifest.json.
- `vital_create_preset`: Sintetiza un preset nativo de Vital (.vital) con ruteo de osciladores,
- `vital_list_user_presets`: Lista presets de Vital (.vital) disponibles en la librería del usuario y en el motor.
- `reference_deconstruct`: Deconstruye una pista de referencia de audio:
- `reference_reconstruct_in_live`: Deconstruye un archivo de audio y genera el plan de reconstrucción
- `humanize_track_clip`: Applies genre-specific micro-timing, organic swing, velocity contour,
- `evolve_arrangement_phrase`: Evolves a musical phrase using formal A -> A' -> B -> A'' arrangement variation logic.
- `apply_transition_automation_weaver`: Weaves continuous parameter automation breakpoint curves into Ableton Live
- `apply_kick_sidechain_to_bass`: Applies closed-loop volume sidechain ducking to an 808 or sub-bass track
- `generate_808_slides`: Generates authentic drill/trap 808 slides, octave glides, and pitch-bend
- `inject_ear_candy`: Injects unexpected transitional ear candy: vinyl tape-stops, glitch stutter rolls,
- `configure_depth_staging`: Applies tempo-synced 3D acoustic depth staging (Foreground, Midground, Background)
- `clean_track_resonances`: Scans audio with high-resolution FFT spectral decomposition to detect narrow
- `reharmonize_chord_progression`: Applies jazz and neo-soul harmonic reharmonization (Secondary Dominants,
- `orchestrate_beat_switch`: Coordinates a dramatic multi-movement mid-song beat switch with tempo automation,
- `copilot_get_status`: Returns current executive copilot production phase, overall progress percentage,
- `copilot_review_decisions`: Returns the interactive checklist of pending production decisions, including
- `copilot_execute_decision`: Resolves an interactive copilot decision:
- `copilot_preflight_check`: Performs a strict pre-flight audit validating that zero unreviewed technical
- `macro_produce_rhythm`: All-in-one macro recipe producing a complete rhythm section: drums + 808 + pocket micro-timing + turnaround slides + closed-loop sidechain + timeline duplication.
- `macro_produce_harmony`: All-in-one macro recipe producing harmony and lead layers: chords + secondary dominants + physical strumming + 3D depth staging.
- `macro_finalize_song`: All-in-one macro recipe finalizing the song:
- `export_and_audit_stems`: All-in-one multitrack stem export coordinator & audio forensics phase auditor.
- `generate_organic_foley_bed`: Generates tempo-synced organic foley and environmental texture beds (vinyl, rain, tape hiss, room tone)
- `chop_drum_loop_transients`: Slices drum breaks and acoustic loops by transients and resequences them into classic
- `generate_vocal_hook_chops`: Generates scale-quantized, in-key melodic vocal chops and hook motifs with alternating
- `macro_orchestrate_full_song`: Grand orchestrator producing an entire 96-bar (~3 minute) commercial arrangement in Ableton Live:
- `generate_transition_risers`: Generates continuous transition risers leading into a drop or section transition:
- `evolve_drum_patterns`: Evolves drum sequences to eradicate loop monotony:
- `session_auto_curate`: 1-click session rescue and auto-curation:
- `generate_counter_melody_and_arp`: Composes soaring guide-tone counter-melodies (focusing on 3rds and 7ths in upper registers C5-C7)
- `auto_gain_stage_session`: Calculates and applies hierarchical acoustic gain staging across all session track faders
- `generate_impact_and_downlifters`: Generates dynamic transitional impact releases and post-drop sweeps:
- `export_and_audit_stems`: Multi-stem export coordinator and deep forensic phase auditor:
- `apply_groove_pool_template`: Applies iconic hardware groove templates and multitrack pocket locking:
- `get_available_vst_and_presets`: Scans the Ableton Live browser catalog and system VST3 folders for installed synths and presets:
- `setup_multitrack_drums`: Sets up multi-track drum architecture in Ableton Live:
- `configure_physical_sidechain`: Configures physical sidechain compression in Ableton Live:
- `apply_physical_arrangement_automations`: Applies physical arrangement automation envelopes and transition cuts in Ableton Live:
- `apply_track_channel_strip`: Applies surgical channel strip EQ processing to an individual track:
- `apply_group_bus_processing`: Applies group bus processing to glue stems together:
- `setup_full_mastering_chain`: Deploys the complete 5-device native mastering chain in Ableton Live:
- `apply_adaptive_deesser`: Deploys a surgical adaptive De-Esser on a track in Ableton Live:
- `export_commercial_release_package`: Exports the complete market-ready commercial release package:
- `dna_create_creative_brief`: Phase 1: Generates the master Creative Direction and Song DNA brief.
- `dna_scaffold_live_project`: Phase 1: Physically instantiates the 8-track frequency-reserved scaffolding,
- `dna_get_reference_profiles`: Phase 1: Returns available acoustic and stylistic reference profiles (Tyler/JID, Atlanta Trap, Dilla Neo-Soul, West Coast).
- `music_compose_full_harmony`: Phase 2: Composes and injects the progressive 96-bar harmonic chord progression
- `music_compose_808_bassline`: Phase 2: Composes and injects the interlocking 808 sub-bassline across 96 bars,
- `music_compose_topline_melody`: Phase 2: Composes and injects the conversational Call-and-Response top-line melody
- `music_compose_vocal_hook`: Phase 2: Generates and injects infectious, syncopated vocal chop hook motifs
- `instrument_scan_host_vsts`: Phase 3: Scans the user's host system (VST3 and VST directories), indexes installed plugins
- `drum_rack_load_authentic_library`: Phase 3: Scans the user's local sample libraries (D:\Documentos\Librerias FL Studio, Cymatics, ASAN Essentials)
- `sound_load_role_instrument`: Phase 3: Loads a premier VST3 plugin (Analog Lab V, Stage-73 V2, Vital, Serum 2, Kontakt 8)
- `apply_sound_blueprint`: Applies a concrete parameter blueprint (knobs, macros, timbre shaping) to an instrument
- `apply_vst_effect_chain`: Loads authentic physical VST effect chains onto the track:
- `sound_apply_timbre_morph`: Phase 3: Generates and formats section-by-section dynamic timbre macro automations
- `groove_apply_hardware_pocket`: Phase 4: Applies classic hardware micro-timing (Akai MPC 60, SP-1200, Dilla)
- `harmony_apply_chord_strum`: Phase 4: Staggers polyphonic chord notes (8-18 ms finger-roll) and applies physiological
- `expression_apply_mpe_vibrato`: Phase 4: Calculates and attaches expressive pitch bend scoops on attack and sinusoidal
- `drums_inject_ghost_notes`: Phase 4: Injects turnaround ghost snares (velocity 25-45) and applies 16th-note velocity wave
- `transitions_inject_section_impacts`: Phase 5: Injects sub-booms (40 Hz) and arrival crashes on the Foley/FX track
- `transitions_build_tension_risers`: Phase 5: Generates exponential filter sweeps, pitch risers, and accelerating snare rolls
- `transitions_apply_pre_drop_vacuum`: Phase 5: Generates acoustic vacuum silence windows (bars 31.4 and 71.4) and low-end cut
- `transitions_inject_ear_candy_fx`: Phase 5: Generates analog vinyl tape stops, reverse vocal swells, and freeze washes
- `mix_apply_frequency_slotting`: Phase 6: Applies multitrack complementary frequency slotting and surgical High-Pass Filtering
- `mix_audit_phase_and_mono_compatibility`: Phase 6: Audits Pearson phase correlation coefficients between interacting stems (Kick vs 808)
- `mix_apply_vocal_lead_fader_riding`: Phase 6: Computes section-aware dynamic fader riding automation curves across 96 bars
- `mix_apply_multitrack_sidechain_ducking`: Phase 6: Coordinates physical sidechain compression routing and envelope ducking
- `preset_search`: Search presets across 14,105 Arturia patches (Analog Lab V, Pigments, Jup-8, etc.),
- `preset_select_for_track`: Selects and applies a preset to a track:
- `genre_offer_production_options`: [EXPERIMENTAL FEATURE - DORMANT BY DEFAULT]
- `genre_generate_drum_pattern`: [EXPERIMENTAL FEATURE - DORMANT BY DEFAULT]
- `suggest_clip_automations`: Inspects a track and returns contextual, tangible vector automation recipes suited for the clip
- `apply_clip_automation`: Bakes a tangible, vector automation envelope into an Ableton Live clip
- `drum_rack_audit_clip_octaves`: Audits the MIDI clip on a Drum Rack track against physical pad quadrants.
- `drum_rack_transpose_clip_octaves`: Transposes all notes in a drum clip by semitone_shift (default -24 semitones / 2 octaves)
- `orchestrate_role_track`: Atomic Role Orchestration (Capa 3: Operaciones Atómicas de Rol):
- `copilot_auto_produce`: Autonomous End-to-End Copilot Producer:
- `copilot_guided_session`: Conversational State Machine Wizard for Interactive Music Production (Strict 7-Phase Flow).
- `save_favorite_pattern`: Save an approved or high-rated MIDI pattern into user persistent memory.
- `get_favorite_patterns`: Retrieve top-rated user patterns from persistent memory for inspiration.
- `save_user_preference`: Persist a user taste/preference (scales, mixing, default headroom, VSTs).
- `get_user_preferences`: Retrieve saved preferences from user persistent memory.
- `search_samples_in_library`: Search the Apache Parquet sample manifest by multi-attribute tags (type, mood, BPM, key).
- `reindex_sample_library`: Reindex sample library into Apache Parquet incrementally with tokenized tag extraction.
- `analyze_mix_static`: Run a pre-flight static mix audit checking for fader clipping, silent active tracks, and FX overload.
- `get_producer_info`: Get signature production blueprint, drum selection, swing, and hardware emulation for 13 legendary producers.
- `get_serum_patch`: Get step-by-step synthesis patch recipe for Serum 2 (808s, leads, keys, pads, plucks).
- `get_fabfilter_preset`: Get surgical presets for FabFilter Pro-Q 4, Pro-C 3, or Saturn 2 by instrument element.
- `get_vocal_chain_guide`: Get complete 10-slot vocal chain order with Auto-Tune Pro, RX 11, EQ, and dynamics settings.
- `audio_semantic_sample_match`: Matches natural language intent ('punchy kick', 'dark boomy 808', 'crisp snap') to audio samples using physical 6D acoustic signatures.
- `audio_deconstruct_reference`: Separates reference track into drums, bass, vocals, other stems (via Meta Demucs or DSP fallback) and extracts arrangement energy profile.
- `audio_transcribe_to_midi`: Transcribes monophonic audio recording into expressive MIDI notes with pitch bends and velocity dynamics.
- `mix_audit_psychoacoustic_masking`: Audits full-spectrum psychoacoustic masking (Zwicker 24 Bark critical bands) and calculates surgical dynamic EQ carving parameters.
- `main`: Run the FastMCP server with all legacy, Phase 1, Phase 2, Phase 3, and Phase 4 sound tools registered

---

## Módulo: `telemetry_decorator.py`

**Descripción del Módulo:**
```text
Telemetry decorator for Ableton MCP tools

Two types of decorators:
- telemetry_tool: Basic tracking (tool name, success, duration)
- rich_telemetry_tool: Extended tracking with metadata (MIDI notes, instrument URIs, etc.)
  - Only collects detailed metadata with user consent
```

### Funciones Globales

- `_debug_print`: Print debug message to stderr so it shows in MCP logs
- `_extract_tool_params`: Extract relevant params from kwargs for logging.
- `telemetry_tool`: Decorator to add basic telemetry tracking to MCP tools.
- `rich_telemetry_tool`: Decorator that records tool execution with rich metadata.

---

## Módulo: `generate_docs.py`

### Funciones Globales

- `index_project`: Sin documentación

---

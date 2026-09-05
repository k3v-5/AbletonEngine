# Ableton Live 12 Suite Native Browser Catalog & URI Reference

> **Engine Module**: `engine.instruments.library.preset_catalog`  
> **Target Version**: Ableton Live 12 Suite  
> **Protocol**: Native Ableton Remote Script URI Format (`query:<Category>#<Identifier>`)

---

## 1. Architecture & Live 12 API Constraints

### The Drum Rack Loading Constraint & Resolution
In Ableton Live 12 Suite's Python API, the `drum_rack.view.selected_drum_pad` property is **read-only** (i.e., it has no Python setter). Attempting to load individual `.wav` samples directly into individual pad slots via the GUI view raises:
```python
AttributeError: property of 'View' object has no setter
```
**Engine Solution**:
To populate all 16 pads natively and immediately with authentic, velocity-mapped samples and devices, the Engine loads complete `.adg` Drum Kits (`query:Drums#FileId_5422`) directly onto the track via `load_instrument_or_effect`.
- This creates the Drum Rack container.
- Instantiates Simpler / Sampler devices on each pad.
- Sets choke groups, filter values, and velocity curves automatically.
- Allows immediate manipulation via `get_drum_rack_pads`, `set_drum_pad_parameter`, and GM drum mapping (Kick = 36, Snare = 38, Clap = 39, Closed Hat = 40, Open Hat = 41).

---

## 2. Verified Curated Preset Catalog

### 🎹 Piano & Keys
| Preset Name | Role | Category | Character / Timbre | Verified Live 12 URI | Best For Genres |
|---|---|---|---|---|---|
| **Grand Piano** | `PIANO` | Piano & Keys | Concert Grand, natural resonance | `query:Sounds#Piano%20&%20Keys:FileId_4870` | Hip Hop, Neo-Soul, Pop, Classical |
| **Childhood Home Piano** | `PIANO` | Piano & Keys | Intimate Felt Upright, tape flutter | `query:Sounds#Piano%20&%20Keys:FileId_4848` | Neo-Soul, Tyler-style ballads, Lofi |
| **Ac Piano Upright** | `PIANO` | Piano & Keys | Crisp, punchy upright piano | `query:Sounds#Piano%20&%20Keys:FileId_4847` | House, Jazz, Hip Hop |
| **Clav Electric** | `KEYS` | Piano & Keys | Funky clavinet with pickup bite | `query:Sounds#Piano%20&%20Keys:FileId_6395` | Funk, R&B, Old School Hip Hop |

---

### 🔊 808 & Sub Bass
| Preset Name | Role | Category | Character / Timbre | Verified Live 12 URI | Best For Genres |
|---|---|---|---|---|---|
| **808 BNYX Stopper** | `SUB_BASS` | Bass | Saturated, hard-hitting modern 808 | `query:Sounds#Bass:FileId_5175` | Modern Trap, Rage, Drill |
| **808 Drifter** | `SUB_BASS` | Bass | Analog Drift 808 with pitch glide | `query:Sounds#Bass:FileId_5176` | Atlanta Trap, Lofi Hip Hop |
| **808 Pure** | `SUB_BASS` | Bass | Clean deep sub sine fundamental | `query:Sounds#Bass:FileId_5177` | R&B, Chill Trap, Pop |
| **808 Slapping** | `SUB_BASS` | Bass | Heavy transient punch for bouncy rap | `query:Sounds#Bass:FileId_5179` | JID-style Atlanta bounce, Trap |
| **Analog Bass** | `BASS` | Bass | Warm ladder-filter dual-oscillator Moog | `query:Sounds#Bass:FileId_5181` | Synthwave, Funk, House, Techno |
| **Basic Sub Sine** | `SUB_BASS` | Bass | Ultra-clean sub foundation (< 80 Hz) | `query:Sounds#Bass:FileId_5196` | Techno, DnB, Dubstep |

---

### 🎛️ Synth Leads & Hooks
| Preset Name | Role | Category | Character / Timbre | Verified Live 12 URI | Best For Genres |
|---|---|---|---|---|---|
| **Acceleration Lead** | `LEAD` | Synth Lead | Bright cutting saw with portamento | `query:Sounds#Synth%20Lead:FileId_4589` | EDM, Melodic Techno, Synthwave |
| **Agenda Lead** | `LEAD` | Synth Lead | Punchy staccato analog hook lead | `query:Sounds#Synth%20Lead:FileId_6743` | Hip Hop hooks, Indie Pop |

---

### 🎻 Strings & Atmospheric Pads
| Preset Name | Role | Category | Character / Timbre | Verified Live 12 URI | Best For Genres |
|---|---|---|---|---|---|
| **Warm Analog Pad** | `PAD` | Pad | Lush, spacious chorus pad | `query:Sounds#Pad:FileId_4993` | Ambient, Neo-Soul, Deep House |
| **VHS Dreams** | `PAD` | Pad | Vintage tape flutter & filtered top | `query:Sounds#Pad:FileId_4984` | Lofi Chillhop, Indie R&B |
| **Ac Strings Orch** | `STRINGS` | Strings | Full orchestral ensemble section | `query:Sounds#Strings:FileId_4765` | Cinematic, Orchestral Trap, Ballads |
| **Ac Strings Pizz Basic** | `PLUCK` | Strings | Tight acoustic pizzicato plucks | `query:Sounds#Strings:FileId_4766` | Tension hooks, Drill, Trap arps |

---

### 🥁 Full Drum Kits (Native Drum Racks)
| Drum Kit Name | Role | Description | Verified Live 12 URI | Musical Applications |
|---|---|---|---|---|
| **808 Core Kit** | `DRUM_KIT` | Classic Roland TR-808 drum machine (Boom kick, snappy snare, metallic hats) | `query:Drums#FileId_5422` | Trap, Hip Hop, Modern R&B, Atlanta bounce |
| **909 Core Kit** | `DRUM_KIT` | Punchy analog Roland TR-909 (Hard kick, punchy snare, open hat sizzle) | `query:Drums#FileId_5423` | House, Techno, Dance, Electro |
| **707 Core Kit** | `DRUM_KIT` | Digital PCM Roland TR-707 (Tight retro snare, percussive claps) | `query:Drums#FileId_5421` | Synthwave, Disco, 80s Retro |
| **AG Techno Kit** | `DRUM_KIT` | Heavy techno kit (Sub rumble kick, industrial percs, cutting hats) | `query:Drums#FileId_5367` | Melodic Techno, Peak Time Techno |

---

## 3. Usage via Python and FastMCP

### Python API
```python
from engine.instruments import PresetCatalog, instrument_engine

# 1. Resolve preset by musical role and genre
preset = PresetCatalog.resolve_preset("PIANO", genre="neo_soul", mood="felt")
print(preset.name)  # -> 'Childhood Home Piano'
print(preset.uri)   # -> 'query:Sounds#Piano%20&%20Keys:FileId_4848'

# 2. Load onto an active Ableton track
result = instrument_engine.load_preset(track_index=3, preset_name_or_role="808 Pure")
```

### FastMCP Tool Calls
```json
// List available presets for a role
{
  "name": "preset_list_available",
  "arguments": {
    "role": "SUB_BASS",
    "genre": "trap"
  }
}

// Load directly to track
{
  "name": "instrument_load_preset",
  "arguments": {
    "track_index_or_id": "2",
    "preset_name_or_role": "Childhood Home Piano"
  }
}
```

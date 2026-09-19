# engine/mix/channel_strip.py
"""
Channel Strip & Bus Frequency Processing Engine:
Inserts and configures physical EQ Eight, Channel EQ, Drum Buss, and Glue Compressor
devices on individual tracks and group busses to enforce professional frequency separation,
high-pass filtering, surgical resonance dips, air boosts, and bus glue.
"""

import math
import logging
from typing import Dict, Any, Optional, List, Union

logger = logging.getLogger("ChannelStripEngine")


class ChannelStripEngine:
    """Architect for individual channel strips and group bus processing chains in Ableton Live."""

    # Mathematical frequency mapping for Live 12's EQ Eight:
    # f in [10 Hz, 22000 Hz] -> normalized value v in [0.0, 1.0]
    # v = log10(f / 10.0) / log10(22000.0 / 10.0)
    F_MIN = 10.0
    F_MAX = 22000.0
    LOG_RANGE = math.log10(F_MAX / F_MIN)

    @classmethod
    def freq_to_normalized(cls, freq_hz: float) -> float:
        """Converts frequency in Hz (10 to 22000) to EQ Eight's exact normalized float [0.0..1.0]."""
        clamped = max(cls.F_MIN, min(cls.F_MAX, freq_hz))
        return round(math.log10(clamped / cls.F_MIN) / cls.LOG_RANGE, 6)

    @classmethod
    def normalized_to_freq(cls, norm_val: float) -> float:
        """Converts EQ Eight normalized float [0.0..1.0] back to frequency in Hz."""
        clamped = max(0.0, min(1.0, norm_val))
        return round(cls.F_MIN * (10.0 ** (clamped * cls.LOG_RANGE)), 1)

    @classmethod
    def pitch_to_hz(cls, pitch: Union[int, float, None]) -> Optional[float]:
        """Converts MIDI pitch (0-127) to physical frequency in Hz."""
        if pitch is None:
            return None
        return round(440.0 * (2.0 ** ((float(pitch) - 69.0) / 12.0)), 2)

    @classmethod
    def get_role_eq_settings(cls, role: str) -> Dict[str, Any]:
        """
        Returns surgical EQ Eight parameter profiles tailored for specific instrument roles:
        - Filter 1: HPF (anti-rumble, clears low mud)
        - Filter 2: Bell (anti-mud or body boost)
        - Filter 3: Bell (presence or surgical dip)
        - Filter 4: High Shelf / Air (clarity and sheen)
        """
        r = role.lower().strip()

        if any(w in r for w in ["kick"]):
            return {
                "f1_on": 1.0, "f1_type": 0.0, "f1_freq": cls.freq_to_normalized(30.0), "f1_gain": 0.0, "f1_q": 0.38,
                "f2_on": 1.0, "f2_type": 3.0, "f2_freq": cls.freq_to_normalized(60.0), "f2_gain": 2.0, "f2_q": 0.40,
                "f3_on": 1.0, "f3_type": 3.0, "f3_freq": cls.freq_to_normalized(300.0), "f3_gain": -2.5, "f3_q": 0.50,
                "f4_on": 1.0, "f4_type": 5.0, "f4_freq": cls.freq_to_normalized(4500.0), "f4_gain": 1.5, "f4_q": 0.38
            }
        elif any(w in r for w in ["808", "bass", "sub"]):
            return {
                "f1_on": 1.0, "f1_type": 0.0, "f1_freq": cls.freq_to_normalized(25.0), "f1_gain": 0.0, "f1_q": 0.38,
                "f2_on": 1.0, "f2_type": 3.0, "f2_freq": cls.freq_to_normalized(55.0), "f2_gain": 1.5, "f2_q": 0.40,
                "f3_on": 1.0, "f3_type": 3.0, "f3_freq": cls.freq_to_normalized(220.0), "f3_gain": -2.0, "f3_q": 0.45,
                "f4_on": 1.0, "f4_type": 7.0, "f4_freq": cls.freq_to_normalized(7000.0), "f4_gain": 0.0, "f4_q": 0.38
            }
        elif any(w in r for w in ["snare", "clap"]):
            return {
                "f1_on": 1.0, "f1_type": 0.0, "f1_freq": cls.freq_to_normalized(90.0), "f1_gain": 0.0, "f1_q": 0.38,
                "f2_on": 1.0, "f2_type": 3.0, "f2_freq": cls.freq_to_normalized(200.0), "f2_gain": 1.0, "f2_q": 0.40,
                "f3_on": 1.0, "f3_type": 3.0, "f3_freq": cls.freq_to_normalized(800.0), "f3_gain": -1.5, "f3_q": 0.45,
                "f4_on": 1.0, "f4_type": 5.0, "f4_freq": cls.freq_to_normalized(8000.0), "f4_gain": 2.0, "f4_q": 0.38
            }
        elif any(w in r for w in ["hat", "cymbal", "perc", "crash", "shaker"]):
            return {
                "f1_on": 1.0, "f1_type": 0.0, "f1_freq": cls.freq_to_normalized(350.0), "f1_gain": 0.0, "f1_q": 0.38,
                "f2_on": 1.0, "f2_type": 3.0, "f2_freq": cls.freq_to_normalized(4500.0), "f2_gain": 1.0, "f2_q": 0.38,
                "f3_on": 0.0, "f3_type": 3.0, "f3_freq": cls.freq_to_normalized(1000.0), "f3_gain": 0.0, "f3_q": 0.38,
                "f4_on": 1.0, "f4_type": 5.0, "f4_freq": cls.freq_to_normalized(10000.0), "f4_gain": 2.5, "f4_q": 0.38
            }
        elif any(w in r for w in ["key", "piano", "rhodes", "chord"]):
            return {
                "f1_on": 1.0, "f1_type": 0.0, "f1_freq": cls.freq_to_normalized(110.0), "f1_gain": 0.0, "f1_q": 0.38,
                "f2_on": 1.0, "f2_type": 3.0, "f2_freq": cls.freq_to_normalized(320.0), "f2_gain": -2.0, "f2_q": 0.45,
                "f3_on": 1.0, "f3_type": 3.0, "f3_freq": cls.freq_to_normalized(2500.0), "f3_gain": 1.2, "f3_q": 0.40,
                "f4_on": 1.0, "f4_type": 5.0, "f4_freq": cls.freq_to_normalized(10000.0), "f4_gain": 1.5, "f4_q": 0.38
            }
        elif any(w in r for w in ["lead", "synth", "pluck", "arp"]):
            return {
                "f1_on": 1.0, "f1_type": 0.0, "f1_freq": cls.freq_to_normalized(130.0), "f1_gain": 0.0, "f1_q": 0.38,
                "f2_on": 1.0, "f2_type": 3.0, "f2_freq": cls.freq_to_normalized(500.0), "f2_gain": -1.5, "f2_q": 0.40,
                "f3_on": 1.0, "f3_type": 3.0, "f3_freq": cls.freq_to_normalized(3200.0), "f3_gain": 1.5, "f3_q": 0.40,
                "f4_on": 1.0, "f4_type": 5.0, "f4_freq": cls.freq_to_normalized(11000.0), "f4_gain": 2.0, "f4_q": 0.38
            }
        elif any(w in r for w in ["vocal", "vox", "hook", "chop"]):
            return {
                "f1_on": 1.0, "f1_type": 0.0, "f1_freq": cls.freq_to_normalized(100.0), "f1_gain": 0.0, "f1_q": 0.38,
                "f2_on": 1.0, "f2_type": 3.0, "f2_freq": cls.freq_to_normalized(300.0), "f2_gain": -2.5, "f2_q": 0.45,
                "f3_on": 1.0, "f3_type": 3.0, "f3_freq": cls.freq_to_normalized(3500.0), "f3_gain": 2.0, "f3_q": 0.40,
                "f4_on": 1.0, "f4_type": 5.0, "f4_freq": cls.freq_to_normalized(12000.0), "f4_gain": 2.5, "f4_q": 0.38
            }
        else:  # Foley, texture, or generic
            return {
                "f1_on": 1.0, "f1_type": 0.0, "f1_freq": cls.freq_to_normalized(150.0), "f1_gain": 0.0, "f1_q": 0.38,
                "f2_on": 0.0, "f2_type": 3.0, "f2_freq": cls.freq_to_normalized(500.0), "f2_gain": 0.0, "f2_q": 0.38,
                "f3_on": 0.0, "f3_type": 3.0, "f3_freq": cls.freq_to_normalized(2000.0), "f3_gain": 0.0, "f3_q": 0.38,
                "f4_on": 1.0, "f4_type": 5.0, "f4_freq": cls.freq_to_normalized(10000.0), "f4_gain": -1.5, "f4_q": 0.38
            }

    @classmethod
    def analyze_track_frequencies(
        cls,
        conn: Any,
        track_index: int,
        track_name: str = ""
    ) -> Dict[str, Any]:
        """
        Inspects live track content (MIDI notes across clips, audio clips, instrument devices)
        and extracts musical frequency metrics: lowest fundamental (min_hz), highest harmonic
        (max_hz), dominant pitch (dominant_hz), average pitch, and note count.
        """
        profile: Dict[str, Any] = {
            "track_index": track_index,
            "track_name": track_name,
            "devices": [],
            "note_count": 0,
            "min_pitch": None,
            "max_pitch": None,
            "dominant_pitch": None,
            "avg_pitch": None,
            "min_hz": None,
            "max_hz": None,
            "dominant_hz": None,
            "avg_hz": None,
            "audio_clips_count": 0,
            "detected_role": "lead"
        }

        if conn is None or not hasattr(conn, "send_command"):
            from engine.mix.gain_staging.auto_stager import AutoGainStagingEngine
            profile["detected_role"] = AutoGainStagingEngine.classify_role(track_name)
            return profile

        try:
            code = f"""
t = song.tracks[{track_index}]
t_name = t.name
devs = [d.name for d in t.devices]
all_pitches = []

# Arrangement clips
try:
    for c in getattr(t, 'arrangement_clips', []):
        if getattr(c, 'is_midi_clip', False):
            notes = c.get_notes_extended(from_time=0.0, from_pitch=0, time_span=max(0.1, c.length), pitch_span=128)
            all_pitches.extend([n.pitch for n in notes])
except Exception:
    pass

# Session clips
try:
    for cs in getattr(t, 'clip_slots', []):
        if getattr(cs, 'has_clip', False) and getattr(cs.clip, 'is_midi_clip', False):
            notes = cs.clip.get_notes_extended(from_time=0.0, from_pitch=0, time_span=max(0.1, cs.clip.length), pitch_span=128)
            all_pitches.extend([n.pitch for n in notes])
except Exception:
    pass

# Audio clips
audio_count = 0
try:
    for c in getattr(t, 'arrangement_clips', []):
        if getattr(c, 'is_audio_clip', False):
            audio_count += 1
    for cs in getattr(t, 'clip_slots', []):
        if getattr(cs, 'has_clip', False) and getattr(cs.clip, 'is_audio_clip', False):
            audio_count += 1
except Exception:
    pass

output = {{
    'name': t_name,
    'devices': devs,
    'pitches': all_pitches,
    'audio_count': audio_count
}}
"""
            r = conn.send_command("execute_code", {"code": code})
            raw = r.get("result", {}).get("output", {}) if isinstance(r, dict) else {}
            if raw:
                profile["track_name"] = raw.get("name", track_name)
                profile["devices"] = raw.get("devices", [])
                profile["audio_clips_count"] = raw.get("audio_count", 0)
                pitches = raw.get("pitches", [])
                if pitches:
                    profile["note_count"] = len(pitches)
                    profile["min_pitch"] = min(pitches)
                    profile["max_pitch"] = max(pitches)
                    profile["avg_pitch"] = round(sum(pitches) / len(pitches), 1)
                    from collections import Counter
                    c = Counter(pitches)
                    profile["dominant_pitch"] = c.most_common(1)[0][0]
                    profile["min_hz"] = cls.pitch_to_hz(profile["min_pitch"])
                    profile["max_hz"] = cls.pitch_to_hz(profile["max_pitch"])
                    profile["dominant_hz"] = cls.pitch_to_hz(profile["dominant_pitch"])
                    profile["avg_hz"] = cls.pitch_to_hz(profile["avg_pitch"])
        except Exception as e:
            logger.debug(f"Frequency analysis notice on track {track_index}: {e}")

        from engine.mix.gain_staging.auto_stager import AutoGainStagingEngine
        t_nm = profile["track_name"] or track_name
        profile["detected_role"] = AutoGainStagingEngine.classify_role(t_nm, profile["devices"])
        return profile

    @classmethod
    def get_adaptive_eq_settings(
        cls,
        freq_profile: Dict[str, Any],
        role: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculates surgical EQ Eight parameters dynamically derived from the physical
        frequency profile (min_hz, max_hz, dominant_hz) and musical role.
        Enforces Fundamental Preservation Law: HPF cut-off is placed strictly below min_hz.
        """
        detected_role = freq_profile.get("detected_role", "")
        r = (role or detected_role or "synth").lower().strip()
        min_hz = freq_profile.get("min_hz")
        dominant_hz = freq_profile.get("dominant_hz")
        devices = [str(d).lower() for d in freq_profile.get("devices", [])]
        is_sub_inst = any(k in d for d in devices for k in ["sublab", "808", "trilian", "sub bass"])

        # If detected as sub-bass via devices or physical low fundamental
        if is_sub_inst or (min_hz is not None and min_hz <= 75.0 and not any(k in r for k in ["drum", "kick", "loop"])):
            r = "bass"

        if r in ["bass", "sub", "808"]:
            # Sub-bass: cut ONLY inaudible subsonic rumble (< 25 Hz)
            # 100% of the 55 Hz fundamental for SubLabXL is preserved intact!
            if min_hz is not None:
                hpf_hz = min(25.0, max(15.0, min_hz * 0.45))
            else:
                hpf_hz = 22.0
            f2_freq = dominant_hz if (dominant_hz and dominant_hz <= 85.0) else (min_hz if min_hz else 55.0)
            return {
                "role": "bass",
                "hpf_hz": hpf_hz,
                "f1_on": 1.0, "f1_type": 0.0, "f1_freq": cls.freq_to_normalized(hpf_hz), "f1_gain": 0.0, "f1_q": 0.38,
                "f2_on": 1.0, "f2_type": 3.0, "f2_freq": cls.freq_to_normalized(f2_freq), "f2_gain": 1.2, "f2_q": 0.42,
                "f3_on": 1.0, "f3_type": 3.0, "f3_freq": cls.freq_to_normalized(220.0), "f3_gain": -2.0, "f3_q": 0.45,
                "f4_on": 1.0, "f4_type": 5.0, "f4_freq": cls.freq_to_normalized(7000.0), "f4_gain": 0.0, "f4_q": 0.38
            }

        elif any(w in r for w in ["kick", "bombo"]):
            hpf_hz = 30.0
            return {
                "role": "kick",
                "hpf_hz": hpf_hz,
                "f1_on": 1.0, "f1_type": 0.0, "f1_freq": cls.freq_to_normalized(hpf_hz), "f1_gain": 0.0, "f1_q": 0.38,
                "f2_on": 1.0, "f2_type": 3.0, "f2_freq": cls.freq_to_normalized(60.0), "f2_gain": 1.5, "f2_q": 0.42,
                "f3_on": 1.0, "f3_type": 3.0, "f3_freq": cls.freq_to_normalized(300.0), "f3_gain": -2.5, "f3_q": 0.50,
                "f4_on": 1.0, "f4_type": 5.0, "f4_freq": cls.freq_to_normalized(4800.0), "f4_gain": 1.5, "f4_q": 0.38
            }

        elif any(w in r for w in ["drum", "kit", "break", "loop"]):
            hpf_hz = 30.0
            return {
                "role": "drums",
                "hpf_hz": hpf_hz,
                "f1_on": 1.0, "f1_type": 0.0, "f1_freq": cls.freq_to_normalized(hpf_hz), "f1_gain": 0.0, "f1_q": 0.38,
                "f2_on": 1.0, "f2_type": 3.0, "f2_freq": cls.freq_to_normalized(65.0), "f2_gain": 1.2, "f2_q": 0.42,
                "f3_on": 1.0, "f3_type": 3.0, "f3_freq": cls.freq_to_normalized(320.0), "f3_gain": -2.5, "f3_q": 0.50,
                "f4_on": 1.0, "f4_type": 5.0, "f4_freq": cls.freq_to_normalized(5000.0), "f4_gain": 1.5, "f4_q": 0.38
            }

        elif any(w in r for w in ["snare", "clap"]):
            hpf_hz = 85.0
            return {
                "role": "snare",
                "hpf_hz": hpf_hz,
                "f1_on": 1.0, "f1_type": 0.0, "f1_freq": cls.freq_to_normalized(hpf_hz), "f1_gain": 0.0, "f1_q": 0.38,
                "f2_on": 1.0, "f2_type": 3.0, "f2_freq": cls.freq_to_normalized(200.0), "f2_gain": 1.0, "f2_q": 0.40,
                "f3_on": 1.0, "f3_type": 3.0, "f3_freq": cls.freq_to_normalized(800.0), "f3_gain": -1.5, "f3_q": 0.45,
                "f4_on": 1.0, "f4_type": 5.0, "f4_freq": cls.freq_to_normalized(8000.0), "f4_gain": 2.0, "f4_q": 0.38
            }

        elif any(w in r for w in ["hat", "cymbal", "perc", "shaker"]):
            hpf_hz = 350.0
            return {
                "role": "perc",
                "hpf_hz": hpf_hz,
                "f1_on": 1.0, "f1_type": 0.0, "f1_freq": cls.freq_to_normalized(hpf_hz), "f1_gain": 0.0, "f1_q": 0.38,
                "f2_on": 1.0, "f2_type": 3.0, "f2_freq": cls.freq_to_normalized(4500.0), "f2_gain": 1.0, "f2_q": 0.38,
                "f3_on": 0.0, "f3_type": 3.0, "f3_freq": cls.freq_to_normalized(1000.0), "f3_gain": 0.0, "f3_q": 0.38,
                "f4_on": 1.0, "f4_type": 5.0, "f4_freq": cls.freq_to_normalized(10000.0), "f4_gain": 2.5, "f4_q": 0.38
            }

        elif any(w in r for w in ["vocal", "vox"]):
            if min_hz is not None:
                hpf_hz = max(80.0, min(120.0, min_hz * 0.75))
            else:
                hpf_hz = 95.0
            return {
                "role": "vocal",
                "hpf_hz": hpf_hz,
                "f1_on": 1.0, "f1_type": 0.0, "f1_freq": cls.freq_to_normalized(hpf_hz), "f1_gain": 0.0, "f1_q": 0.38,
                "f2_on": 1.0, "f2_type": 3.0, "f2_freq": cls.freq_to_normalized(300.0), "f2_gain": -2.0, "f2_q": 0.45,
                "f3_on": 1.0, "f3_type": 3.0, "f3_freq": cls.freq_to_normalized(3500.0), "f3_gain": 2.0, "f3_q": 0.40,
                "f4_on": 1.0, "f4_type": 5.0, "f4_freq": cls.freq_to_normalized(12000.0), "f4_gain": 2.5, "f4_q": 0.38
            }

        else:
            # Melodic & harmonic instruments: Piano, Keys, Pads, Strings, Leads, Synths
            # HPF calculated strictly relative to lowest physical fundamental note
            if min_hz is not None:
                if min_hz < 100.0:
                    hpf_hz = max(45.0, min(90.0, min_hz * 0.75))
                elif min_hz < 220.0:
                    hpf_hz = max(75.0, min(145.0, min_hz * 0.70))
                elif min_hz < 450.0:
                    hpf_hz = max(120.0, min(220.0, min_hz * 0.60))
                else:
                    hpf_hz = max(180.0, min(350.0, min_hz * 0.40))
            else:
                if any(w in r for w in ["key", "piano", "rhodes"]):
                    hpf_hz = 77.0
                elif any(w in r for w in ["pad", "string"]):
                    hpf_hz = 115.0
                else:
                    hpf_hz = 120.0

            # Tailor bands based on harmonic category
            if any(w in r for w in ["key", "piano", "rhodes"]):
                f2_f, f2_g = 350.0, -1.8
                f3_f, f3_g = 2500.0, 1.2
                f4_f, f4_g = 10000.0, 1.5
            elif any(w in r for w in ["pad", "atmos", "ambient"]):
                f2_f, f2_g = 320.0, -1.5
                f3_f, f3_g = 600.0, -1.5   # Mid scoop creates spatial depth
                f4_f, f4_g = 10000.0, 1.5
            elif any(w in r for w in ["string", "cuerda"]):
                f2_f, f2_g = 380.0, -1.5
                f3_f, f3_g = 2000.0, 1.0
                f4_f, f4_g = 10000.0, 1.5
            else:  # Lead, synth, pluck, arp
                f2_f, f2_g = 450.0, -1.5
                f3_f, f3_g = 3200.0, 1.5   # Lead bite & articulation
                f4_f, f4_g = 11000.0, 1.8

            return {
                "role": r,
                "hpf_hz": hpf_hz,
                "f1_on": 1.0, "f1_type": 0.0, "f1_freq": cls.freq_to_normalized(hpf_hz), "f1_gain": 0.0, "f1_q": 0.38,
                "f2_on": 1.0, "f2_type": 3.0, "f2_freq": cls.freq_to_normalized(f2_f), "f2_gain": f2_g, "f2_q": 0.45,
                "f3_on": 1.0, "f3_type": 3.0, "f3_freq": cls.freq_to_normalized(f3_f), "f3_gain": f3_g, "f3_q": 0.40,
                "f4_on": 1.0, "f4_type": 5.0, "f4_freq": cls.freq_to_normalized(f4_f), "f4_gain": f4_g, "f4_q": 0.38
            }

    @classmethod
    def apply_channel_strip(
        cls,
        conn: Any,
        track_index: int,
        role: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Performs physical frequency analysis of the track content and configures
        surgical EQ Eight parameters matched to its detected fundamentals.
        """
        # 1. Physical Frequency Analysis & Dynamic Calibration
        freq_profile = cls.analyze_track_frequencies(conn, track_index)
        settings = cls.get_adaptive_eq_settings(freq_profile, role=role)
        resolved_role = settings.get("role", role or freq_profile.get("detected_role", "lead"))
        hpf_hz = settings.get("hpf_hz", 30.0)

        results: Dict[str, Any] = {
            "track_index": track_index,
            "role": resolved_role,
            "min_hz": freq_profile.get("min_hz"),
            "max_hz": freq_profile.get("max_hz"),
            "dominant_hz": freq_profile.get("dominant_hz"),
            "hpf_hz": hpf_hz,
            "loaded": False,
            "params_set": 0
        }

        if conn is None or not hasattr(conn, "send_command"):
            results["mock"] = True
            results["settings"] = settings
            return {"status": "SUCCESS", "mock": True, **results}

        import time

        # 2. Check if EQ Eight already exists on the track
        t_info = conn.send_command("get_track_info", {"track_index": track_index})
        devices = t_info.get("devices", t_info.get("result", {}).get("devices", [])) if isinstance(t_info, dict) else []
        eq_dev_idx = None
        for idx, d in enumerate(devices):
            if "EQ Eight" in d.get("name", ""):
                eq_dev_idx = idx
                results["loaded"] = True
                break

        # 3. If not found, load it and poll until Live instantiates it
        if eq_dev_idx is None:
            load_res = conn.send_command("load_instrument_or_effect", {
                "track_index": track_index,
                "uri": "query:AudioFx#EQ%20Eight"
            })
            results["loaded"] = load_res.get("status") in ("success", "SUCCESS") or load_res.get("loaded", False)

            t_info = conn.send_command("get_track_info", {"track_index": track_index})
            devices = t_info.get("devices", t_info.get("result", {}).get("devices", [])) if isinstance(t_info, dict) else []
            for idx, d in enumerate(devices):
                if "EQ Eight" in d.get("name", ""):
                    eq_dev_idx = idx
                    break

            if eq_dev_idx is None:
                for _ in range(8):
                    time.sleep(0.25)
                    t_info = conn.send_command("get_track_info", {"track_index": track_index})
                    devices = t_info.get("devices", t_info.get("result", {}).get("devices", [])) if isinstance(t_info, dict) else []
                    for idx, d in enumerate(devices):
                        if "EQ Eight" in d.get("name", ""):
                            eq_dev_idx = idx
                            break
                    if eq_dev_idx is not None:
                        break

        if eq_dev_idx is not None:
            param_updates = [
                (0, 1.0),  # Device On: Always ensure device is activated
                (4, settings["f1_on"]),
                (5, settings["f1_type"]),
                (6, settings["f1_freq"]),
                (7, settings["f1_gain"]),
                (8, settings["f1_q"]),
                (14, settings["f2_on"]),
                (15, settings["f2_type"]),
                (16, settings["f2_freq"]),
                (17, settings["f2_gain"]),
                (18, settings["f2_q"]),
                (24, settings["f3_on"]),
                (25, settings["f3_type"]),
                (26, settings["f3_freq"]),
                (27, settings["f3_gain"]),
                (28, settings["f3_q"]),
                (34, settings["f4_on"]),
                (35, settings["f4_type"]),
                (36, settings["f4_freq"]),
                (37, settings["f4_gain"]),
                (38, settings["f4_q"])
            ]
            # Direct atomic parameter setting in 1 single roundtrip
            try:
                code_p = f"""
t = song.tracks[{track_index}]
d = t.devices[{eq_dev_idx}]
for p_idx, val in {param_updates}:
    if p_idx < len(d.parameters):
        d.parameters[p_idx].value = float(val)
"""
                conn.send_command("execute_code", {"code": code_p})
                results["params_set"] = len(param_updates)
            except Exception:
                for p_idx, val in param_updates:
                    try:
                        conn.send_command("set_device_parameter", {
                            "track_index": track_index,
                            "device_index": eq_dev_idx,
                            "parameter": p_idx,
                            "parameter_index": p_idx,
                            "value": float(val)
                        })
                        results["params_set"] += 1
                    except Exception:
                        pass

            # Register as sculpted in supervisor without generic override
            try:
                from engine.fx.device_parameter_supervisor import DeviceParameterSupervisor
                DeviceParameterSupervisor._SCULPTED_REGISTRY.add((track_index, eq_dev_idx))
            except Exception:
                pass

        return {
            "status": "SUCCESS",
            "track_index": track_index,
            "role": resolved_role,
            "min_hz": freq_profile.get("min_hz"),
            "max_hz": freq_profile.get("max_hz"),
            "dominant_hz": freq_profile.get("dominant_hz"),
            "hpf_hz": hpf_hz,
            "eq_device_index": eq_dev_idx,
            "parameters_configured": results["params_set"],
            "settings": settings
        }


    @classmethod
    def apply_bus_processing(
        cls,
        conn: Any,
        group_track_index: int,
        bus_type: str = "drums"
    ) -> Dict[str, Any]:
        """
        Applies group/bus processing to tie stems together:
        - Drum Bus: Drum Buss device (Drive 20%, Soft, Crunch 15%, Transients +0.10, Compressor On)
        - Synth/Instrument Bus: Glue Compressor (Ratio 2:1, Attack 30ms, Auto Release, Soft Clip) + EQ Eight
        """
        b_type = bus_type.lower().strip()
        results = {"group_track_index": group_track_index, "bus_type": b_type, "devices_loaded": []}

        if conn is None or not hasattr(conn, "send_command"):
            results["mock"] = True
            return {"status": "SUCCESS", "mock": True, **results}

        if "drum" in b_type:
            # 1. Load Drum Buss
            load_db = conn.send_command("load_instrument_or_effect", {
                "track_index": group_track_index,
                "uri": "query:AudioFx#Drum%20Buss"
            })
            if load_db.get("status") in ("success", "SUCCESS"):
                results["devices_loaded"].append("Drum Buss")

            # Calibrate Drum Buss
            t_info = conn.send_command("get_track_info", {"track_index": group_track_index})
            devices = t_info.get("devices", t_info.get("result", {}).get("devices", [])) if isinstance(t_info, dict) else []
            db_idx = None
            for idx, d in enumerate(devices):
                if "Drum Buss" in d.get("name", ""):
                    db_idx = idx

            if db_idx is not None:
                for p_idx, val in [(0, 1.0), (1, 1.0), (2, 0.20), (3, 0.0), (4, 0.15), (6, 0.10)]:
                    try:
                        conn.send_command("set_device_parameter", {
                            "track_index": group_track_index,
                            "device_index": db_idx,
                            "parameter": p_idx,
                            "parameter_index": p_idx,
                            "value": float(val)
                        })
                    except Exception:
                        pass
        else:
            # Synths / Harmonic Bus: Glue Compressor + EQ Eight
            # 1. Glue Compressor
            load_glue = conn.send_command("load_instrument_or_effect", {
                "track_index": group_track_index,
                "uri": "query:AudioFx#Glue%20Compressor"
            })
            if load_glue.get("status") in ("success", "SUCCESS"):
                results["devices_loaded"].append("Glue Compressor")

            t_info = conn.send_command("get_track_info", {"track_index": group_track_index})
            devices = t_info.get("devices", t_info.get("result", {}).get("devices", [])) if isinstance(t_info, dict) else []
            glue_idx = None
            for idx, d in enumerate(devices):
                if "Glue Compressor" in d.get("name", ""):
                    glue_idx = idx

            if glue_idx is not None:
                for p_idx, val in [(0, 1.0), (1, -12.0), (4, 6.0), (5, 0.0), (6, 6.0), (8, 1.0)]:
                    try:
                        conn.send_command("set_device_parameter", {
                            "track_index": group_track_index,
                            "device_index": glue_idx,
                            "parameter": p_idx,
                            "parameter_index": p_idx,
                            "value": float(val)
                        })
                    except Exception:
                        pass

            # 2. EQ Eight for Bus carving
            load_eq = conn.send_command("load_instrument_or_effect", {
                "track_index": group_track_index,
                "uri": "query:AudioFx#EQ%20Eight"
            })
            if load_eq.get("status") in ("success", "SUCCESS"):
                results["devices_loaded"].append("EQ Eight")

            t_info2 = conn.send_command("get_track_info", {"track_index": group_track_index})
            devices2 = t_info2.get("devices", t_info2.get("result", {}).get("devices", [])) if isinstance(t_info2, dict) else []
            eq_idx = None
            for idx, d in enumerate(devices2):
                if "EQ Eight" in d.get("name", ""):
                    eq_idx = idx

            if eq_idx is not None:
                bus_params = [
                    (0, 1.0),
                    (4, 1.0), (5, 0.0), (6, cls.freq_to_normalized(40.0)), (7, 0.0),
                    (14, 1.0), (15, 3.0), (16, cls.freq_to_normalized(2500.0)), (17, -1.2), (18, 0.45),
                    (34, 1.0), (35, 5.0), (36, cls.freq_to_normalized(12000.0)), (37, 0.8), (38, 0.38)
                ]
                for p_idx, val in bus_params:
                    try:
                        conn.send_command("set_device_parameter", {
                            "track_index": group_track_index,
                            "device_index": eq_idx,
                            "parameter": p_idx,
                            "parameter_index": p_idx,
                            "value": float(val)
                        })
                    except Exception:
                        pass

        return {
            "status": "SUCCESS",
            "group_track_index": group_track_index,
            "bus_type": b_type,
            "devices_loaded": results["devices_loaded"]
        }

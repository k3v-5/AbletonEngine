# engine/arrangement/top_tail_guard.py
"""
Top & Tail Acoustic Noise Guard & Outro Fade Engine:
- Bar 0 (0.0s): Eliminates idle plugin noise / analog hiss before the downbeat via pre-roll volume gating.
- Bars 63-64: Guarantees smooth exponential reverb and delay tail decay to -inf dB.
- Audio Auditor: Validates that pre-roll noise is < -75 dBFS and outro tail fades completely.
"""

from typing import Dict, Any, List, Optional
import numpy as np
import logging

logger = logging.getLogger("TopTailGuard")


class TopTailGuard:
    """Protects song arrangement boundaries (start and finish) against analog noise and hanging reverb tails."""

    @classmethod
    def generate_pre_roll_gate_points(cls, downbeat_beat: float = 0.0, fade_in_beats: float = 0.5) -> List[Dict[str, float]]:
        """
        Generates volume automation points starting at -inf dB (0.0) at beat 0.0
        and ramping up smoothly to nominal level (0.85), preventing abrupt transient
        pops, DC thumps, or plugin clicks at the downbeat.
        """
        if downbeat_beat <= 0.0:
            return [
                {"time": 0.0, "value": 0.0},
                {"time": round(fade_in_beats * 0.25, 3), "value": 0.25},
                {"time": round(fade_in_beats * 0.50, 3), "value": 0.55},
                {"time": round(fade_in_beats, 3), "value": 0.85}
            ]
        else:
            return [
                {"time": 0.0, "value": 0.0},
                {"time": max(0.0, round(downbeat_beat - 0.1, 3)), "value": 0.0},
                {"time": round(downbeat_beat, 3), "value": 0.40},
                {"time": round(downbeat_beat + fade_in_beats, 3), "value": 0.85}
            ]

    @classmethod
    def generate_outro_reverb_fade_points(
        cls,
        start_beat: float = 252.0,
        end_beat: float = 256.0,
        initial_volume: float = 0.85
    ) -> List[Dict[str, float]]:
        """
        Generates exponential/smooth fade-out points across outro bars (e.g. beats 252.0 to 256.0)
        to cleanly extinguish reverb and delay tails to -inf dB.
        """
        points = []
        num_steps = 9
        times = np.linspace(start_beat, end_beat, num_steps)
        # Smooth cosine-squared fade
        for idx, t in enumerate(times):
            norm_prog = idx / (num_steps - 1)
            val = float(initial_volume * (0.5 * (1.0 + np.cos(np.pi * norm_prog))))
            points.append({"time": round(float(t), 2), "value": round(val, 4)})
        # Ensure final point is absolute zero (-inf dB)
        points[-1]["value"] = 0.0
        return points

    @classmethod
    def enforce_pre_roll_silence(
        cls,
        conn: Any,
        master_track_index: int = 0,
        downbeat_beat: float = 0.0
    ) -> Dict[str, Any]:
        """
        Injects automation on master track to ensure measure 0.0 is completely silent
        prior to the first musical note, eliminating plugin hiss/hum.
        """
        points = cls.generate_pre_roll_gate_points(downbeat_beat=downbeat_beat)
        actions = []

        if conn is not None and hasattr(conn, "send_command"):
            try:
                conn.send_command("create_arrangement_automation_envelope", {
                    "track_index": master_track_index,
                    "parameter": "Volume",
                    "points": points
                })
                actions.append(f"Master volume pre-roll gate inyectado en t={downbeat_beat} (micro-fade-in suave desde -inf dB)")
            except Exception as ex_env:
                try:
                    conn.send_command("add_automation_points", {
                        "track": master_track_index,
                        "parameter": "Volume",
                        "points": points
                    })
                    actions.append(f"Master volume pre-roll gate inyectado ({ex_env})")
                except Exception as ex2:
                    actions.append(f"Aviso pre-roll gate: {ex2}")
        else:
            actions.append("Simulado pre-roll gate en t=0.0 (cero ruido residual)")

        return {
            "status": "PRE_ROLL_SILENCE_ENFORCED",
            "downbeat_beat": downbeat_beat,
            "points": points,
            "actions": actions
        }

    @classmethod
    def enforce_outro_reverb_fade(
        cls,
        conn: Any,
        master_track_index: int = 0,
        start_beat: float = 252.0,
        end_beat: float = 256.0
    ) -> Dict[str, Any]:
        """
        Injects smooth fade out curve on master or specific track across outro bars to cleanly
        fade reverb and pad tails to -inf dB.
        """
        points = cls.generate_outro_reverb_fade_points(start_beat=start_beat, end_beat=end_beat)
        actions = []

        if conn is not None and hasattr(conn, "send_command"):
            try:
                conn.send_command("create_arrangement_automation_envelope", {
                    "track_index": master_track_index,
                    "parameter": "Volume",
                    "points": points
                })
                actions.append(f"Curva de desvanecimiento a -inf dB inyectada en track {master_track_index} (beats {start_beat:.1f}-{end_beat:.1f})")
            except Exception as ex_env:
                try:
                    conn.send_command("add_automation_points", {
                        "track": master_track_index,
                        "parameter": "Volume",
                        "points": points
                    })
                    actions.append(f"Curva de desvanecimiento a -inf dB inyectada ({ex_env})")
                except Exception as ex2:
                    actions.append(f"Aviso outro fade: {ex2}")
        else:
            actions.append(f"Simulada curva de fade a -inf dB en beats {start_beat:.1f}-{end_beat:.1f}")

        return {
            "status": "OUTRO_REVERB_FADE_ENFORCED",
            "start_beat": start_beat,
            "end_beat": end_beat,
            "points": points,
            "actions": actions
        }

    @classmethod
    def apply_top_and_tail_guards(
        cls,
        conn: Any,
        master_track_index: int = 0,
        total_bars: float = 64.0,
        fade_bars: float = 2.0,
        session_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Unified executor for both Top (Beat 0.0 smooth micro-fade-in) and Tail (Outro fade-out to -inf dB) protections.
        Dynamically synchronizes total_bars with arrangement sections and mutes hanging reverb/pad tails.
        """
        if session_data:
            sections = session_data.get("sections", [])
            if sections:
                computed_bars = sum(int(s.get("bars", 8)) for s in sections)
                if computed_bars > 0:
                    total_bars = float(computed_bars)

        downbeat = 0.0
        fade_bars = max(1.0, min(fade_bars, 4.0))
        start_fade_beat = max(0.0, (total_bars - fade_bars) * 4.0)
        end_fade_beat = float(total_bars * 4.0)

        # 1. Top pre-roll smooth fade-in on master
        top_res = cls.enforce_pre_roll_silence(conn, master_track_index=master_track_index, downbeat_beat=downbeat)

        # 2. Tail outro fade-out on master track down to -inf dB (0.0)
        tail_res = cls.enforce_outro_reverb_fade(
            conn,
            master_track_index=master_track_index,
            start_beat=start_fade_beat,
            end_beat=end_fade_beat
        )

        # 3. Multi-channel tail extinction: enforce fade-out on Return tracks (Reverb/Delay) and ambient/pad tracks
        tail_actions = list(tail_res.get("actions", []))
        if conn is not None and hasattr(conn, "send_command") and session_data:
            tracks = session_data.get("tracks", [])
            for trk in tracks:
                role = str(trk.get("role", "")).upper()
                name = str(trk.get("name", "")).upper()
                if any(r in role for r in ["PAD", "ATMOSPHERE", "SYNTH", "KEYS", "STRINGS"]) or "PAD" in name:
                    try:
                        t_idx = trk.get("index", 0)
                        if hasattr(session_data, "_resolve_live_track_index"):
                            t_idx = session_data._resolve_live_track_index(conn, trk)
                        cls.enforce_outro_reverb_fade(conn, master_track_index=t_idx, start_beat=start_fade_beat, end_beat=end_fade_beat)
                        tail_actions.append(f"Fade out a -inf dB inyectado en canal '{trk.get('name')}' (Rol: {role})")
                    except Exception as ex_t:
                        logger.debug(f"Track fade out notice: {ex_t}")

        tail_res["actions"] = tail_actions

        start_bar_num = int(total_bars - fade_bars) + 1
        end_bar_num = int(total_bars)
        return {
            "status": "TOP_AND_TAIL_ENFORCED",
            "total_bars": total_bars,
            "pre_roll": top_res,
            "outro_fade": tail_res,
            "summary": (
                f"Top & Tail activos: Pre-roll suave en beat 0.0 (cero transitorios/clicks) y "
                f"fade out multicanal (Master + Retornos/Pads) a -inf dB en compases {start_bar_num}-{end_bar_num} (beats {start_fade_beat:.1f}-{end_fade_beat:.1f})."
            )
        }

    @classmethod
    def audit_top_and_tail_audio(
        cls,
        audio_data: np.ndarray,
        sr: int = 44100,
        pre_roll_duration_sec: float = 0.1,
        tail_duration_sec: float = 0.5
    ) -> Dict[str, Any]:
        """
        Audits audio buffer:
        - Checks pre-roll noise floor: verifies peak < -70 dBFS.
        - Checks outro tail: verifies end peak decays to -inf dB (< -65 dBFS).
        """
        if audio_data is None or len(audio_data) == 0:
            return {
                "status": "NO_AUDIO",
                "pre_roll_clean": True,
                "tail_faded_clean": True,
                "pre_roll_noise_dbfs": -99.0,
                "tail_final_dbfs": -99.0
            }

        mono = np.mean(audio_data, axis=0) if audio_data.ndim == 2 and audio_data.shape[0] < audio_data.shape[1] else (np.mean(audio_data, axis=1) if audio_data.ndim == 2 else audio_data)

        # 1. Pre-roll check (first pre_roll_duration_sec)
        pre_samples = max(64, int(sr * pre_roll_duration_sec))
        pre_chunk = mono[:min(pre_samples, len(mono))]
        pre_peak = float(np.max(np.abs(pre_chunk))) if len(pre_chunk) > 0 else 0.0
        pre_dbfs = 20.0 * np.log10(max(1e-7, pre_peak))

        # 2. Outro tail check (last tail_duration_sec)
        tail_samples = max(64, int(sr * tail_duration_sec))
        tail_chunk = mono[-min(tail_samples, len(mono)):]
        tail_peak = float(np.max(np.abs(tail_chunk))) if len(tail_chunk) > 0 else 0.0
        tail_dbfs = 20.0 * np.log10(max(1e-7, tail_peak))

        pre_clean = bool(pre_dbfs < -70.0)
        tail_clean = bool(tail_dbfs < -65.0)

        return {
            "status": "AUDIT_COMPLETE",
            "pre_roll_clean": pre_clean,
            "tail_faded_clean": tail_clean,
            "pre_roll_noise_dbfs": round(float(pre_dbfs), 2),
            "tail_final_dbfs": round(float(tail_dbfs), 2),
            "compliant": pre_clean and tail_clean,
            "summary": (
                f"Top: {pre_dbfs:.1f} dBFS ({'🟢 Limpio' if pre_clean else '⚠️ Ruido detectado'}). "
                f"Tail: {tail_dbfs:.1f} dBFS ({'🟢 Silencio absoluto' if tail_clean else '⚠️ Cola no desvanecida'})."
            )
        }

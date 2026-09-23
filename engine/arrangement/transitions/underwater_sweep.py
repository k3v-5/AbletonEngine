# engine/arrangement/transitions/underwater_sweep.py
"""
Underwater & Radio Sweep Transition Generator:
Produces signature pre-drop acoustic collapses popular in modern hip-hop, ambient pop,
and electronic music (Drake, 40, Travis Scott, OVO sound).
Modes:
1. UNDERWATER: Exponential low-pass filter dive down to ~450 Hz paired with an atmospheric
   reverb wash (up to 45% wet), creating complete acoustic submersion before detonating into full
   frequency impact on beat 1 of the drop.
2. RADIO / TELEPHONE: Bandpass isolation (450 Hz to 3200 Hz) simulating lo-fi transistor radio
   or phone acoustics before expanding into high-fidelity width.
"""

from typing import Dict, Any, List, Optional
import math
import logging

logger = logging.getLogger("UnderwaterRadioSweepGenerator")


class UnderwaterRadioSweepGenerator:
    """
    Computes precise cutoff and reverb wet/dry automation envelopes for acoustic rupture transitions.
    """

    @classmethod
    def generate_underwater_sweep(
        cls,
        drop_start_beat: float,
        duration_beats: float = 4.0,
        mode: str = "UNDERWATER",
        target_track: str = "Master",
        reverb_intensity: float = 0.45,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generates filter and spatial envelopes plunging into acoustic collapse right before a drop.
        """
        mode = mode.upper() if mode else "UNDERWATER"
        start_beat = max(0.0, drop_start_beat - duration_beats)
        steps = 12

        lpf_points: List[Dict[str, float]] = []
        hpf_points: List[Dict[str, float]] = []
        reverb_points: List[Dict[str, float]] = []

        if mode == "RADIO" or mode == "TELEPHONE":
            # Radio mode: bandpass collapse (450 Hz HPF, 3200 Hz LPF)
            for i in range(steps):
                frac = i / float(steps - 1)
                t = start_beat + (frac * duration_beats)

                # Low-pass drops from 20kHz to 3200Hz
                lpf_val = 20000.0 * ((3200.0 / 20000.0) ** (frac ** 1.2))
                lpf_points.append({"time": round(t, 3), "frequency_hz": round(lpf_val, 1)})

                # High-pass rises from 20Hz to 450Hz
                hpf_val = 20.0 + (430.0 * (frac ** 1.2))
                hpf_points.append({"time": round(t, 3), "frequency_hz": round(hpf_val, 1)})

                # Moderate dry/wet reverb or room resonance
                rev_val = (reverb_intensity * 0.4) * (frac ** 1.5)
                reverb_points.append({"time": round(t, 3), "wet_percent": round(rev_val * 100.0, 1)})

            # Snap back to full spectrum at drop beat
            lpf_points.append({"time": round(drop_start_beat, 3), "frequency_hz": 20000.0})
            hpf_points.append({"time": round(drop_start_beat, 3), "frequency_hz": 20.0})
            reverb_points.append({"time": round(drop_start_beat, 3), "wet_percent": 0.0})

        else:
            # UNDERWATER mode: steep low-pass sweep down to ~450 Hz + wet reverb wash
            for i in range(steps):
                frac = i / float(steps - 1)
                t = start_beat + (frac * duration_beats)

                # Exponential dive from 20,000 Hz down to 450 Hz
                lpf_val = 20000.0 * ((450.0 / 20000.0) ** (frac ** 1.4))
                lpf_points.append({"time": round(t, 3), "frequency_hz": round(lpf_val, 1)})

                # Reverb wash rises progressively
                rev_val = reverb_intensity * (frac ** 1.6)
                reverb_points.append({"time": round(t, 3), "wet_percent": round(rev_val * 100.0, 1)})

            # Instantaneous snap back on drop beat
            lpf_points.append({"time": round(drop_start_beat, 3), "frequency_hz": 20000.0})
            reverb_points.append({"time": round(drop_start_beat, 3), "wet_percent": 0.0})

        return {
            "status": "SWEEP_GENERATED",
            "mode": mode,
            "target_track": target_track,
            "drop_start_beat": drop_start_beat,
            "start_beat": start_beat,
            "duration_beats": duration_beats,
            "min_cutoff_hz": 450.0 if mode == "UNDERWATER" else 3200.0,
            "max_reverb_wet": round(reverb_intensity * 100.0, 1) if mode == "UNDERWATER" else round(reverb_intensity * 40.0, 1),
            "filter_cutoff_envelope": lpf_points,
            "highpass_cutoff_envelope": hpf_points if mode in ["RADIO", "TELEPHONE"] else [],
            "reverb_wet_envelope": reverb_points,
            "recommended_devices": ["AutoFilter (Lowpass 24dB/oct)", "Reverb (Wet/Dry automation)"]
        }

    @classmethod
    def deploy_sweep_in_live(
        cls,
        conn: Any,
        target_track_index: int,
        sweep_recipe: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Dispatches automation points to Live via OSC/IPC connection.
        """
        applied = False
        if conn is not None and hasattr(conn, "send_command"):
            try:
                conn.send_command("add_automation_points", {
                    "track": target_track_index,
                    "parameter": "Filter Frequency",
                    "points": sweep_recipe.get("filter_cutoff_envelope", [])
                })
                conn.send_command("add_automation_points", {
                    "track": target_track_index,
                    "parameter": "Reverb Wet",
                    "points": sweep_recipe.get("reverb_wet_envelope", [])
                })
                applied = True
            except Exception as e:
                logger.warning(f"Notice deploying sweep in Live: {e}")

        return {
            "status": "APPLIED" if applied else "CALCULATED",
            "target_track": target_track_index,
            "recipe": sweep_recipe
        }

    @classmethod
    def render_markdown_summary(cls, result: Dict[str, Any]) -> str:
        """Renders clear, human-readable markdown summary."""
        mode_desc = (
            "Colapso acústico subacuático (LPF 20kHz ➔ 450Hz) con lavado reverberante"
            if result.get("mode") == "UNDERWATER"
            else "Aislamiento radio transistor / teléfono (Paso banda 450Hz - 3.2kHz)"
        )
        return (
            "🌊 **Transición de Ruptura Acústica 'Underwater' / Filtro Radio**\n\n"
            f"• **Modo Seleccionado:** `{result.get('mode', 'UNDERWATER')}` ({mode_desc})\n"
            f"• **Punto de Impacto (Drop):** Beat {result.get('drop_start_beat')} (Duración pre-drop: {result.get('duration_beats')} beats)\n"
            f"• **Frecuencia Mínima:** `{result.get('min_cutoff_hz')} Hz` | **Reverb Máximo:** `{result.get('max_reverb_wet')}%`\n"
            f"• **Puntos de Automatización:** {len(result.get('filter_cutoff_envelope', []))} nodos de curva exponencial\n"
            "• **Efecto de Producción:** Vacía el espectro y el aire justo antes del drop, maximizando el impacto físico cuando entran el sub y la batería."
        )

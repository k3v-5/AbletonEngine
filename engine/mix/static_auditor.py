"""
AbletonEngine Static Mix Auditor:
Analyzes DAW track layout, device chains, fader staging, and routing
prior to playback or mastering, flagging risks and generating actionable advice.
"""

from typing import Dict, List, Any, Optional

FX_HEAVY_THRESHOLD = 4   # More than 4 insert effects on a single track
UNITY_VOLUME = 0.85      # Ableton fader unity (0 dB is typically 0.85 in Live API or 1.0 in normalized representation)
NEAR_CLIP_VOLUME = 0.95  # Above this without limiter indicates high clipping risk


class StaticMixAuditor:
    """
    Evaluates session layout without requiring playback or audio capture.
    """

    GENRE_TARGETS = {
        "boom_bap": {"lufs": -9.0, "true_peak": -1.0, "headroom_db": 6.0, "dynamics": "wide"},
        "trap":     {"lufs": -7.0, "true_peak": -1.0, "headroom_db": 5.0, "dynamics": "medium"},
        "phonk":    {"lufs": -6.0, "true_peak": -0.3, "headroom_db": 4.0, "dynamics": "tight"},
        "club":     {"lufs": -8.5, "true_peak": -0.5, "headroom_db": 4.5, "dynamics": "compressed"},
        "streaming":{"lufs": -14.0, "true_peak": -1.0, "headroom_db": 6.0, "dynamics": "open"},
        "neutral":  {"lufs": -14.0, "true_peak": -1.0, "headroom_db": 6.0, "dynamics": "medium"},
    }

    @classmethod
    def audit_session(cls, session_info: Dict[str, Any], genre: str = "streaming") -> Dict[str, Any]:
        """
        Takes session info dictionary (tracks, master volume, etc.) and returns structured report.
        """
        tracks = session_info.get("tracks", [])
        flagged_tracks = []
        global_flags = []
        fixes = []

        # 1. Master Fader Check
        master_vol = session_info.get("project", {}).get("master_volume", 0.85)
        if master_vol > 0.90:
            global_flags.append("master-clipping-risk")
            fixes.append("El fader del Master está por encima de unity (0 dB). Bájalo para evitar distorsión inter-sample en la conversión D/A.")

        # 2. Per-Track Audit
        active_count = 0
        for idx, t in enumerate(tracks):
            t_idx = t.get("index", idx)
            name = t.get("name", f"Track {t_idx}")
            vol = t.get("volume", 0.85)
            mute = t.get("mute", False)
            devices = t.get("devices", [])
            flags = []

            if not mute:
                active_count += 1

            # Check silent but active
            if (vol <= 0.001 or vol == 0.0) and not mute:
                flags.append("silent-active")
                fixes.append(f"{name}: Volumen en 0 pero pista activa. Silénciala (Mute) para ahorrar CPU y evitar ruidos analógicos residuales.")

            # Check overloaded FX
            # Filter out instrument (device 0) if present
            fx_count = len(devices) - 1 if len(devices) > 1 else len(devices)
            if fx_count > FX_HEAVY_THRESHOLD:
                flags.append("fx-heavy")
                fixes.append(f"{name}: Más de {FX_HEAVY_THRESHOLD} efectos cargados. Revisa la cadena y consolida procesadores redundantes.")

            # Check near-clipping fader
            if vol > NEAR_CLIP_VOLUME and not mute:
                flags.append("near-clip-fader")
                fixes.append(f"{name}: Fader en {vol:.2f}, muy cerca del techo digital. Aplica gain staging bajando el fader a ~0.70-0.80.")

            if flags:
                flagged_tracks.append({
                    "track_index": t_idx,
                    "name": name,
                    "volume": vol,
                    "mute": mute,
                    "fx_count": len(devices),
                    "flags": flags,
                })

        target = cls.GENRE_TARGETS.get(genre.lower(), cls.GENRE_TARGETS["neutral"])

        return {
            "kind": "static_audit",
            "genre": genre,
            "target": target,
            "total_tracks": len(tracks),
            "active_tracks": active_count,
            "flagged_tracks": flagged_tracks,
            "global_flags": global_flags,
            "fixes": fixes,
            "passed": len(global_flags) == 0 and len([t for t in flagged_tracks if "near-clip-fader" in t["flags"]]) == 0,
        }

    @classmethod
    def format_report_es(cls, report: Dict[str, Any]) -> str:
        """
        Formats audit report into concise Spanish markdown.
        """
        lines = [
            f"### [Auditoría Estática de Mezcla] (Perfil: {report.get('genre', 'General').upper()})",
            f"• Pistas Totales: {report.get('total_tracks', 0)} | Pistas Activas: {report.get('active_tracks', 0)}",
            f"• Target de Sonoridad: `{report.get('target', {}).get('lufs')} LUFS` | Techo True Peak: `{report.get('target', {}).get('true_peak')} dBTP`",
        ]

        if report.get("global_flags"):
            lines.append("\n**[!] Alertas Globales:**")
            for gf in report["global_flags"]:
                lines.append(f"  • `{gf}`")

        flagged = report.get("flagged_tracks", [])
        if flagged:
            lines.append("\n**Pistas con Observaciones:**")
            for t in flagged:
                lines.append(f"  • **{t['name']}** (Idx: {t['track_index']}): {', '.join(t['flags'])}")
        else:
            lines.append("\n[OK] **Estructura de canales limpia:** Sin sobrecarga de FX ni faders en peligro de clip.")

        fixes = report.get("fixes", [])
        if fixes:
            lines.append("\n**-> Acciones Sugeridas:**")
            for f in fixes:
                lines.append(f"  -> {f}")

        return "\n".join(lines)

"""
Forensic Stem Export and Quality Audit Gatekeeper for Phase 10:
Verifies sub-bass phase cross-correlation (rho Kick vs Bass >= +0.30),
headroom ceilings (<= -1.0 dBTP), creates stem partitioning, generates metadata manifest,
and provides self-healing feedback or actionable instructions for the assistant.
"""

import os
import json
import time
import logging
from typing import Dict, Any, List

from engine.audio.stem_audit import StemAuditor, PhaseCorrelationStatus

logger = logging.getLogger("CopilotGuidedSession.Phase10.StemCoordinator")


def audit_and_prepare_stems(session: Any, conn: Any) -> Dict[str, Any]:
    """
    Audits the entire arrangement, verifies sub-bass phase cross-correlation (rho >= +0.30),
    headroom ceilings (<= -1.0 dBTP), creates stem partitioning, generates metadata manifest,
    and provides self-healing feedback or actionable instructions for the assistant.
    """
    tracks = session.data.get("tracks", [])
    bpm = float(session.data.get("bpm", 120.0))
    total_bars = float(session.data.get("total_bars", 64.0))
    key = session.data.get("key", "F")
    scale = session.data.get("scale", "natural_minor")

    # 1. Fetch live session tracks if available
    live_tracks = []
    if conn and hasattr(conn, "send_command"):
        try:
            s_info = conn.send_command("get_session_info", {})
            s_res = s_info.get("result", s_info) if isinstance(s_info, dict) else {}
            num_t = s_res.get("track_count", len(tracks))
            for i in range(min(num_t, 32)):
                t_info = conn.send_command("get_track_info", {"track_index": i})
                t_res = t_info.get("result", t_info) if isinstance(t_info, dict) else {}
                if isinstance(t_res, dict) and "name" in t_res:
                    live_tracks.append(t_res)
        except Exception as e:
            logger.debug(f"Live track fetch notice: {e}")

    effective_tracks = live_tracks if len(live_tracks) >= len(tracks) else tracks
    formatted_tracks = []
    for idx, t in enumerate(effective_tracks):
        formatted_tracks.append({
            "index": t.get("index", idx),
            "name": t.get("name", f"Track {idx}"),
            "role": t.get("role", "OTHER")
        })

    # 2. Run Forensic Stem Audit & Partitioning
    export_dir = "exports/stems"
    os.makedirs(export_dir, exist_ok=True)

    audit_res = StemAuditor.orchestrate_stem_export_and_audit(
        tracks=formatted_tracks,
        export_dir=export_dir,
        bpm=bpm,
        start_bar=1.0,
        end_bar=total_bars + 1.0,
        commercial_delivery_5=True,
        sample_rate=44100,
        bit_depth=24
    )

    metrics = audit_res.stem_metrics
    phase_corrs = audit_res.phase_correlations
    ready = audit_res.ready_for_distribution

    # 3. Quality Control Checklist & Actionable Remedies
    remedy_instructions = []
    applied_compensations = []

    # Check A: Headroom compliance (<= -1.0 dBTP)
    for m in metrics:
        if not m.headroom_safe:
            excess_db = m.true_peak_dbtp - (-1.0)
            remedy_instructions.append(
                f"⚠️ [HEADROOM EXCEDIDO]: El stem '{m.stem_name}' tiene un pico de {m.true_peak_dbtp:.2f} dBTP (límite: -1.0 dBTP). "
                f"Acción requerida: Bajar el fader de '{m.stem_name}' en -{excess_db:.1f} dB para evitar distorsión en distribución."
            )
        else:
            applied_compensations.append(f"Stem '{m.stem_name}': Headroom óptimo ({m.true_peak_dbtp:.2f} dBTP, {m.integrated_lufs:.1f} LUFS)")

    # Check B: Phase correlation between sub-bass stems (Kick vs Bass)
    for pc in phase_corrs:
        status = pc.get("status")
        rho = pc.get("correlation_coefficient", pc.get("rho", 1.0))
        if status == PhaseCorrelationStatus.DESTRUCTIVE_CANCEL.value or rho < -0.30:
            ready = False
            remedy_instructions.append(
                f"⛔ [CANCELACIÓN DE FASE DESTRUCTIVA]: Correlación de Pearson negativa (rho = {rho:.2f}) detectada en subgraves (20-150 Hz) "
                f"entre {pc.get('stem_a')} y {pc.get('stem_b')}. "
                f"Acción obligatoria: Invertir polaridad de fase (180°) en el canal de bajo usando Utility, o desplazar 3-5 ms para evitar pérdida total de pegada."
            )
        elif status == PhaseCorrelationStatus.WARNING_LOW.value or (-0.30 <= rho < 0.30):
            remedy_instructions.append(
                f"⚠️ [AVISO DE FASE]: Correlación moderada (rho = {rho:.2f}) en subgraves. Se sugiere verificar compatibilidad mono."
            )

    # Check C: Empty or orphaned stems
    if len(metrics) == 0:
        ready = False
        remedy_instructions.append("⛔ [ERROR CRÍTICO]: No se detectaron pistas con audio en la sesión. Se prohíbe la exportación vacía.")

    # 4. Save Official Stems Manifest
    manifest_path = os.path.join(export_dir, "stems_manifest.json")
    manifest_payload = {
        "project_name": "Copilot Guided Production",
        "key": key,
        "scale": scale,
        "bpm": bpm,
        "sample_rate": 44100,
        "bit_depth": 24,
        "format": "WAV Broadcast 24-bit / 44.1 kHz",
        "delivery_groups": ["01_DRUMS", "02_BASS", "03_KEYS_BRASS", "04_VOCALS", "05_FX", "00_MASTER"],
        "total_bars": total_bars,
        "ready_for_distribution": ready,
        "stems_count": len(metrics),
        "stems": [m.to_dict() for m in metrics],
        "phase_correlations": phase_corrs,
        "remedy_instructions": remedy_instructions,
        "timestamp": time.time()
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_payload, f, indent=2)

    session.data["stems_export"] = manifest_payload
    session._save_state()

    # 5. Build Human-Readable Formatted Report
    status_banner = "✅ **PAQUETE DE STEMS VERIFICADO Y LISTO PARA DISTRIBUCIÓN**" if ready else "⚠️ **COMPUERTA DE STEMS: CORRECCIONES REQUERIDAS ANTES DE EXPORTAR**"

    stem_rows = []
    for m in metrics:
        h_icon = "🟢" if m.headroom_safe else "🔴"
        stem_rows.append(f"  • {h_icon} **{m.stem_name}**: Peak: `{m.true_peak_dbtp:.2f} dBTP` | Sonoridad: `{m.integrated_lufs:.1f} LUFS` | Crest: `{m.crest_factor_db:.1f} dB`")
    stems_table = "\n".join(stem_rows)

    phase_summary = "🟢 Coherente (mono compatible)"
    if phase_corrs:
        p0 = phase_corrs[0]
        rho_val = p0.get("correlation_coefficient", p0.get("rho", 1.0))
        phase_summary = f"{'🟢 Coherente' if rho_val >= 0.3 else '🔴 Destructiva'} (rho = {rho_val:.2f})"

    report_md = (
        f"{status_banner}\n\n"
        f"• **Directorio de Exportación:** `{export_dir}/`\n"
        f"• **Formato:** Broadcast WAV 24-bit / 44.1 kHz (Estándar de Entrega Comercial)\n"
        f"• **Límites de Arreglo:** Compases 1 a {int(total_bars)} ({int(total_bars)} compases completos)\n"
        f"• **Grupos de Stems:** `DRUMS`, `BASS`, `KEYS/BRASS`, `VOCALS`, `FX` y `MASTER WAV`\n"
        f"• **Correlación de Fase Subgrave (Kick vs Bajo):** {phase_summary}\n\n"
        f"**Auditoría Individual de Stems:**\n{stems_table}\n\n"
        f"📄 **Manifiesto Oficial:** Guardado en `{manifest_path}`\n"
    )

    if remedy_instructions:
        report_md += "\n🛠️ **Acciones de Corrección Detectadas por el Motor:**\n"
        for ri in remedy_instructions:
            report_md += f"{ri}\n"
        instructions_for_ai = "El motor detectó desbalances en los stems. Corrige las alertas reportadas antes de proceder a la distribución comercial."
    else:
        report_md += "\n💎 **Todos los stems están en regla:** Cero saturación, margen de pico verdadero certificado y coherencia de fase óptima."
        instructions_for_ai = "Los stems están 100% en regla y certificados para mezcla/mastering externo o distribución."

    return {
        "summary": f"{len(metrics)} stems auditados. Estado: {'LISTO' if ready else 'REQUIERE_CORRECCIÓN'}",
        "report_text": report_md,
        "ready_for_distribution": ready,
        "manifest_path": manifest_path,
        "instructions_for_ai": instructions_for_ai,
        "stems_count": len(metrics)
    }

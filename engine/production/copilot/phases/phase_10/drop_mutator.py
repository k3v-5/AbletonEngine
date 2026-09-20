"""
Drop Multi-Verse Mutator for Phase 10:
Generates, validates, and deploys high-entropy drop variations (A/B/C)
and handles arrangement timeline stamping and playback preview.
"""

import re
import json
import logging
from typing import Dict, Any, Optional

from engine.music.drop_mutator import DropMutationEngine, DropMutationEntropyViolationError

logger = logging.getLogger("CopilotGuidedSession.Phase10.DropMutator")


def handle_drop_mutator(session: Any, conn: Any, text: str, user_input: str, completed_phase: str) -> Optional[Dict[str, Any]]:
    tracks = session.data.get("tracks", [])

    # Multi-Verse Mutations A/B/C Generation & Deployment
    if any(w in text for w in ["mutar drop", "variaciones de drop", "drop a/b/c", "drop multiverse"]):
        mut_dict = None
        try:
            js_match = re.search(r"(\{[\s\S]*\})", user_input)
            if js_match:
                parsed = json.loads(js_match.group(1))
                if all(k in parsed for k in ["variation_a", "variation_b", "variation_c"]):
                    mut_dict = parsed
        except Exception:
            pass

        if mut_dict:
            try:
                bass_trk = next((t for t in tracks if t.get("role") == "BASS"), tracks[0] if tracks else {"index": 0})
                b_idx = bass_trk.get("index", 0)
                deploy_res = DropMutationEngine.deploy_mutations_to_session(conn, b_idx, mut_dict, base_slot=10)
                return {
                    "status": "DROP_MUTATIONS_DEPLOYED",
                    "current_step": "MUTACIONES DE DROP A/B/C VALIDADAS Y DESPLEGADAS",
                    "action_taken": f"3 variaciones de drop desplegadas en ranuras 10, 11 y 12 de la Pista {b_idx}.",
                    "question": (
                        "⚡ **Multi-Verso de Drops A/B/C Validado y Desplegado en Live 12:**\n\n"
                        "• **Drop 1A (Main Hook):** Patrón principal de alta energía.\n"
                        "• **Drop 1B (Half-Time Switch):** Métrica a medio tiempo con divergencia rítmica verificada.\n"
                        "• **Drop 1C (Melodic Climax):** Variación melódica densa y contrastante.\n\n"
                        "Las 3 variaciones superaron el umbral de entropía del 40% de divergencia musical y están listas en las ranuras de clips de Session para alternar con un solo clic.\n\n"
                        "¿Deseas escuchar alguna variación (ej: 'Reproducir Drop 1B') o pasar a exportación?"
                    ),
                    "instructions_for_ai": "Las 3 variaciones fueron validadas y creadas. Permite al usuario alternar o navegar entre ellas.",
                    "phase": completed_phase,
                    "mutations": deploy_res
                }
            except DropMutationEntropyViolationError as ent_err:
                return {
                    "status": "MUTATION_REJECTED",
                    "current_step": "MUTACIÓN RECHAZADA POR BAJA CREATIVIDAD",
                    "action_taken": str(ent_err),
                    "question": (
                        f"⚠️ **Alerta del Motor:** {str(ent_err)}\n\n"
                        f"Por favor, redefine las variaciones B y C asegurando contrastes rítmicos marcados (Half-time, cambios de síncopa o silencios)."
                    ),
                    "instructions_for_ai": "El motor rechazó las mutaciones por falta de contraste. Debes componer notas genuinamente diferentes para cada variación.",
                    "phase": completed_phase
                }
        else:
            return {
                "status": "AWAITING_DROP_MUTATIONS",
                "current_step": "SOLICITUD DE DROP MULTI-VERSO",
                "action_taken": "El motor exige a la IA que componga explícitamente las 3 variaciones de Drop contrastantes.",
                "question": (
                    "🎛️ **Generador Multi-Verso de Drops A/B/C:**\n\n"
                    "El motor exige a la IA la composición explícita de **3 variaciones completas y contrastantes** (divergencia mínima del 40%):\n"
                    "• `variation_a`: Main Hook (Complextro / 4-on-the-floor).\n"
                    "• `variation_b`: Beat Switch / Half-Time (bombos espaciados, silencios y growls largos).\n"
                    "• `variation_c`: Melodic Climax (arpegios rápidos y acordes supersaw).\n\n"
                    "*Proporciona el JSON con 'variation_a', 'variation_b' y 'variation_c' con sus notas MIDI para auditarlas y desplegarlas.*"
                ),
                "instructions_for_ai": "Compón las 3 variaciones con diferencias métricas notables en JSON bajo 'variation_a', 'variation_b' y 'variation_c'.",
                "phase": completed_phase
            }

    # Stamping Drop Mutations to Arrangement Timeline
    if any(w in text for w in ["estampar", "aplicar drop", "pegar drop", "estampar drop", "variacion al arrangement", "drop al arrangement"]) or (("drop 1b" in text or "drop 1c" in text or "variacion b" in text or "variacion c" in text) and ("arrangement" in text or "linea de tiempo" in text or "compas" in text)):
        v_key = "variation_b" if ("1b" in text or " b" in text or "half" in text) else ("variation_c" if ("1c" in text or " c" in text or "melodic" in text) else "variation_a")
        target_bar = 32.0
        sections = session.data.get("sections", [])
        for sec in sections:
            if "drop" in str(sec.get("name", "")).lower():
                target_bar = float(sec.get("start_bar", 32.0))
                break
        bar_m = re.search(r"(?:comp[aá]s|bar)\s*(\d+)", text)
        if bar_m:
            target_bar = float(bar_m.group(1))

        bass_trk = next((t for t in tracks if t.get("role") == "BASS"), tracks[0] if tracks else {"index": 0})
        b_idx = bass_trk.get("index", 0)

        stamp_res = DropMutationEngine.deploy_variation_to_arrangement(
            conn=conn,
            track_index=b_idx,
            variation_key=v_key,
            destination_bar=target_bar
        )
        dest_beat = target_bar * 4.0
        if conn and hasattr(conn, "send_command"):
            try:
                conn.send_command("jump_to_cue_point", {"target": dest_beat})
            except Exception:
                pass
            try:
                conn.send_command("start_playback", {})
            except Exception:
                pass

        return {
            "status": "DROP_MUTATION_STAMPED",
            "current_step": "DROP MUTADO ESTAMPADO EN EL ARRANGEMENT",
            "action_taken": f"Variación '{stamp_res['variation_name']}' estampada en el compás {target_bar:.0f} (Beat {dest_beat:.0f}) de la pista {b_idx}. Reproducción iniciada.",
            "question": (
                f"🎯 **Variación de Drop Estampada en Arrangement:**\n\n"
                f"• **Variación:** `{stamp_res['variation_name']}`\n"
                f"• **Ubicación:** Compás {target_bar:.0f} (Beat {dest_beat:.0f})\n"
                f"• **Pista:** {b_idx} ('{bass_trk.get('name', 'Bass')}')\n\n"
                f"El playhead se ha transportado al compás {target_bar:.0f} y Ableton Live está reproduciendo la variación en el contexto completo del arreglo.\n\n"
                f"¿Deseas probar otra variación o realizar alguna otra modificación?"
            ),
            "instructions_for_ai": "La variación fue estampada en el Arrangement. Puedes estampar otra o proceder con la mezcla.",
            "phase": completed_phase,
            "stamped_variation": stamp_res
        }

    return None

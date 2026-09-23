# engine/mix/spatial_panning.py
"""
Instrument Panning Evaluator and Anti-Masking Spatial Architecture (SOLID Refactored):
Evaluates instrument stereo distribution prior to the vocal stage.
Prevents frequency and spatial collisions by clearing the phantom center
strictly for Lead Vocals, Kick, and Sub-Bass, while distributing harmonic
and rhythmic elements into complementary stereo pockets.

Decomposed Components (SRP):
- SpatialReportRenderer: Formatting and markdown report presentation.
- SpatialRuleEngine: Panning calculation heuristics and stereo balance rules.
- MaskingConflictDetector: Detection of stereo collisions between non-mono elements.
- SpatialPlanExecutor: Physical dispatching of panning commands to DAW adapter.
- InstrumentPanningEvaluator: High-level unified facade maintaining full API compatibility.
"""

from typing import Dict, Any, List, Optional, Tuple
import logging

from engine.core.roles import RoleClassifier

logger = logging.getLogger("InstrumentPanningEvaluator")


class SpatialReportRenderer:
    """Renders human-readable pan positions and markdown audit tables (SRP)."""

    @staticmethod
    def pan_to_display(pan_val: float) -> str:
        """Converts float [-1.0 .. 1.0] to readable pan position (e.g. '24L', 'Center', '16R')."""
        if abs(pan_val) < 0.02:
            return "Center"
        val_int = int(round(abs(pan_val) * 100))
        return f"{val_int}L" if pan_val < 0 else f"{val_int}R"

    @classmethod
    def render_summary_table(cls, directives: List[Dict[str, Any]]) -> str:
        """Formats panning directives into a structured markdown table."""
        table_lines = [
            "| Pista | Nombre | Rol | Paneo Actual | Paneo Recomendado | Diagnóstico Acústico |",
            "| :---: | :--- | :---: | :---: | :---: | :--- |"
        ]
        for d in directives:
            t_idx = d["track_index"]
            t_name = d["name"]
            t_role = d["role"]
            cur_dsp = d["current_display"]
            rec_dsp = d["recommended_display"]
            rat = d["rationale"]
            table_lines.append(f"| {t_idx} | **{t_name}** | `{t_role}` | `{cur_dsp}` | **`{rec_dsp}`** | {rat} |")
        return "\n".join(table_lines)


class SpatialRuleEngine:
    """Calculates recommended pan positions and rationales based on acoustic roles and stereo balance (SRP)."""

    # Target panning positions [-1.0 .. 1.0]
    # -1.0 = 50L (Hard Left), 0.0 = Center, +1.0 = 50R (Hard Right)
    DEFAULT_ROLE_PAN_TARGETS = {
        "KICK": 0.0,
        "DRUMS": 0.0,
        "DEMBOW": 0.0,
        "BASS": 0.0,
        "SUB": 0.0,
        "808": 0.0,
        "808_BASS": 0.0,
        "ELECTRIC_BASS": 0.0,
        "VOCALS": 0.0,
        "LEAD_VOCAL": 0.0,
        "BACKING_VOCALS": 0.40,
        "SNARE": 0.0,
        "CLAP": 0.0,
        "KEYS": -0.24,       # ~24L (Left pocket for harmonic chords)
        "PIANO": -0.24,
        "CHORDS": -0.24,
        "RHYTHM_GUITAR": -0.32, # ~32L (Harmonic pocket complementary to keys/lead)
        "LEAD_GUITAR": 0.30,   # ~30R (Melodic solo pocket complementary to synth lead)
        "LEAD": 0.24,        # ~24R (Right pocket for melodic topline/accent)
        "SYNTH": 0.24,
        "PLUCK": 0.22,
        "GUITAR": 0.25,
        "HI_HATS": 0.16,     # ~16R (Air and rhythm offset)
        "HATS": 0.16,
        "PERCUSSION": -0.18, # ~18L (Polyrhythmic counter-balance)
        "SHAKER": -0.18,
        "TOMS": -0.15,
        "PAD": -0.32,        # ~32L (Atmospheric width pushed to sides)
        "STRINGS": 0.30,
        "ATMOSPHERE": -0.35,
        "FX": 0.28,
        "COUNTER_LEAD": -0.22, # ~22L (Call-and-response pocket opposite to lead)
        "EAR_CANDY": 0.35,     # ~35R (Wide peripheral accents)
        "TEXTURE_FOLEY": -0.38 # ~38L (Wide organic ambient bed)
    }

    @classmethod
    def calculate_directives(
        cls,
        track_items: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[str], int]:
        """
        Calculates panning directives, tracks center clumping and harmonic balance.
        Returns (directives, center_conflicts, center_clump_count).
        """
        panning_directives = []
        conflicts = []
        center_clump_count = 0

        harmonic_left_count = 0
        harmonic_right_count = 0

        for t in track_items:
            role = t["classified_role"]
            cur_p = t["current_pan"]
            idx = t["track_index"]
            name = t["name"]

            rec_p = cls.DEFAULT_ROLE_PAN_TARGETS.get(role, 0.0)
            rationale = ""

            if role in ("KICK", "DRUMS", "DEMBOW"):
                rec_p = 0.0
                rationale = "Ancla rítmica central (0.0). Preserva pegada transiente y energía mono en club."
            elif role in ("SUB", "BASS", "808", "808_BASS", "ELECTRIC_BASS"):
                rec_p = 0.0
                rationale = "Graves monofónicos (<120 Hz) centrados. Previene cancelaciones de fase acústicas."
            elif role in ("VOCALS", "LEAD_VOCAL"):
                rec_p = 0.0
                rationale = "Centro puro reservado para la presencia in-your-face de la voz principal."
            elif role in ("BACKING_VOCALS", "COROS"):
                if harmonic_right_count <= harmonic_left_count:
                    rec_p = 0.40
                    harmonic_right_count += 1
                else:
                    rec_p = -0.40
                    harmonic_left_count += 1
                rationale = f"Amplitud lateral periférica ({SpatialReportRenderer.pan_to_display(rec_p)}). Bolsillo estéreo abierto que libera el canal central para la voz solista."
                if abs(cur_p) < 0.05:
                    center_clump_count += 1
                    conflicts.append(f"Pista {idx} ('{name}'): Voces de apoyo/coros centrados enturbian y solapan la inteligibilidad de la voz solista.")
            elif role in ("SNARE", "CLAP"):
                rec_p = 0.0
                rationale = "Golpe central con el bombo para sostener el pulso principal del compás."
            elif role == "KEYS":
                rec_p = -0.24
                harmonic_left_count += 1
                rationale = "Apertura a la izquierda (24L). Despeja el centro para la voz y crea bolsillo para el lead."
                if abs(cur_p) < 0.05:
                    center_clump_count += 1
                    conflicts.append(f"Pista {idx} ('{name}'): Chords/Keys centrados enmascaran el centro espectral de la voz (300 Hz - 2.5 kHz).")
            elif role in ("RHYTHM_GUITAR", "GUITAR_RHYTHM"):
                if harmonic_left_count > harmonic_right_count:
                    rec_p = 0.32
                    harmonic_right_count += 1
                else:
                    rec_p = -0.32
                    harmonic_left_count += 1
                rationale = f"Bolsillo armónico complementario ({SpatialReportRenderer.pan_to_display(rec_p)}). Opuesto a otras pistas armónicas para evitar solapamiento."
                if abs(cur_p) < 0.05:
                    center_clump_count += 1
                    conflicts.append(f"Pista {idx} ('{name}'): Rhythm Guitar centrado enmascara el rango medio y compite con la voz central.")
            elif role == "LEAD":
                rec_p = 0.24
                harmonic_right_count += 1
                rationale = "Apertura a la derecha (24R). Posición simétrica complementaria respecto a Keys; centro libre para voz."
                if abs(cur_p) < 0.05:
                    center_clump_count += 1
                    conflicts.append(f"Pista {idx} ('{name}'): Sintetizador Lead centrado compite directamente con la futura melodía vocal.")
            elif role in ("LEAD_GUITAR", "GUITAR_LEAD", "SOLO_GUITAR"):
                if harmonic_right_count >= harmonic_left_count:
                    rec_p = -0.30
                    harmonic_left_count += 1
                else:
                    rec_p = 0.30
                    harmonic_right_count += 1
                rationale = f"Bolsillo melódico solista ({SpatialReportRenderer.pan_to_display(rec_p)}). Ubicación anti-enmascaramiento complementaria."
                if abs(cur_p) < 0.05:
                    center_clump_count += 1
                    conflicts.append(f"Pista {idx} ('{name}'): Lead Guitar centrado compite directamente con la voz principal.")
            elif role == "HI_HATS":
                rec_p = 0.16
                rationale = "Apertura a la derecha (16R). Simulación acústica natural; libera aire y brillo central."
                if abs(cur_p) < 0.05:
                    center_clump_count += 1
                    conflicts.append(f"Pista {idx} ('{name}'): Hi-Hats en el centro saturan frecuencias altas donde respiran los formantes vocales.")
            elif role == "PERCUSSION":
                rec_p = -0.18
                rationale = "Apertura a la izquierda (18L). Contrapeso rítmico frente a Hi-Hats; espacialidad orgánica."
                if abs(cur_p) < 0.05:
                    center_clump_count += 1
            elif role == "COUNTER_LEAD":
                rec_p = -0.22
                harmonic_left_count += 1
                rationale = "Apertura a la izquierda (22L). Bolsillo complementario opuesto al Lead (24R); llamada y respuesta nítida sin pisar el centro."
                if abs(cur_p) < 0.05:
                    center_clump_count += 1
            elif role == "PAD":
                rec_p = -0.32
                rationale = "Amplitud lateral (32L). Colchón atmosférico empujado a los extremos estéreo."
                if abs(cur_p) < 0.05:
                    center_clump_count += 1
                    conflicts.append(f"Pista {idx} ('{name}'): Pad atmosférico centrado ahoga la profundidad de la sesión.")
            elif role == "EAR_CANDY":
                rec_p = 0.35
                rationale = "Efecto espacial lateral (35R). Dinamismo periférico sin tocar el canal medio."
            elif role == "TEXTURE_FOLEY":
                rec_p = -0.38
                rationale = "Lecho textural periférico (38L). Genera profundidad orgánica a -24 dBFS sin enturbiar el centro."
            else:
                if harmonic_left_count <= harmonic_right_count:
                    rec_p = -0.15
                    harmonic_left_count += 1
                else:
                    rec_p = 0.15
                    harmonic_right_count += 1
                rationale = "Separación estéreo secundaria equilibrada."

            is_optimized = abs(cur_p - rec_p) < 0.04
            status = "OPTIMIZADO" if is_optimized else "SOLAPAMIENTO_DETECTADO" if abs(cur_p) < 0.05 and rec_p != 0.0 else "AJUSTE_RECOMENDADO"

            panning_directives.append({
                "track_index": idx,
                "name": name,
                "role": role,
                "current_pan": round(cur_p, 2),
                "current_display": SpatialReportRenderer.pan_to_display(cur_p),
                "recommended_pan": round(rec_p, 2),
                "recommended_display": SpatialReportRenderer.pan_to_display(rec_p),
                "status": status,
                "rationale": rationale
            })

        return panning_directives, conflicts, center_clump_count


class MaskingConflictDetector:
    """Detects stereo collisions and masking between non-mono-locked instruments (SRP)."""

    MONO_LOCKED_ROLES = (
        "KICK", "DRUMS", "DEMBOW", "SUB", "BASS", "808", "808_BASS",
        "ELECTRIC_BASS", "VOCALS", "LEAD_VOCAL", "SNARE", "CLAP"
    )

    @classmethod
    def detect_conflicts(cls, track_items: List[Dict[str, Any]]) -> List[str]:
        """Detects mutual masking when two stereo instruments collapse to approximately the same pan position."""
        conflicts = []
        for i in range(len(track_items)):
            for j in range(i + 1, len(track_items)):
                ti, tj = track_items[i], track_items[j]
                pi, pj = ti["current_pan"], tj["current_pan"]
                ri, rj = ti["classified_role"], tj["classified_role"]
                if ri not in cls.MONO_LOCKED_ROLES and rj not in cls.MONO_LOCKED_ROLES:
                    if abs(pi - pj) < 0.08 and abs(pi) > 0.05:
                        conflicts.append(
                            f"Solapamiento estéreo detectado: Pista {ti['track_index']} ('{ti['name']}') y Pista {tj['track_index']} ('{tj['name']}') "
                            f"están colapsadas en {SpatialReportRenderer.pan_to_display(pi)}, generando interferencia y enmascaramiento mutuo."
                        )
        return conflicts


class SpatialPlanExecutor:
    """Executes panning directives by sending set_track_panning commands to Ableton Live (SRP)."""

    @classmethod
    def apply_plan(
        cls,
        conn: Any,
        directives: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Sends set_track_panning commands to Ableton Live for each directive in the plan."""
        applied = []
        errors = []

        if conn is None:
            return {"status": "BYPASS", "applied_count": 0, "message": "Conexión a Live no disponible."}

        for d in directives:
            idx = d.get("track_index", 0)
            pan = float(d.get("recommended_pan", 0.0))
            name = d.get("name", f"Track {idx}")
            disp = d.get("recommended_display", SpatialReportRenderer.pan_to_display(pan))

            try:
                res = conn.send_command("set_track_panning", {
                    "track_index": idx,
                    "panning": pan
                })
                applied.append({
                    "track_index": idx,
                    "name": name,
                    "panning": pan,
                    "display": disp,
                    "result": res
                })
            except Exception as e:
                logger.warning(f"Error setting panning on track {idx}: {e}")
                errors.append({"track_index": idx, "error": str(e)})

        return {
            "status": "SUCCESS" if not errors else "PARTIAL_SUCCESS",
            "applied_count": len(applied),
            "applied": applied,
            "errors": errors
        }


class InstrumentPanningEvaluator:
    """
    Evaluates stereo field occupancy of instrumental tracks, detects center clumping /
    masking conflicts, and designs an anti-overlap panning blueprint before vocal introduction.
    Facade delegating to SpatialRuleEngine, MaskingConflictDetector, SpatialReportRenderer, and SpatialPlanExecutor.
    """

    DEFAULT_ROLE_PAN_TARGETS = SpatialRuleEngine.DEFAULT_ROLE_PAN_TARGETS

    @classmethod
    def classify_role(cls, name: str, role: str = "") -> str:
        """Determines acoustic role category from track name and metadata."""
        return RoleClassifier.classify_for_panning(name, role)

    @classmethod
    def pan_to_display(cls, pan_val: float) -> str:
        """Converts float [-1.0 .. 1.0] to readable pan position (e.g. '24L', 'Center', '16R')."""
        return SpatialReportRenderer.pan_to_display(pan_val)

    @classmethod
    def evaluate_session_panning(
        cls,
        tracks: List[Dict[str, Any]],
        conn: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Audits the stereo panning layout across all tracks in the session.
        Detects center clumping, stereo masking conflicts, and calculates
        an anti-overlap panning plan.
        """
        # 1. Fetch current panning from Live connection if available
        live_pans = {}
        if conn is not None and hasattr(conn, "send_command"):
            try:
                s_info = conn.send_command("get_session_info", {})
                s_data = s_info.get("result", s_info) if isinstance(s_info, dict) else {}
                t_count = s_data.get("track_count", 0)
                for i in range(t_count):
                    t_info = conn.send_command("get_track_info", {"track_index": i})
                    t_d = t_info.get("result", t_info) if isinstance(t_info, dict) else {}
                    if "panning" in t_d:
                        live_pans[i] = float(t_d["panning"])
            except Exception as e:
                logger.debug(f"Could not read live panning via connection: {e}")

        # 2. Build list of candidate tracks
        track_items = []
        for trk in tracks:
            idx = trk.get("index", 0)
            name = trk.get("name", f"Track {idx}")
            role = trk.get("role", "")
            classified_role = cls.classify_role(name, role)
            current_pan = live_pans.get(idx, trk.get("panning", 0.0))
            track_items.append({
                "track_index": idx,
                "name": name,
                "original_role": role,
                "classified_role": classified_role,
                "current_pan": float(current_pan),
                "is_audio": trk.get("is_audio_track", False) or trk.get("is_audio", False)
            })

        # 3. Dynamic complimentary assignment via SpatialRuleEngine
        panning_directives, center_conflicts, center_clump_count = SpatialRuleEngine.calculate_directives(track_items)

        # 4. Cross-track stereo masking detection via MaskingConflictDetector
        masking_conflicts = MaskingConflictDetector.detect_conflicts(track_items)
        conflicts = center_conflicts + masking_conflicts

        # 5. Energy balance and formatting via SpatialReportRenderer
        left_energy = sum(abs(d["recommended_pan"]) for d in panning_directives if d["recommended_pan"] < 0)
        right_energy = sum(abs(d["recommended_pan"]) for d in panning_directives if d["recommended_pan"] > 0)
        balance_ratio = round(left_energy / max(0.01, right_energy), 2)
        table_md = SpatialReportRenderer.render_summary_table(panning_directives)

        has_masking_risk = len(conflicts) > 0 or center_clump_count >= 2

        return {
            "status": "PANNING_AUDIT_COMPLETED",
            "has_masking_risk": has_masking_risk,
            "center_clumping_tracks_count": center_clump_count,
            "conflicts": conflicts,
            "directives": panning_directives,
            "balance_ratio": balance_ratio,
            "summary_table": table_md,
            "center_reserved_for": ["Lead Vocal", "Kick", "Sub-Bass", "Snare"]
        }

    @classmethod
    def apply_panning_plan(
        cls,
        conn: Any,
        directives: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Sends set_track_panning commands to Ableton Live for each directive in the plan."""
        return SpatialPlanExecutor.apply_plan(conn, directives)

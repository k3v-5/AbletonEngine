"""
Clip Automation Suggester:
Proactively generates and offers tangible, contextual vector automation recipes
whenever a clip is created or added to Ableton Live.
"""

from typing import List, Dict, Any, Optional, Tuple, Union
import math
import logging

logger = logging.getLogger(__name__)


class ClipAutomationRecipe:
    """Represents a specific, tangible automation curve recipe."""

    def __init__(
        self,
        recipe_id: str,
        name: str,
        description: str,
        parameter_candidates: List[str],
        curve_type: str,
        start_val: float,
        end_val: float,
        category: str = "swell"
    ):
        self.recipe_id = recipe_id
        self.name = name
        self.description = description
        self.parameter_candidates = parameter_candidates
        self.curve_type = curve_type
        self.start_val = start_val
        self.end_val = end_val
        self.category = category

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recipe_id": self.recipe_id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "curve_type": self.curve_type,
            "suggested_range": [self.start_val, self.end_val],
            "target_candidates": self.parameter_candidates
        }


class ClipAutomationSuggester:
    """
    Analyzes track instruments, devices, and musical context to offer
    and stamp vector automation curves on clips.
    """

    DEFAULT_RECIPES = [
        ClipAutomationRecipe(
            recipe_id="timbre_swell",
            name="Timbre / Brightness Swell",
            description="Smooth exponential rise in timbre/brightness (0.15 -> 0.85) to build anticipation.",
            parameter_candidates=["P1 Timbre", "P1 Brightness", "Timbre", "Brightness", "Macro 1", "Cutoff"],
            curve_type="exponential",
            start_val=0.15,
            end_val=0.85,
            category="riser"
        ),
        ClipAutomationRecipe(
            recipe_id="filter_riser",
            name="Filter Cutoff Sweep / Riser",
            description="Exponential lowpass opening (0.20 -> 0.95) driving energy into the next section.",
            parameter_candidates=["LP Freq", "Cutoff", "Filter Frequency", "Filter 1 Frequency", "Frequency", "Macro 1"],
            curve_type="exponential",
            start_val=0.20,
            end_val=0.95,
            category="riser"
        ),
        ClipAutomationRecipe(
            recipe_id="filter_breathing",
            name="Organic Filter Breathing",
            description="Subtle rhythmic pulsation (0.45 <-> 0.65) keeping pads and textures evolving and alive.",
            parameter_candidates=["LP Freq", "Cutoff", "Filter Frequency", "P1 Timbre", "Macro 1"],
            curve_type="breathing",
            start_val=0.45,
            end_val=0.65,
            category="modulation"
        ),
        ClipAutomationRecipe(
            recipe_id="pre_drop_vacuum",
            name="Pre-Drop Vacuum Cut",
            description="Deep energy vacuum: cuts volume/filter 2 beats before the downbeat for maximum impact.",
            parameter_candidates=["Volume", "Dry/Wet", "Cutoff", "P1 Timbre"],
            curve_type="vacuum_cut",
            start_val=0.85,
            end_val=0.0,
            category="impact"
        ),
        ClipAutomationRecipe(
            recipe_id="reverb_washout",
            name="Reverb Space Washout",
            description="Wet buildup to 0.70 near the end of the phrase, snapping to dry on the downbeat.",
            parameter_candidates=["Dry/Wet", "Mix", "Reverb Level", "Decay Time"],
            curve_type="washout",
            start_val=0.10,
            end_val=0.70,
            category="transition"
        ),
        ClipAutomationRecipe(
            recipe_id="volume_crescendo",
            name="Dynamic Volume Crescendo",
            description="Gradual volume gain rise (-12dB to 0dB / 0.50 -> 0.85) opening the mix.",
            parameter_candidates=["Volume", "Gain"],
            curve_type="exponential",
            start_val=0.50,
            end_val=0.85,
            category="dynamics"
        ),
        ClipAutomationRecipe(
            recipe_id="sub_turnaround",
            name="Sub Bass Harmonic Turnaround",
            description="Drive/filter surge on the turnaround bars to signal section changes.",
            parameter_candidates=["Drive", "Saturation", "Filter Frequency", "Cutoff"],
            curve_type="ease_in_out",
            start_val=0.25,
            end_val=0.75,
            category="bass"
        )
    ]

    @classmethod
    def get_recipe(cls, recipe_id: str) -> Optional[ClipAutomationRecipe]:
        for r in cls.DEFAULT_RECIPES:
            if r.recipe_id.lower() == recipe_id.lower():
                return r
        return None

    @classmethod
    def suggest_for_track(
        cls,
        track_info: Dict[str, Any],
        clip_length: float = 16.0,
        section: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Inspects track devices and name to return the top 3-4 contextual automation recipes.
        """
        t_name = str(track_info.get("name", "")).lower()
        devices = track_info.get("devices", [])
        dev_names = [str(d.get("name", "")).lower() for d in devices]

        is_pad = any(k in t_name for k in ["pad", "string", "atmos", "ambient", "texture"]) or any("analog lab" in d for d in dev_names)
        is_bass = any(k in t_name for k in ["bass", "808", "sub"])
        is_lead = any(k in t_name for k in ["lead", "synth", "screech", "growl", "vital", "serum"])
        is_drum = any(k in t_name for k in ["drum", "kick", "snare", "hat", "percussion", "perc"])

        suggestions: List[Dict[str, Any]] = []

        if is_pad:
            s_ids = ["timbre_swell", "filter_breathing", "filter_riser", "reverb_washout"]
        elif is_bass:
            s_ids = ["pre_drop_vacuum", "sub_turnaround", "filter_riser"]
        elif is_lead:
            s_ids = ["filter_riser", "reverb_washout", "pre_drop_vacuum", "volume_crescendo"]
        elif is_drum:
            s_ids = ["pre_drop_vacuum", "volume_crescendo", "filter_riser"]
        else:
            s_ids = ["filter_riser", "timbre_swell", "volume_crescendo", "reverb_washout"]

        for r_id in s_ids:
            recipe = cls.get_recipe(r_id)
            if recipe:
                item = recipe.to_dict()
                item["estimated_duration_beats"] = clip_length
                suggestions.append(item)

        return suggestions

    @classmethod
    def generate_points(
        cls,
        recipe_id: str,
        clip_length: float = 16.0,
        start_val: Optional[float] = None,
        end_val: Optional[float] = None,
        num_steps: int = 32
    ) -> List[Dict[str, float]]:
        """
        Generates mathematically precise normalized breakpoint points across the clip duration.
        """
        recipe = cls.get_recipe(recipe_id)
        s_val = start_val if start_val is not None else (recipe.start_val if recipe else 0.15)
        e_val = end_val if end_val is not None else (recipe.end_val if recipe else 0.85)
        c_type = recipe.curve_type if recipe else "exponential"

        points: List[Dict[str, float]] = []
        step_dur = clip_length / float(num_steps)

        for i in range(num_steps):
            t = float(i) * step_dur
            prog = float(i) / float(num_steps - 1) if num_steps > 1 else 0.0

            if c_type == "exponential":
                factor = prog ** 2.4
                val = s_val + (e_val - s_val) * factor
            elif c_type == "logarithmic":
                factor = prog ** 0.4
                val = s_val + (e_val - s_val) * factor
            elif c_type == "breathing":
                cycles = 2.0
                val = s_val + (e_val - s_val) * 0.5 * (1.0 + math.sin(2.0 * math.pi * cycles * prog - math.pi / 2.0))
            elif c_type == "vacuum_cut":
                vacuum_threshold = max(0.0, clip_length - 2.0)
                if t >= vacuum_threshold:
                    val = 0.0
                else:
                    val = s_val
            elif c_type == "washout":
                if i == num_steps - 1:
                    val = 0.0
                else:
                    factor = prog ** 2.2
                    val = s_val + (e_val - s_val) * factor
            elif c_type == "ease_in_out":
                factor = 0.5 * (1.0 - math.cos(prog * math.pi))
                val = s_val + (e_val - s_val) * factor
            else:
                val = s_val + (e_val - s_val) * prog

            points.append({
                "time": round(t, 4),
                "value": round(float(val), 4)
            })

        return points

    @classmethod
    def apply_recipe_to_clip(
        cls,
        conn: Any,
        track_index: int,
        clip_index: int,
        recipe_id: str,
        destination_time: Optional[float] = None,
        parameter: Optional[Union[str, int]] = None,
        start_val: Optional[float] = None,
        end_val: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Bakes an automation recipe into a Session clip's envelope and optionally duplicates it
        to the Arrangement timeline, creating tangible red vector breakpoints.
        """
        recipe = cls.get_recipe(recipe_id)
        target_param = parameter
        candidates = recipe.parameter_candidates if recipe else ["LP Freq", "Cutoff", "P1 Timbre", "Volume"]

        resolved_device_idx = 0
        resolved_param = target_param

        if resolved_param is None:
            try:
                t_info = conn.send_command("get_track_info", {"track_index": track_index})
                res_info = t_info.get("result", {}) if isinstance(t_info, dict) else {}
                devices = res_info.get("devices", [])
                for d_idx, dev in enumerate(devices):
                    params_res = conn.send_command("get_device_parameters", {
                        "track_index": track_index,
                        "device_index": d_idx
                    })
                    p_list = params_res.get("result", {}).get("parameters", []) if isinstance(params_res, dict) else []
                    for cand in candidates:
                        for p in p_list:
                            p_name = p.get("name", "")
                            if cand.lower() in p_name.lower() or p_name.lower() in cand.lower():
                                resolved_device_idx = d_idx
                                resolved_param = p.get("index", p_name)
                                break
                        if resolved_param is not None:
                            break
                    if resolved_param is not None:
                        break
            except Exception as scan_err:
                logger.warning(f"Parameter scan warning: {scan_err}")

        if resolved_param is None:
            resolved_param = candidates[0]

        clip_len = 16.0
        try:
            c_info = conn.send_command("get_clip_notes", {"track_index": track_index, "clip_index": clip_index})
        except Exception:
            pass

        points = cls.generate_points(
            recipe_id=recipe_id,
            clip_length=clip_len,
            start_val=start_val,
            end_val=end_val
        )

        inject_res = conn.send_command("create_arrangement_automation_envelope", {
            "track_index": track_index,
            "device_index": resolved_device_idx,
            "parameter": resolved_param,
            "clip_index": clip_index,
            "points": points
        })

        dup_res = None
        if destination_time is not None:
            dup_res = conn.send_command("duplicate_session_clip_to_arrangement", {
                "track_index": track_index,
                "clip_index": clip_index,
                "destination_time": float(destination_time)
            })

        return {
            "status": "SUCCESS",
            "recipe_applied": recipe_id,
            "recipe_name": recipe.name if recipe else recipe_id,
            "track_index": track_index,
            "clip_index": clip_index,
            "device_index": resolved_device_idx,
            "parameter": resolved_param,
            "points_count": len(points),
            "envelope_result": inject_res,
            "arrangement_duplicate": dup_res,
            "tangible_vector_active": True,
            "editable_with_A_key": True
        }

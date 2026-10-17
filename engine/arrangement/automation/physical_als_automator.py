# engine/arrangement/automation/physical_als_automator.py
r"""
Physical ALS Automation Injector:
Directly writes physical Ableton Live arrangement automation envelopes into the .als XML file.
Enforces Directives 5, 18, 23, and 30:
- Pre-drop / Pre-chorus micro-stops (silence vacuum cuts on bass and drums).
- Dynamic filter sweeps (lowpass cutoff opening on build-ups / transitions).
- Vocal & Lead volume riding (+1.5 dB in choruses, -1.0 dB in verses).
- Reverb / Delay washout build-ups snapping to dry on the downbeat.
- Panning automation for spatial movement.
"""

import gzip
import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger("PhysicalAlsAutomator")


class PhysicalAlsAutomator:
    """Injects authoritative physical automation envelopes directly into Ableton Live XML projects."""

    @classmethod
    def inject_arrangement_automations(
        cls,
        als_path: Path,
        sections: List[Dict[str, Any]],
        climax_beat: Optional[float] = None,
        bpm: float = 120.0
    ) -> Dict[str, Any]:
        """
        Parses the .als XML, locates AutomationTargets on tracks, and injects physical automation envelopes.
        """
        als_path = Path(als_path)
        if not als_path.exists():
            return {"status": "ERROR", "message": f"ALS file not found: {als_path}"}

        try:
            with gzip.open(als_path, "rb") as gz_in:
                tree = ET.parse(gz_in)
            root = tree.getroot()

            # Calculate section beat boundaries
            curr_beat = 0.0
            section_bounds = []
            for s in sections:
                bars = s.get("bars", 8)
                beats = float(bars * 4.0)
                section_bounds.append({
                    "name": s.get("name", "Section"),
                    "start_beat": curr_beat,
                    "end_beat": curr_beat + beats,
                    "bars": bars
                })
                curr_beat += beats

            total_beats = curr_beat

            # If climax_beat not given, find chorus or drop section
            if climax_beat is None:
                for sb in section_bounds:
                    s_low = sb["name"].lower()
                    if any(k in s_low for k in ["coro", "chorus", "drop", "clímax", "climax"]):
                        climax_beat = sb["start_beat"]
                        break
            if climax_beat is None:
                climax_beat = 32.0  # default bar 8

            injected_envelopes = 0
            tracks = root.findall(".//Tracks/*")

            for t_idx, t in enumerate(tracks):
                if t.tag not in ("MidiTrack", "AudioTrack", "MainTrack", "ReturnTrack"):
                    continue

                name_elem = t.find(".//Name/EffectiveName")
                t_name = name_elem.attrib.get("Value", f"Track_{t_idx}") if name_elem is not None else f"Track_{t_idx}"
                t_name_low = t_name.lower()

                auto_envs_parent = t.find(".//AutomationEnvelopes/Envelopes")
                if auto_envs_parent is None:
                    continue

                # -------------------------------------------------------------
                # 1. VOLUME AUTOMATION (Micro-Stops, Pre-Ducking & Climax Boost)
                # -------------------------------------------------------------
                vol_target = t.find(".//MixerDevice/Volume/AutomationTarget")
                if vol_target is not None:
                    vol_id = vol_target.attrib.get("Id")
                    if vol_id:
                        is_bass = any(k in t_name_low for k in ["bass", "808", "sub"])
                        is_drums = any(k in t_name_low for k in ["drum", "perc", "kick", "bombo", "batería", "bateria"])
                        is_lead = any(k in t_name_low for k in ["lead", "vocal", "guitar", "melodía", "melodia", "hook"])

                        events = []
                        # Baseline at -inf time
                        events.append({"id": "0", "time": "-63072000", "value": "0.85"})
                        events.append({"id": "1", "time": "0.0", "value": "0.85"})

                        # Section volume riding with Drop 2 Climax Boost
                        for sb in section_bounds:
                            s_name = sb["name"].lower()
                            s_start = sb["start_beat"]
                            is_d2 = "drop 2" in s_name or "2" in s_name
                            if any(k in s_name for k in ["coro", "chorus", "drop", "clímax", "climax"]):
                                # Drop 1 (+1.5 dB: 0.88) vs Drop 2 Grand Climax (+2.2 dB: 0.90)
                                target_val = "0.90" if is_d2 else ("0.88" if is_lead else "0.86")
                                events.append({"id": str(len(events)), "time": f"{s_start:.2f}", "value": target_val})
                            elif any(k in s_name for k in ["verso", "verse", "chanteo"]):
                                target_val = "0.82" if (is_bass or is_drums) else "0.80"
                                events.append({"id": str(len(events)), "time": f"{s_start:.2f}", "value": target_val})
                            elif any(k in s_name for k in ["puente", "bridge", "subida", "build"]):
                                events.append({"id": str(len(events)), "time": f"{s_start:.2f}", "value": "0.84"})

                        # Micro-Stop / Silence Vacuum with Exponential Pre-Ducking
                        if is_bass or is_drums:
                            for sb in section_bounds:
                                s_name = sb["name"].lower()
                                if any(k in s_name for k in ["coro", "chorus", "drop", "clímax", "climax"]):
                                    drop_start = sb["start_beat"]
                                    if drop_start > 8.0:
                                        # Pre-ducking curve across 2 beats before cut
                                        events.append({"id": str(len(events)), "time": f"{drop_start - 3.0:.2f}", "value": "0.85"})
                                        events.append({"id": str(len(events)), "time": f"{drop_start - 2.0:.2f}", "value": "0.72"})
                                        # Hard tension vacuum cut at drop_start - 1.5
                                        events.append({"id": str(len(events)), "time": f"{drop_start - 1.5:.2f}", "value": "0.0001"})
                                        events.append({"id": str(len(events)), "time": f"{drop_start - 0.05:.2f}", "value": "0.0001"})
                                        # Slam back in at full power on downbeat
                                        events.append({"id": str(len(events)), "time": f"{drop_start:.2f}", "value": "0.89"})

                        # Final Fade-out on Outro
                        if section_bounds:
                            last_sec = section_bounds[-1]
                            events.append({"id": str(len(events)), "time": f"{last_sec['start_beat']:.2f}", "value": "0.85"})
                            events.append({"id": str(len(events)), "time": f"{last_sec['end_beat']:.2f}", "value": "0.0001"})

                        cls._add_or_update_envelope_node(auto_envs_parent, vol_id, events)
                        injected_envelopes += 1

                # -------------------------------------------------------------
                # 2. FILTER CUTOFF AUTOMATION (Exponential J-Curves & Drop 2 Climax)
                # -------------------------------------------------------------
                filter_targets = cls._find_filter_automation_targets(t)
                for f_target_id, f_param_name in filter_targets:
                    f_events = []
                    f_events.append({"id": "0", "time": "-63072000", "value": "0.85"})
                    f_events.append({"id": "1", "time": "0.0", "value": "0.85"})

                    for sb in section_bounds:
                        s_name = sb["name"].lower()
                        s_start = sb["start_beat"]
                        s_end = sb["end_beat"]
                        is_d2 = "drop 2" in s_name or "2" in s_name

                        if any(k in s_name for k in ["puente", "bridge", "subida", "build", "pre"]):
                            # 8-step Exponential J-Curve (stays low, accelerates into vacuum)
                            n_steps = 8
                            for step_idx in range(n_steps + 1):
                                step_t = s_start + (s_end - s_start) * (step_idx / n_steps)
                                frac = step_idx / n_steps
                                curve_val = 0.18 + 0.80 * (frac ** 2.4)
                                f_events.append({"id": str(len(f_events)), "time": f"{step_t:.2f}", "value": f"{curve_val:.4f}"})
                        elif any(k in s_name for k in ["coro", "chorus", "drop", "clímax", "climax"]):
                            # Drop 1 (0.75 -> 0.95) vs Drop 2 Grand Climax (opens to 0.999)
                            top_val = "0.999" if is_d2 else "0.96"
                            f_events.append({"id": str(len(f_events)), "time": f"{s_start:.2f}", "value": "0.75"})
                            f_events.append({"id": str(len(f_events)), "time": f"{s_start + (s_end - s_start)*0.5:.2f}", "value": "0.89"})
                            f_events.append({"id": str(len(f_events)), "time": f"{s_end - 0.25:.2f}", "value": top_val})
                        elif any(k in s_name for k in ["break", "breakdown"]):
                            # Gritty underground Akai S1000 filtered breakbeat
                            f_events.append({"id": str(len(f_events)), "time": f"{s_start:.2f}", "value": "0.58"})
                            f_events.append({"id": str(len(f_events)), "time": f"{s_start + (s_end - s_start)*0.5:.2f}", "value": "0.66"})
                        elif any(k in s_name for k in ["verso", "verse", "intro", "outro"]):
                            f_events.append({"id": str(len(f_events)), "time": f"{s_start:.2f}", "value": "0.65"})

                    cls._add_or_update_envelope_node(auto_envs_parent, f_target_id, f_events)
                    injected_envelopes += 1

                # -------------------------------------------------------------
                # 3. SATURATION & DRIVE AUTOMATION (Drop 2 Climax Overdrive 0.85)
                # -------------------------------------------------------------
                sat_targets = cls._find_saturation_automation_targets(t)
                for s_target_id, s_param_name in sat_targets:
                    sat_events = []
                    sat_events.append({"id": "0", "time": "-63072000", "value": "0.35"})
                    sat_events.append({"id": "1", "time": "0.0", "value": "0.35"})
                    for sb in section_bounds:
                        s_name = sb["name"].lower()
                        s_start = sb["start_beat"]
                        s_end = sb["end_beat"]
                        is_d2 = "drop 2" in s_name or "2" in s_name

                        if any(k in s_name for k in ["coro", "chorus", "drop", "clímax", "climax"]):
                            # Drop 1 (0.72) vs Drop 2 Peak Overdrive (0.85)
                            peak_drive = "0.85" if is_d2 else "0.72"
                            sat_events.append({"id": str(len(sat_events)), "time": f"{s_start:.2f}", "value": peak_drive})
                            sat_events.append({"id": str(len(sat_events)), "time": f"{s_end - 0.25:.2f}", "value": peak_drive})
                        elif any(k in s_name for k in ["break", "breakdown"]):
                            sat_events.append({"id": str(len(sat_events)), "time": f"{s_start:.2f}", "value": "0.60"})
                        elif any(k in s_name for k in ["build", "subida"]):
                            sat_events.append({"id": str(len(sat_events)), "time": f"{s_start:.2f}", "value": "0.40"})
                            sat_events.append({"id": str(len(sat_events)), "time": f"{s_end:.2f}", "value": "0.68"})
                        else:
                            sat_events.append({"id": str(len(sat_events)), "time": f"{s_start:.2f}", "value": "0.35"})
                    cls._add_or_update_envelope_node(auto_envs_parent, s_target_id, sat_events)
                    injected_envelopes += 1

                # -------------------------------------------------------------
                # 4. STEREO WIDTH AUTOMATION (Monolithic Mono -> Festival Wide 1.65)
                # -------------------------------------------------------------
                width_targets = cls._find_width_automation_targets(t)
                for w_target_id, w_param_name in width_targets:
                    w_events = []
                    w_events.append({"id": "0", "time": "-63072000", "value": "1.0"})
                    w_events.append({"id": "1", "time": "0.0", "value": "1.0"})
                    for sb in section_bounds:
                        s_name = sb["name"].lower()
                        s_start = sb["start_beat"]
                        is_d2 = "drop 2" in s_name or "2" in s_name
                        if any(k in s_name for k in ["coro", "chorus", "drop", "clímax", "climax"]):
                            w_val = "1.65" if is_d2 else "1.45"
                            w_events.append({"id": str(len(w_events)), "time": f"{s_start:.2f}", "value": w_val})
                        elif any(k in s_name for k in ["verso", "verse", "intro"]):
                            w_events.append({"id": str(len(w_events)), "time": f"{s_start:.2f}", "value": "0.70"})
                        elif any(k in s_name for k in ["break", "breakdown"]):
                            w_events.append({"id": str(len(w_events)), "time": f"{s_start:.2f}", "value": "0.75"})
                        elif any(k in s_name for k in ["puente", "bridge"]):
                            w_events.append({"id": str(len(w_events)), "time": f"{s_start:.2f}", "value": "1.0"})
                    cls._add_or_update_envelope_node(auto_envs_parent, w_target_id, w_events)
                    injected_envelopes += 1

                # -------------------------------------------------------------
                # 5. STEREO PANORAMA AUTOMATION (3D Spatial Movement & Drop Centering)
                # -------------------------------------------------------------
                pan_target = t.find(".//MixerDevice/Panorama/AutomationTarget")
                if pan_target is not None:
                    pan_id = pan_target.attrib.get("Id")
                    if pan_id:
                        is_melodic = any(k in t_name_low for k in ["lead", "keys", "choir", "synth", "ear_candy", "fx"])
                        if is_melodic:
                            p_events = []
                            p_events.append({"id": "0", "time": "-63072000", "value": "0.0"})
                            p_events.append({"id": "1", "time": "0.0", "value": "0.0"})
                            for sb in section_bounds:
                                s_name = sb["name"].lower()
                                s_start = sb["start_beat"]
                                s_end = sb["end_beat"]
                                bars = sb["bars"]
                                if any(k in s_name for k in ["break", "breakdown"]):
                                    # 3D spatial rotation across breakdown bars (-0.42 Left to +0.42 Right)
                                    for bar_i in range(bars):
                                        b_t = s_start + float(bar_i * 4.0)
                                        pan_val = -0.42 if (bar_i % 2 == 0) else 0.42
                                        p_events.append({"id": str(len(p_events)), "time": f"{b_t:.2f}", "value": f"{pan_val:.3f}"})
                                elif any(k in s_name for k in ["build", "subida", "pre"]):
                                    # Accelerating ping-pong into vacuum stop
                                    for bar_i in range(bars):
                                        b_t = s_start + float(bar_i * 4.0)
                                        pan_val = 0.48 if (bar_i % 2 == 1) else -0.48
                                        p_events.append({"id": str(len(p_events)), "time": f"{b_t:.2f}", "value": f"{pan_val:.3f}"})
                                    p_events.append({"id": str(len(p_events)), "time": f"{s_end - 2.0:.2f}", "value": "0.0"})
                                elif any(k in s_name for k in ["drop", "clímax", "climax"]):
                                    p_events.append({"id": str(len(p_events)), "time": f"{s_start:.2f}", "value": "0.0"})

                            cls._add_or_update_envelope_node(auto_envs_parent, pan_id, p_events)
                            injected_envelopes += 1

                # -------------------------------------------------------------
                # 6. REVERB & DELAY WASHOUT (Buildup Swell -> Vacuum Snap to 0.0001)
                # -------------------------------------------------------------
                rd_targets = cls._find_reverb_and_delay_targets(t)
                for rd_id, rd_param_name in rd_targets:
                    rd_events = []
                    rd_events.append({"id": "0", "time": "-63072000", "value": "0.20"})
                    rd_events.append({"id": "1", "time": "0.0", "value": "0.20"})
                    for sb in section_bounds:
                        s_name = sb["name"].lower()
                        s_start = sb["start_beat"]
                        s_end = sb["end_beat"]
                        if any(k in s_name for k in ["puente", "bridge", "subida", "build", "pre"]):
                            # Massive swell across last 4 bars (beats s_start+16 to s_end)
                            rd_events.append({"id": str(len(rd_events)), "time": f"{s_start:.2f}", "value": "0.20"})
                            rd_events.append({"id": str(len(rd_events)), "time": f"{s_start + 16.0:.2f}", "value": "0.35"})
                            rd_events.append({"id": str(len(rd_events)), "time": f"{s_end - 2.5:.2f}", "value": "0.85"})
                            # Snap to dead dry in the vacuum silence
                            rd_events.append({"id": str(len(rd_events)), "time": f"{s_end - 2.0:.2f}", "value": "0.0001"})
                            rd_events.append({"id": str(len(rd_events)), "time": f"{s_end - 0.05:.2f}", "value": "0.0001"})
                        elif any(k in s_name for k in ["coro", "chorus", "drop", "clímax", "climax"]):
                            # Tight and punchy in drops
                            rd_events.append({"id": str(len(rd_events)), "time": f"{s_start:.2f}", "value": "0.15"})
                        elif any(k in s_name for k in ["outro"]):
                            # Infinite dissolve fadeout
                            rd_events.append({"id": str(len(rd_events)), "time": f"{s_start:.2f}", "value": "0.25"})
                            rd_events.append({"id": str(len(rd_events)), "time": f"{s_end:.2f}", "value": "0.95"})
                    cls._add_or_update_envelope_node(auto_envs_parent, rd_id, rd_events)
                    injected_envelopes += 1

            # Save back modified ALS XML
            with gzip.open(als_path, "wb") as gz_out:
                tree.write(gz_out, encoding="UTF-8", xml_declaration=True)

            logger.info(f"Physically injected {injected_envelopes} arrangement automation envelopes into {als_path.name}")
            return {
                "status": "SUCCESS",
                "als_path": str(als_path),
                "injected_envelopes": injected_envelopes,
                "sections_processed": len(sections),
                "climax_beat": climax_beat
            }

        except Exception as ex:
            logger.error(f"Error injecting physical automations into {als_path}: {ex}", exc_info=True)
            return {"status": "ERROR", "error": str(ex)}

    @classmethod
    def _has_envelope_for_target(cls, envelopes_parent: ET.Element, target_id: str) -> bool:
        """Checks if an envelope already exists targeting this AutomationTarget Id."""
        for env in envelopes_parent.findall("AutomationEnvelope"):
            p_elem = env.find(".//EnvelopeTarget/PointeeId")
            if p_elem is not None and p_elem.attrib.get("Value") == target_id:
                return True
        return False

    @classmethod
    def _find_filter_automation_targets(cls, track_elem: ET.Element) -> List[tuple]:
        """Finds AutomationTarget elements for filter cutoff / frequency parameters on devices."""
        targets = []
        for dev in track_elem.findall(".//DeviceChain/Devices/*"):
            # Check Eq8 frequency bands or AutoFilter frequency
            for p in dev.findall(".//*"):
                p_name = p.tag.lower()
                p_name_elem = p.find("UserName") or p.find("Name")
                if p_name_elem is not None:
                    p_name = p_name_elem.attrib.get("Value", p.tag).lower()
                target_elem = p.find("AutomationTarget")
                if target_elem is not None:
                    t_id = target_elem.attrib.get("Id")
                    if t_id and any(k in p_name for k in ["freq", "cutoff", "filter"]):
                        targets.append((t_id, p_name or "filter_freq"))
                        if len(targets) >= 1:
                            break
            if targets:
                break
        return targets

    @classmethod
    def _find_width_automation_targets(cls, track_elem: ET.Element) -> List[tuple]:
        """Finds AutomationTarget elements for stereo width parameters on devices."""
        targets = []
        for dev in track_elem.findall(".//DeviceChain/Devices/*"):
            for p in dev.findall(".//*"):
                p_name = p.tag.lower()
                p_name_elem = p.find("UserName") or p.find("Name")
                if p_name_elem is not None:
                    p_name = p_name_elem.attrib.get("Value", p.tag).lower()
                target_elem = p.find("AutomationTarget")
                if target_elem is not None:
                    t_id = target_elem.attrib.get("Id")
                    if t_id and any(k in p_name for k in ["width", "stereo width", "stereo_width"]):
                        targets.append((t_id, p_name or "width"))
                        if len(targets) >= 1:
                            break
            if targets:
                break
        return targets

    @classmethod
    def _find_saturation_automation_targets(cls, track_elem: ET.Element) -> List[tuple]:
        """Finds AutomationTarget elements for saturation, drive, and crunch parameters on devices."""
        targets = []
        for dev in track_elem.findall(".//DeviceChain/Devices/*"):
            for p in dev.findall(".//*"):
                p_name = p.tag.lower()
                p_name_elem = p.find("UserName") or p.find("Name")
                if p_name_elem is not None:
                    p_name = p_name_elem.attrib.get("Value", p.tag).lower()
                target_elem = p.find("AutomationTarget")
                if target_elem is not None:
                    t_id = target_elem.attrib.get("Id")
                    if t_id and any(k in p_name for k in ["drive", "crunch", "saturat", "overdrive", "distort", "boom"]):
                        targets.append((t_id, p_name or "drive"))
                        if len(targets) >= 1:
                            break
            if targets:
                break
        return targets

    @classmethod
    def _find_reverb_and_delay_targets(cls, track_elem: ET.Element) -> List[tuple]:
        """Finds AutomationTarget elements for Reverb and Delay washout parameters."""
        targets = []
        for dev in track_elem.findall(".//DeviceChain/Devices/*"):
            for p in dev.findall(".//*"):
                p_name = p.tag.lower()
                p_name_elem = p.find("UserName") or p.find("Name")
                if p_name_elem is not None:
                    p_name = p_name_elem.attrib.get("Value", p.tag).lower()
                target_elem = p.find("AutomationTarget")
                if target_elem is not None:
                    t_id = target_elem.attrib.get("Id")
                    if t_id and any(k in p_name for k in ["decay", "diffuse", "drywet", "dry/wet", "feedback"]):
                        targets.append((t_id, p_name or "reverb_delay"))
                        if len(targets) >= 2:
                            break
            if targets:
                break
        return targets

    @classmethod
    def _add_or_update_envelope_node(
        cls,
        parent: ET.Element,
        target_id: str,
        events: List[Dict[str, str]]
    ):
        """Constructs or updates an Ableton Live compliant AutomationEnvelope XML subtree."""
        target_env = None
        for env in parent.findall("AutomationEnvelope"):
            p_elem = env.find(".//EnvelopeTarget/PointeeId")
            if p_elem is not None and p_elem.attrib.get("Value") == target_id:
                target_env = env
                break

        if target_env is not None:
            events_node = target_env.find(".//Automation/Events")
            if events_node is not None:
                events_node.clear()
            else:
                auto = target_env.find("Automation")
                if auto is None:
                    auto = ET.SubElement(target_env, "Automation")
                events_node = ET.SubElement(auto, "Events")
        else:
            existing_envs = len(parent.findall("AutomationEnvelope"))
            envelope_id = str(existing_envs)
            target_env = ET.SubElement(parent, "AutomationEnvelope", {"Id": envelope_id})
            tgt = ET.SubElement(target_env, "EnvelopeTarget")
            ET.SubElement(tgt, "PointeeId", {"Value": target_id})
            auto = ET.SubElement(target_env, "Automation")
            events_node = ET.SubElement(auto, "Events")
            trans_node = ET.SubElement(auto, "AutomationTransformViewState")
            ET.SubElement(trans_node, "IsTransformPending", {"Value": "false"})
            ET.SubElement(trans_node, "TimeAndValueTransforms")

        sorted_events = sorted(events, key=lambda e: float(e["time"]))
        for idx, ev in enumerate(sorted_events):
            ET.SubElement(events_node, "FloatEvent", {
                "Id": str(idx),
                "Time": ev["time"],
                "Value": ev["value"]
            })

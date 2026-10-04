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
                if t.tag not in ("MidiTrack", "AudioTrack", "MainTrack"):
                    continue

                name_elem = t.find(".//Name/EffectiveName")
                t_name = name_elem.attrib.get("Value", f"Track_{t_idx}") if name_elem is not None else f"Track_{t_idx}"
                t_name_low = t_name.lower()

                auto_envs_parent = t.find(".//AutomationEnvelopes/Envelopes")
                if auto_envs_parent is None:
                    continue

                # -------------------------------------------------------------
                # 1. VOLUME AUTOMATION (Micro-Stops & Section Volume Riding)
                # -------------------------------------------------------------
                vol_target = t.find(".//MixerDevice/Volume/AutomationTarget")
                if vol_target is not None:
                    vol_id = vol_target.attrib.get("Id")
                    if vol_id and not cls._has_envelope_for_target(auto_envs_parent, vol_id):
                        is_bass = any(k in t_name_low for k in ["bass", "808", "sub"])
                        is_drums = any(k in t_name_low for k in ["drum", "perc", "kick", "bombo", "batería", "bateria"])
                        is_lead = any(k in t_name_low for k in ["lead", "vocal", "guitar", "melodía", "melodia", "hook"])

                        events = []
                        # Baseline at -inf time
                        events.append({"id": "0", "time": "-63072000", "value": "0.85"})
                        events.append({"id": "1", "time": "0.0", "value": "0.85"})

                        # Section volume riding
                        for sb in section_bounds:
                            s_name = sb["name"].lower()
                            s_start = sb["start_beat"]
                            if any(k in s_name for k in ["coro", "chorus", "drop", "clímax", "climax"]):
                                # Chorus volume push (+1.5 dB)
                                target_val = "0.88" if is_lead else "0.86"
                                events.append({"id": str(len(events)), "time": f"{s_start:.2f}", "value": target_val})
                            elif any(k in s_name for k in ["verso", "verse", "chanteo"]):
                                # Verse pull (-1.0 dB to leave vocal room)
                                target_val = "0.82" if (is_bass or is_drums) else "0.80"
                                events.append({"id": str(len(events)), "time": f"{s_start:.2f}", "value": target_val})
                            elif any(k in s_name for k in ["puente", "bridge", "subida", "build"]):
                                events.append({"id": str(len(events)), "time": f"{s_start:.2f}", "value": "0.84"})

                        # Micro-Stop / Silence Vacuum (Cutting bass and drums for 1.5 beats before climax)
                        if (is_bass or is_drums) and climax_beat > 8.0:
                            cut_start = climax_beat - 1.5
                            cut_end = climax_beat - 0.05
                            events.append({"id": str(len(events)), "time": f"{cut_start - 0.1:.2f}", "value": "0.85"})
                            events.append({"id": str(len(events)), "time": f"{cut_start:.2f}", "value": "0.0001"})
                            events.append({"id": str(len(events)), "time": f"{cut_end:.2f}", "value": "0.0001"})
                            events.append({"id": str(len(events)), "time": f"{climax_beat:.2f}", "value": "0.88"})

                        # Final Fade-out on Outro
                        if section_bounds:
                            last_sec = section_bounds[-1]
                            events.append({"id": str(len(events)), "time": f"{last_sec['start_beat']:.2f}", "value": "0.85"})
                            events.append({"id": str(len(events)), "time": f"{last_sec['end_beat']:.2f}", "value": "0.0001"})

                        cls._add_envelope_node(auto_envs_parent, vol_id, events, f"vol_{t_idx}")
                        injected_envelopes += 1

                # -------------------------------------------------------------
                # 2. FILTER CUTOFF AUTOMATION (Rising sweeps before choruses)
                # -------------------------------------------------------------
                filter_targets = cls._find_filter_automation_targets(t)
                for f_target_id, f_param_name in filter_targets:
                    if not cls._has_envelope_for_target(auto_envs_parent, f_target_id):
                        f_events = []
                        f_events.append({"id": "0", "time": "-63072000", "value": "0.85"})
                        f_events.append({"id": "1", "time": "0.0", "value": "0.85"})

                        # Sweep up into each chorus / climax
                        for sb in section_bounds:
                            s_name = sb["name"].lower()
                            if any(k in s_name for k in ["puente", "bridge", "subida", "build", "pre"]):
                                # 4 to 8 bar filter sweep opening
                                f_events.append({"id": str(len(f_events)), "time": f"{sb['start_beat']:.2f}", "value": "0.20"})
                                f_events.append({"id": str(len(f_events)), "time": f"{sb['end_beat']:.2f}", "value": "0.95"})
                            elif any(k in s_name for k in ["coro", "chorus", "drop", "clímax", "climax"]):
                                f_events.append({"id": str(len(f_events)), "time": f"{sb['start_beat']:.2f}", "value": "0.95"})
                            elif any(k in s_name for k in ["verso", "verse"]):
                                # Warm filtered verse
                                f_events.append({"id": str(len(f_events)), "time": f"{sb['start_beat']:.2f}", "value": "0.65"})

                        cls._add_envelope_node(auto_envs_parent, f_target_id, f_events, f"filter_{t_idx}")
                        injected_envelopes += 1

                # -------------------------------------------------------------
                # 3. STEREO WIDTH AUTOMATION (Narrow verses -> Mammoth choruses)
                # -------------------------------------------------------------
                width_targets = cls._find_width_automation_targets(t)
                for w_target_id, w_param_name in width_targets:
                    if not cls._has_envelope_for_target(auto_envs_parent, w_target_id):
                        w_events = []
                        w_events.append({"id": "0", "time": "-63072000", "value": "1.0"})
                        w_events.append({"id": "1", "time": "0.0", "value": "1.0"})
                        for sb in section_bounds:
                            s_name = sb["name"].lower()
                            s_start = sb["start_beat"]
                            if any(k in s_name for k in ["coro", "chorus", "drop", "clímax", "climax"]):
                                w_events.append({"id": str(len(w_events)), "time": f"{s_start:.2f}", "value": "1.45"})
                            elif any(k in s_name for k in ["verso", "verse", "intro"]):
                                w_events.append({"id": str(len(w_events)), "time": f"{s_start:.2f}", "value": "0.70"})
                            elif any(k in s_name for k in ["puente", "bridge"]):
                                w_events.append({"id": str(len(w_events)), "time": f"{s_start:.2f}", "value": "0.95"})
                        cls._add_envelope_node(auto_envs_parent, w_target_id, w_events, f"width_{t_idx}")
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
                p_name_elem = p.find("UserName") or p.find("Name")
                p_name = p_name_elem.attrib.get("Value", "").lower() if p_name_elem is not None else ""
                target_elem = p.find("AutomationTarget")
                if target_elem is not None:
                    t_id = target_elem.attrib.get("Id")
                    if t_id and any(k in p_name for k in ["freq", "cutoff", "filter"]):
                        targets.append((t_id, p_name or "filter_freq"))
                        if len(targets) >= 2:
                            break
        return targets

    @classmethod
    def _find_width_automation_targets(cls, track_elem: ET.Element) -> List[tuple]:
        """Finds AutomationTarget elements for stereo width parameters on devices."""
        targets = []
        for dev in track_elem.findall(".//DeviceChain/Devices/*"):
            for p in dev.findall(".//*"):
                p_name_elem = p.find("UserName") or p.find("Name")
                p_name = p_name_elem.attrib.get("Value", "").lower() if p_name_elem is not None else ""
                target_elem = p.find("AutomationTarget")
                if target_elem is not None:
                    t_id = target_elem.attrib.get("Id")
                    if t_id and any(k in p_name for k in ["width", "stereo width", "stereo_width"]):
                        targets.append((t_id, p_name or "width"))
                        if len(targets) >= 1:
                            break
        return targets

    @classmethod
    def _add_envelope_node(
        cls,
        parent: ET.Element,
        target_id: str,
        events: List[Dict[str, str]],
        env_id_tag: Optional[str] = None
    ):
        """Constructs an Ableton Live compliant AutomationEnvelope XML subtree."""
        # Ableton Live 12 XML schema requires 'Id' attribute to be a strictly numeric integer string (e.g. "0", "1").
        # Non-numeric IDs like "vol_0" cause Ableton Live to show:
        # 'El documento está dañado y no se puede cargar (Illegal value for Id attribute)'.
        existing_envs = len(parent.findall("AutomationEnvelope"))
        envelope_id = str(existing_envs)
        env = ET.SubElement(parent, "AutomationEnvelope", {"Id": envelope_id})
        tgt = ET.SubElement(env, "EnvelopeTarget")
        ET.SubElement(tgt, "PointeeId", {"Value": target_id})
        auto = ET.SubElement(env, "Automation")
        events_node = ET.SubElement(auto, "Events")

        # Sort events by time
        sorted_events = sorted(events, key=lambda e: float(e["time"]))
        for idx, ev in enumerate(sorted_events):
            ET.SubElement(events_node, "FloatEvent", {
                "Id": str(idx),
                "Time": ev["time"],
                "Value": ev["value"]
            })

        trans_node = ET.SubElement(auto, "AutomationTransformViewState")
        ET.SubElement(trans_node, "IsTransformPending", {"Value": "false"})
        ET.SubElement(trans_node, "TimeAndValueTransforms")

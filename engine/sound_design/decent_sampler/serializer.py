# engine/sound_design/decent_sampler/serializer.py
"""
Deterministic XML Serializer & Deserializer for Decent Sampler Presets.

Converts between InstrumentModel and .dspreset XML files.
Ensures deterministic tag ordering, clean indentation, and round-trip fidelity.
"""

from typing import Optional, Dict, Any, List, Tuple
import re
import xml.etree.ElementTree as ET
from xml.dom import minidom

from .model import (
    InstrumentModel,
    GroupModel,
    SampleZoneModel,
    EffectModel,
    ModulatorModel,
    BindingModel,
    UIModel,
    ControlModel,
)
from .schema import DecentSamplerSchema


class DSPresetSerializer:
    """
    Serializes InstrumentModel to valid UTF-8 .dspreset XML,
    and deserializes XML back to InstrumentModel.
    """

    @classmethod
    def serialize(cls, instrument: InstrumentModel) -> str:
        """Serializes an InstrumentModel to a formatted XML string."""
        root = ET.Element("DecentSampler")
        root.set("minVersion", instrument.min_version)
        root.set("pluginVersion", instrument.plugin_version)
        if instrument.volume != 1.0:
            root.set("volume", str(instrument.volume))
        if instrument.global_pan != 0.0:
            root.set("globalPan", str(instrument.global_pan))
        if instrument.global_tuning != 0.0:
            root.set("globalTuning", str(instrument.global_tuning))
        if instrument.glide_time != 0.0:
            root.set("glideTime", str(instrument.glide_time))
        if instrument.glide_mode != "legato":
            root.set("glideMode", instrument.glide_mode)

        # 1. <ui> Element
        ui_elem = ET.SubElement(root, "ui")
        ui_elem.set("width", str(instrument.ui.width))
        ui_elem.set("height", str(instrument.ui.height))
        if instrument.ui.bg_image:
            ui_elem.set("bgImage", instrument.ui.bg_image)

        if instrument.ui.controls:
            tab_elem = ET.SubElement(ui_elem, "tab")
            for ctrl in instrument.ui.controls:
                ctrl_elem = ET.SubElement(tab_elem, ctrl.control_type)
                ctrl_elem.set("x", str(ctrl.x))
                ctrl_elem.set("y", str(ctrl.y))
                ctrl_elem.set("width", str(ctrl.width))
                ctrl_elem.set("height", str(ctrl.height))
                ctrl_elem.set("label", ctrl.label)
                ctrl_elem.set("type", ctrl.type or "float")
                ctrl_elem.set("minValue", str(ctrl.min_value))
                ctrl_elem.set("maxValue", str(ctrl.max_value))
                ctrl_elem.set("value", str(ctrl.value))
                ctrl_elem.set("defaultValue", str(ctrl.default_value))
                ctrl_elem.set("textColor", ctrl.text_color)
                if ctrl.text_size:
                    ctrl_elem.set("textSize", str(ctrl.text_size))
                if ctrl.track_foreground_color:
                    ctrl_elem.set("trackForegroundColor", ctrl.track_foreground_color)
                if ctrl.track_background_color:
                    ctrl_elem.set("trackBackgroundColor", ctrl.track_background_color)
                ctrl_elem.set("valueType", ctrl.value_type)

                for b in ctrl.bindings:
                    b_elem = ET.SubElement(ctrl_elem, "binding")
                    cls._write_binding_attributes(b_elem, b)

        # 2. <groups> Element
        groups_elem = ET.SubElement(root, "groups")
        for group in instrument.groups:
            g_elem = ET.SubElement(groups_elem, "group")
            if group.tags:
                g_elem.set("tags", group.tags)
            if not group.enabled:
                g_elem.set("enabled", "false")
            if group.volume != 1.0:
                g_elem.set("volume", str(group.volume))
            if group.pan != 0.0:
                g_elem.set("pan", str(group.pan))
            if group.amp_vel_track != 1.0:
                g_elem.set("ampVelTrack", str(group.amp_vel_track))
            if not group.amp_env_enabled:
                g_elem.set("ampEnvEnabled", "false")
            else:
                g_elem.set("attack", str(group.attack))
                g_elem.set("decay", str(group.decay))
                g_elem.set("sustain", str(group.sustain))
                g_elem.set("release", str(group.release))

            if group.seq_mode != "always":
                g_elem.set("seqMode", group.seq_mode)
            if group.silenced_by_tags:
                g_elem.set("silencedByTags", group.silenced_by_tags)
                g_elem.set("silencingMode", group.silencing_mode)
                if group.silencing_decay > 0.0:
                    g_elem.set("silencingDecay", str(group.silencing_decay))

            # Samples
            for sample in group.samples:
                s_elem = ET.SubElement(g_elem, "sample")
                s_elem.set("path", sample.path)
                s_elem.set("rootNote", str(sample.root_note))
                s_elem.set("loNote", str(sample.lo_note))
                s_elem.set("hiNote", str(sample.hi_note))
                s_elem.set("loVel", str(sample.lo_vel))
                s_elem.set("hiVel", str(sample.hi_vel))

                if sample.tuning != 0.0:
                    s_elem.set("tuning", str(sample.tuning))
                if sample.volume != 1.0:
                    s_elem.set("volume", str(sample.volume))
                if sample.pan != 0.0:
                    s_elem.set("pan", str(sample.pan))
                if sample.trigger != "attack":
                    s_elem.set("trigger", sample.trigger)
                if sample.loop_enabled:
                    s_elem.set("loopEnabled", "true")
                    if sample.loop_start > 0:
                        s_elem.set("loopStart", str(sample.loop_start))
                    if sample.loop_end is not None:
                        s_elem.set("loopEnd", str(sample.loop_end))
                if sample.seq_mode != "always":
                    s_elem.set("seqMode", sample.seq_mode)
                    s_elem.set("seqPosition", str(sample.seq_position))
                    s_elem.set("seqLength", str(sample.seq_length))
                if sample.tags:
                    s_elem.set("tags", sample.tags)

            # Group Effects
            if group.effects:
                effs_elem = ET.SubElement(g_elem, "effects")
                for eff in group.effects:
                    cls._write_effect_element(effs_elem, eff)

        # 3. Global <effects>
        if instrument.effects:
            global_effs = ET.SubElement(root, "effects")
            for eff in instrument.effects:
                cls._write_effect_element(global_effs, eff)

        # 4. Global <modulators>
        if instrument.modulators:
            mods_elem = ET.SubElement(root, "modulators")
            for mod in instrument.modulators:
                m_elem = ET.SubElement(mods_elem, mod.mod_type)
                m_elem.set("shape", mod.shape)
                m_elem.set("frequency", str(mod.frequency))
                m_elem.set("modAmount", str(mod.mod_amount))
                m_elem.set("scope", mod.scope)
                m_elem.set("modBehavior", mod.mod_behavior)
                for b in mod.bindings:
                    b_elem = ET.SubElement(m_elem, "binding")
                    cls._write_binding_attributes(b_elem, b)

        # Format with pretty indentation
        raw_xml = ET.tostring(root, encoding="utf-8")
        parsed = minidom.parseString(raw_xml)
        pretty = parsed.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")
        # Remove extra empty lines sometimes produced by minidom
        cleaned = "\n".join([line for line in pretty.splitlines() if line.strip() != ""])
        return cleaned

    @classmethod
    def clean_xml_content(cls, xml_text: str) -> Tuple[str, List[str]]:
        """
        Pre-processes raw XML to be tolerant like JUCE C++:
        - Deduplicates attributes inside start tags (last occurrence wins, matching JUCE).
        - Strips accidental newlines and excess whitespace inside attribute values.
        Returns (cleaned_xml, list_of_corrections).
        """
        tag_pattern = re.compile(r'<([a-zA-Z0-9_\-]+)(\s+[^>]*?)(\/?)>', re.DOTALL)
        attr_pattern = re.compile(r'([a-zA-Z0-9_\-:]+)\s*=\s*([\"\'][^\"\']*?[\"\'])', re.DOTALL)
        corrections: List[str] = []

        def replacer(match):
            tag_name = match.group(1)
            attr_blob = match.group(2)
            closing = match.group(3)
            attrs = attr_pattern.findall(attr_blob)
            seen = {}
            for k, v in attrs:
                if k in seen:
                    corrections.append(
                        f"Deduplicated attribute '{k}' in <{tag_name}>: overwritten with '{v.strip()}'."
                    )
                seen[k] = v
            tag_str = f"<{tag_name}"
            for k, v in seen.items():
                clean_v = " ".join(v.split())
                if clean_v != v:
                    corrections.append(
                        f"Normalized whitespace in <{tag_name}> attribute '{k}'."
                    )
                tag_str += f" {k}={clean_v}"
            if closing:
                tag_str += " />"
            else:
                tag_str += ">"
            return tag_str

        cleaned_xml = tag_pattern.sub(replacer, xml_text)
        return cleaned_xml, corrections

    @classmethod
    def deserialize(cls, xml_content: str, tolerant: bool = True) -> InstrumentModel:
        """Parses a .dspreset XML string back into an InstrumentModel."""
        if tolerant:
            xml_content, _ = cls.clean_xml_content(xml_content)

        root = ET.fromstring(xml_content)
        if root.tag != DecentSamplerSchema.ROOT_TAG:
            raise ValueError(f"Expected root tag <DecentSampler>, got <{root.tag}>")

        instrument = InstrumentModel(
            min_version=root.get("minVersion", "1.0.0"),
            plugin_version=root.get("pluginVersion", "1"),
            volume=DecentSamplerSchema.parse_volume_string(root.get("volume", "1.0")),
            global_pan=float(root.get("globalPan", "0.0")),
            global_tuning=float(root.get("globalTuning", "0.0")),
            glide_time=float(root.get("glideTime", "0.0")),
            glide_mode=root.get("glideMode", "legato"),
        )

        # Parse <ui>
        ui_elem = root.find("ui")
        if ui_elem is not None:
            instrument.ui.width = int(ui_elem.get("width", "812"))
            instrument.ui.height = int(ui_elem.get("height", "375"))
            instrument.ui.bg_image = ui_elem.get("bgImage")

            for ctrl_elem in ui_elem.findall(".//labeled-knob"):
                ctrl = ControlModel(
                    control_type="labeled-knob",
                    label=ctrl_elem.get("label", ""),
                    x=int(ctrl_elem.get("x", "0")),
                    y=int(ctrl_elem.get("y", "0")),
                    width=int(ctrl_elem.get("width", "90")),
                    height=int(ctrl_elem.get("height", "90")),
                    min_value=float(ctrl_elem.get("minValue", "0.0")),
                    max_value=float(ctrl_elem.get("maxValue", "1.0")),
                    value=float(ctrl_elem.get("value", "1.0")),
                    default_value=float(ctrl_elem.get("defaultValue", "1.0")),
                    text_color=ctrl_elem.get("textColor", "FFFFFFFF"),
                    text_size=int(ctrl_elem.get("textSize")) if ctrl_elem.get("textSize") is not None else None,
                    track_foreground_color=ctrl_elem.get("trackForegroundColor"),
                    track_background_color=ctrl_elem.get("trackBackgroundColor"),
                    type=ctrl_elem.get("type", "float"),
                    value_type=ctrl_elem.get("valueType", "linear"),
                )
                for b_elem in ctrl_elem.findall("binding"):
                    ctrl.bindings.append(cls._parse_binding_element(b_elem))
                instrument.ui.controls.append(ctrl)

        # Parse <groups>
        groups_elem = root.find("groups")
        if groups_elem is not None:
            grp_vol_def = DecentSamplerSchema.parse_volume_string(groups_elem.get("volume", "1.0"))
            grp_pan_def = float(groups_elem.get("pan", "0.0"))
            grp_vel_track_def = float(groups_elem.get("ampVelTrack", "1.0"))
            grp_attack_def = float(groups_elem.get("attack", "0.001"))
            grp_decay_def = float(groups_elem.get("decay", "1.0"))
            grp_sustain_def = float(groups_elem.get("sustain", "1.0"))
            grp_release_def = float(groups_elem.get("release", "0.3"))
            grp_glide_time_def = float(groups_elem.get("glideTime", "0.0"))
            grp_glide_mode_def = groups_elem.get("glideMode", "legato")

            for g_elem in groups_elem.findall("group"):
                group = GroupModel(
                    name=g_elem.get("name", "Default Group"),
                    tags=g_elem.get("tags"),
                    enabled=g_elem.get("enabled", "true") == "true",
                    volume=DecentSamplerSchema.parse_volume_string(g_elem.get("volume")) if g_elem.get("volume") is not None else grp_vol_def,
                    pan=float(g_elem.get("pan")) if g_elem.get("pan") is not None else grp_pan_def,
                    amp_vel_track=float(g_elem.get("ampVelTrack")) if g_elem.get("ampVelTrack") is not None else grp_vel_track_def,
                    amp_env_enabled=g_elem.get("ampEnvEnabled", "true") == "true",
                    attack=float(g_elem.get("attack")) if g_elem.get("attack") is not None else grp_attack_def,
                    decay=float(g_elem.get("decay")) if g_elem.get("decay") is not None else grp_decay_def,
                    sustain=float(g_elem.get("sustain")) if g_elem.get("sustain") is not None else grp_sustain_def,
                    release=float(g_elem.get("release")) if g_elem.get("release") is not None else grp_release_def,
                    glide_time=float(g_elem.get("glideTime")) if g_elem.get("glideTime") is not None else grp_glide_time_def,
                    glide_mode=g_elem.get("glideMode") if g_elem.get("glideMode") is not None else grp_glide_mode_def,
                    seq_mode=g_elem.get("seqMode", "always"),
                    silenced_by_tags=g_elem.get("silencedByTags"),
                    silencing_mode=g_elem.get("silencingMode", "fast"),
                    silencing_decay=float(g_elem.get("silencingDecay", "0.0")),
                )

                for s_elem in g_elem.findall("sample"):
                    sample = SampleZoneModel(
                        path=s_elem.get("path", ""),
                        root_note=int(s_elem.get("rootNote", "60")),
                        lo_note=int(s_elem.get("loNote", "0")),
                        hi_note=int(s_elem.get("hiNote", "127")),
                        lo_vel=int(s_elem.get("loVel", "0")),
                        hi_vel=int(s_elem.get("hiVel", "127")),
                        tuning=float(s_elem.get("tuning", "0.0")),
                        volume=DecentSamplerSchema.parse_volume_string(s_elem.get("volume", "1.0")),
                        pan=float(s_elem.get("pan", "0.0")),
                        trigger=s_elem.get("trigger", "attack"),
                        loop_enabled=s_elem.get("loopEnabled", "false") == "true",
                        seq_mode=s_elem.get("seqMode", "always"),
                        seq_position=int(s_elem.get("seqPosition", "1")),
                        seq_length=int(s_elem.get("seqLength", "1")),
                        tags=s_elem.get("tags"),
                    )
                    group.add_sample(sample)

                # Group effects
                for eff_elem in g_elem.findall("./effects/effect"):
                    group.effects.append(cls._parse_effect_element(eff_elem))

                instrument.add_group(group)

        # Parse global <effects>
        for eff_elem in root.findall("./effects/effect"):
            instrument.add_effect(cls._parse_effect_element(eff_elem))

        # Parse global <modulators>
        for mod_elem in root.findall("./modulators/lfo"):
            mod = ModulatorModel(
                mod_type="lfo",
                shape=mod_elem.get("shape", "sine"),
                frequency=float(mod_elem.get("frequency", "1.0")),
                mod_amount=float(mod_elem.get("modAmount", "1.0")),
                scope=mod_elem.get("scope", "global"),
                mod_behavior=mod_elem.get("modBehavior", "set"),
            )
            for b_elem in mod_elem.findall("binding"):
                mod.bindings.append(cls._parse_binding_element(b_elem))
            instrument.add_modulator(mod)

        return instrument

    @classmethod
    def _write_effect_element(cls, parent: ET.Element, effect: EffectModel) -> None:
        eff_elem = ET.SubElement(parent, "effect")
        eff_elem.set("type", effect.type.lower())
        if effect.tags:
            eff_elem.set("tags", effect.tags)
        if not effect.enabled:
            eff_elem.set("enabled", "false")
        for k, v in effect.parameters.items():
            eff_elem.set(k, str(v))

    @classmethod
    def _parse_effect_element(cls, eff_elem: ET.Element) -> EffectModel:
        attribs = dict(eff_elem.attrib)
        eff_type = attribs.pop("type", "lowpass")
        tags = attribs.pop("tags", None)
        enabled = attribs.pop("enabled", "true") == "true"
        return EffectModel(
            type=eff_type,
            tags=tags,
            enabled=enabled,
            parameters=attribs,
        )

    @classmethod
    def _write_binding_attributes(cls, elem: ET.Element, binding: BindingModel) -> None:
        elem.set("type", binding.type)
        elem.set("level", binding.level)
        elem.set("parameter", binding.parameter)
        if binding.position is not None:
            elem.set("position", str(binding.position))
        if binding.tags:
            elem.set("tags", binding.tags)
        if binding.translation != "linear":
            elem.set("translation", binding.translation)
        if binding.translation_output_min is not None:
            elem.set("translationOutputMin", str(binding.translation_output_min))
        if binding.translation_output_max is not None:
            elem.set("translationOutputMax", str(binding.translation_output_max))

    @classmethod
    def _parse_binding_element(cls, b_elem: ET.Element) -> BindingModel:
        pos = b_elem.get("position")
        out_min = b_elem.get("translationOutputMin")
        out_max = b_elem.get("translationOutputMax")

        return BindingModel(
            type=b_elem.get("type", "amp"),
            level=b_elem.get("level", "instrument"),
            parameter=b_elem.get("parameter", "AMP_VOLUME"),
            position=int(pos) if pos is not None else None,
            tags=b_elem.get("tags"),
            translation=b_elem.get("translation", "linear"),
            translation_output_min=float(out_min) if out_min is not None else None,
            translation_output_max=float(out_max) if out_max is not None else None,
        )

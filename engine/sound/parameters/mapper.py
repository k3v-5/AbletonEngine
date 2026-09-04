"""
Parameter Translation Layer:
Maps high-level semantic sound parameters to concrete physical device parameters
across multiple target devices (EQ, Filter, Saturation, Reverb, Delay, Utility).
"""
from typing import Dict, List, Any
from .curves import ParameterCurve

class ParameterMapper:
    """Translates semantic parameters into multi-device parameter assignments."""

    @staticmethod
    def map_semantic_to_devices(param_name: str, value: float) -> List[Dict[str, Any]]:
        """
        Returns a list of device target bindings for a semantic parameter.
        Example: 'brightness' -> Filter Cutoff + EQ High Shelf + Saturation Tone.
        """
        norm = max(0.0, min(1.0, float(value)))
        bindings = []

        if param_name == "brightness":
            # 1. Filter Cutoff: 200 Hz to 18000 Hz (Logarithmic)
            cutoff_hz = ParameterCurve.logarithmic(norm, 200.0, 18000.0)
            bindings.append({"device": "DEVICE:PRIMARY_INSTRUMENT", "parameter": "Filter Frequency", "value": cutoff_hz})
            bindings.append({"device": "DEVICE:PRIMARY_INSTRUMENT", "parameter": "Cutoff", "value": cutoff_hz})
            # 2. EQ High Shelf: -12.0 dB to +6.0 dB (Linear)
            shelf_db = ParameterCurve.linear(norm, -12.0, 6.0)
            bindings.append({"device": "DEVICE:EQ", "parameter": "Gain 8", "value": shelf_db})
            # 3. Saturation Tone / Drive Color
            bindings.append({"device": "DEVICE:SATURATION", "parameter": "Tone", "value": norm})

        elif param_name == "space":
            # 1. Reverb Dry/Wet: 0% to 75%
            rw = ParameterCurve.linear(norm, 0.0, 75.0)
            bindings.append({"device": "DEVICE:REVERB", "parameter": "Dry/Wet", "value": rw})
            # 2. Reverb Decay: 0.4s to 6.0s
            decay = ParameterCurve.exponential(norm, 0.4, 6.0, 1.5)
            bindings.append({"device": "DEVICE:REVERB", "parameter": "Decay Time", "value": decay})
            # 3. Delay Dry/Wet: 0% to 45%
            dw = ParameterCurve.linear(norm, 0.0, 45.0)
            bindings.append({"device": "DEVICE:DELAY", "parameter": "Dry/Wet", "value": dw})

        elif param_name == "weight":
            # 1. Sub Bass / Low Shelf Boost: -6.0 dB to +8.0 dB
            low_db = ParameterCurve.linear(norm, -6.0, 8.0)
            bindings.append({"device": "DEVICE:EQ", "parameter": "Gain 1", "value": low_db})
            # 2. Compressor Threshold / Drive
            thresh = ParameterCurve.linear(norm, -12.0, -32.0)
            bindings.append({"device": "DEVICE:COMPRESSOR", "parameter": "Threshold", "value": thresh})

        elif param_name == "grit":
            # 1. Saturator Drive: 0.0 dB to 18.0 dB
            drive_db = ParameterCurve.linear(norm, 0.0, 18.0)
            bindings.append({"device": "DEVICE:SATURATION", "parameter": "Drive", "value": drive_db})
            # 2. Saturator Dry/Wet: 0% to 100%
            bindings.append({"device": "DEVICE:SATURATION", "parameter": "Dry/Wet", "value": norm * 100.0})

        elif param_name == "width":
            # 1. Utility Stereo Width: 0% (Mono) to 200% (Super-Wide)
            stereo_width = ParameterCurve.linear(norm, 0.0, 200.0)
            bindings.append({"device": "DEVICE:UTILITY", "parameter": "Width", "value": stereo_width})
            # If width < 0.05, enable Bass Mono
            if norm < 0.05:
                bindings.append({"device": "DEVICE:UTILITY", "parameter": "Bass Mono", "value": 1.0})

        elif param_name == "punch":
            # 1. Compressor Attack (fast for punch control): 30ms to 2ms
            att = ParameterCurve.inverse(norm, 2.0, 30.0)
            bindings.append({"device": "DEVICE:COMPRESSOR", "parameter": "Attack", "value": att})
            # 2. Drum Buss Boom/Drive
            bindings.append({"device": "DEVICE:COMPRESSOR", "parameter": "Drive", "value": norm * 10.0})

        return bindings

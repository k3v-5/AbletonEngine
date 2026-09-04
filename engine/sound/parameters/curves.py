"""
Parameter Curves:
Transfer functions translating [0.0, 1.0] semantic values to physical parameter units (Hz, dB, ms, %).
"""
import math
from typing import Callable

class ParameterCurve:
    @staticmethod
    def linear(val: float, min_val: float, max_val: float) -> float:
        return min_val + (max_val - min_val) * max(0.0, min(1.0, val))

    @staticmethod
    def exponential(val: float, min_val: float, max_val: float, curve_factor: float = 2.0) -> float:
        norm = max(0.0, min(1.0, val)) ** curve_factor
        return min_val + (max_val - min_val) * norm

    @staticmethod
    def logarithmic(val: float, min_val: float, max_val: float) -> float:
        """Logarithmic curve (ideal for frequency in Hz)."""
        norm = max(0.0001, min(1.0, val))
        log_min = math.log10(max(1.0, min_val))
        log_max = math.log10(max(1.0, max_val))
        interp = log_min + (log_max - log_min) * norm
        return 10.0 ** interp

    @staticmethod
    def inverse(val: float, min_val: float, max_val: float) -> float:
        norm = 1.0 - max(0.0, min(1.0, val))
        return min_val + (max_val - min_val) * norm

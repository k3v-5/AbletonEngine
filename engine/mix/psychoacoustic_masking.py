# engine/mix/psychoacoustic_masking.py
"""
Full-Spectrum Psychoacoustic Masking Auditor.
Implements Zwicker's 24 Critical Bark Bands and Auditory Spreading Functions
to evaluate real perceptual masking conflicts across all frequency ranges:
- Low-End (20-150 Hz): Kick vs Sub/Bass
- Low-Mids (200-600 Hz): Bass harmonics vs Keys/Guitars/Mud
- Mids & High-Mids (1-5 kHz): Vocals vs Lead Synths (Intelligibility)
- Air (8-16 kHz): Hi-hats vs Cymbals / Sibilance
Calculates exact Signal-to-Mask Ratio (SMR) and surgical dynamic EQ carving parameters.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import numpy as np


# 24 Bark Critical Bands (Zwicker & Fastl, ISO 532)
# (Center Frequency Hz, Lower Band Edge Hz, Upper Band Edge Hz)
BARK_BANDS_24 = [
    (50.0, 20.0, 100.0),        # Bark 1
    (150.0, 100.0, 200.0),      # Bark 2
    (250.0, 200.0, 300.0),      # Bark 3
    (350.0, 300.0, 400.0),      # Bark 4
    (450.0, 400.0, 510.0),      # Bark 5
    (570.0, 510.0, 630.0),      # Bark 6
    (700.0, 630.0, 770.0),      # Bark 7
    (840.0, 770.0, 920.0),      # Bark 8
    (1000.0, 920.0, 1080.0),    # Bark 9
    (1170.0, 1080.0, 1270.0),   # Bark 10
    (1370.0, 1270.0, 1480.0),   # Bark 11
    (1600.0, 1480.0, 1720.0),   # Bark 12
    (1850.0, 1720.0, 2000.0),   # Bark 13
    (2150.0, 2000.0, 2320.0),   # Bark 14
    (2500.0, 2320.0, 2700.0),   # Bark 15
    (2900.0, 2700.0, 3150.0),   # Bark 16
    (3400.0, 3150.0, 3700.0),   # Bark 17
    (4000.0, 3700.0, 4400.0),   # Bark 18
    (4800.0, 4400.0, 5300.0),   # Bark 19
    (5800.0, 5300.0, 6400.0),   # Bark 20
    (7000.0, 6400.0, 7700.0),   # Bark 21
    (8500.0, 7700.0, 9500.0),   # Bark 22
    (10500.0, 9500.0, 12000.0), # Bark 23
    (13500.0, 12000.0, 15500.0) # Bark 24
]


@dataclass
class PsychoacousticMaskingReport:
    """Comprehensive auditory masking analysis between two tracks."""
    masker_role: str
    target_role: str
    overall_masking_score: float  # [0.0 = completely unmasked, 1.0 = total severe masking]
    most_clashing_bark_band: int
    clash_center_freq_hz: float
    min_smr_db: float             # Lowest Signal-to-Mask Ratio (negative = inaudible)
    severely_masked_bands: List[int]
    recommended_eq_cuts: List[Dict[str, Any]]
    evidence: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "masker_role": self.masker_role,
            "target_role": self.target_role,
            "overall_masking_score": round(float(self.overall_masking_score), 3),
            "clash_center_freq_hz": round(float(self.clash_center_freq_hz), 1),
            "min_smr_db": round(float(self.min_smr_db), 1),
            "severely_masked_bands_count": len(self.severely_masked_bands),
            "recommended_eq_cuts": self.recommended_eq_cuts,
            "evidence": self.evidence
        }


class PsychoacousticMaskingAuditor:
    """Audits full-spectrum auditory masking using 24 Bark critical bands and spreading models."""

    @classmethod
    def compute_bark_energy_distribution(cls, audio: np.ndarray, sr: int) -> np.ndarray:
        """
        Calculates total energy in dB in each of the 24 Bark critical bands.
        Returns 1D array of shape (24,) with energy levels in dB.
        """
        if audio.ndim > 1:
            audio_mono = np.mean(audio, axis=1)
        else:
            audio_mono = audio.copy()

        n_samples = len(audio_mono)
        if n_samples < 256:
            return np.full(24, -96.0, dtype=np.float32)

        # Track absolute RMS level
        rms_val = float(np.sqrt(np.mean(audio_mono ** 2)) + 1e-12)
        rms_dbfs = float(20.0 * np.log10(max(1e-6, rms_val)))

        n_fft = min(8192, max(512, 1 << (n_samples - 1).bit_length()))
        windowed = audio_mono[:n_fft] * np.hanning(min(n_samples, n_fft))
        mag_spec = np.abs(np.fft.rfft(windowed, n=n_fft))
        freqs = np.fft.rfftfreq(n_fft, d=1.0 / sr)

        bark_energies_db = np.zeros(24, dtype=np.float32)
        total_spec_energy = float(np.sum(mag_spec ** 2)) + 1e-12

        for b_idx, (fc, flow, fhigh) in enumerate(BARK_BANDS_24):
            band_mask = (freqs >= flow) & (freqs < fhigh)
            if np.any(band_mask):
                band_pwr = float(np.sum(mag_spec[band_mask] ** 2))
                rel_band_db = float(10.0 * np.log10(max(1e-9, band_pwr / total_spec_energy)))
                # Absolute dBFS in critical band
                db_lvl = float(rms_dbfs + rel_band_db)
            else:
                db_lvl = -96.0
            bark_energies_db[b_idx] = float(np.clip(db_lvl, -96.0, 0.0))

        return bark_energies_db

    @classmethod
    def apply_auditory_spreading_function(cls, bark_energies_db: np.ndarray) -> np.ndarray:
        """
        Applies Zwicker psychoacoustic spreading function across adjacent Bark bands:
        - Lower frequencies spread upward at -24 dB/Bark
        - Higher frequencies spread downward at -27 dB/Bark
        Returns effective masking threshold curve in dB across 24 bands.
        """
        n_bands = len(bark_energies_db)
        masking_curve = np.full(n_bands, -96.0, dtype=np.float32)

        for i in range(n_bands):
            pwr_i = bark_energies_db[i]
            # Band self-masking threshold is ~ 12 to 18 dB below stimulus level
            self_threshold = pwr_i - 15.0
            masking_curve[i] = max(masking_curve[i], self_threshold)

            # Spreading downward (lower bands j < i)
            for j in range(i - 1, -1, -1):
                dist = i - j
                spread_val = self_threshold - (dist * 27.0)
                masking_curve[j] = max(masking_curve[j], spread_val)

            # Spreading upward (higher bands j > i)
            for j in range(i + 1, n_bands):
                dist = j - i
                spread_val = self_threshold - (dist * 24.0)
                masking_curve[j] = max(masking_curve[j], spread_val)

        return masking_curve

    @classmethod
    def audit_masking_conflict(
        cls,
        masker_audio: np.ndarray,
        target_audio: np.ndarray,
        sr: int,
        masker_role: str = "DRUMS",
        target_role: str = "BASS"
    ) -> PsychoacousticMaskingReport:
        """
        Audits spectral masking exerted by masker_audio onto target_audio.
        Calculates Signal-to-Mask Ratio (SMR) per critical band.
        """
        masker_bark = cls.compute_bark_energy_distribution(masker_audio, sr)
        target_bark = cls.compute_bark_energy_distribution(target_audio, sr)

        # Compute effective auditory masking threshold created by masker
        effective_mask = cls.apply_auditory_spreading_function(masker_bark)

        # SMR = Target Energy - Effective Masking Threshold
        # Negative SMR means target is psychoacoustically inaudible
        smr = target_bark - effective_mask

        # Masking occurs when masker is strong AND target is close to or below mask threshold
        severely_masked = []
        clashing_scores = []

        for b in range(24):
            # Masking only exists if both masker and target have audible energy in this band
            if masker_bark[b] > -45.0 and target_bark[b] > -55.0:
                if smr[b] < 0.0:        # Target is completely submerged
                    severely_masked.append(b)
                    clashing_scores.append(1.0 + abs(smr[b]) / 20.0)
                elif smr[b] < 6.0:      # Heavy clash / muddy masking
                    severely_masked.append(b)
                    clashing_scores.append((6.0 - smr[b]) / 6.0)
                else:
                    clashing_scores.append(0.0)
            else:
                clashing_scores.append(0.0)

        overall_score = float(np.clip(np.mean(clashing_scores) * 2.0, 0.0, 1.0))
        worst_band = int(np.argmax(clashing_scores))
        clash_freq = float(BARK_BANDS_24[worst_band][0])
        min_smr = float(np.min(smr))

        # Generate surgical recommendations
        recommended_cuts = []
        evidence = []

        if len(severely_masked) > 0:
            evidence.append(
                f"Severe auditory masking detected in {len(severely_masked)} critical Bark bands. "
                f"Worst collision at Bark {worst_band + 1} ({clash_freq} Hz) with SMR of {round(min_smr, 1)} dB."
            )
            # Recommend surgical dynamic EQ cut on the masker (or ducking)
            cut_db = float(np.clip(abs(min_smr) * 0.5 + 2.0, 2.0, 6.0))
            recommended_cuts.append({
                "target_track": masker_role,
                "filter_type": "Bell / Dynamic Notch",
                "center_freq_hz": clash_freq,
                "q_factor": 2.5,
                "gain_reduction_db": round(cut_db, 1),
                "action": f"Apply surgical dynamic notch on {masker_role} around {int(clash_freq)} Hz to unmask {target_role}."
            })
        else:
            evidence.append("No critical psychoacoustic masking detected. Both signals maintain clear auditory separation.")

        return PsychoacousticMaskingReport(
            masker_role=masker_role,
            target_role=target_role,
            overall_masking_score=overall_score,
            most_clashing_bark_band=worst_band + 1,
            clash_center_freq_hz=clash_freq,
            min_smr_db=min_smr,
            severely_masked_bands=severely_masked,
            recommended_eq_cuts=recommended_cuts,
            evidence=evidence
        )

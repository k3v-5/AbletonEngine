"""
Unit & Acceptance Test Suite for ITU-R BS.1770-5 and Delivery Profile Separation (HITO 1 — DOCUMENTO 04).
Verifies:
- Strict architectural separation: Audio -> LoudnessAnalyzer -> LoudnessMeasurement -> LoudnessProfile.evaluate() -> ProfileCompliance.
- Typed and immutable contracts: MeasurementMetadata, LoudnessMeasurement, LoudnessProfile, ProfileCompliance.
- Elimination of target duplication across mix and mastering domains.
- Numeric validation & finite value enforcement (rejection of NaN/Inf).
- Exact boundary tests for LUFS, True Peak, and LRA.
- Side-effect-free pure deterministic evaluation.
- Inter-sample True Peak detection (sample_peak ≈ -0.2 dBFS, true_peak > +0.3 dBTP).
- Multi-profile independent evaluation of a single measurement without re-running DSP.
- Central registry resolution and UnknownLoudnessProfileError.
- Complete backward compatibility with existing system consumers.
"""
import unittest
import math
import json
from dataclasses import FrozenInstanceError
import numpy as np

from engine.mix.loudness_standards import (
    ProfileType,
    MeasurementStatus,
    MeasurementWindow,
    ChannelLayout,
    MeasurementMetadata,
    LoudnessMeasurement,
    LoudnessProfile,
    ProfileCompliance,
    LoudnessComplianceResult,
    ProfileEvaluationResult,
    ProfileRegistry,
    LOUDNESS_PROFILES,
    get_loudness_profile,
    list_loudness_profiles,
    UnknownLoudnessProfileError,
    EBU_R128,
    STREAMING,
    CLUB
)
from engine.mix.loudness_analyzer import LoudnessAnalyzer
from engine.mastering.loudness_target import LoudnessTargetCalculator, DELIVERY_SPECS
from engine.mastering.models import DeliveryTarget
from engine.mastering.true_peak import TruePeakEngine


class TestLoudnessProfileSeparation(unittest.TestCase):
    """GATE 1 Test Suite: PASO 04 — Loudness & Profile Separation."""

    def setUp(self):
        self.sr = 44100
        self.duration = 3.0
        self.t = np.arange(int(self.sr * self.duration)) / self.sr

    # --------------------------------------------------------------------------
    # 1. Contratos de Datos (Section 38)
    # --------------------------------------------------------------------------

    def test_01_metadata_contract_and_defaults(self):
        """1. MeasurementMetadata con defaults canónicos, extensiones y validación."""
        meta = MeasurementMetadata()
        self.assertEqual(meta.standard, "ITU-R BS.1770-5")
        self.assertEqual(meta.standard_version, "BS.1770-5 (2023)")
        self.assertEqual(meta.algorithm_version, "1.0.0")
        self.assertEqual(meta.sample_rate, 44100)
        self.assertEqual(meta.bit_depth, 24)
        self.assertEqual(meta.channel_layout, "stereo")
        self.assertEqual(meta.duration_seconds, 0.0)
        self.assertEqual(meta.measurement_window, "integrated")
        self.assertEqual(meta.channels, 2)
        self.assertEqual(meta.true_peak_method, "4x_sinc_fir_annex2")
        self.assertTrue(meta.gating_enabled)

        # Inmutabilidad
        with self.assertRaises(FrozenInstanceError):
            meta.sample_rate = 48000

    def test_02_metadata_validation_errors(self):
        """2. MeasurementMetadata rechaza valores negativos, no finitos o vacíos."""
        with self.assertRaises(ValueError):
            MeasurementMetadata(sample_rate=0)
        with self.assertRaises(ValueError):
            MeasurementMetadata(sample_rate=-44100)
        with self.assertRaises(ValueError):
            MeasurementMetadata(bit_depth=0)
        with self.assertRaises(ValueError):
            MeasurementMetadata(duration_seconds=-0.5)
        with self.assertRaises(ValueError):
            MeasurementMetadata(duration_seconds=float("nan"))
        with self.assertRaises(ValueError):
            MeasurementMetadata(duration_seconds=float("inf"))
        with self.assertRaises(ValueError):
            MeasurementMetadata(channel_layout="")
        with self.assertRaises(ValueError):
            MeasurementMetadata(standard="   ")
        with self.assertRaises(ValueError):
            MeasurementMetadata(measurement_window="unsupported_window")

    def test_03_measurement_contract_and_finite_validation(self):
        """3. LoudnessMeasurement inmutable rechaza NaN e Inf y provee ambos alias true_peak."""
        meta = MeasurementMetadata()
        meas = LoudnessMeasurement(
            integrated_lufs=-14.0,
            short_term_lufs=-13.5,
            momentary_lufs=-12.8,
            loudness_range_lra=6.0,
            true_peak_dbtp=-1.2,
            sample_peak_dbfs=-1.8,
            crest_factor_db=10.0,
            measurement_valid=True,
            metadata=meta,
            status=MeasurementStatus.VALID
        )
        self.assertEqual(meas.integrated_lufs, -14.0)
        self.assertEqual(meas.true_peak_dbtp, -1.2)
        self.assertEqual(meas.true_peak_dbfs, -1.2)
        self.assertTrue(meas.measurement_valid)
        self.assertEqual(meas.status, MeasurementStatus.VALID)

        # Inmutabilidad
        with self.assertRaises(FrozenInstanceError):
            meas.integrated_lufs = -10.0

        # Rechazo de NaN e Inf (Section 31)
        with self.assertRaises(ValueError):
            LoudnessMeasurement(
                integrated_lufs=float("nan"),
                short_term_lufs=-14.0,
                momentary_lufs=-14.0,
                loudness_range_lra=5.0,
                true_peak_dbtp=-1.0,
                metadata=meta
            )
        with self.assertRaises(ValueError):
            LoudnessMeasurement(
                integrated_lufs=-14.0,
                short_term_lufs=float("inf"),
                momentary_lufs=-14.0,
                loudness_range_lra=5.0,
                true_peak_dbtp=-1.0,
                metadata=meta
            )

    def test_04_profile_compliance_contract(self):
        """4. ProfileCompliance con campos obligatorios de Documento 04 y alias backward-compatible."""
        res = ProfileCompliance(
            profile_name="STREAMING",
            compliant=True,
            loudness_pass=True,
            true_peak_pass=True,
            lra_pass=True,
            clipping_pass=True,
            reasons=(),
            measured_lufs=-14.2,
            target_lufs=-14.0,
            loudness_delta_lu=-0.2,
            measured_true_peak_dbtp=-1.2,
            max_true_peak_dbtp=-1.0
        )
        self.assertTrue(res.compliant)
        self.assertTrue(res.loudness_pass)
        self.assertTrue(res.true_peak_pass)
        self.assertTrue(res.lra_pass)
        self.assertTrue(res.clipping_pass)
        self.assertEqual(res.measured_lufs, -14.2)
        self.assertEqual(res.target_lufs, -14.0)
        self.assertEqual(res.loudness_delta_lu, -0.2)
        self.assertEqual(res.measured_true_peak_dbtp, -1.2)
        self.assertEqual(res.max_true_peak_dbtp, -1.0)

        # Backward compatibility properties
        self.assertTrue(res.profile_compliant)
        self.assertTrue(res.target_met)
        self.assertTrue(res.true_peak_safe)
        self.assertTrue(res.lra_compliant)
        self.assertEqual(res.lufs_delta, -0.2)
        self.assertAlmostEqual(res.true_peak_margin_db, 0.2, places=3)
        self.assertEqual(len(res.violations), 0)

    # --------------------------------------------------------------------------
    # 2. Pruebas de Frontera en Perfiles (Section 39)
    # --------------------------------------------------------------------------

    def test_05_profile_boundary_lufs(self):
        """5. Pruebas de frontera inclusiva para LUFS: -15.0 PASS, -13.0 PASS, -15.000001 FAIL, -12.999999 FAIL."""
        def make_meas(lufs):
            return LoudnessMeasurement(
                integrated_lufs=lufs,
                short_term_lufs=lufs,
                momentary_lufs=lufs,
                loudness_range_lra=5.0,
                true_peak_dbtp=-1.5,
                sample_peak_dbfs=-2.0,
                crest_factor_db=8.0,
                measurement_valid=True
            )

        self.assertTrue(STREAMING.evaluate(make_meas(-15.0)).loudness_pass)
        self.assertTrue(STREAMING.evaluate(make_meas(-14.0)).loudness_pass)
        self.assertTrue(STREAMING.evaluate(make_meas(-13.0)).loudness_pass)

        # Epsilon breaches
        self.assertFalse(STREAMING.evaluate(make_meas(-15.000001)).loudness_pass)
        self.assertFalse(STREAMING.evaluate(make_meas(-12.999999)).loudness_pass)

    def test_06_profile_boundary_true_peak(self):
        """6. Pruebas de frontera para True Peak: max = -1.0 dBTP."""
        def make_meas(tp):
            return LoudnessMeasurement(
                integrated_lufs=-14.0,
                short_term_lufs=-14.0,
                momentary_lufs=-14.0,
                loudness_range_lra=5.0,
                true_peak_dbtp=tp,
                sample_peak_dbfs=-2.0,
                crest_factor_db=8.0,
                measurement_valid=True
            )

        self.assertTrue(STREAMING.evaluate(make_meas(-1.001)).true_peak_pass)
        self.assertTrue(STREAMING.evaluate(make_meas(-1.000)).true_peak_pass)
        self.assertFalse(STREAMING.evaluate(make_meas(-0.999)).true_peak_pass)

    def test_07_profile_boundary_lra(self):
        """7. Pruebas de frontera para LRA en EBU R 128 (max = 14.0 LU)."""
        def make_meas(lra):
            return LoudnessMeasurement(
                integrated_lufs=-23.0,
                short_term_lufs=-23.0,
                momentary_lufs=-23.0,
                loudness_range_lra=lra,
                true_peak_dbtp=-1.5,
                sample_peak_dbfs=-2.0,
                crest_factor_db=10.0,
                measurement_valid=True
            )

        self.assertTrue(EBU_R128.evaluate(make_meas(13.999)).lra_pass)
        self.assertTrue(EBU_R128.evaluate(make_meas(14.000)).lra_pass)
        self.assertFalse(EBU_R128.evaluate(make_meas(14.001)).lra_pass)

    # --------------------------------------------------------------------------
    # 3. True Peak Inter-Sample y Distinción Obligatoria (Section 40)
    # --------------------------------------------------------------------------

    def test_08_inter_sample_true_peak_near_minus_02_dbfs(self):
        """
        8. Distinción obligatoria entre Sample Peak y True Peak:
        Señal donde sample_peak ≈ -0.2 dBFS y true_peak > +0.3 dBTP.
        """
        # Seno a fs/4 (11025 Hz) con fase 0.65 rad y amplitud 1.23:
        # Picos discretos caen en ~0.979 (-0.18 dBFS ≈ -0.2 dBFS).
        # Reconstrucción continua recupera la amplitud 1.23 (+1.8 dBTP > +0.3 dBTP).
        freq = self.sr / 4.0
        amp = 1.23
        phase = 0.65
        x = amp * np.sin(2 * np.pi * freq * self.t + phase)
        audio = np.array([x])

        meas = LoudnessAnalyzer.measure(audio, sr=self.sr)

        self.assertAlmostEqual(meas.sample_peak_dbfs, -0.18, delta=0.1,
                               msg=f"Sample peak debe ser ≈ -0.2 dBFS, obtenido: {meas.sample_peak_dbfs}")
        self.assertGreater(meas.true_peak_dbtp, 0.3,
                           msg=f"True Peak debe ser > +0.3 dBTP, obtenido: {meas.true_peak_dbtp}")
        self.assertGreater(meas.true_peak_dbtp - meas.sample_peak_dbfs, 1.0,
                           "Debe existir una elevación inter-sample medible mayor a 1.0 dB")

    # --------------------------------------------------------------------------
    # 4. Separación Arquitectónica e Independencia de Perfiles (Sections 41-43)
    # --------------------------------------------------------------------------

    def test_09_measurement_independent_of_profile(self):
        """9. LoudnessAnalyzer.measure() no depende de ningún perfil ni intención comercial."""
        # Generar señal de audio
        sine = 0.5 * np.sin(2 * np.pi * 1000.0 * self.t)
        stereo_audio = np.stack([sine, sine], axis=0)

        # Medir sin perfil
        meas = LoudnessAnalyzer.measure(stereo_audio, sr=self.sr)
        self.assertTrue(meas.measurement_valid)
        self.assertIsInstance(meas, LoudnessMeasurement)
        # El analizador no toma decisiones de masterización
        self.assertFalse(hasattr(meas, "compliant"))
        self.assertFalse(hasattr(meas, "profile_compliant"))

    def test_10_single_measurement_evaluated_across_multiple_profiles(self):
        """
        10. La misma medición se evalúa independientemente contra EBU_R128, STREAMING y CLUB
        sin volver a ejecutar procesamiento DSP.
        """
        # Señal medida una sola vez: -14.2 LUFS, -1.2 dBTP, LRA 6.0 LU
        meas = LoudnessMeasurement(
            integrated_lufs=-14.2,
            short_term_lufs=-13.8,
            momentary_lufs=-13.5,
            loudness_range_lra=6.0,
            true_peak_dbtp=-1.2,
            sample_peak_dbfs=-1.8,
            crest_factor_db=10.0,
            measurement_valid=True
        )

        r128 = EBU_R128.evaluate(meas)
        streaming = STREAMING.evaluate(meas)
        club = CLUB.evaluate(meas)

        # STREAMING: pasa (-14.2 está en -14 ± 1.0)
        self.assertTrue(streaming.compliant)
        self.assertEqual(streaming.profile_name, "STREAMING")

        # EBU R 128: falla (excede -23.0 ± 0.5)
        self.assertFalse(r128.compliant)
        self.assertEqual(r128.profile_name, "EBU_R128")
        self.assertFalse(r128.loudness_pass)

        # CLUB: falla (-14.2 está por debajo de -7.5 ± 1.0)
        self.assertFalse(club.compliant)
        self.assertEqual(club.profile_name, "CLUB")
        self.assertFalse(club.loudness_pass)

    def test_11_measurement_immutable_after_sequential_evaluations(self):
        """11. evaluate(profile_A) seguido de evaluate(profile_B) no muta la medición."""
        meas = LoudnessMeasurement(
            integrated_lufs=-14.0,
            short_term_lufs=-13.5,
            momentary_lufs=-13.0,
            loudness_range_lra=5.0,
            true_peak_dbtp=-1.2,
            sample_peak_dbfs=-1.5,
            crest_factor_db=9.0,
            measurement_valid=True
        )
        before_dict = meas.to_dict()

        _ = STREAMING.evaluate(meas)
        _ = EBU_R128.evaluate(meas)
        _ = CLUB.evaluate(meas)

        after_dict = meas.to_dict()
        self.assertEqual(before_dict, after_dict)

    # --------------------------------------------------------------------------
    # 5. Tests de Invalidez e Independencia de Métricas (Sections 44-46)
    # --------------------------------------------------------------------------

    def test_12_invalid_measurement_always_fails_compliance(self):
        """12. measurement_valid=False produce compliant=False independientemente de los números."""
        meas_invalid = LoudnessMeasurement(
            integrated_lufs=-14.0,
            short_term_lufs=-14.0,
            momentary_lufs=-14.0,
            loudness_range_lra=5.0,
            true_peak_dbtp=-2.0,
            sample_peak_dbfs=-2.5,
            crest_factor_db=10.0,
            measurement_valid=False,
            status=MeasurementStatus.NUMERIC_FAILURE
        )
        res = STREAMING.evaluate(meas_invalid)
        self.assertFalse(res.compliant)
        self.assertFalse(res.loudness_pass)
        self.assertFalse(res.true_peak_pass)
        self.assertTrue(any("MEASUREMENT_INVALID" in r for r in res.reasons))

    def test_13_independent_loudness_pass_and_true_peak_fail(self):
        """13. Loudness cumple pero True Peak excede: compliant=False, loudness_pass=True, true_peak_pass=False."""
        meas = LoudnessMeasurement(
            integrated_lufs=-14.0,  # Loudness perfecto
            short_term_lufs=-13.5,
            momentary_lufs=-13.0,
            loudness_range_lra=5.0,
            true_peak_dbtp=-0.5,   # Excede techo de -1.0 dBTP
            sample_peak_dbfs=-0.8,
            crest_factor_db=10.0,
            measurement_valid=True
        )
        res = STREAMING.evaluate(meas)
        self.assertFalse(res.compliant)
        self.assertTrue(res.loudness_pass)
        self.assertFalse(res.true_peak_pass)
        self.assertTrue(any("TRUE_PEAK_EXCEEDED" in r for r in res.reasons))

    def test_14_lra_below_min_and_above_max(self):
        """14. LRA evaluado contra límites inferior, superior o no restringido."""
        # 1. Below minimum en STREAMING (min = 4.0 LU)
        meas_low = LoudnessMeasurement(
            integrated_lufs=-14.0,
            short_term_lufs=-14.0,
            momentary_lufs=-14.0,
            loudness_range_lra=2.5,
            true_peak_dbtp=-1.5,
            sample_peak_dbfs=-2.0,
            crest_factor_db=8.0,
            measurement_valid=True
        )
        res_low = STREAMING.evaluate(meas_low)
        self.assertFalse(res_low.compliant)
        self.assertFalse(res_low.lra_pass)
        self.assertTrue(any("LRA_BELOW_MINIMUM" in r for r in res_low.reasons))

        # 2. Above maximum en EBU R 128 (max = 14.0 LU)
        meas_high = LoudnessMeasurement(
            integrated_lufs=-23.0,
            short_term_lufs=-23.0,
            momentary_lufs=-23.0,
            loudness_range_lra=16.0,
            true_peak_dbtp=-1.5,
            sample_peak_dbfs=-2.0,
            crest_factor_db=10.0,
            measurement_valid=True
        )
        res_high = EBU_R128.evaluate(meas_high)
        self.assertFalse(res_high.compliant)
        self.assertFalse(res_high.lra_pass)
        self.assertTrue(any("LRA_ABOVE_MAXIMUM" in r for r in res_high.reasons))

        # 3. LRA within range
        meas_ok = LoudnessMeasurement(
            integrated_lufs=-14.0,
            short_term_lufs=-14.0,
            momentary_lufs=-14.0,
            loudness_range_lra=6.0,
            true_peak_dbtp=-1.5,
            sample_peak_dbfs=-2.0,
            crest_factor_db=8.0,
            measurement_valid=True
        )
        res_ok = STREAMING.evaluate(meas_ok)
        self.assertTrue(res_ok.compliant)
        self.assertTrue(res_ok.lra_pass)

    # --------------------------------------------------------------------------
    # 6. Central Registry y Unificación (Sections 47, 50, 51)
    # --------------------------------------------------------------------------

    def test_15_unknown_profile_raises_error(self):
        """15. Solicitar un perfil no registrado dispara UnknownLoudnessProfileError."""
        with self.assertRaises(UnknownLoudnessProfileError):
            get_loudness_profile("DOES_NOT_EXIST")

        with self.assertRaises(UnknownLoudnessProfileError):
            ProfileRegistry.get("DOES_NOT_EXIST")

    def test_16_single_source_of_truth_unification(self):
        """
        16. Unificación formal: LoudnessTargetCalculator y TruePeakEngine consumen
        directamente de loudness_standards sin duplicación de valores numéricos.
        """
        # Streaming target coherente
        self.assertEqual(LoudnessTargetCalculator.get_target_lufs(DeliveryTarget.STREAMING), -14.0)
        self.assertEqual(STREAMING.target_lufs, -14.0)
        self.assertEqual(DELIVERY_SPECS[DeliveryTarget.STREAMING]["target_lufs"], -14.0)
        self.assertEqual(TruePeakEngine.get_ceiling(DeliveryTarget.STREAMING), -1.0)
        self.assertEqual(STREAMING.max_true_peak_dbtp, -1.0)

        # Club target coherente
        self.assertEqual(LoudnessTargetCalculator.get_target_lufs(DeliveryTarget.CLUB), -7.5)
        self.assertEqual(CLUB.target_lufs, -7.5)
        self.assertEqual(DELIVERY_SPECS[DeliveryTarget.CLUB]["target_lufs"], -7.5)
        self.assertEqual(TruePeakEngine.get_ceiling(DeliveryTarget.CLUB), -0.3)
        self.assertEqual(CLUB.max_true_peak_dbtp, -0.3)

    def test_17_deterministic_serialization(self):
        """17. Serialización determinista a JSON sin punteros ni campos volátiles."""
        meas = LoudnessMeasurement(
            integrated_lufs=-14.23,
            short_term_lufs=-13.81,
            momentary_lufs=-12.97,
            loudness_range_lra=7.4,
            true_peak_dbtp=-0.91,
            sample_peak_dbfs=-1.02,
            crest_factor_db=9.3,
            measurement_valid=True
        )
        d = meas.to_dict()
        json_str = json.dumps(d, sort_keys=True)
        self.assertIn('"integrated_lufs": -14.23', json_str)
        self.assertIn('"true_peak_dbtp": -0.91', json_str)
        self.assertIn('"true_peak_dbfs": -0.91', json_str)
        self.assertIn('"measurement_valid": true', json_str)


if __name__ == "__main__":
    unittest.main()

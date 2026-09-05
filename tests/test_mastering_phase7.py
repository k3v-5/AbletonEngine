# tests/test_mastering_phase7.py
"""
Test Suite for Phase 7: Mastering & Commercial Release Delivery.
Validates:
1. LiveMasterChainEngine: ITU-R BS.1770-5 target profiles (Streaming, Club, CD, Broadcast), 5-device chain.
2. CommercialReleasePackager: ISRC/UPC generation, TPDF dither, multi-format bundle (WAV 24/48, CD 16/44.1, MP3, Stems, Manifest).
3. ExecutiveCopilotEngine: Phase 7 mastering and delivery decisions discovery and interactive execution.
"""

import pytest
import os
import json
import tempfile
import numpy as np
from pathlib import Path
from engine.mastering.live_master_chain import LiveMasterChainEngine
from engine.mastering.release_package import CommercialReleasePackager
from engine.production.copilot.stepper import ExecutiveCopilotEngine, ProductionPhase


class TestLiveMasterChainEngine:
    """Tests for native 5-device mastering chain and ITU-R BS.1770-5 compliance."""

    def test_target_specs_profiles(self):
        streaming = LiveMasterChainEngine.get_target_specs("STREAMING")
        assert streaming["target_lufs"] == -14.0
        assert streaming["ceiling_db"] <= -1.0

        club = LiveMasterChainEngine.get_target_specs("CLUB")
        assert club["target_lufs"] == -9.0
        assert club["ceiling_db"] <= -0.5

        cd = LiveMasterChainEngine.get_target_specs("CD")
        assert cd["target_lufs"] == -12.0

        broadcast = LiveMasterChainEngine.get_target_specs("BROADCAST")
        assert broadcast["target_lufs"] == -24.0

    def test_setup_live_mastering_chain_mock(self):
        res = LiveMasterChainEngine.setup_live_mastering_chain(
            conn=None,
            track_index=12,
            target_profile="STREAMING"
        )
        assert res["status"] == "SUCCESS"
        assert res["track_index"] == 12
        assert res["target_profile"] == "STREAMING"
        assert res["target_lufs"] == -14.0
        assert res["ceiling_db"] == -1.0


class TestCommercialReleasePackager:
    """Tests for commercial distribution packaging, dithering, and metadata manifest."""

    def test_isrc_generation(self):
        isrc = CommercialReleasePackager.generate_isrc(country="US", registrant="AGY", year=26, designation=42)
        assert isrc == "US-AGY-26-00042"

    def test_upc_barcode_checksum(self):
        upc = CommercialReleasePackager.generate_upc_barcode(prefix=123456, product=7890)
        assert len(upc) == 12
        # Verify Mod-10 check digit math
        odd_sum = sum(int(upc[i]) for i in range(0, 11, 2))
        even_sum = sum(int(upc[i]) for i in range(1, 11, 2))
        assert (odd_sum * 3 + even_sum + int(upc[11])) % 10 == 0

    def test_tpdf_dither_statistics(self):
        # Create silent 24-bit audio array
        silence = np.zeros((2, 48000), dtype=np.float64)
        dithered = CommercialReleasePackager.apply_tpdf_dither(silence, target_bits=16)

        # Mean of TPDF noise should be approximately zero
        mean_noise = float(np.mean(dithered))
        assert abs(mean_noise) < 1e-4

        # Max noise amplitude should be bounded within ~1 LSB of 16-bit word length
        lsb = 1.0 / (2 ** 15)
        assert np.max(np.abs(dithered)) <= lsb * 2.5

    def test_complete_commercial_release_package_creation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            res = CommercialReleasePackager.create_release_package(
                output_directory=tmpdir,
                song_title="Hit Record",
                artist_name="Antigravity",
                genre="trap",
                target_profile="STREAMING"
            )
            assert res["status"] == "SUCCESS"
            assert "package_path" in res
            out_dir = Path(res["package_path"])
            assert out_dir.exists()

            # Verify core delivery files exist
            assert (out_dir / "01_Master_Lossless_24bit_48kHz.wav").exists()
            assert (out_dir / "02_Master_CD_16bit_44.1kHz.wav").exists()
            assert (out_dir / "04_Master_Instrumental_24bit.wav").exists()
            assert (out_dir / "05_Master_Acapella_24bit.wav").exists()
            assert (out_dir / "release_manifest.json").exists()

            # Verify stems
            stems_dir = out_dir / "Stems"
            assert stems_dir.exists()
            stem_files = list(stems_dir.glob("*.wav"))
            assert len(stem_files) == 5

            # Verify release_manifest.json contents
            with open(out_dir / "release_manifest.json", "r", encoding="utf-8") as f:
                manifest = json.load(f)
            assert manifest["metadata"]["title"] == "Hit Record"
            assert manifest["metadata"]["artist"] == "Antigravity"
            assert manifest["metadata"]["isrc_code"].startswith("US-AGY-")
            assert "acoustic_compliance" in manifest
            assert manifest["acoustic_compliance"]["true_peak_dbtp"] <= -0.9


class TestCopilotPhase7Integration:
    """Tests Phase 7 mastering copilot decision stepping."""

    def test_copilot_discovers_phase7_decisions(self):
        copilot = ExecutiveCopilotEngine()
        mock_tracks = [
            {"name": "Drums Bus", "track_index": 0},
            {"name": "Kick (808)", "track_index": 1},
            {"name": "Synths", "track_index": 2},
            {"name": "Master Bus", "track_index": 12}
        ]
        state = copilot.inspect_session(tracks=mock_tracks)
        pending_ids = [d.id for d in state.pending_decisions]

        assert "DEC-P7-LIVE-MASTERING-CHAIN" in pending_ids
        assert "DEC-P7-COMMERCIAL-RELEASE-PACKAGE" in pending_ids
        assert "DEC-P7-MASTER-CHAIN-DELIVERY" in pending_ids
        assert "DEC-P7-STEM-PHASE-AUDIT" in pending_ids

        for d in state.pending_decisions:
            if d.id.startswith("DEC-P7-"):
                assert d.phase == ProductionPhase.PHASE_7_MASTER_DELIVERY

    def test_copilot_executes_phase7_decisions(self):
        copilot = ExecutiveCopilotEngine()
        mock_tracks = [
            {"name": "Kick (808)", "track_index": 0},
            {"name": "Master Bus", "track_index": 12}
        ]
        copilot.inspect_session(tracks=mock_tracks)

        # Execute live mastering chain with YES
        dec_master = "DEC-P7-LIVE-MASTERING-CHAIN"
        res1 = copilot.execute_decision(dec_master, choice="YES")
        assert res1["status"] == "success"
        assert res1["action"] == "APPLIED"
        assert dec_master in copilot.resolved_decisions

        # Execute commercial release package with NO (rejection)
        dec_pkg = "DEC-P7-COMMERCIAL-RELEASE-PACKAGE"
        res2 = copilot.execute_decision(dec_pkg, choice="NO", justification="Demo mix only, deferred commercial packaging")
        assert res2["status"] == "success"
        assert res2["action"] == "REJECTED"
        assert res2["justification"] == "Demo mix only, deferred commercial packaging"
        assert dec_pkg in copilot.resolved_decisions

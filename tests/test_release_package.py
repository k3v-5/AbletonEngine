# tests/test_release_package.py
import pytest
import json
import numpy as np
from pathlib import Path
from engine.mastering.release_package import CommercialReleasePackager
from engine.production.copilot.stepper import ExecutiveCopilotEngine


def test_isrc_and_upc_generation():
    """Verify standard ISO 3901 ISRC and UPC-A Mod-10 checksum codes."""
    isrc = CommercialReleasePackager.generate_isrc("US", "AGY", 26, 1)
    assert isrc == "US-AGY-26-00001"

    upc = CommercialReleasePackager.generate_upc_barcode(prefix=890123, product=4567)
    assert len(upc) == 12
    # Verify Modulo 10 check digit validity
    odd_sum = sum(int(upc[i]) for i in range(0, 11, 2))
    even_sum = sum(int(upc[i]) for i in range(1, 11, 2))
    total = (odd_sum * 3) + even_sum
    assert (total + int(upc[11])) % 10 == 0


def test_tpdf_dither_properties():
    """Verify TPDF dither is zero-mean and bounded."""
    audio = np.linspace(-0.5, 0.5, 10000)
    dithered = CommercialReleasePackager.apply_tpdf_dither(audio, target_bits=16)
    diff = dithered - audio
    # Mean error should be virtually zero
    assert abs(np.mean(diff)) < 0.001
    assert np.all(dithered >= -1.0) and np.all(dithered <= 1.0)


def test_create_release_package_end_to_end(tmp_path):
    """Verify complete generation of all deliverables, stems, and manifest."""
    res = CommercialReleasePackager.create_release_package(
        output_directory=tmp_path,
        song_title="Neon Nights",
        artist_name="DeepMind Beats",
        genre="atlanta_trap",
        bpm=138.0,
        key="F minor",
        target_profile="STREAMING"
    )

    assert res["status"] == "SUCCESS"
    assert res["isrc"].startswith("US-AGY")
    assert len(res["files_generated"]) >= 5
    assert res["stems_count"] == 5

    pkg_dir = Path(res["package_path"])
    assert (pkg_dir / "01_Master_Lossless_24bit_48kHz.wav").exists()
    assert (pkg_dir / "02_Master_CD_16bit_44.1kHz.wav").exists()
    assert (pkg_dir / "04_Master_Instrumental_24bit.wav").exists()
    assert (pkg_dir / "05_Master_Acapella_24bit.wav").exists()
    assert (pkg_dir / "Stems" / "Stem_Drums_24bit.wav").exists()

    manifest_file = Path(res["manifest_file"])
    assert manifest_file.exists()
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert manifest["metadata"]["title"] == "Neon Nights"
    assert manifest["acoustic_compliance"]["standard"] == "ITU-R BS.1770-5 / EBU R128"
    assert "spotify" in manifest["platform_delivery_readiness"]
    assert "master_24bit" in manifest["files"]


def test_copilot_discovers_deesser_and_release_package():
    """Verify ExecutiveCopilotEngine discovers and resolves new release decisions."""
    copilot = ExecutiveCopilotEngine()
    dummy_tracks = [
        {"name": "Drums Bus", "track_index": 0},
        {"name": "Lead Vocal", "track_index": 4},
        {"name": "Master Bus", "track_index": 12}
    ]

    state = copilot.inspect_session(conn=None, tracks=dummy_tracks)
    pending_ids = [d.id for d in state.pending_decisions]

    assert "DEC-P6-ADAPTIVE-DEESSER-T4" in pending_ids
    assert "DEC-P7-COMMERCIAL-RELEASE-PACKAGE" in pending_ids

    # Execute decisions
    res_deess = copilot.execute_decision("DEC-P6-ADAPTIVE-DEESSER-T4", choice="YES")
    assert res_deess["status"] == "success"
    assert res_deess["action"] == "APPLIED"

    res_rel = copilot.execute_decision("DEC-P7-COMMERCIAL-RELEASE-PACKAGE", choice="YES")
    assert res_rel["status"] == "success"
    assert res_rel["action"] == "APPLIED"

# tests/test_stem_bouncer.py
import os
import tempfile
import pytest
from engine.audio.stem_bouncer import StemBouncer

def test_stem_bouncer_plan_creation():
    with tempfile.TemporaryDirectory() as tmpdir:
        bouncer = StemBouncer(export_dir=tmpdir)
        
        tracks = [
            {"index": 0, "name": "Kick & Snare Drum Rack"},
            {"index": 1, "name": "HiHats & Percussion"},
            {"index": 2, "name": "808 Sub Bassline"},
            {"index": 3, "name": "Rhodes Piano Chords"},
            {"index": 4, "name": "Vital Synth Lead Hook"},
            {"index": 5, "name": "Lead Vocal"},
            {"index": 6, "name": "Riser & Sweep FX"}
        ]
        
        plan = bouncer.create_export_plan(
            tracks=tracks,
            bpm=142.0,
            start_bar=1.0,
            end_bar=65.0
        )
        
        assert plan.total_bars == 64.0
        assert plan.bpm == 142.0
        # 64 bars * 4 beats = 256 beats. 256 / (142 / 60) ≈ 108.17 seconds
        assert plan.duration_seconds == pytest.approx(108.17, abs=0.5)
        
        stems_dict = {s.stem_id: s for s in plan.stems}
        assert "01_Drums" in stems_dict
        assert stems_dict["01_Drums"].track_indices == [0, 1]
        
        assert "02_Bass" in stems_dict
        assert stems_dict["02_Bass"].track_indices == [2]

        assert "03_Keys" in stems_dict
        assert stems_dict["03_Keys"].track_indices == [3]

        assert "04_Lead" in stems_dict
        assert stems_dict["04_Lead"].track_indices == [4]

        assert "05_Vocals" in stems_dict
        assert stems_dict["05_Vocals"].track_indices == [5]

        assert "06_FX" in stems_dict
        assert stems_dict["06_FX"].track_indices == [6]

        assert "00_Master" in stems_dict

        # Test manifest writing
        manifest_path = bouncer.generate_manifest(plan)
        assert os.path.exists(manifest_path)

# tests/test_parquet_indexer.py
import pytest
import tempfile
from pathlib import Path
from engine.indexer.parser import parse_path, extract_bpm, extract_key
from engine.indexer.storage import save_manifest, load_manifest
from engine.indexer.manifest import search_samples

def test_parser_extracts_all_metadata():
    res = parse_path("Drums/Kicks/Kick_Punchy_140bpm_F#min.wav", "")
    assert res["sample_type"] == "kick"
    assert res["bpm"] == 140
    assert res["key"] == "F#min"
    assert "punchy" in res["moods"]

def test_parquet_manifest_crud_and_search():
    with tempfile.TemporaryDirectory() as tmpdir:
        m_path = Path(tmpdir) / "manifest.parquet"
        sample_rows = [
            {
                "path": "samples/kick1.wav", "filename": "kick1.wav", "relative_folder": "",
                "extension": ".wav", "size_bytes": 1024, "mtime": 1000, "content_hash": "hash1",
                "sample_type": "kick", "subtype": "punchy", "genres": ["trap"],
                "moods": ["punchy"], "key": "Fmin", "bpm": 140, "is_loop": False,
                "is_oneshot": True, "raw_tags": ["kick"], "indexed_at": 1000
            },
            {
                "path": "samples/snare1.wav", "filename": "snare1.wav", "relative_folder": "",
                "extension": ".wav", "size_bytes": 2048, "mtime": 1000, "content_hash": "hash2",
                "sample_type": "snare", "subtype": "clap", "genres": ["boom_bap"],
                "moods": ["vintage"], "key": "Cmin", "bpm": 90, "is_loop": False,
                "is_oneshot": True, "raw_tags": ["snare"], "indexed_at": 1000
            }
        ]
        save_manifest(m_path, sample_rows)
        loaded = load_manifest(m_path)
        assert len(loaded) == 2

        # Filter query
        kicks = search_samples(m_path, sample_type="kick", bpm=140)
        assert len(kicks) == 1
        assert kicks[0]["filename"] == "kick1.wav"

        snares = search_samples(m_path, sample_type="snare")
        assert len(snares) == 1
        assert snares[0]["filename"] == "snare1.wav"

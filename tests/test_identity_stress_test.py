# tests/test_identity_stress_test.py
"""
Unit and Integration Tests for Identity Stress Test:
Validates that the generative engine creates 10 genuinely distinct musical worlds
rather than repackaging the same techniques across contrasting archetypes.
"""
import pytest
from engine.creative.identity_stress_test import IdentityStressTest, IdentityStressTestReport


def test_identity_stress_test_10_archetypes_divergence():
    """
    Executes the 10-archetype identity stress test:
    1. Minimal / Intimate
    2. Aggressive / Dense
    3. Psychedelic
    4. Melancholic
    5. Futuristic
    6. Raw / Lo-Fi
    7. Soulful
    8. Rhythmically Strange
    9. Cinematic
    10. Deliberately Sparse
    """
    report = IdentityStressTest.run_10_song_stress_test()

    # 1. Total songs generated and audited
    assert report.total_songs_tested == 10
    assert len(report.song_results) == 10

    # 2. All 10 must pass the rigorous 7-critic court
    assert report.all_passed_critics is True
    for s in report.song_results:
        assert s.critic_verdict.passed is True
        assert s.critic_verdict.overall_artistic_score >= 0.76

    # 3. High Catalog Diversity Index
    assert report.catalog_diversity_index >= 0.85

    # 4. Zero cross-song recipe cliches or identical motif intervals
    assert report.pairwise_recipe_collisions == 0
    assert report.pairwise_motif_collisions == 0

    # 5. Distinct sonic signatures
    signatures = [s.intent.signature_sound_brief for s in report.song_results]
    assert len(signatures) == len(set(signatures))  # All 10 signatures are 100% distinct

    # 6. Distinct BPMs and tonal centers
    bpms = [s.dna.bpm for s in report.song_results]
    assert min(bpms) == 55.0   # Sparse
    assert max(bpms) == 168.0  # Hyperpop Futuristic

    # 7. Formatted markdown report contains all 10 entries
    md = report.format_markdown_report()
    assert "Identity Stress Test Report" in md
    assert "ÉXITO TOTAL" in md
    assert "Song 01" in md
    assert "Song 10" in md

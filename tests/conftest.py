# tests/conftest.py
"""
Pytest configuration and global fixtures for AbletonEngine test isolation.
Ensures ephemeral test state files are automatically cleaned up so tests
remain 100% idempotent and isolated from one another.
"""
import os
import pytest
from pathlib import Path


@pytest.fixture(autouse=True)
def clean_test_state_isolation():
    """Removes leftover ephemeral test session state before and after each test."""
    test_state = Path("state/test/guided_session_test.json")
    if test_state.exists():
        try:
            test_state.unlink()
        except Exception:
            pass
    yield
    if test_state.exists():
        try:
            test_state.unlink()
        except Exception:
            pass

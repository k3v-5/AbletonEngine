import os
import pytest
from pathlib import Path
from engine.production.copilot.state_manager import CopilotStateManager


def test_copilot_state_manager_test_isolation():
    # In pytest, PYTEST_CURRENT_TEST is automatically set by pytest
    assert "PYTEST_CURRENT_TEST" in os.environ
    assert CopilotStateManager.STATE_FILE == Path("state/test/guided_session_test.json")
    assert CopilotStateManager.CHECKPOINTS_DIR == Path("state/test/checkpoints")
    assert CopilotStateManager.JOURNAL_FILE == Path("state/test/session_journal.jsonl")


def test_copilot_state_manager_prod_when_not_in_test():
    saved = os.environ.pop("PYTEST_CURRENT_TEST", None)
    try:
        assert CopilotStateManager.STATE_FILE == Path("state/production/guided_session.json")
        assert CopilotStateManager.CHECKPOINTS_DIR == Path("state/production/checkpoints")
        assert CopilotStateManager.JOURNAL_FILE == Path("state/production/session_journal.jsonl")
    finally:
        if saved:
            os.environ["PYTEST_CURRENT_TEST"] = saved

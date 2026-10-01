# tests/test_project_lifecycle.py
"""
Test Suite for ProjectLifecycleManager.
Verifies project archiving, clean-slate resetting, and decision handling.
"""

import sys
import json
import shutil
from pathlib import Path
from unittest.mock import MagicMock

# Ensure repo root in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from engine.session.project_lifecycle import ProjectLifecycleManager


def run_tests():
    print("=== Testing ProjectLifecycleManager ===")

    # 1. Test Project Name Derivation
    mock_session = MagicMock()
    mock_session.data = {
        "song_title": "Casti",
        "genre": "Reggaeton",
        "tracks": [{"name": "Dembow Kit"}]
    }
    name = ProjectLifecycleManager.get_current_project_name(mock_session)
    assert name == "Casti", f"Expected 'Casti' but got '{name}'"
    print("[OK] Test 1: Project name derived correctly")

    # 2. Test Project Archiving
    archive_res = ProjectLifecycleManager.archive_current_project(mock_session, custom_name="Test_Casti")
    assert archive_res["status"] == "ARCHIVED"
    archive_dir = Path(archive_res["archive_dir"])
    assert archive_dir.exists(), f"Archive dir does not exist: {archive_dir}"
    assert (archive_dir / "project_manifest.json").exists(), "Manifest missing"

    with open(archive_dir / "project_manifest.json", "r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest["project_name"] == "Test_Casti"
    print(f"[OK] Test 2: Project archived successfully at {archive_dir}")

    # Clean up test archive
    if archive_dir.exists():
        shutil.rmtree(archive_dir, ignore_errors=True)

    # 3. Test Prompt Generation
    prompt_res = ProjectLifecycleManager.prompt_lifecycle_decision(mock_session)
    assert prompt_res["current_step"] == "DECISIÓN: GUARDAR PROYECTO Y EMPEZAR DE NUEVO"
    assert "Opción 1" in prompt_res["question"]
    assert "Opción 2" in prompt_res["question"]
    assert "Opción 3" in prompt_res["question"]
    assert "Opción 4" in prompt_res["question"]
    print("[OK] Test 3: Lifecycle prompt rendered correctly with 4 options")

    # 4. Test Decision Handling: Cancel
    mock_session.data["lifecycle_decision_active"] = True
    cancel_res = ProjectLifecycleManager.handle_lifecycle_decision(mock_session, None, "Opción 4: Cancelar")
    assert cancel_res["current_step"] == "OPERACIÓN CANCELADA"
    assert mock_session.data.get("lifecycle_decision_active") is False
    print("[OK] Test 4: Cancel option handled safely")

    # 5. Test Decision Handling: Only Save
    mock_session.data["lifecycle_decision_active"] = True
    save_res = ProjectLifecycleManager.handle_lifecycle_decision(mock_session, None, "Opción 3: Solo guardar")
    assert save_res["current_step"] == "PROYECTO GUARDADO Y ARCHIVADO"
    save_dir = Path(save_res["archive_info"]["archive_dir"])
    assert save_dir.exists()
    shutil.rmtree(save_dir, ignore_errors=True)
    print("[OK] Test 5: Only Save option handled successfully")

    # 6. Test Start New Project (with mock conn)
    mock_conn = MagicMock()
    mock_conn.send_command.return_value = {"status": "ok"}
    mock_session.reset = MagicMock()
    mock_session._prompt_phase_1 = MagicMock(return_value={"question": "¿Qué género y BPM deseas?"})

    new_proj_res = ProjectLifecycleManager.start_new_project(
        mock_session,
        mock_conn,
        target_bpm=95.0,
        save_first=False
    )
    assert new_proj_res["status"] == "NEW_PROJECT_STARTED"
    assert mock_session.reset.called
    assert mock_conn.send_command.called
    print("[OK] Test 6: Start New Project executed and reset triggered")

    print("\nALL 6 PROJECT LIFECYCLE TESTS PASSED PERFECTLY!")


if __name__ == "__main__":
    run_tests()

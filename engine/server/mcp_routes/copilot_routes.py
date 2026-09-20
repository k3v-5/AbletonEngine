"""
Copilot MCP Routes:
Modular route handlers for executive copilot, guided session, session doctor,
and decision checklist workflows.
"""

import sys
import logging
import importlib
from typing import Optional, Dict, Any, Callable

logger = logging.getLogger("AbletonMCPServer.CopilotRoutes")


def handle_copilot_get_status(get_connection: Callable[[], Any]) -> dict:
    """Returns current executive copilot production phase and progress."""
    try:
        from engine.production.copilot.stepper import executive_copilot
        conn = get_connection()
        state = executive_copilot.inspect_session(conn=conn)
        return state.to_dict()
    except Exception as e:
        logger.error(f"Error in copilot_get_status: {e}")
        return {"status": "error", "message": str(e)}


def handle_copilot_review_decisions(get_connection: Callable[[], Any], phase: Optional[str] = None) -> dict:
    """Returns the interactive checklist of pending production decisions."""
    try:
        import engine.production.copilot.stepper as _stepper_mod
        if phase in ["RESET", "NEW_SONG", "NEW"]:
            importlib.reload(_stepper_mod)
            sys.modules["engine.production.copilot.stepper"] = _stepper_mod
        ec = sys.modules["engine.production.copilot.stepper"].executive_copilot
        if phase in ["RESET", "NEW_SONG", "NEW"]:
            ec.reset()
            phase = None
        conn = get_connection()
        state = ec.inspect_session(conn=conn)
        pending = state.pending_decisions
        if phase:
            pending = [d for d in pending if d.phase == phase]
        return {
            "pending_count": len(pending),
            "decisions": [d.to_dict() for d in pending],
            "guidance": "Review each decision. To accept recommended action, call copilot_execute_decision(decision_id, choice='YES'). To consciously omit, call with choice='NO' and your justification."
        }
    except Exception as e:
        logger.error(f"Error in copilot_review_decisions: {e}")
        return {"status": "error", "message": str(e)}


def handle_copilot_execute_decision(
    get_connection: Callable[[], Any],
    decision_id: str,
    choice: str = "YES",
    justification: Optional[str] = None,
    custom_args: Optional[dict] = None
) -> dict:
    """Resolves an interactive copilot decision."""
    try:
        ec = sys.modules["engine.production.copilot.stepper"].executive_copilot
        conn = get_connection()
        res = ec.execute_decision(
            decision_id=decision_id,
            choice=choice,
            justification=justification,
            custom_args=custom_args,
            conn=conn
        )
        return res
    except Exception as e:
        logger.error(f"Error in copilot_execute_decision: {e}")
        return {"status": "error", "message": str(e)}


def handle_copilot_preflight_check(get_connection: Callable[[], Any]) -> dict:
    """Performs a strict pre-flight audit validating zero unreviewed technical steps remain."""
    try:
        ec = sys.modules["engine.production.copilot.stepper"].executive_copilot
        conn = get_connection()
        ec.inspect_session(conn=conn)
        report = ec.preflight_check()
        return report
    except Exception as e:
        logger.error(f"Error in copilot_preflight_check: {e}")
        return {"status": "error", "message": str(e)}


def handle_copilot_auto_produce(
    get_connection: Callable[[], Any],
    genre: str = "hip_hop_neo_soul",
    bpm: float = 120.0,
    key: str = "F",
    scale: str = "natural_minor",
    max_steps: int = 80
) -> dict:
    """Autonomous End-to-End Copilot Producer."""
    try:
        from engine.production.copilot.stepper import executive_copilot
        conn = get_connection()
        return executive_copilot.run_autonomous_pipeline(
            conn=conn,
            genre=genre,
            bpm=bpm,
            key=key,
            scale=scale,
            max_steps=max_steps
        )
    except Exception as e:
        logger.error(f"Error in copilot_auto_produce: {e}")
        return {"status": "error", "message": str(e)}


def handle_copilot_guided_session(
    get_connection: Callable[[], Any],
    user_input: str = "",
    reset: bool = False
) -> dict:
    """Conversational State Machine Wizard for Interactive Music Production (Strict 7-Phase Flow)."""
    try:
        if reset:
            for mod_name in list(sys.modules.keys()):
                if mod_name.startswith("engine."):
                    try:
                        importlib.reload(sys.modules[mod_name])
                    except Exception:
                        pass
        for mod_name in list(sys.modules.keys()):
            if mod_name.startswith("engine.creative.") or mod_name.startswith("engine.sound."):
                try:
                    importlib.reload(sys.modules[mod_name])
                except Exception:
                    pass
        import engine.production.copilot.guided_session as _gs_mod
        importlib.reload(_gs_mod)
        copilot_guided_session_engine = _gs_mod.copilot_guided_session_engine
        conn = get_connection()
        return copilot_guided_session_engine.step(conn=conn, user_input=user_input, reset=reset)
    except Exception as e:
        logger.error(f"Error in copilot_guided_session: {e}")
        return {"status": "error", "message": str(e)}


def handle_copilot_session_doctor(
    get_connection: Callable[[], Any],
    user_input: str = "",
    reset: bool = False
) -> dict:
    """Studio Doctor & Clinical Acoustic Repair for Existing Ableton Live Projects."""
    try:
        if reset:
            for mod_name in list(sys.modules.keys()):
                if mod_name.startswith("engine.production.doctor"):
                    try:
                        importlib.reload(sys.modules[mod_name])
                    except Exception:
                        pass
        import engine.production.doctor.session_doctor as _sd_mod
        importlib.reload(_sd_mod)
        copilot_session_doctor_engine = _sd_mod.copilot_session_doctor_engine
        conn = get_connection()
        return copilot_session_doctor_engine.step(conn=conn, user_input=user_input, reset=reset)
    except Exception as e:
        logger.error(f"Error in copilot_session_doctor: {e}")
        return {"status": "error", "message": str(e)}

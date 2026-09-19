import pytest
from engine.adapters.mock_adapter import MockAbletonAdapter
from engine.production.copilot.guided_session import CopilotGuidedSession
from engine.production.recipe_engine import ProductionRecipeEngine

def test_optimize_points_for_clip_clamping():
    raw_points = [{'time': float(i), 'value': float(i % 10) / 10.0} for i in range(50)]
    opt = ProductionRecipeEngine.optimize_points_for_clip(raw_points, min_points=2, max_points=8)
    assert 2 <= len(opt) <= 8
    assert opt[0]['time'] == raw_points[0]['time']
    assert opt[-1]['time'] == raw_points[-1]['time']

def test_phase_2_scale_and_key_asking_and_tuning():
    session = CopilotGuidedSession()
    session.reset()
    adapter = MockAbletonAdapter()
    p1 = session.step(conn=adapter, user_input='Opción A')
    assert p1['phase'] == 'PHASE_2_SECTIONS'
    assert 'Tonalidad/Escala' in p1['question']
    assert 'Afinación Armónica' in p1['question']

    p2 = session.step(conn=adapter, user_input='Opción A en Fa Menor (F Minor)')
    assert session.data.get('key') == 'F'
    assert session.data.get('scale') == 'Minor'
    assert session.data.get('current_phase') == 'PHASE_3_INSTRUMENTS'

def test_step_direct_tuning_command():
    session = CopilotGuidedSession()
    adapter = MockAbletonAdapter()
    res = session.step(conn=adapter, user_input='afinar en Re Menor')
    assert res['status'] == 'SESSION_TUNED'
    assert session.data.get('key') == 'D'
    assert session.data.get('scale') == 'Minor'

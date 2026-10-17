from .weaver import ArrangementAutomationWeaver, TransitionAutomationType
from .live_automation import LiveAutomationEngine
from .recorder import ArrangementAutomationRecorder
from .clip_suggester import ClipAutomationSuggester, ClipAutomationRecipe
from .clip_envelopes import ClipEnvelopeEngine, EnvelopeBreakpoint

__all__ = [
    "ArrangementAutomationWeaver",
    "TransitionAutomationType",
    "LiveAutomationEngine",
    "ArrangementAutomationRecorder",
    "ClipAutomationSuggester",
    "ClipAutomationRecipe",
    "ClipEnvelopeEngine",
    "EnvelopeBreakpoint"
]


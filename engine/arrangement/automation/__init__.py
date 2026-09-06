# engine/arrangement/automation/__init__.py
from .weaver import ArrangementAutomationWeaver, TransitionAutomationType
from .live_automation import LiveAutomationEngine
from .recorder import ArrangementAutomationRecorder

from .clip_suggester import ClipAutomationSuggester, ClipAutomationRecipe

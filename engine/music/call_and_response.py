# engine/music/call_and_response.py
"""
Call-and-Response Modular Bass Orchestrator:
Splits complex basslines and riffs across multiple complementary tracks (Growl vs Laser vs Sub)
for authentic Complextro, Dubstep and Electro House arrangements.
"""

from typing import Dict, Any, List, Tuple
import logging

logger = logging.getLogger("CallAndResponse")


class CallAndResponseOrchestrator:
    """Distributes unified rhythmic phrases across multiple sound tracks."""

    @classmethod
    def split_phrase_into_call_and_response(
        cls,
        melody_notes: List[Dict[str, Any]],
        call_track_index: int,
        response_track_index: int,
        sub_track_index: Optional[int] = None
    ) -> Dict[int, List[Dict[str, Any]]]:
        """
        Splits a note list:
        - Call track receives downbeat / low-register notes (pitches < 50)
        - Response track receives syncopated offbeats / high-register stabs (pitches >= 50)
        - Sub track receives sustained fundamental sub notes
        """
        call_notes = []
        response_notes = []
        sub_notes = []

        for n in melody_notes:
            n_copy = dict(n)
            st = float(n_copy.get("start_time", 0.0))
            p = int(n_copy.get("pitch", 36))
            beat_pos = st % 2.0  # Even or odd beat

            # Low pitch or on downbeat: CALL
            if p < 48 or beat_pos < 0.75:
                call_notes.append(n_copy)
                if sub_track_index is not None and p < 45:
                    sub_copy = dict(n_copy)
                    sub_copy["pitch"] = 36  # Force root C1 / F1
                    sub_notes.append(sub_copy)
            else:
                # High pitch on offbeat: RESPONSE
                response_notes.append(n_copy)

        result = {
            call_track_index: call_notes,
            response_track_index: response_notes
        }
        if sub_track_index is not None:
            result[sub_track_index] = sub_notes

        return result

# tests/test_session_graph.py
import unittest
from engine.session.graph import SessionShadowGraph
from engine.models import TrackNode, generate_id
from engine.adapters.mock_adapter import MockAbletonAdapter
from engine.session.synchronizer import SessionSynchronizer
from engine.errors import ObjectLockedError

class TestSessionGraph(unittest.TestCase):
    def setUp(self):
        self.graph = SessionShadowGraph()
        self.mock_adapter = MockAbletonAdapter()
        self.synchronizer = SessionSynchronizer(self.graph, self.mock_adapter)
        self.synchronizer.refresh()

    def test_track_identity_preserved_across_moves(self):
        """Test 1: Track identity is preserved when track index changes in Ableton"""
        # Find 'Bass' track in shadow graph
        bass_track = next(t for t in self.graph.tracks.values() if t.name == "Bass")
        initial_id = bass_track.id
        self.assertEqual(bass_track.ableton_index, 1)

        # Move 'Bass' to index 0 in Ableton Live (swap with Kick)
        # In mock adapter, insert a new track before it or rearrange
        bass_adapter_track = self.mock_adapter.tracks.pop(1)
        self.mock_adapter.tracks.insert(0, bass_adapter_track)
        self.mock_adapter._reindex_tracks()

        # Refresh from Ableton
        diff = self.synchronizer.refresh()

        # Check that bass still has the exact same track_id, but updated ableton_index
        bass_after = self.graph.get_track(initial_id)
        self.assertIsNotNone(bass_after, "Bass track ID must still exist in graph")
        self.assertEqual(bass_after.id, initial_id, "Track ID must remain identical")
        self.assertEqual(bass_after.ableton_index, 0, "Track ableton_index must be updated to 0")
        self.assertTrue(any(m["id"] == initial_id for m in diff.moved), "Diff must report track moved")

    def test_locked_object_protection(self):
        """Test 6: Locked object cannot be deleted or modified"""
        kick_track = next(t for t in self.graph.tracks.values() if t.name == "Kick")
        self.graph.lock_object(kick_track.id, reason="Protected user master kick")
        self.assertTrue(kick_track.metadata.locked)

        # Attempting to delete locked track must raise ObjectLockedError
        with self.assertRaises(ObjectLockedError):
            self.graph.remove_track(kick_track.id)

        # Attempting to set role on locked track must raise ObjectLockedError
        with self.assertRaises(ObjectLockedError):
            self.graph.set_track_role(kick_track.id, "DRUMS")

        # Unlock works
        self.graph.unlock_object(kick_track.id)
        self.assertFalse(kick_track.metadata.locked)
        self.graph.set_track_role(kick_track.id, "KICK")
        self.assertEqual(kick_track.metadata.role, "KICK")

if __name__ == "__main__":
    unittest.main()

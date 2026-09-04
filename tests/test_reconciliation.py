# tests/test_reconciliation.py
import unittest
import os
import json
from engine.session.graph import SessionShadowGraph
from engine.adapters.mock_adapter import MockAbletonAdapter
from engine.session.synchronizer import SessionSynchronizer
from engine.session.diff import SessionDiff
from engine.persistence.storage import storage

class TestReconciliation(unittest.TestCase):
    def setUp(self):
        self.graph = SessionShadowGraph()
        self.adapter = MockAbletonAdapter()
        self.synchronizer = SessionSynchronizer(self.graph, self.adapter)
        self.synchronizer.refresh()

    def test_external_track_deletion(self):
        """Test 2: Deleting track externally in Ableton is caught by session.refresh() as removed"""
        # We start with 2 tracks: Kick, Bass
        self.assertEqual(len(self.graph.tracks), 2)
        bass = next(t for t in self.graph.tracks.values() if t.name == "Bass")
        
        # User deletes Bass directly in Ableton Live
        self.adapter.delete_track(bass.ableton_index)
        self.assertEqual(len(self.adapter.tracks), 1)

        # Refresh
        diff = self.synchronizer.refresh()

        # Check diff and graph
        self.assertEqual(len(self.graph.tracks), 1)
        self.assertIsNone(self.graph.get_track(bass.id))
        self.assertTrue(any(rem["id"] == bass.id for rem in diff.removed))

    def test_external_property_modification_diff(self):
        """Test 3: Modifying volume directly in Ableton is detected by session.diff()"""
        kick = next(t for t in self.graph.tracks.values() if t.name == "Kick")
        
        # User changes volume directly in Ableton to 0.42
        self.adapter.set_track_volume(kick.ableton_index, 0.42)

        # Calculate diff
        real_tracks = [self.adapter.get_track_info(i) for i in range(len(self.adapter.tracks))]
        diff = SessionDiff.compute_diff(self.graph.tracks, real_tracks)

        self.assertFalse(diff.is_empty())
        self.assertTrue(any(
            m["id"] == kick.id and m["property"] == "volume" and m["after"] == 0.42
            for m in diff.modified
        ))

    def test_restart_recovery_and_reconcile(self):
        """Test 8: System reboots, loads persisted state, reconciles with live Ableton"""
        # Assign role to Bass in the graph
        bass = next(t for t in self.graph.tracks.values() if t.name == "Bass")
        self.graph.set_track_role(bass.id, "SUB_BASS")
        self.graph.lock_object(bass.id, "Protected sub")
        
        # Save graph state to disk
        persisted_data = self.graph.to_dict()
        storage.save_graph(persisted_data)

        # Simulate server crash/reboot: new graph instance
        rebooted_graph = SessionShadowGraph()
        rebooted_sync = SessionSynchronizer(rebooted_graph, self.adapter)
        
        # Reconcile with live Ableton session
        rebooted_sync.reconcile(persisted_data)

        # Verify that role and lock were preserved during reconciliation
        rebooted_bass = next(t for t in rebooted_graph.tracks.values() if t.name == "Bass")
        self.assertEqual(rebooted_bass.metadata.role, "SUB_BASS")
        self.assertTrue(rebooted_bass.metadata.locked)
        self.assertEqual(rebooted_graph.project_state.sync_status, "SYNCHRONIZED")

if __name__ == "__main__":
    unittest.main()

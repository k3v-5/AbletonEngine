# tests/test_transactions.py
import unittest
from engine.session.graph import SessionShadowGraph
from engine.adapters.mock_adapter import MockAbletonAdapter
from engine.session.synchronizer import SessionSynchronizer
from engine.transactions.manager import TransactionManager
from engine.errors import TransactionFailedError, ObjectLockedError

class TestTransactions(unittest.TestCase):
    def setUp(self):
        self.graph = SessionShadowGraph()
        self.adapter = MockAbletonAdapter()
        self.synchronizer = SessionSynchronizer(self.graph, self.adapter)
        self.synchronizer.refresh()
        self.tx_manager = TransactionManager(self.graph, self.adapter)

    def test_transaction_success_and_commit(self):
        """Test 4: Atomic unit of work (create track, set volume, set role) commits successfully"""
        initial_track_count = len(self.graph.tracks)
        
        tx = self.tx_manager.begin(name="Add HiHat and Adjust Kick")
        # 1. Stage track creation
        self.tx_manager.stage_create_track(tx.id, name="HiHat Closed", track_type="midi", role="HIHAT")
        
        # 2. Stage volume on existing Kick
        kick = next(t for t in self.graph.tracks.values() if t.name == "Kick")
        self.tx_manager.stage_set_volume(tx.id, track_id=kick.id, volume=0.90)

        # Commit
        res = self.tx_manager.commit(tx.id)
        self.assertEqual(res["status"], "COMMITTED")

        # Verify state in Graph and Adapter
        self.assertEqual(len(self.graph.tracks), initial_track_count + 1)
        self.assertEqual(len(self.adapter.tracks), initial_track_count + 1)
        
        hihat_track = next(t for t in self.graph.tracks.values() if t.name == "HiHat Closed")
        self.assertEqual(hihat_track.metadata.role, "HIHAT")
        self.assertEqual(kick.volume, 0.90)
        self.assertEqual(self.adapter.tracks[kick.ableton_index]["volume"], 0.90)

    def test_transaction_failure_and_rollback(self):
        """Test 5: If an operation fails during transaction commit, all prior operations are rolled back"""
        initial_track_count = len(self.graph.tracks)
        kick = next(t for t in self.graph.tracks.values() if t.name == "Kick")
        initial_kick_vol = kick.volume

        tx = self.tx_manager.begin(name="Faulty Transaction")
        
        # Op 1: Valid track creation
        self.tx_manager.stage_create_track(tx.id, name="Temporary Lead", track_type="midi", role="LEAD")
        
        # Op 2: Valid volume change on Kick
        self.tx_manager.stage_set_volume(tx.id, track_id=kick.id, volume=0.35)
        
        # Op 3: Inject a failing operation (e.g. disconnect adapter right before commit to simulate error, or invalid parameter during execution)
        # We can simulate failure by corrupting the adapter or monkey patching
        original_set_volume = self.adapter.set_track_volume
        def faulty_volume(idx, vol):
            raise RuntimeError("Hardware/Ableton communication crash during volume write")
        self.adapter.set_track_volume = faulty_volume

        try:
            with self.assertRaises(TransactionFailedError):
                self.tx_manager.commit(tx.id)
        finally:
            # Restore adapter method
            self.adapter.set_track_volume = original_set_volume

        # Check that track count was rolled back and kick volume is restored
        self.assertEqual(len(self.graph.tracks), initial_track_count, "Rolled back graph must not contain new track")
        self.assertEqual(len(self.adapter.tracks), initial_track_count, "Rolled back adapter must not contain new track")
        self.assertEqual(kick.volume, initial_kick_vol, "Kick volume must be rolled back to initial value")

    def test_dry_run_preview(self):
        """Test 10: transaction.preview() calculates intended changes without modifying Ableton"""
        initial_tracks_count = len(self.adapter.tracks)
        tx = self.tx_manager.begin(name="Dry Run Test")
        self.tx_manager.stage_create_track(tx.id, name="Ghost Track")
        
        preview_res = self.tx_manager.preview(tx.id)
        self.assertTrue(preview_res["dry_run"])
        self.assertEqual(len(preview_res["changes"]), 1)
        self.assertEqual(preview_res["changes"][0]["type"], "create_track")

        # Ableton tracks must not have changed
        self.assertEqual(len(self.adapter.tracks), initial_tracks_count)
        self.assertEqual(len(self.graph.tracks), initial_tracks_count)

if __name__ == "__main__":
    unittest.main()

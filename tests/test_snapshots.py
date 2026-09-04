# tests/test_snapshots.py
import unittest
from MCP_Server.engine.session.graph import SessionShadowGraph
from MCP_Server.engine.snapshots.manager import snapshot_manager

class TestSnapshots(unittest.TestCase):
    def setUp(self):
        self.graph = SessionShadowGraph()
        self.graph.add_section("Intro", 1, 16, "INTRO", energy=0.25)

    def test_snapshot_create_and_restore(self):
        # Initial snapshot
        snap = snapshot_manager.create_snapshot(self.graph, name="Initial Intro Snapshot")
        self.assertIsNotNone(snap.id)

        # Modify graph (add another section)
        self.graph.add_section("Drop 1", 17, 32, "DROP", energy=0.90)
        self.assertEqual(len(self.graph.sections), 2)

        # Restore snapshot
        snapshot_manager.restore_snapshot(snap.id, self.graph)
        self.assertEqual(len(self.graph.sections), 1)
        self.assertIn("Intro", [s.name for s in self.graph.sections.values()])

    def test_list_snapshots(self):
        snap = snapshot_manager.create_snapshot(self.graph, name="List Test Snapshot")
        snapshots = snapshot_manager.list_snapshots()
        self.assertTrue(any(s["id"] == snap.id for s in snapshots))

if __name__ == "__main__":
    unittest.main()

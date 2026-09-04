# tests/test_concurrency.py
import unittest
from MCP_Server.engine.session.graph import SessionShadowGraph
from MCP_Server.engine.adapters.mock_adapter import MockAbletonAdapter
from MCP_Server.engine.session.synchronizer import SessionSynchronizer
from MCP_Server.engine.transactions.manager import TransactionManager
from MCP_Server.engine.errors import TransactionConflictError

class TestConcurrency(unittest.TestCase):
    def setUp(self):
        self.graph = SessionShadowGraph()
        self.adapter = MockAbletonAdapter()
        self.synchronizer = SessionSynchronizer(self.graph, self.adapter)
        self.synchronizer.refresh()
        self.tx_manager = TransactionManager(self.graph, self.adapter)

    def test_optimistic_concurrency_conflict(self):
        """Test 7: If graph version changes while transaction is open, commit fails with TransactionConflictError"""
        tx = self.tx_manager.begin(name="Conflicting Transaction")
        self.assertEqual(tx.base_version, self.graph.version)

        # Stage an operation
        self.tx_manager.stage_create_track(tx.id, name="Concurrent Synth")

        # Simulate an external modification that changes graph version
        self.graph.increment_version()
        self.assertNotEqual(tx.base_version, self.graph.version)

        # Attempting commit must raise TransactionConflictError
        with self.assertRaises(TransactionConflictError) as ctx:
            self.tx_manager.commit(tx.id)

        self.assertEqual(ctx.exception.details["base_version"], tx.base_version)
        self.assertEqual(ctx.exception.details["current_version"], self.graph.version)

if __name__ == "__main__":
    unittest.main()

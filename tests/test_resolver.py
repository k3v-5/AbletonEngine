# tests/test_resolver.py
import unittest
from engine.session.graph import SessionShadowGraph
from engine.session.resolver import SessionResolver
from engine.models import TrackNode, generate_id
from engine.errors import AmbiguousObjectError, ObjectNotFoundError

class TestResolver(unittest.TestCase):
    def setUp(self):
        self.graph = SessionShadowGraph()
        self.resolver = SessionResolver(self.graph)

    def test_ambiguous_resolution_detection(self):
        """Test 9: Multiple matches with same name raise AmbiguousObjectError instead of picking arbitrarily"""
        t1 = TrackNode(id=generate_id("track"), ableton_index=0, name="Synth Lead", type="midi")
        t2 = TrackNode(id=generate_id("track"), ableton_index=1, name="Synth Lead", type="midi")
        self.graph.add_track(t1)
        self.graph.add_track(t2)

        # Resolving by name "Synth Lead" must raise AmbiguousObjectError
        with self.assertRaises(AmbiguousObjectError) as ctx:
            self.resolver.resolve(name="Synth Lead")

        self.assertEqual(ctx.exception.details["matches_count"], 2)
        match_ids = [m["id"] for m in ctx.exception.details["matches"]]
        self.assertIn(t1.id, match_ids)
        self.assertIn(t2.id, match_ids)

        # Disambiguating by explicit ID works cleanly
        resolved = self.resolver.resolve(id=t1.id)
        self.assertEqual(resolved.id, t1.id)

    def test_single_resolution_by_role_and_tag(self):
        t1 = TrackNode(id=generate_id("track"), ableton_index=0, name="Sub", type="midi")
        t1.metadata.role = "SUB_BASS"
        t1.metadata.tags = ["low_end", "mono"]
        self.graph.add_track(t1)

        resolved_role = self.resolver.resolve(role="SUB_BASS")
        self.assertEqual(resolved_role.id, t1.id)

        resolved_tag = self.resolver.resolve(tags="mono")
        self.assertEqual(resolved_tag.id, t1.id)

    def test_not_found_resolution(self):
        with self.assertRaises(ObjectNotFoundError):
            self.resolver.resolve(name="NonexistentInstrument")

if __name__ == "__main__":
    unittest.main()

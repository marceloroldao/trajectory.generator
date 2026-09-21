import unittest

from trajectory_generator.weighted_path_trajectory import (
    WeightedEdge,
    WeightedPathCodec,
)


def reference_codec(width=None):
    edges = [
        WeightedEdge("AB1", "A", "B", 1, ("A", "B")),
        WeightedEdge(
            "AA12",
            "A",
            "A",
            12,
            tuple(["A"] + [f"x{i}" for i in range(1, 12)] + ["A"]),
        ),
        WeightedEdge("BA2", "B", "A", 2, ("B", "y", "A")),
        WeightedEdge("BA5", "B", "A", 5, ("B", "z1", "z2", "z3", "z4", "A")),
    ]
    return WeightedPathCodec(("A", "B"), edges, width=width)


class WeightedPathTrajectoryTests(unittest.TestCase):
    def test_all_small_exact_states_roundtrip(self):
        codec = reference_codec()
        for physical_steps in range(31):
            for state in range(codec.total_count(physical_steps)):
                start, edges = codec.decode_edges(state, physical_steps)
                got_state, got_steps = codec.encode_edges(
                    start,
                    [edge.label for edge in edges],
                )
                self.assertEqual((got_state, got_steps), (state, physical_steps))

    def test_physical_path_is_regenerated(self):
        codec = reference_codec()
        physical_steps = 30
        for state in range(codec.total_count(physical_steps)):
            path = codec.reconstruct_physical_path(state, physical_steps)
            self.assertEqual(len(path), physical_steps + 1)

    def test_63_bit_conservative_streaming_frontier(self):
        codec = reference_codec(width=63)
        self.assertTrue(codec.capacity_ok(233))
        self.assertFalse(codec.capacity_ok(234))
        self.assertTrue(codec.capacity_ok(235))

    def test_reverse_step_recovers_last_macro_edge(self):
        codec = reference_codec()
        state, t = codec.encode_edges("A", ["AB1", "BA5", "AA12"])
        state, t, edge = codec.reverse_step(state, t)
        self.assertEqual(edge.label, "AA12")
        state, t, edge = codec.reverse_step(state, t)
        self.assertEqual(edge.label, "BA5")
        state, t, edge = codec.reverse_step(state, t)
        self.assertEqual(edge.label, "AB1")
        self.assertEqual((state, t), (codec.initial_state("A"), 0))


if __name__ == "__main__":
    unittest.main()

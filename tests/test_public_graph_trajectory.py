import unittest

from trajectory_generator.public_graph_trajectory import (
    build_public_graph_codec,
    monotone_graph_frontier,
)


class PublicGraphTrajectoryTests(unittest.TestCase):
    def test_transient_and_recurrent_paths_roundtrip(self):
        graph = {
            "s": ["a", "b"],
            "a": ["c"],
            "b": ["c"],
            "c": ["c", "d"],
            "d": ["c"],
        }
        _, codec = build_public_graph_codec(
            graph,
            start_nodes=("s",),
            width=32,
        )

        for steps in range(10):
            for state in range(codec.total_count(steps)):
                start, edges = codec.decode_edges(state, steps)
                rebuilt, rebuilt_steps = codec.encode_edges(
                    start,
                    [edge.label for edge in edges],
                )
                self.assertEqual((rebuilt, rebuilt_steps), (state, steps))

                path = codec.reconstruct_physical_path(state, steps)
                self.assertEqual(path[0], "s")
                self.assertEqual(len(path), steps + 1)

    def test_parallel_edges_remain_distinct_trajectories(self):
        graph = {
            "s": ["a", "a"],
            "a": ["a"],
        }
        _, codec = build_public_graph_codec(
            graph,
            start_nodes=("s",),
            width=16,
        )

        self.assertEqual(codec.total_count(1), 2)
        decoded = [
            codec.decode_edges(state, 1)[1][0].label
            for state in range(2)
        ]
        self.assertEqual(len(set(decoded)), 2)

    def test_multiple_initial_nodes_are_encoded_in_address(self):
        graph = {
            "a": ["a"],
            "b": ["b"],
        }
        _, codec = build_public_graph_codec(
            graph,
            start_nodes=("a", "b"),
            width=8,
        )
        for steps in range(8):
            self.assertEqual(codec.total_count(steps), 2)
            starts = {
                codec.decode_edges(state, steps)[0]
                for state in range(2)
            }
            self.assertEqual(starts, {"a", "b"})

    def test_frontier_helper(self):
        graph = {
            "s": ["a", "b"],
            "a": ["a", "b"],
            "b": ["a", "b"],
        }
        _, codec = build_public_graph_codec(
            graph,
            start_nodes=("s",),
            width=8,
        )
        frontier = monotone_graph_frontier(codec)
        self.assertTrue(codec.capacity_ok(frontier))
        self.assertFalse(codec.capacity_ok(frontier + 1))


if __name__ == "__main__":
    unittest.main()

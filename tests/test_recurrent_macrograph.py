import unittest

from trajectory_generator.recurrent_macrograph import (
    build_physical_core_codec,
    component_spectral_radius,
    derive_recurrent_structure,
    dominant_recurrent_component,
    monotone_physical_frontier,
)


def synthetic_information_clock_graph():
    g = {}

    def add(source, target):
        g.setdefault(source, []).append(target)
        g.setdefault(target, [])

    add("A", "B")

    previous = "A"
    for i in range(1, 12):
        current = f"a{i}"
        add(previous, current)
        previous = current
    add(previous, "A")

    add("B", "y")
    add("y", "A")

    previous = "B"
    for i in range(1, 5):
        current = f"z{i}"
        add(previous, current)
        previous = current
    add(previous, "A")

    return g


class RecurrentMacrographTests(unittest.TestCase):
    def test_detects_macro_lengths_without_hardcoding(self):
        graph = synthetic_information_clock_graph()
        structure = derive_recurrent_structure(graph)

        self.assertEqual(set(structure.branch_nodes), {"A", "B"})
        self.assertEqual(
            sorted(edge.length for edge in structure.macro_edges),
            [1, 2, 5, 12],
        )

    def test_shifted_spectral_radius_handles_periodic_core(self):
        deterministic = {
            "x0": ["x1"],
            "x1": ["x2"],
            "x2": ["x0"],
        }
        self.assertAlmostEqual(
            component_spectral_radius(
                deterministic,
                set(deterministic),
            ),
            1.0,
            places=12,
        )

        graph = synthetic_information_clock_graph()
        lam = component_spectral_radius(
            graph,
            set(graph),
        )
        residual = (
            lam**12
            - lam**9
            - lam**6
            - 1.0
        )
        self.assertAlmostEqual(
            residual,
            0.0,
            places=10,
        )

    def test_physical_codec_covers_midflight_endpoints(self):
        graph = synthetic_information_clock_graph()
        structure, codec = build_physical_core_codec(graph, width=32)

        # Every exact physical prefix state is reversible, including endpoints
        # that are not information-clock branch nodes.
        for steps in range(16):
            for state in range(codec.total_count(steps)):
                start, edges = codec.decode_edges(state, steps)
                rebuilt, rebuilt_steps = codec.encode_edges(
                    start,
                    [edge.label for edge in edges],
                )
                self.assertEqual((rebuilt, rebuilt_steps), (state, steps))

                path = codec.reconstruct_physical_path(state, steps)
                self.assertEqual(len(path), steps + 1)

        internal_nodes = set(structure.component) - set(structure.branch_nodes)
        observed_internal_endpoint = False
        for state in range(codec.total_count(3)):
            path = codec.reconstruct_physical_path(state, 3)
            if path[-1] in internal_nodes:
                observed_internal_endpoint = True
                break
        self.assertTrue(observed_internal_endpoint)

    def test_prefers_branching_component_over_deterministic_cycle(self):
        graph = synthetic_information_clock_graph()
        graph.update({
            "d0": ["d1"],
            "d1": ["d2"],
            "d2": ["d0"],
        })
        component = dominant_recurrent_component(graph)
        self.assertIn("A", component)
        self.assertNotIn("d0", component)

    def test_deterministic_cycle_is_supported(self):
        graph = {
            "x0": ["x1"],
            "x1": ["x2"],
            "x2": ["x0"],
        }
        structure, codec = build_physical_core_codec(graph, width=8)

        self.assertEqual(len(structure.branch_nodes), 1)
        self.assertEqual(len(structure.macro_edges), 1)
        self.assertEqual(structure.macro_edges[0].length, 3)

        for steps in range(20):
            self.assertEqual(codec.total_count(steps), 3)
            for state in range(3):
                start, edges = codec.decode_edges(state, steps)
                rebuilt, rebuilt_steps = codec.encode_edges(
                    start,
                    [edge.label for edge in edges],
                )
                self.assertEqual((rebuilt, rebuilt_steps), (state, steps))

    def test_frontier_helper_is_consecutive(self):
        graph = synthetic_information_clock_graph()
        _, codec = build_physical_core_codec(graph, width=12)
        frontier = monotone_physical_frontier(codec)
        self.assertTrue(codec.capacity_ok(frontier))
        self.assertFalse(codec.capacity_ok(frontier + 1))


if __name__ == "__main__":
    unittest.main()

import unittest

from trajectory_generator.information_clock_statistics import (
    information_clock_statistics,
)
from trajectory_generator.recurrent_macrograph import (
    component_spectral_radius,
    derive_recurrent_structure,
)


def synthetic_information_clock_graph():
    graph = {}

    def add(source, target):
        graph.setdefault(source, []).append(target)
        graph.setdefault(target, [])

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

    return graph


class InformationClockStatisticsTests(unittest.TestCase):
    def test_balanced_synthetic_clock_identity(self):
        graph = synthetic_information_clock_graph()
        structure = derive_recurrent_structure(graph)
        lam = component_spectral_radius(
            graph,
            structure.component,
        )
        stats = information_clock_statistics(
            structure.branch_nodes,
            structure.macro_edges,
            growth_rate=lam,
        )

        self.assertAlmostEqual(
            stats.reconstructed_bits_per_physical_step,
            stats.bits_per_physical_step,
            places=11,
        )
        self.assertAlmostEqual(
            stats.average_physical_steps_per_event,
            2.59856,
            places=4,
        )
        self.assertAlmostEqual(
            stats.bits_per_information_event,
            0.70280,
            places=4,
        )
        self.assertLess(
            stats.maximum_row_probability_residual,
            1e-10,
        )
        self.assertLess(
            stats.stationary_residual,
            1e-10,
        )

    def test_single_branch_clock_is_supported(self):
        graph = {
            "A": ["x", "y"],
            "x": ["A"],
            "y": ["z"],
            "z": ["A"],
        }
        structure = derive_recurrent_structure(graph)
        stats = information_clock_statistics(
            structure.branch_nodes,
            structure.macro_edges,
            growth_rate=structure.growth_rate,
        )

        self.assertEqual(
            len(structure.branch_nodes),
            1,
        )
        self.assertEqual(
            len(stats.branch_stationary),
            1,
        )
        self.assertAlmostEqual(
            stats.branch_stationary[0],
            1.0,
            places=12,
        )
        self.assertAlmostEqual(
            stats.identity_residual,
            0.0,
            places=11,
        )


if __name__ == "__main__":
    unittest.main()

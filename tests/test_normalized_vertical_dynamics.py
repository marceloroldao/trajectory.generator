import unittest

from trajectory_generator.information_clock_statistics import (
    information_clock_statistics,
)
from trajectory_generator.normalized_vertical_dynamics import (
    exact_normalized_block_width,
    exact_target_partition_residual,
    normalized_forward,
    normalized_reverse,
    reverse_parry_geometry,
)
from trajectory_generator.recurrent_macrograph import (
    derive_recurrent_structure,
)


class NormalizedVerticalDynamicsTests(unittest.TestCase):
    def test_exact_block_widths_partition_target_fiber(self):
        edges = {
            "a": ["c"],
            "b": ["c"],
            "c": ["a", "b"],
        }
        structure = derive_recurrent_structure(edges)

        counts_before = {
            "a": 2,
            "b": 3,
            "c": 5,
        }
        counts_after = {
            "a": 5,
            "b": 5,
            "c": 5,
        }

        physical = structure.physical_edges
        residual = exact_target_partition_residual(
            counts_before,
            counts_after,
            physical,
        )
        self.assertAlmostEqual(
            residual,
            0.0,
            places=12,
        )

        incoming_c = [
            edge
            for edge in physical
            if edge.target == "c"
        ]
        widths = sorted(
            exact_normalized_block_width(
                counts_before,
                counts_after,
                edge,
            )
            for edge in incoming_c
        )
        self.assertEqual(
            widths,
            [0.4, 0.6],
        )

    def test_affine_normalization_roundtrip(self):
        for local in (0.0, 0.1, 0.5, 0.999):
            target = normalized_forward(
                local,
                block_offset=0.3,
                block_width=0.2,
            )
            recovered = normalized_reverse(
                target,
                block_offset=0.3,
                block_width=0.2,
            )
            self.assertAlmostEqual(
                recovered,
                local,
                places=12,
            )

    def test_reverse_parry_entropy_matches_physical_rate(self):
        graph = {
            "A": ["A", "B"],
            "B": ["A"],
        }
        structure = derive_recurrent_structure(graph)
        stats = information_clock_statistics(
            structure.component,
            structure.physical_edges,
            growth_rate=structure.growth_rate,
        )
        reverse = reverse_parry_geometry(
            structure.component,
            stats,
        )

        self.assertLess(
            reverse.maximum_target_normalization_residual,
            1e-10,
        )
        self.assertAlmostEqual(
            reverse.expected_reverse_information_bits,
            stats.bits_per_physical_step,
            places=11,
        )


if __name__ == "__main__":
    unittest.main()

import unittest

from trajectory_generator.fiber_bundle_geometry import (
    ceil_log2_int,
    fiber_bundle_geometry,
)


class FiberBundleGeometryTests(unittest.TestCase):
    def test_uniform_fibers_are_exact_cartesian_product(self):
        row = fiber_bundle_geometry(
            {"a": 4, "b": 4, "c": 4},
            total_base_states=3,
        )
        self.assertFalse(row.fibers_are_nonuniform)
        self.assertEqual(
            row.active_rectangular_slots,
            row.total_histories,
        )
        self.assertAlmostEqual(
            row.active_rectangular_occupancy,
            1.0,
            places=12,
        )
        self.assertAlmostEqual(
            row.active_rectangular_redundancy_bits,
            0.0,
            places=12,
        )

    def test_nonuniform_fibers_require_rectangular_padding(self):
        row = fiber_bundle_geometry(
            {"a": 1, "b": 3, "c": 8, "d": 0},
            total_base_states=4,
        )
        self.assertTrue(row.fibers_are_nonuniform)
        self.assertEqual(row.total_histories, 12)
        self.assertEqual(row.maximum_fiber, 8)
        self.assertEqual(row.active_rectangular_slots, 24)
        self.assertLess(
            row.active_rectangular_occupancy,
            1.0,
        )
        self.assertGreater(
            row.active_rectangular_redundancy_bits,
            0.0,
        )
        self.assertGreaterEqual(
            row.full_rectangular_integer_bits,
            row.optimal_integer_bits,
        )

    def test_integer_ceiling(self):
        expected = {
            1: 0,
            2: 1,
            3: 2,
            4: 2,
            5: 3,
            8: 3,
            9: 4,
        }
        for value, bits in expected.items():
            self.assertEqual(
                ceil_log2_int(value),
                bits,
            )


if __name__ == "__main__":
    unittest.main()

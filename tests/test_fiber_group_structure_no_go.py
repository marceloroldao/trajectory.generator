import unittest

from trajectory_generator.fiber_group_structure_no_go import (
    all_set_relabelings,
    canonical_origin_exists_from_cardinality,
    common_fixed_points,
)


class FiberGroupStructureNoGoTests(unittest.TestCase):
    def test_only_singleton_has_canonical_origin(self):
        self.assertTrue(
            canonical_origin_exists_from_cardinality(1)
        )
        for size in range(2, 8):
            self.assertFalse(
                canonical_origin_exists_from_cardinality(
                    size
                )
            )

    def test_full_symmetric_group_has_no_common_fixed_point(self):
        for size in range(2, 8):
            gauges = all_set_relabelings(size)
            self.assertEqual(
                common_fixed_points(gauges),
                (),
            )


if __name__ == "__main__":
    unittest.main()

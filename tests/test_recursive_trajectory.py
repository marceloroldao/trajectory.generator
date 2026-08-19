import unittest

from trajectory_generator.recursive_trajectory import (
    RecursiveTrajectoryConfig,
    address_envelope_count,
    capacity_ok,
    choose_level,
    decode_recursive_trajectory,
    encode_recursive_trajectory,
    inverse_level,
    transform_level,
)


class RecursiveTrajectoryTests(unittest.TestCase):
    def test_transform_round_trip_levels(self):
        patterns = [
            [],
            [0],
            [1],
            [0, 1] * 16,
            [0, 0, 1, 1] * 8,
            [0, 0, 0, 0, 1, 1, 1, 1] * 4,
        ]
        for bits in patterns:
            for level in range(5):
                self.assertEqual(inverse_level(transform_level(bits, level), level), bits)

    def test_recursive_level_finds_pattern_of_patterns(self):
        cfg = RecursiveTrajectoryConfig(width=63, max_deviations=5, max_level=3)
        alternating = [0, 1] * 16
        level, deviations = choose_level(alternating, cfg)
        self.assertEqual(level, 2)
        self.assertEqual(deviations, 1)

        period_0011 = [0, 0, 1, 1] * 8
        level, deviations = choose_level(period_0011, cfg)
        self.assertEqual(level, 3)
        self.assertEqual(deviations, 1)

    def test_address_round_trip(self):
        cfg = RecursiveTrajectoryConfig(width=63, max_deviations=5, max_level=3)
        samples = [
            [0] * 100,
            [1] * 100,
            [0, 1] * 100,
            [0, 0, 1, 1] * 100,
        ]
        for bits in samples:
            state, steps = encode_recursive_trajectory(bits, cfg)
            self.assertEqual(decode_recursive_trajectory(state, steps, cfg), bits)

    def test_63bit_capacity_frontier(self):
        cfg = RecursiveTrajectoryConfig(width=63, max_deviations=5, max_level=3)
        self.assertTrue(capacity_ok(10672, cfg))
        self.assertFalse(capacity_ok(10673, cfg))
        self.assertLessEqual(address_envelope_count(10672, cfg), 1 << 63)
        self.assertGreater(address_envelope_count(10673, cfg), 1 << 63)


if __name__ == "__main__":
    unittest.main()

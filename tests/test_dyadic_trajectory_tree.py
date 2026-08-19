import unittest

from trajectory_generator import (
    DyadicTrajectoryConfig,
    decode_dyadic_trajectory,
    dyadic_capacity_ok,
    encode_dyadic_trajectory,
)


class DyadicTrajectoryTreeTests(unittest.TestCase):
    def test_roundtrip_unsplit(self):
        cfg = DyadicTrajectoryConfig(width=32, max_deviations=3, max_level=3)
        bits = [0, 1] * 16
        state, steps = encode_dyadic_trajectory(bits, cfg)
        self.assertEqual(decode_dyadic_trajectory(state, steps, cfg), bits)

    def test_roundtrip_midpoint_split(self):
        cfg = DyadicTrajectoryConfig(width=32, max_deviations=3, max_level=3)
        left = [0, 1] * 8
        right = [0, 0, 1, 1] * 4
        bits = left + right
        state, steps = encode_dyadic_trajectory(bits, cfg)
        self.assertEqual(decode_dyadic_trajectory(state, steps, cfg), bits)

    def test_default_capacity_frontier(self):
        cfg = DyadicTrajectoryConfig()
        self.assertTrue(dyadic_capacity_ok(274, cfg))
        self.assertFalse(dyadic_capacity_ok(275, cfg))


if __name__ == "__main__":
    unittest.main()

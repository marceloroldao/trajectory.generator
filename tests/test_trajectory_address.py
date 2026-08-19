import random
import unittest

from trajectory_generator import (
    TrajectoryAddressConfig,
    decode_trajectory_address,
    encode_trajectory_address,
)


class TrajectoryAddressTests(unittest.TestCase):
    def test_exhaustive_small_widths(self):
        for width in (4, 6, 8):
            cfg = TrajectoryAddressConfig(width=width)
            for steps in range(width + 1):
                for value in range(1 << steps):
                    bits = [(value >> shift) & 1 for shift in range(steps - 1, -1, -1)]
                    final_state, count = encode_trajectory_address(bits, cfg)
                    self.assertEqual(count, steps)
                    self.assertEqual(
                        decode_trajectory_address(final_state, steps, cfg),
                        bits,
                    )

    def test_random_full_capacity_63_bits(self):
        cfg = TrajectoryAddressConfig(width=63)
        rng = random.Random(20260819)
        for _ in range(100):
            bits = [rng.randrange(2) for _ in range(63)]
            final_state, steps = encode_trajectory_address(bits, cfg)
            self.assertEqual(
                decode_trajectory_address(final_state, steps, cfg),
                bits,
            )

    def test_rejects_over_capacity(self):
        cfg = TrajectoryAddressConfig(width=8)
        with self.assertRaises(ValueError):
            encode_trajectory_address([0] * 9, cfg)
        with self.assertRaises(ValueError):
            decode_trajectory_address(0, 9, cfg)


if __name__ == "__main__":
    unittest.main()

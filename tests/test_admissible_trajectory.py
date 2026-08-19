import unittest

from trajectory_generator.admissible_trajectory import (
    PeriodicAdmissibilityConfig,
    admissible_count,
    capacity_ok,
    decode_admissible_trajectory,
    encode_admissible_trajectory,
    free_count,
    unrank_admissible,
    validate_trajectory,
)


class PeriodicAdmissibilityTests(unittest.TestCase):
    def test_default_frontier(self):
        cfg = PeriodicAdmissibilityConfig(width=63, period=3)
        self.assertEqual(free_count(94, cfg), 63)
        self.assertTrue(capacity_ok(94, cfg))
        self.assertEqual(free_count(95, cfg), 64)
        self.assertFalse(capacity_ok(95, cfg))

    def test_exact_roundtrip_from_rank(self):
        cfg = PeriodicAdmissibilityConfig(width=16, period=3)
        for steps in range(0, 20):
            if not capacity_ok(steps, cfg):
                break
            for rank in range(min(admissible_count(steps, cfg), 256)):
                bits = unrank_admissible(rank, steps, cfg)
                self.assertTrue(validate_trajectory(bits, cfg))
                state, n = encode_admissible_trajectory(bits, cfg)
                self.assertEqual(n, steps)
                self.assertEqual(decode_admissible_trajectory(state, n, cfg), bits)

    def test_invalid_forced_bit_is_rejected(self):
        cfg = PeriodicAdmissibilityConfig(width=16, period=3)
        bits = unrank_admissible(3, 9, cfg)
        bits[2] ^= 1
        self.assertFalse(validate_trajectory(bits, cfg))
        with self.assertRaises(ValueError):
            encode_admissible_trajectory(bits, cfg)


if __name__ == "__main__":
    unittest.main()

import unittest

from trajectory_generator.state_admissibility import (
    StateAdmissibilityConfig,
    admissible_count,
    capacity_ok,
    decode_state_admissible,
    encode_state_admissible,
    rank_trajectory,
    unrank_trajectory,
    validate_trajectory,
)


class StateAdmissibilityTests(unittest.TestCase):
    def test_counts_follow_fibonacci_sequence(self):
        expected = [1, 2, 4, 6, 10, 16, 26, 42, 68, 110, 178]
        self.assertEqual([admissible_count(n) for n in range(len(expected))], expected)

    def test_exact_rank_unrank_small_domains(self):
        cfg = StateAdmissibilityConfig(width=16)
        for steps in range(0, 11):
            for rank in range(admissible_count(steps)):
                bits = unrank_trajectory(rank, steps, cfg)
                self.assertTrue(validate_trajectory(bits))
                self.assertEqual(rank_trajectory(bits, cfg)[0], rank)
                state, n = encode_state_admissible(bits, cfg)
                self.assertEqual(decode_state_admissible(state, n, cfg), bits)

    def test_default_63_bit_frontier(self):
        cfg = StateAdmissibilityConfig(width=63)
        self.assertTrue(capacity_ok(89, cfg))
        self.assertFalse(capacity_ok(90, cfg))


if __name__ == "__main__":
    unittest.main()

import unittest

from trajectory_generator.dynamic_policy_universe import (
    admissible_count,
    capacity_ok,
    encode_dynamic_policy_universe,
    decode_dynamic_policy_universe,
    unrank_trajectory,
)


class DynamicPolicyUniverseTests(unittest.TestCase):
    def test_small_exhaustive_round_trip(self):
        for steps in range(0, 9):
            total = admissible_count(steps)
            for rank in range(total):
                bits = unrank_trajectory(rank, steps)
                final_state, got_steps = encode_dynamic_policy_universe(bits)
                self.assertEqual(got_steps, steps)
                self.assertEqual(decode_dynamic_policy_universe(final_state, steps), bits)

    def test_63_bit_frontier(self):
        self.assertTrue(capacity_ok(184))
        self.assertFalse(capacity_ok(185))
        self.assertEqual(admissible_count(184), 1 << 63)
        self.assertEqual(admissible_count(185), 1 << 64)


if __name__ == "__main__":
    unittest.main()

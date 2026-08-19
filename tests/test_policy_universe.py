import unittest

from trajectory_generator.policy_universe import (
    BALANCED_POLICY_WEIGHTS,
    PolicyUniverseConfig,
    admissible_count,
    decode_policy_universe,
    encode_policy_universe,
    unrank_trajectory,
)


class PolicyUniverseTests(unittest.TestCase):
    def test_exhaustive_small_roundtrip(self):
        cfg = PolicyUniverseConfig(width=16, weights=BALANCED_POLICY_WEIGHTS)
        for steps in range(0, 9):
            total = admissible_count(steps, cfg)
            self.assertLessEqual(total, 1 << cfg.width)
            for rank in range(total):
                bits = unrank_trajectory(rank, steps, cfg)
                final_state, got_steps = encode_policy_universe(bits, cfg)
                self.assertEqual(got_steps, steps)
                self.assertEqual(decode_policy_universe(final_state, steps, cfg), bits)

    def test_default_frontier_184(self):
        cfg = PolicyUniverseConfig(width=63, weights=BALANCED_POLICY_WEIGHTS)
        self.assertLessEqual(admissible_count(184, cfg), 1 << 63)
        self.assertGreater(admissible_count(185, cfg), 1 << 63)


if __name__ == "__main__":
    unittest.main()

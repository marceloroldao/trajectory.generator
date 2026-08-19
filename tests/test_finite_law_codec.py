import unittest
from itertools import product

from trajectory_generator.finite_law_codec import (
    FiniteLawConfig,
    MEMORY3_PHI_RULE,
    MEMORY3_PLASTIC_RULE,
    MEMORY3_TRIBONACCI_RULE,
    admissible_count,
    decode_finite_law,
    encode_finite_law,
    rank_trajectory,
    unrank_trajectory,
    validate,
)


class FiniteLawCodecTests(unittest.TestCase):
    def _roundtrip_all(self, cfg: FiniteLawConfig, steps: int):
        total = admissible_count(steps, cfg)
        for rank in range(total):
            bits = unrank_trajectory(rank, steps, cfg)
            self.assertTrue(validate(bits, cfg))
            rank2, steps2 = rank_trajectory(bits, cfg)
            self.assertEqual(rank, rank2)
            self.assertEqual(steps, steps2)
            final_state, n = encode_finite_law(bits, cfg)
            self.assertEqual(n, steps)
            self.assertEqual(bits, decode_finite_law(final_state, n, cfg))

    def test_small_exhaustive_phi_rule(self):
        cfg = FiniteLawConfig(rule=MEMORY3_PHI_RULE, memory=3, width=16)
        for steps in range(0, 9):
            self._roundtrip_all(cfg, steps)

    def test_small_exhaustive_plastic_rule(self):
        cfg = FiniteLawConfig(rule=MEMORY3_PLASTIC_RULE, memory=3, width=16)
        for steps in range(0, 9):
            self._roundtrip_all(cfg, steps)

    def test_small_exhaustive_tribonacci_rule(self):
        cfg = FiniteLawConfig(rule=MEMORY3_TRIBONACCI_RULE, memory=3, width=16)
        for steps in range(0, 8):
            self._roundtrip_all(cfg, steps)

    def test_rejects_invalid_trajectory(self):
        cfg = FiniteLawConfig(rule=(0,) * 8, memory=3, width=16)
        self.assertTrue(validate([0, 0, 0, 0], cfg))
        self.assertFalse(validate([0, 0, 0, 1], cfg))


if __name__ == "__main__":
    unittest.main()

import unittest

from trajectory_generator.emergent_law_bank import (
    ALL_RULES,
    DEFAULT_EMERGENT_LAW_BANK_CONFIG,
    admissible_count,
    decode_emergent_law_bank,
    encode_emergent_law_bank,
    selected_rule_index,
    unrank_trajectory,
)


class EmergentLawBankTests(unittest.TestCase):
    def test_bank_size(self):
        self.assertEqual(len(ALL_RULES), 6561)

    def test_selector_is_public_and_deterministic(self):
        for phase in range(3):
            for state in range(8):
                a = selected_rule_index(state, phase)
                b = selected_rule_index(state, phase)
                self.assertEqual(a, b)
                self.assertTrue(0 <= a < 6561)

    def test_exhaustive_roundtrip_small_lengths(self):
        cfg = DEFAULT_EMERGENT_LAW_BANK_CONFIG
        for steps in range(0, 11):
            total = admissible_count(steps)
            for rank in range(total):
                bits = unrank_trajectory(rank, steps, cfg)
                final_state, got_steps = encode_emergent_law_bank(bits, cfg)
                self.assertEqual(got_steps, steps)
                recovered = decode_emergent_law_bank(final_state, steps, cfg)
                self.assertEqual(recovered, bits)

    def test_63bit_frontier(self):
        cfg = DEFAULT_EMERGENT_LAW_BANK_CONFIG
        self.assertLessEqual(admissible_count(80), 1 << cfg.width)
        self.assertGreater(admissible_count(81), 1 << cfg.width)


if __name__ == "__main__":
    unittest.main()

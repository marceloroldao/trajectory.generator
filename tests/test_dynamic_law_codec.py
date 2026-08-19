import unittest

from trajectory_generator.dynamic_law_codec import (
    DEFAULT_DYNAMIC_CONFIG,
    admissible_count,
    decode_dynamic_law,
    encode_dynamic_law,
    unrank_trajectory,
    validate,
)


class DynamicLawCodecTests(unittest.TestCase):
    def test_small_families_roundtrip_exhaustively(self):
        cfg = DEFAULT_DYNAMIC_CONFIG
        for steps in range(0, 13):
            total = admissible_count(steps, cfg)
            for rank in range(total):
                bits = unrank_trajectory(rank, steps, cfg)
                self.assertTrue(validate(bits, cfg))
                final_state, returned_steps = encode_dynamic_law(bits, cfg)
                self.assertEqual(returned_steps, steps)
                self.assertEqual(decode_dynamic_law(final_state, steps, cfg), bits)

    def test_rule_schedule_is_not_external(self):
        cfg = DEFAULT_DYNAMIC_CONFIG
        steps = 20
        total = admissible_count(steps, cfg)
        for rank in (0, total // 3, total // 2, total - 1):
            bits = unrank_trajectory(rank, steps, cfg)
            final_state, _ = encode_dynamic_law(bits, cfg)
            recovered = decode_dynamic_law(final_state, steps, cfg)
            self.assertEqual(recovered, bits)


if __name__ == "__main__":
    unittest.main()

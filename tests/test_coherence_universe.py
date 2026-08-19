import unittest

from trajectory_generator.coherence_universe import (
    DEFAULT_COHERENCE_UNIVERSE_CONFIG as CFG,
    admissible_count,
    decode_coherence_universe,
    encode_coherence_universe,
    unrank_trajectory,
    validate,
)


class CoherenceUniverseTests(unittest.TestCase):
    def test_small_family_roundtrip(self):
        for steps in range(0, 9):
            total = admissible_count(steps, CFG)
            for rank in range(total):
                bits = unrank_trajectory(rank, steps, CFG)
                self.assertTrue(validate(bits, CFG))
                final_state, recovered_steps = encode_coherence_universe(bits, CFG)
                self.assertEqual(recovered_steps, steps)
                self.assertEqual(decode_coherence_universe(final_state, steps, CFG), bits)

    def test_frontier(self):
        self.assertLessEqual(admissible_count(117, CFG), 1 << 63)
        self.assertGreater(admissible_count(118, CFG), 1 << 63)


if __name__ == "__main__":
    unittest.main()

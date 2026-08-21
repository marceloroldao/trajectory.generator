import unittest

from trajectory_generator.coherence_memory_universe import (
    CoherenceMemoryConfig,
    admissible_count,
    decode_coherence_memory,
    encode_coherence_memory,
    unrank_trajectory,
)


class CoherenceMemoryUniverseTests(unittest.TestCase):
    def test_small_exhaustive_roundtrip_default(self):
        cfg = CoherenceMemoryConfig(width=32)
        for steps in range(0, 10):
            total = admissible_count(steps, cfg)
            for rank in range(total):
                bits = unrank_trajectory(rank, steps, cfg)
                state, n = encode_coherence_memory(bits, cfg)
                self.assertEqual(n, steps)
                self.assertEqual(decode_coherence_memory(state, n, cfg), bits)

    def test_alternate_update_modes(self):
        for mode in ("occupancy", "signed_bit", "rolling"):
            cfg = CoherenceMemoryConfig(width=32, update_mode=mode, policy_map=(1, 0, 3, 4))
            for steps in range(3, 9):
                total = admissible_count(steps, cfg)
                for rank in range(min(total, 256)):
                    bits = unrank_trajectory(rank, steps, cfg)
                    state, n = encode_coherence_memory(bits, cfg)
                    self.assertEqual(decode_coherence_memory(state, n, cfg), bits)


if __name__ == "__main__":
    unittest.main()

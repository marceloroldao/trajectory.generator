import unittest

from trajectory_generator.coherence_memory_universe import (
    BALANCED_COHERENCE_MEMORY_CONFIG,
    LONG_FRONTIER_COHERENCE_MEMORY_CONFIG,
    CoherenceMemoryConfig,
    admissible_count,
    capacity_ok,
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

    def test_balanced_frontier_187_188(self):
        cfg = BALANCED_COHERENCE_MEMORY_CONFIG
        self.assertEqual(admissible_count(187, cfg), 8070450532247928961)
        self.assertEqual(admissible_count(188, cfg), 16140901064495857795)
        self.assertTrue(capacity_ok(187, cfg))
        self.assertFalse(capacity_ok(188, cfg))

    def test_long_frontier_244_245(self):
        cfg = LONG_FRONTIER_COHERENCE_MEMORY_CONFIG
        self.assertEqual(admissible_count(244, cfg), 8887676923343977346)
        self.assertEqual(admissible_count(245, cfg), 14225417450507601237)
        self.assertTrue(capacity_ok(244, cfg))
        self.assertFalse(capacity_ok(245, cfg))


if __name__ == "__main__":
    unittest.main()

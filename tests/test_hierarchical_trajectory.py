import unittest

from trajectory_generator import (
    HierarchicalTrajectoryConfig,
    admissible_count,
    capacity_ok,
    decode_hierarchical_trajectory,
    encode_hierarchical_trajectory,
    rank_trajectory,
    unrank_trajectory,
)


class HierarchicalTrajectoryTests(unittest.TestCase):
    def test_rank_unrank_all_small_admissible_trajectories(self):
        cfg = HierarchicalTrajectoryConfig(width=16, max_changes=2)
        for steps in range(1, 9):
            for value in range(1 << steps):
                bits = [(value >> shift) & 1 for shift in range(steps - 1, -1, -1)]
                changes = sum(bits[i] != bits[i - 1] for i in range(1, steps))
                if changes > cfg.max_changes:
                    continue
                rank, got_steps = rank_trajectory(bits, cfg)
                self.assertEqual(got_steps, steps)
                self.assertEqual(unrank_trajectory(rank, steps, cfg), bits)

    def test_final_state_plus_steps_recovers_exactly(self):
        cfg = HierarchicalTrajectoryConfig(width=24, max_changes=3)
        cases = [
            [0] * 64,
            [1] * 64,
            [0] * 10 + [1] * 20 + [0] * 34,
            [1] * 5 + [0] * 9 + [1] * 17 + [0] * 33,
        ]
        for bits in cases:
            final_state, steps = encode_hierarchical_trajectory(bits, cfg)
            recovered = decode_hierarchical_trajectory(final_state, steps, cfg)
            self.assertEqual(recovered, bits)

    def test_capacity_count_matches_exhaustive_small_domain(self):
        cfg = HierarchicalTrajectoryConfig(width=16, max_changes=2)
        steps = 8
        expected = 0
        for value in range(1 << steps):
            bits = [(value >> shift) & 1 for shift in range(steps - 1, -1, -1)]
            changes = sum(bits[i] != bits[i - 1] for i in range(1, steps))
            expected += changes <= cfg.max_changes
        self.assertEqual(admissible_count(steps, cfg), expected)

    def test_63bit_five_change_family_supports_14082_steps(self):
        cfg = HierarchicalTrajectoryConfig(width=63, max_changes=5)
        self.assertTrue(capacity_ok(14082, cfg))
        self.assertFalse(capacity_ok(14083, cfg))


if __name__ == "__main__":
    unittest.main()

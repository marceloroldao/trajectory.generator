import unittest

from trajectory_generator import (
    MultiScaleTrajectoryConfig,
    choose_mode,
    decode_multiscale_trajectory,
    deviation_count,
    encode_multiscale_trajectory,
    inverse_transform,
    multiscale_capacity_ok,
    transform,
)


class MultiScaleTrajectoryTests(unittest.TestCase):
    def test_transform_roundtrip(self):
        for mode in ("local", "fenwick"):
            for bits in (
                [0],
                [1],
                [0, 1, 1, 0, 1, 0, 0, 1],
                [0, 0, 1, 1] * 8,
                [0, 0, 0, 0, 1, 1, 1, 1] * 4,
            ):
                self.assertEqual(inverse_transform(transform(bits, mode), mode), bits)

    def test_fenwick_sees_block_pattern_at_coarser_scale(self):
        bits = [0, 0, 0, 0, 1, 1, 1, 1] * 4
        self.assertEqual(deviation_count(bits, "local"), 7)
        self.assertEqual(deviation_count(bits, "fenwick"), 4)

    def test_mode_selection_prefers_hierarchical_view(self):
        cfg = MultiScaleTrajectoryConfig(width=63, max_deviations=5)
        bits = [0, 0, 0, 0, 1, 1, 1, 1] * 4
        mode, score = choose_mode(bits, cfg)
        self.assertEqual(mode, "fenwick")
        self.assertEqual(score, 4)

    def test_end_to_end_recovery_uses_final_state_and_steps(self):
        cfg = MultiScaleTrajectoryConfig(width=32, max_deviations=5)
        bits = [0, 0, 0, 0, 1, 1, 1, 1] * 4
        final_state, steps = encode_multiscale_trajectory(bits, cfg)
        self.assertEqual(decode_multiscale_trajectory(final_state, steps, cfg), bits)

    def test_63_bit_capacity_frontier_for_two_modes_k5(self):
        cfg = MultiScaleTrajectoryConfig(width=63, max_deviations=5)
        self.assertTrue(multiscale_capacity_ok(12259, cfg))
        self.assertFalse(multiscale_capacity_ok(12260, cfg))


if __name__ == "__main__":
    unittest.main()

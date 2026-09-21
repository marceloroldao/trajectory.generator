import unittest

from trajectory_generator.hierarchical_trajectory import (
    HierarchicalTrajectoryConfig,
    admissible_count as hierarchical_count,
)
from trajectory_generator.streaming_colex_trajectory import (
    StreamingColexConfig,
    admissible_count,
    capacity_ok,
    decode,
    encode,
    forward_step,
    reverse_step,
)


class StreamingColexTrajectoryTests(unittest.TestCase):
    def test_family_matches_hierarchical_count(self):
        hcfg = HierarchicalTrajectoryConfig(width=63, max_changes=5)
        scfg = StreamingColexConfig(width=63, max_changes=5)
        for steps in (0, 1, 2, 10, 100, 1000, 14082):
            self.assertEqual(
                admissible_count(steps, scfg),
                hierarchical_count(steps, hcfg),
            )

    def test_exhaustive_small_family(self):
        cfg = StreamingColexConfig(width=32, max_changes=3)
        steps = 10
        seen = set()
        checked = 0

        for word in range(1 << steps):
            bits = [(word >> i) & 1 for i in range(steps)]
            changes = sum(bits[i] != bits[i - 1] for i in range(1, steps))
            if changes > cfg.max_changes:
                continue

            state, got_steps = encode(bits, cfg)
            self.assertEqual(got_steps, steps)
            self.assertNotIn(state, seen)
            seen.add(state)
            self.assertEqual(decode(state, steps, cfg), bits)
            checked += 1

        self.assertEqual(checked, admissible_count(steps, cfg))
        self.assertEqual(len(seen), checked)

    def test_stepwise_reverse_matches_every_prefix(self):
        cfg = StreamingColexConfig(width=32, max_changes=4)
        bits = [1, 1, 0, 0, 0, 1, 1, 0, 0]
        state = 0
        steps = 0
        history = [(state, steps)]

        for bit in bits:
            state, steps = forward_step(state, steps, bit, cfg)
            history.append((state, steps))

        current = state
        n = steps
        for i in range(len(bits) - 1, -1, -1):
            current, n, recovered, _ = reverse_step(current, n, cfg)
            self.assertEqual(recovered, bits[i])
            self.assertEqual((current, n), history[i])

    def test_63_bit_frontier_and_full_length_roundtrip(self):
        cfg = StreamingColexConfig(width=63, max_changes=5)
        self.assertTrue(capacity_ok(14082, cfg))
        self.assertFalse(capacity_ok(14083, cfg))

        change_positions = {1, 100, 1000, 5000, 14081}
        bits = [0] * 14082
        current = 0
        for i in range(14082):
            if i in change_positions:
                current ^= 1
            bits[i] = current

        state, steps = encode(bits, cfg)
        self.assertLess(state, 1 << 63)
        self.assertEqual(steps, 14082)
        self.assertEqual(decode(state, steps, cfg), bits)

    def test_change_budget_exhaustion_is_rejected(self):
        cfg = StreamingColexConfig(width=16, max_changes=1)
        state = 0
        steps = 0
        state, steps = forward_step(state, steps, 0, cfg)
        state, steps = forward_step(state, steps, 1, cfg)
        with self.assertRaises(ValueError):
            forward_step(state, steps, 0, cfg)


if __name__ == "__main__":
    unittest.main()

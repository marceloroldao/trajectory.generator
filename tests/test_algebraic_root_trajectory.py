import itertools
import random
import unittest

from trajectory_generator.algebraic_root_trajectory import (
    decode,
    encode,
    forward_step,
    pack_state,
    reverse_step,
    state_width_bits,
    unpack_state,
    zero_state,
)


class AlgebraicRootTrajectoryTests(unittest.TestCase):
    def test_exhaustive_k3_t10(self):
        p = 17
        k = 3
        steps = 10
        seen = set()

        for positions_count in range(k + 1):
            for positions in itertools.combinations(range(steps), positions_count):
                bits = [0] * steps
                for i in positions:
                    bits[i] = 1

                state = encode(bits, k, p)
                packed = pack_state(state, p)

                self.assertNotIn(packed, seen)
                seen.add(packed)
                self.assertEqual(unpack_state(packed, k, p), state)
                self.assertEqual(decode(state, steps, p), bits)

        self.assertEqual(len(seen), 176)

    def test_reverse_step_is_local(self):
        p = 31
        k = 3
        state = zero_state(k)
        history = []

        bits = [0, 1, 0, 0, 1, 0, 1, 0]
        for t, bit in enumerate(bits):
            history.append(state)
            state = forward_step(state, bit, t, p)

        current = state
        recovered = []
        for t in range(len(bits) - 1, -1, -1):
            current, bit = reverse_step(current, t, p)
            recovered.append(bit)
            self.assertEqual(current, history[t])

        self.assertEqual(list(reversed(recovered)), bits)
        self.assertEqual(current, zero_state(k))

    def test_large_63_bit_reference(self):
        p = 6203
        k = 5
        steps = 6202
        self.assertEqual(state_width_bits(k, p), 63)

        rng = random.Random(0xC0FFEE)
        positions = rng.sample(range(steps), k)
        bits = [0] * steps
        for i in positions:
            bits[i] = 1

        state = encode(bits, k, p)
        self.assertEqual(decode(state, steps, p), bits)
        self.assertLess(pack_state(state, p), 1 << 63)

    def test_budget_exhaustion_is_rejected(self):
        p = 17
        k = 2
        state = zero_state(k)
        state = forward_step(state, 1, 0, p)
        state = forward_step(state, 1, 1, p)
        with self.assertRaises(ValueError):
            forward_step(state, 1, 2, p)

    def test_horizon_alias_is_rejected(self):
        p = 17
        with self.assertRaises(ValueError):
            decode(zero_state(2), p, p)


if __name__ == "__main__":
    unittest.main()

import unittest

from trajectory_generator import (
    MachineConfig,
    decode_exhaustive,
    encode_bits,
    int_to_bits,
    step_forward,
    step_inverse,
)


class ReversibleCoreTests(unittest.TestCase):
    def test_step_inverse_for_both_bits(self):
        cfg = MachineConfig(width=16)
        for t in range(24):
            for bit in (0, 1):
                for x in (0, 1, 7, 0x1234, cfg.mask):
                    y = step_forward(x, bit, t, cfg)
                    self.assertEqual(step_inverse(y, bit, t, cfg), x & cfg.mask)

    def test_exact_recovery_small_domain(self):
        cfg = MachineConfig(width=16)
        for value in range(1 << 8):
            bits = int_to_bits(value, 8)
            final_state, steps = encode_bits(bits, cfg)
            result = decode_exhaustive(final_state, steps, cfg, max_matches=2)
            self.assertTrue(result.unique)
            self.assertEqual(result.bits, bits)

    def test_order_matters_for_selected_pair(self):
        cfg = MachineConfig(width=16)
        a = [1, 0, 0, 1, 1, 0, 1, 0]
        b = [0, 1, 0, 1, 1, 0, 1, 0]
        xa, _ = encode_bits(a, cfg)
        xb, _ = encode_bits(b, cfg)
        self.assertNotEqual(xa, xb)


if __name__ == "__main__":
    unittest.main()

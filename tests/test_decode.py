import unittest

from trajectory_generator import (
    DEFAULT_CONFIG,
    decode_exhaustive,
    decode_mitm,
    encode_bits,
    int_to_bits,
    recover_unique,
)


class TestDecode(unittest.TestCase):
    def test_mitm_matches_exhaustive_small_domain(self):
        for n in range(1, 9):
            for value in range(1 << n):
                bits = int_to_bits(value, n)
                final_state, steps = encode_bits(bits, DEFAULT_CONFIG)
                a = decode_exhaustive(final_state, steps, max_matches=2)
                b = decode_mitm(final_state, steps, max_matches=2)
                self.assertEqual(a.matches, b.matches)

    def test_mitm_recovers_22_bit_trajectory(self):
        bits = int_to_bits(0x2A55AA, 22)
        final_state, steps = encode_bits(bits, DEFAULT_CONFIG)
        result = decode_mitm(final_state, steps)
        self.assertTrue(result.unique)
        self.assertEqual(result.bits, bits)
        self.assertEqual(result.method, "mitm")

    def test_recover_unique_uses_only_final_and_steps(self):
        bits = [1, 0, 1, 1, 0, 0, 1, 0, 1, 0, 1, 1]
        final_state, steps = encode_bits(bits, DEFAULT_CONFIG)
        self.assertEqual(recover_unique(final_state, steps), bits)

    def test_zero_steps(self):
        result = decode_mitm(DEFAULT_CONFIG.initial_state, 0)
        self.assertTrue(result.unique)
        self.assertEqual(result.bits, [])


if __name__ == "__main__":
    unittest.main()

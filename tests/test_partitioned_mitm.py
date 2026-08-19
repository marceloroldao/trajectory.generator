import unittest

from trajectory_generator import (
    decode_mitm,
    decode_mitm_partitioned,
    encode_bits,
    int_to_bits,
)


class PartitionedMitmTests(unittest.TestCase):
    def test_matches_standard_mitm_small_domains(self):
        for steps in range(1, 9):
            for value in range(1 << steps):
                bits = int_to_bits(value, steps)
                final_state, count = encode_bits(bits)
                self.assertEqual(count, steps)

                base = decode_mitm(final_state, steps, max_matches=2)
                part = decode_mitm_partitioned(
                    final_state,
                    steps,
                    partition_bits=min(3, steps),
                    max_matches=2,
                )
                self.assertEqual(base.matches, part.matches)

    def test_partition_zero_degenerates_to_mitm(self):
        bits = int_to_bits(0b101101001011, 12)
        final_state, steps = encode_bits(bits)
        base = decode_mitm(final_state, steps, max_matches=2)
        part = decode_mitm_partitioned(
            final_state,
            steps,
            partition_bits=0,
            max_matches=2,
        )
        self.assertEqual(base.matches, part.matches)


if __name__ == "__main__":
    unittest.main()

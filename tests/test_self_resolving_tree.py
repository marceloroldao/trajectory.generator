import unittest

from trajectory_generator.self_resolving_tree import (
    DEFAULT_SELF_RESOLVING_CONFIG,
    address_envelope_count,
    capacity_ok,
    decode_self_resolving_tree,
    encode_self_resolving_tree,
)


class SelfResolvingTreeTests(unittest.TestCase):
    def test_leaf_round_trip(self):
        bits = [0, 1] * 8
        state, steps = encode_self_resolving_tree(bits)
        self.assertEqual(decode_self_resolving_tree(state, steps), bits)

    def test_canonical_split_round_trip(self):
        # Globally complex under levels 0..3 with K=5, but each public midpoint
        # half is leaf-admissible. The encoder must therefore split canonically.
        bits = [int(c) for c in "10001001001110101011"]
        state, steps = encode_self_resolving_tree(bits)
        self.assertEqual(decode_self_resolving_tree(state, steps), bits)

    def test_default_capacity_frontier(self):
        self.assertTrue(capacity_ok(20))
        self.assertFalse(capacity_ok(21))
        self.assertLessEqual(address_envelope_count(20), 1 << DEFAULT_SELF_RESOLVING_CONFIG.width)
        self.assertGreater(address_envelope_count(21), 1 << DEFAULT_SELF_RESOLVING_CONFIG.width)

    def test_invalid_over_capacity(self):
        with self.assertRaises(ValueError):
            encode_self_resolving_tree([0] * 21)


if __name__ == "__main__":
    unittest.main()

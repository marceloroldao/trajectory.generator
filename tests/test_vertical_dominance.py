import unittest

from trajectory_generator.vertical_dominance import (
    asymptotic_vertical_fraction_lower_bound,
    bits_needed_for_vertical_fraction,
    bound_identity_holds,
    dominance_bound,
)


class VerticalDominanceTests(unittest.TestCase):
    def test_exact_counts_respect_horizontal_bound(self):
        cases = [
            {"a": 1},
            {"a": 3, "b": 1},
            {"a": 2, "b": 5, "c": 7},
            {"a": 100, "b": 20, "c": 3},
        ]

        for counts in cases:
            value = dominance_bound(
                counts,
                causal_state_count=len(counts),
            )
            self.assertTrue(
                bound_identity_holds(value)
            )

    def test_lower_bound_approaches_one_as_total_information_grows(self):
        previous = -1.0
        for total_bits in (8, 16, 32, 64, 128, 256):
            bound = (
                asymptotic_vertical_fraction_lower_bound(
                    causal_state_count=16,
                    total_bits=total_bits,
                )
            )
            self.assertGreaterEqual(
                bound,
                previous,
            )
            previous = bound

        self.assertGreater(
            previous,
            0.98,
        )

    def test_sufficient_bit_threshold(self):
        threshold = bits_needed_for_vertical_fraction(
            causal_state_count=16,
            target_fraction=0.95,
        )
        self.assertAlmostEqual(
            threshold,
            80.0,
            places=12,
        )
        self.assertGreaterEqual(
            asymptotic_vertical_fraction_lower_bound(
                causal_state_count=16,
                total_bits=threshold,
            ),
            0.95,
        )


if __name__ == "__main__":
    unittest.main()

import unittest

from trajectory_generator.horizontal_vertical_entropy import (
    decompose_counts,
)
from trajectory_generator.vertical_entropy_rate import (
    entropy_rate_from_growth,
    rate_bound_holds,
    vertical_rate_bound,
)


class VerticalEntropyRateTests(unittest.TestCase):
    def test_rate_gap_is_horizontal_rate(self):
        decomposition = decompose_counts(
            {"a": 100, "b": 20, "c": 3}
        )
        row = vertical_rate_bound(
            decomposition,
            time=50,
            causal_state_count=3,
        )

        self.assertTrue(rate_bound_holds(row))
        self.assertAlmostEqual(
            row.total_rate
            - row.vertical_rate,
            row.horizontal_rate,
            places=12,
        )

    def test_maximum_gap_decays_as_inverse_time(self):
        decomposition = decompose_counts(
            {"a": 1000, "b": 2000}
        )

        first = vertical_rate_bound(
            decomposition,
            time=10,
            causal_state_count=8,
        )
        second = vertical_rate_bound(
            decomposition,
            time=100,
            causal_state_count=8,
        )

        self.assertAlmostEqual(
            first.maximum_rate_gap,
            10 * second.maximum_rate_gap,
            places=12,
        )

    def test_growth_rate_conversion(self):
        self.assertAlmostEqual(
            entropy_rate_from_growth(2.0),
            1.0,
            places=12,
        )


if __name__ == "__main__":
    unittest.main()

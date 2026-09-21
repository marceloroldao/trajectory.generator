import unittest

from trajectory_generator.horizontal_vertical_entropy import (
    decompose_counts,
    entropy_flow_step,
)


class HorizontalVerticalEntropyTests(unittest.TestCase):
    def test_chain_rule_exact(self):
        rows = [
            {"a": 1, "b": 1},
            {"a": 3, "b": 1},
            {"a": 2, "b": 5, "c": 7},
            {"a": 100, "b": 20, "c": 3},
        ]

        for counts in rows:
            value = decompose_counts(counts)
            self.assertAlmostEqual(
                value.total_bits,
                value.horizontal_bits
                + value.vertical_bits,
                places=12,
            )
            self.assertAlmostEqual(
                value.residual,
                0.0,
                places=12,
            )

    def test_deterministic_step_only_redistributes_information(self):
        before = {"a": 2, "b": 2}
        after = {"x": 4}

        row = entropy_flow_step(
            before,
            after,
            time=0,
        )

        self.assertTrue(row.deterministic)
        self.assertAlmostEqual(
            row.branch_created_bits,
            0.0,
            places=12,
        )
        self.assertAlmostEqual(
            row.delta_horizontal_bits
            + row.delta_vertical_bits,
            0.0,
            places=12,
        )
        self.assertLess(
            row.delta_horizontal_bits,
            0.0,
        )
        self.assertGreater(
            row.delta_vertical_bits,
            0.0,
        )

    def test_branch_step_creates_total_information(self):
        before = {"a": 1}
        after = {"x": 1, "y": 1}

        row = entropy_flow_step(
            before,
            after,
            time=0,
        )

        self.assertFalse(row.deterministic)
        self.assertAlmostEqual(
            row.branch_created_bits,
            1.0,
            places=12,
        )
        self.assertAlmostEqual(
            row.delta_horizontal_bits
            + row.delta_vertical_bits,
            1.0,
            places=12,
        )


if __name__ == "__main__":
    unittest.main()

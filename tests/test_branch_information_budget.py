import unittest

from trajectory_generator.branch_information_budget import (
    cumulative_created_bits,
    endpoint_information_gain,
    information_budget,
)


class BranchInformationBudgetTests(unittest.TestCase):
    def test_deterministic_cycle_creates_zero_bits(self):
        graph = {
            0: (1,),
            1: (2,),
            2: (0,),
        }
        rows = information_budget(
            graph,
            start_nodes=(0,),
            steps=20,
        )

        self.assertTrue(
            all(row.branch_excess == 0 for row in rows)
        )
        self.assertTrue(
            all(row.delta_bits == 0.0 for row in rows)
        )

    def test_binary_branch_creates_exact_history_growth(self):
        graph = {
            0: (0, 0),
        }
        rows = information_budget(
            graph,
            start_nodes=(0,),
            steps=12,
        )

        for time, row in enumerate(rows):
            self.assertEqual(
                row.total_before,
                1 << time,
            )
            self.assertEqual(
                row.branch_excess,
                1 << time,
            )
            self.assertEqual(
                row.total_after,
                1 << (time + 1),
            )
            self.assertAlmostEqual(
                row.delta_bits,
                1.0,
            )

    def test_information_increments_telescope(self):
        graph = {
            0: (0, 1),
            1: (0,),
        }
        rows = information_budget(
            graph,
            start_nodes=(0,),
            steps=30,
        )

        self.assertAlmostEqual(
            cumulative_created_bits(rows),
            endpoint_information_gain(rows),
            places=12,
        )

    def test_deterministic_step_has_zero_increment(self):
        graph = {
            0: (1, 2),
            1: (3,),
            2: (3,),
            3: (0,),
        }
        rows = information_budget(
            graph,
            start_nodes=(0,),
            steps=12,
        )

        self.assertTrue(
            any(row.deterministic for row in rows)
        )
        for row in rows:
            if row.deterministic:
                self.assertEqual(
                    row.total_after,
                    row.total_before,
                )
                self.assertEqual(
                    row.delta_bits,
                    0.0,
                )


if __name__ == "__main__":
    unittest.main()

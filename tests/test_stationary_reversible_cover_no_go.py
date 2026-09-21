import unittest

from trajectory_generator.stationary_reversible_cover_no_go import (
    exact_stationary_partition_holds,
    maximum_fiber_demand,
    stationary_cover_inequality_holds,
    total_path_count,
)


class StationaryReversibleCoverNoGoTests(unittest.TestCase):
    def test_deterministic_cycle_admits_constant_stationary_fiber(self):
        graph = {
            0: (1,),
            1: (2,),
            2: (0,),
        }
        sizes = {0: 7, 1: 7, 2: 7}

        self.assertTrue(
            stationary_cover_inequality_holds(
                graph,
                sizes,
            )
        )
        self.assertTrue(
            exact_stationary_partition_holds(
                graph,
                sizes,
            )
        )

    def test_binary_branch_cycle_rejects_constant_fiber(self):
        graph = {
            0: (0, 0),
        }
        sizes = {0: 100}

        self.assertFalse(
            stationary_cover_inequality_holds(
                graph,
                sizes,
            )
        )
        self.assertFalse(
            exact_stationary_partition_holds(
                graph,
                sizes,
            )
        )

    def test_history_fiber_demand_grows_in_positive_entropy_graph(self):
        graph = {
            0: (0, 1),
            1: (0,),
        }

        maxima = [
            maximum_fiber_demand(
                graph,
                start_nodes=(0,),
                steps=t,
            )
            for t in range(12)
        ]
        totals = [
            total_path_count(
                graph,
                start_nodes=(0,),
                steps=t,
            )
            for t in range(12)
        ]

        self.assertGreater(maxima[-1], maxima[0])
        self.assertGreater(totals[-1], totals[0])


if __name__ == "__main__":
    unittest.main()

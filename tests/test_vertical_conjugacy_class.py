import unittest
from itertools import permutations

from trajectory_generator.gauge_invariant_vertical_law import (
    conjugate,
)
from trajectory_generator.vertical_conjugacy_class import (
    cycle_type,
    information_event_action_class,
    is_involution,
    reflection_cycle_type,
    reflection_representative,
)


class VerticalConjugacyClassTests(unittest.TestCase):
    def test_reflection_formula_matches_representative(self):
        for size in range(1, 12):
            representative = reflection_representative(
                size
            )
            self.assertEqual(
                cycle_type(representative),
                reflection_cycle_type(size),
            )
            self.assertTrue(
                is_involution(representative)
            )

    def test_reflection_cycle_type_survives_all_small_gauges(self):
        for size in range(1, 7):
            representative = reflection_representative(
                size
            )
            expected = cycle_type(representative)

            for gauge in permutations(range(size)):
                transformed = conjugate(
                    representative,
                    tuple(gauge),
                )
                self.assertEqual(
                    cycle_type(transformed),
                    expected,
                )

    def test_branch_class_is_nontrivial_once_fiber_has_three_states(self):
        for size in range(3, 12):
            branch = information_event_action_class(
                fiber_size=size,
                is_branch=True,
            )
            deterministic = information_event_action_class(
                fiber_size=size,
                is_branch=False,
            )
            self.assertTrue(branch.nontrivial)
            self.assertFalse(deterministic.nontrivial)
            self.assertNotEqual(
                branch.signature,
                deterministic.signature,
            )


if __name__ == "__main__":
    unittest.main()

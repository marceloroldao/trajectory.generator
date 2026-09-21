import unittest

from trajectory_generator.gauge_covariant_vertical_event import (
    MaximalPairingBranchLift,
    conjugacy_class_preserved,
    cycle_type,
    fixed_point_count,
    is_involution,
    maximal_pairing_cycle_type,
    maximal_pairing_involutions,
    reversal_involution,
)
from trajectory_generator.gauge_invariant_vertical_law import (
    transposition,
)
from trajectory_generator.scalar_partition_trajectory import (
    build_scalar_partition_translation_machine,
)


def phase_graph():
    return {
        ("a", 0): [("a", 1), ("b", 1)],
        ("b", 0): [("a", 1)],
        ("a", 1): [("a", 2)],
        ("b", 1): [("a", 2), ("b", 2)],
        ("a", 2): [("a", 0), ("b", 0)],
        ("b", 2): [("a", 0)],
    }


class GaugeCovariantVerticalEventTests(unittest.TestCase):
    def test_reversal_is_fixed_point_minimal_involution(self):
        for size in range(1, 9):
            value = reversal_involution(size)
            self.assertTrue(is_involution(value))
            self.assertEqual(
                fixed_point_count(value),
                size % 2,
            )
            self.assertEqual(
                cycle_type(value),
                maximal_pairing_cycle_type(size),
            )

    def test_small_n_all_maximal_pairings_share_one_cycle_type(self):
        for size in range(1, 7):
            rows = maximal_pairing_involutions(size)
            self.assertTrue(rows)
            types = {
                cycle_type(value)
                for value in rows
            }
            self.assertEqual(
                types,
                {maximal_pairing_cycle_type(size)},
            )

    def test_conjugation_preserves_pairing_class(self):
        for size in range(3, 8):
            law = reversal_involution(size)
            for i in range(size):
                for j in range(i + 1, size):
                    gauge = transposition(
                        size,
                        i,
                        j,
                    )
                    self.assertTrue(
                        conjugacy_class_preserved(
                            law,
                            gauge,
                        )
                    )

    def test_lift_is_exactly_reversible(self):
        machine = build_scalar_partition_translation_machine(
            phase_graph(),
            start_nodes=(("a", 0),),
            phase_of=lambda node: node[1],
            period=3,
            width=32,
            seed_cache_entries=64,
        )
        lift = MaximalPairingBranchLift(machine)

        nontrivial = 0
        for time in range(14):
            for packed in range(lift.total_states(time)):
                state = lift.from_packed(
                    packed,
                    time,
                )
                for edge in lift.machine.codec.outgoing[
                    state.node
                ]:
                    size = lift.fiber_size(
                        state.node,
                        time,
                    )
                    drive = lift.drive(edge, time)
                    mapped = lift.permute_local(
                        state.vertical,
                        size,
                        drive,
                    )
                    if mapped != state.vertical:
                        nontrivial += 1

                    nxt = lift.advance(
                        state,
                        time,
                        edge.label,
                    )
                    previous, recovered = lift.rewind(
                        nxt,
                        time + 1,
                    )
                    self.assertEqual(previous, state)
                    self.assertEqual(recovered, edge)

        self.assertGreater(nontrivial, 0)


if __name__ == "__main__":
    unittest.main()

import unittest

from trajectory_generator.branch_reflection_vertical_dynamics import (
    BranchReflectionVerticalLift,
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


class BranchReflectionVerticalLiftTests(unittest.TestCase):
    def build_lift(self):
        machine = build_scalar_partition_translation_machine(
            phase_graph(),
            start_nodes=(("a", 0),),
            phase_of=lambda node: node[1],
            period=3,
            width=32,
            seed_cache_entries=64,
        )
        return BranchReflectionVerticalLift(machine)

    def test_orientation_is_exactly_branch_indicator(self):
        lift = self.build_lift()

        for edge in lift.machine.codec.edges:
            expected = (
                -1
                if len(
                    lift.machine.codec.outgoing[
                        edge.source
                    ]
                ) > 1
                else 1
            )
            for time in range(12):
                drive = lift.drive(edge, time)
                self.assertEqual(
                    drive.orientation,
                    expected,
                )
                self.assertEqual(drive.shift_seed, 0)

    def test_drive_is_time_and_phase_number_independent(self):
        lift = self.build_lift()

        for edge in lift.machine.codec.edges:
            reference = lift.drive(edge, 0)
            for time in range(1, 24):
                self.assertEqual(
                    lift.drive(edge, time),
                    reference,
                )

    def test_branch_reflection_is_exactly_reversible(self):
        lift = self.build_lift()
        nontrivial = 0
        branch_edges = 0

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

                    if drive.orientation == -1:
                        branch_edges += 1

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
                    self.assertEqual(
                        lift.project(nxt),
                        edge.target,
                    )

        self.assertGreater(branch_edges, 0)
        self.assertGreater(nontrivial, 0)


if __name__ == "__main__":
    unittest.main()

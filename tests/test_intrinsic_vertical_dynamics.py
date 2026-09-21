import unittest

from trajectory_generator.intrinsic_vertical_dynamics import (
    PhaseReflectionVerticalLift,
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


class PhaseReflectionVerticalLiftTests(unittest.TestCase):
    def build_lift(self):
        machine = build_scalar_partition_translation_machine(
            phase_graph(),
            start_nodes=(("a", 0),),
            phase_of=lambda node: node[1],
            period=3,
            width=32,
            seed_cache_entries=64,
        )
        return PhaseReflectionVerticalLift(machine)

    def test_drive_uses_phase_only(self):
        lift = self.build_lift()

        for edge in lift.machine.codec.edges:
            for time in range(18):
                drive = lift.drive(edge, time)
                expected = -1 if (time % 3) == 1 else 1
                self.assertEqual(
                    drive.orientation,
                    expected,
                )
                self.assertEqual(drive.shift_seed, 0)
                self.assertEqual(
                    drive,
                    lift.drive(
                        edge,
                        time + lift.causal_period,
                    ),
                )

    def test_reflection_is_exactly_reversible(self):
        lift = self.build_lift()
        nontrivial = 0

        for time in range(12):
            for packed in range(lift.total_states(time)):
                state = lift.from_packed(packed, time)

                for edge in lift.machine.codec.outgoing[state.node]:
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
                    self.assertEqual(
                        lift.project(nxt),
                        edge.target,
                    )

        self.assertGreater(nontrivial, 0)


if __name__ == "__main__":
    unittest.main()

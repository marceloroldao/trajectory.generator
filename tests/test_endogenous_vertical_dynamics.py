import unittest

from trajectory_generator.endogenous_vertical_dynamics import (
    EndogenousPeriodicVerticalLift,
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


class EndogenousPeriodicVerticalLiftTests(unittest.TestCase):
    def build_lift(self):
        machine = build_scalar_partition_translation_machine(
            phase_graph(),
            start_nodes=(("a", 0),),
            phase_of=lambda node: node[1],
            period=3,
            width=32,
            seed_cache_entries=64,
        )
        return EndogenousPeriodicVerticalLift(machine)

    def test_driver_is_exactly_periodic(self):
        lift = self.build_lift()

        for edge in lift.machine.codec.edges:
            for time in range(3 * lift.vertical_period):
                self.assertTrue(
                    lift.drive_is_periodic(edge, time)
                )

    def test_local_map_is_bijection_for_many_sizes(self):
        lift = self.build_lift()

        for edge in lift.machine.codec.edges:
            for time in range(lift.vertical_period):
                drive = lift.drive(edge, time)
                for size in range(1, 40):
                    image = {
                        lift.permute_local(y, size, drive)
                        for y in range(size)
                    }
                    self.assertEqual(
                        image,
                        set(range(size)),
                    )
                    for y in range(size):
                        local = lift.permute_local(
                            y,
                            size,
                            drive,
                        )
                        self.assertEqual(
                            lift.invert_local(
                                local,
                                size,
                                drive,
                            ),
                            y,
                        )

    def test_projection_and_reverse_are_exact(self):
        lift = self.build_lift()

        for time in range(12):
            for packed in range(lift.total_states(time)):
                state = lift.from_packed(
                    packed,
                    time,
                )
                self.assertEqual(
                    lift.to_packed(state, time),
                    packed,
                )

                for edge in lift.machine.codec.outgoing[
                    state.node
                ]:
                    self.assertTrue(
                        lift.semiconjugacy_holds(
                            state,
                            time,
                            edge.label,
                        )
                    )
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

    def test_vertical_map_is_not_identity_only(self):
        lift = self.build_lift()
        nontrivial = 0
        flips = 0

        for time in range(20):
            for node, size in lift.active_fibers(time):
                if size <= 1:
                    continue
                for edge in lift.machine.codec.outgoing[node]:
                    drive = lift.drive(edge, time)
                    if drive.orientation == -1:
                        flips += 1

                    probes = {0, size - 1, size // 2}
                    if any(
                        lift.permute_local(
                            y,
                            size,
                            drive,
                        ) != y
                        for y in probes
                    ):
                        nontrivial += 1

        self.assertGreater(nontrivial, 0)
        self.assertGreater(flips, 0)


if __name__ == "__main__":
    unittest.main()

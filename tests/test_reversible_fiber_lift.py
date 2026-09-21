import unittest

from trajectory_generator.reversible_fiber_lift import (
    ReversibleFiberLift,
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


class ReversibleFiberLiftTests(unittest.TestCase):
    def build_lift(self):
        machine = build_scalar_partition_translation_machine(
            phase_graph(),
            start_nodes=(("a", 0),),
            phase_of=lambda node: node[1],
            period=3,
            width=32,
            seed_cache_entries=64,
        )
        return ReversibleFiberLift(machine)

    def test_pack_coordinate_identity(self):
        lift = self.build_lift()

        for t in range(12):
            total = lift.total_states(t)
            for state in range(total):
                coordinate = lift.coordinate(state, t)
                self.assertEqual(
                    lift.pack(
                        coordinate.node,
                        coordinate.rank,
                        t,
                    ),
                    state,
                )

    def test_fibers_partition_complete_address_space(self):
        lift = self.build_lift()

        for t in range(20):
            fibers = lift.active_fibers(t)
            self.assertEqual(
                sum(size for _, size in fibers),
                lift.machine.oracle.total_count(t),
            )

    def test_forward_is_horizontal_edge_plus_vertical_offset(self):
        lift = self.build_lift()

        for t in range(10):
            total = lift.total_states(t)
            for state in range(total):
                coordinate = lift.coordinate(state, t)
                for edge in lift.machine.codec.outgoing[
                    coordinate.node
                ]:
                    nxt = lift.forward(
                        coordinate,
                        edge.label,
                    )
                    previous, recovered_edge = lift.reverse(
                        nxt
                    )
                    self.assertEqual(
                        previous,
                        coordinate,
                    )
                    self.assertEqual(
                        recovered_edge,
                        edge,
                    )

    def test_incoming_subfibers_are_disjoint_and_complete(self):
        lift = self.build_lift()

        for t in range(10):
            for target in lift.machine.nodes:
                blocks = []
                for edge in lift.machine.codec.incoming[target]:
                    start, end = lift.incoming_subfiber(
                        edge,
                        t,
                    )
                    if end > start:
                        blocks.append((start, end))

                if not blocks:
                    continue

                blocks.sort()
                self.assertEqual(blocks[0][0], 0)
                for left, right in zip(
                    blocks,
                    blocks[1:],
                ):
                    self.assertEqual(left[1], right[0])

                target_size = lift.machine.endpoint_count(
                    target,
                    t + 1,
                )
                self.assertEqual(
                    blocks[-1][1],
                    target_size,
                )


if __name__ == "__main__":
    unittest.main()

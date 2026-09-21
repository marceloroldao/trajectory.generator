import unittest

from trajectory_generator.lifted_causal_universe import (
    LiftedCausalState,
    LiftedCausalUniverse,
)
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


class LiftedCausalUniverseTests(unittest.TestCase):
    def build_universe(self):
        machine = build_scalar_partition_translation_machine(
            phase_graph(),
            start_nodes=(("a", 0),),
            phase_of=lambda node: node[1],
            period=3,
            width=32,
            seed_cache_entries=64,
        )
        return LiftedCausalUniverse(
            ReversibleFiberLift(machine)
        )

    def test_projection_semiconjugacy_and_reverse(self):
        universe = self.build_universe()

        for time in range(10):
            total = universe.lift.total_states(time)
            for packed in range(total):
                state = universe.from_packed(packed, time)
                self.assertEqual(
                    universe.to_packed(state, time),
                    packed,
                )

                for edge in universe.machine.codec.outgoing[state.node]:
                    self.assertTrue(
                        universe.semiconjugacy_holds(
                            state,
                            time,
                            edge.label,
                        )
                    )
                    nxt = universe.advance(
                        state,
                        time,
                        edge.label,
                    )
                    previous, recovered_edge = universe.rewind(
                        nxt,
                        time + 1,
                    )
                    self.assertEqual(previous, state)
                    self.assertEqual(recovered_edge, edge)

    def test_incoming_blocks_partition_target_fiber(self):
        universe = self.build_universe()

        for time in range(10):
            for target in universe.machine.nodes:
                blocks = list(
                    universe.fiber_partition(
                        target,
                        time,
                    )
                )
                if not blocks:
                    continue

                self.assertEqual(blocks[0][1], 0)
                for left, right in zip(blocks, blocks[1:]):
                    self.assertEqual(left[2], right[1])

                self.assertEqual(
                    blocks[-1][2],
                    universe.fiber_size(
                        target,
                        time + 1,
                    ),
                )

    def test_local_minimum_equals_exact_history_multiplicity(self):
        universe = self.build_universe()

        for time in range(12):
            for node, size in universe.lift.active_fibers(time):
                self.assertEqual(
                    universe.local_minimum_states(node, time),
                    size,
                )
                self.assertEqual(
                    universe.local_minimum_bits(node, time),
                    0 if size <= 1 else (size - 1).bit_length(),
                )


if __name__ == "__main__":
    unittest.main()

import unittest

from trajectory_generator.exact_vertical_connection import (
    ExactVerticalConnection,
)
from trajectory_generator.scalar_partition_trajectory import (
    build_scalar_partition_translation_machine,
)
from trajectory_generator.seeded_graph_state_machine import (
    SeededGraphStateMachine,
)
from trajectory_generator.seeded_vertical_connection import (
    SeededVerticalConnectionMachine,
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


class SeededVerticalConnectionTests(unittest.TestCase):
    def build(self):
        partition = build_scalar_partition_translation_machine(
            phase_graph(),
            start_nodes=(("a", 0), ("b", 0)),
            phase_of=lambda node: node[1],
            period=3,
            width=32,
            seed_cache_entries=32,
        )
        mapping = {
            0: ("a", 0),
            1: ("b", 0),
        }
        symbol = lambda edge: (
            0 if edge.target[0] == "a" else 1
        )

        local = SeededVerticalConnectionMachine(
            ExactVerticalConnection(partition),
            seed_bits=1,
            seed_to_start_node=mapping,
            edge_symbol=symbol,
        )
        reference = SeededGraphStateMachine(
            partition,
            seed_bits=1,
            seed_to_start_node=mapping,
            edge_symbol=symbol,
        )
        return local, reference

    def test_matches_reference_for_all_small_states(self):
        local, reference = self.build()

        for steps in range(10):
            if steps == 0:
                states = [0]
            elif steps < reference.seed_bits:
                states = range(1 << steps)
            else:
                states = range(
                    reference.partition_machine.oracle.total_count(
                        steps - reference.seed_bits
                    )
                )

            for state in states:
                try:
                    expected = reference.decode(
                        state,
                        steps,
                    )
                except ValueError:
                    continue

                self.assertEqual(
                    local.decode(state, steps),
                    expected,
                )
                self.assertEqual(
                    local.encode(expected),
                    (state, steps),
                )

    def test_cursor_decode_matches_direct_decoder(self):
        local, _ = self.build()

        for steps in range(1, 10):
            if steps < local.seed_bits:
                states = range(1 << steps)
            else:
                states = range(
                    local.connection.machine.oracle.total_count(
                        steps - local.seed_bits
                    )
                )

            for state in states:
                try:
                    direct = local.decode_direct(
                        state,
                        steps,
                    )
                except ValueError:
                    continue
                self.assertEqual(
                    local.decode(state, steps),
                    direct,
                )

    def test_cursor_decode_does_not_use_scalar_oracle(self):
        local, reference = self.build()
        steps = 8
        valid_state = None
        expected = None

        total = (
            reference.partition_machine.oracle.total_count(
                steps - reference.seed_bits
            )
        )
        for state in range(total):
            try:
                expected = reference.decode(
                    state,
                    steps,
                )
                valid_state = state
                break
            except ValueError:
                continue

        self.assertIsNotNone(valid_state)

        def forbidden(*args, **kwargs):
            raise AssertionError(
                "optimized cursor decode requested scalar_at"
            )

        local.connection.machine.oracle.scalar_at = forbidden
        self.assertEqual(
            local.decode(
                valid_state,
                steps,
            ),
            expected,
        )

    def test_empty_trajectory(self):
        local, _ = self.build()
        self.assertEqual(
            local.decode(0, 0),
            [],
        )


if __name__ == "__main__":
    unittest.main()

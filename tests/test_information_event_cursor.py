import unittest

from trajectory_generator.exact_vertical_connection import (
    ExactVerticalConnection,
)
from trajectory_generator.information_clock_trace import (
    InformationClockTraceCodec,
)
from trajectory_generator.information_event_cursor import (
    InformationEventBackwardCursor,
    InformationEventRuntimePlan,
)
from trajectory_generator.scalar_partition_trajectory import (
    build_scalar_partition_translation_machine,
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


class InformationEventCursorTests(unittest.TestCase):
    def build(self):
        adjacency = phase_graph()
        partition = build_scalar_partition_translation_machine(
            adjacency,
            start_nodes=(("a", 0), ("b", 0)),
            phase_of=lambda node: node[1],
            period=3,
            width=32,
            seed_cache_entries=16,
        )
        machine = SeededVerticalConnectionMachine(
            ExactVerticalConnection(partition),
            seed_bits=1,
            seed_to_start_node={
                0: ("a", 0),
                1: ("b", 0),
            },
            edge_symbol=lambda edge: (
                0 if edge.target[0] == "a" else 1
            ),
        )
        return machine, InformationClockTraceCodec(machine)

    def test_event_cursor_trace_expands_to_exact_bits(self):
        machine, trace_codec = self.build()

        for steps in range(2, 11):
            total = (
                machine.connection.machine.oracle.total_count(
                    steps - machine.seed_bits
                )
            )
            for final_state in range(total):
                try:
                    expected = machine.decode(
                        final_state,
                        steps,
                    )
                except ValueError:
                    continue

                cursor = InformationEventBackwardCursor(
                    trace_codec,
                    final_state,
                    steps - machine.seed_bits,
                )
                trace = cursor.decode_trace(
                    seed_bits=machine.seed_bits,
                    start_node_to_seed=(
                        machine.start_node_to_seed
                    ),
                )
                self.assertEqual(
                    trace_codec.expand_bits(trace),
                    expected,
                )
                self.assertEqual(
                    cursor.metrics.equivalent_physical_steps,
                    steps - machine.seed_bits,
                )
                self.assertEqual(
                    cursor.metrics.macro_probe_physical_steps,
                    0,
                )


    def test_shared_runtime_plan_is_exact(self):
        machine, trace_codec = self.build()
        plan = InformationEventRuntimePlan(
            trace_codec
        )

        steps = 9
        total = (
            machine.connection.machine.oracle.total_count(
                steps - machine.seed_bits
            )
        )

        checked = 0
        for final_state in range(total):
            try:
                expected = machine.decode(
                    final_state,
                    steps,
                )
            except ValueError:
                continue

            cursor = InformationEventBackwardCursor(
                trace_codec,
                final_state,
                steps - machine.seed_bits,
                runtime_plan=plan,
            )
            trace = cursor.decode_trace(
                seed_bits=machine.seed_bits,
                start_node_to_seed=(
                    machine.start_node_to_seed
                ),
            )
            self.assertEqual(
                trace_codec.expand_bits(trace),
                expected,
            )
            self.assertEqual(
                cursor.metrics.macro_probe_physical_steps,
                0,
            )
            checked += 1

        self.assertGreater(checked, 0)


if __name__ == "__main__":
    unittest.main()

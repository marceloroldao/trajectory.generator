import unittest

from trajectory_generator.exact_vertical_connection import (
    ExactVerticalConnection,
)
from trajectory_generator.information_clock_trace import (
    FallbackTraceItem,
    InformationClockTraceCodec,
    MacroTraceItem,
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


class InformationClockTraceTests(unittest.TestCase):
    def build(self):
        adjacency = phase_graph()
        starts = (("a", 0), ("b", 0))
        partition = build_scalar_partition_translation_machine(
            adjacency,
            start_nodes=starts,
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

    def test_trace_roundtrip_matches_physical_decoder(self):
        machine, trace_codec = self.build()

        for steps in range(1, 11):
            if steps < machine.seed_bits:
                states = range(1 << steps)
            else:
                states = range(
                    machine.connection.machine.oracle.total_count(
                        steps - machine.seed_bits
                    )
                )

            for final_state in states:
                try:
                    expected = machine.decode(
                        final_state,
                        steps,
                    )
                except ValueError:
                    continue

                trace = trace_codec.decode_trace(
                    final_state,
                    steps,
                )
                self.assertEqual(
                    trace_codec.expand_bits(trace),
                    expected,
                )
                self.assertEqual(
                    machine.encode(expected),
                    (final_state, steps),
                )

    def test_compressed_items_preserve_total_physical_length(self):
        machine, trace_codec = self.build()
        steps = 9
        total = (
            machine.connection.machine.oracle.total_count(
                steps - machine.seed_bits
            )
        )

        for final_state in range(total):
            try:
                trace = trace_codec.decode_trace(
                    final_state,
                    steps,
                )
            except ValueError:
                continue

            self.assertEqual(
                sum(
                    item.physical_steps
                    for item in trace.items
                ),
                steps - machine.seed_bits,
            )
            for item in trace.items:
                self.assertIsInstance(
                    item,
                    (MacroTraceItem, FallbackTraceItem),
                )


if __name__ == "__main__":
    unittest.main()

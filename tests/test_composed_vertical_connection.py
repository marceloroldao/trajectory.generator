import unittest

from trajectory_generator.composed_vertical_connection import (
    ComposedVerticalConnection,
)
from trajectory_generator.exact_vertical_connection import (
    ExactVerticalConnection,
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


class ComposedVerticalConnectionTests(unittest.TestCase):
    def build(self):
        machine = build_scalar_partition_translation_machine(
            phase_graph(),
            start_nodes=(("a", 0), ("b", 0)),
            phase_of=lambda node: node[1],
            period=3,
            width=32,
            seed_cache_entries=16,
        )
        exact = ExactVerticalConnection(machine)
        return machine, exact, ComposedVerticalConnection(exact)

    def test_composed_forward_matches_sequential_edges(self):
        machine, exact, composed = self.build()

        for start_time in range(6):
            for node in machine.nodes:
                size = machine.endpoint_count(
                    node,
                    start_time,
                )
                if size <= 0:
                    continue

                outgoing = machine.codec.outgoing[node]
                if not outgoing:
                    continue
                first = outgoing[0]

                second_edges = machine.codec.outgoing[
                    first.target
                ]
                if not second_edges:
                    continue
                second = second_edges[0]
                labels = (
                    first.label,
                    second.label,
                )

                for rank in {
                    0,
                    size // 2,
                    size - 1,
                }:
                    source = exact.state(
                        node,
                        rank,
                        start_time,
                    )
                    sequential = exact.forward(
                        source,
                        first.label,
                    )
                    sequential = exact.forward(
                        sequential,
                        second.label,
                    )
                    jumped = composed.forward(
                        source,
                        labels,
                    )
                    self.assertEqual(
                        jumped,
                        sequential,
                    )
                    self.assertEqual(
                        composed.reverse(
                            jumped,
                            labels,
                        ),
                        source,
                    )

    def test_compiled_block_matches_sequential_embedding(self):
        machine, _, composed = self.build()

        for start_time in range(12):
            vector = machine.field.vector_at(
                start_time
            )

            for node in machine.nodes:
                outgoing = machine.codec.outgoing[node]
                if not outgoing:
                    continue

                first = outgoing[0]
                second_edges = machine.codec.outgoing[
                    first.target
                ]
                if not second_edges:
                    continue

                labels = (
                    first.label,
                    second_edges[0].label,
                )
                direct = composed.embedding(
                    labels,
                    start_time,
                )
                plan = composed.compile_path(
                    labels
                )
                compiled = (
                    composed.embedding_from_source_vector(
                        plan,
                        start_time=start_time,
                        source_vector=vector,
                        target_size=direct.target_size,
                    )
                )
                self.assertEqual(
                    compiled,
                    direct,
                )

                period_index, phase_offset = divmod(
                    start_time,
                    machine.field.period,
                )
                if (
                    phase_offset
                    == plan.source_phase_offset
                ):
                    base_vector = (
                        machine.field.period_field.vector_at(
                            period_index
                        )
                    )
                    floquet_compiled = (
                        composed.embedding_from_period_base_vector(
                            plan,
                            start_time=start_time,
                            base_vector=base_vector,
                            target_size=direct.target_size,
                        )
                    )
                    self.assertEqual(
                        floquet_compiled,
                        direct,
                    )

    def test_composed_block_width_equals_source_fiber(self):
        machine, exact, composed = self.build()
        source = exact.state(
            ("a", 0),
            0,
            0,
        )
        first = machine.codec.outgoing[
            source.node
        ][0]
        second = machine.codec.outgoing[
            first.target
        ][0]
        block = composed.embedding(
            (first.label, second.label),
            0,
        )
        self.assertEqual(
            block.end - block.start,
            block.source_size,
        )


if __name__ == "__main__":
    unittest.main()

import unittest
from fractions import Fraction

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


class ExactVerticalConnectionTests(unittest.TestCase):
    def build(self):
        machine = build_scalar_partition_translation_machine(
            phase_graph(),
            start_nodes=(("a", 0),),
            phase_of=lambda node: node[1],
            period=3,
            width=32,
            seed_cache_entries=32,
        )
        return (
            machine,
            ExactVerticalConnection(machine),
        )

    def test_pack_unpack_are_only_chart_conversion(self):
        machine, connection = self.build()

        for time in range(12):
            total = machine.oracle.total_count(time)
            for packed in range(total):
                local = connection.unpack(
                    packed,
                    time,
                )
                self.assertEqual(
                    connection.pack(local),
                    packed,
                )

    def test_local_forward_reverse_matches_packed_machine(self):
        machine, connection = self.build()

        for time in range(10):
            total = machine.oracle.total_count(time)
            for packed in range(total):
                local = connection.unpack(
                    packed,
                    time,
                )
                for edge in machine.codec.outgoing[
                    local.node
                ]:
                    next_local = connection.forward(
                        local,
                        edge.label,
                    )
                    next_packed = machine.forward_step(
                        packed,
                        time,
                        edge.label,
                    )
                    self.assertEqual(
                        connection.pack(next_local),
                        next_packed,
                    )

                    previous, recovered_edge = (
                        connection.reverse(next_local)
                    )
                    self.assertEqual(
                        previous,
                        local,
                    )
                    self.assertEqual(
                        recovered_edge,
                        edge,
                    )

    def test_exact_subfiber_partitions_and_fraction_geometry(self):
        machine, connection = self.build()

        for next_time in range(1, 14):
            phase = (
                machine.field.base_phase + next_time
            ) % machine.field.period
            for target in machine.nodes:
                if (
                    machine.field.phase_of(target)
                    % machine.field.period
                    != phase
                ):
                    continue

                size = machine.endpoint_count(
                    target,
                    next_time,
                )
                if size <= 0:
                    continue

                self.assertTrue(
                    connection.partition_is_exact(
                        target,
                        next_time,
                    )
                )
                rows = connection.incoming_embeddings(
                    target,
                    next_time,
                )
                self.assertEqual(
                    sum(
                        row.normalized_width
                        for row in rows
                    ),
                    Fraction(1, 1),
                )
                self.assertEqual(
                    rows[0].normalized_offset,
                    Fraction(0, 1),
                )

    def test_normalized_rank_interval_is_exact_rational_cell(self):
        _, connection = self.build()
        local = connection.unpack(0, 0)
        self.assertEqual(
            connection.normalized_rank_interval(local),
            (Fraction(0, 1), Fraction(1, 1)),
        )


if __name__ == "__main__":
    unittest.main()

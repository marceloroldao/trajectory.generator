import unittest

from trajectory_generator.exact_vertical_connection import (
    ExactVerticalConnection,
)
from trajectory_generator.scalar_partition_trajectory import (
    build_scalar_partition_translation_machine,
)
from trajectory_generator.vertical_connection_cursor import (
    VerticalConnectionBackwardCursor,
    VerticalConnectionForwardCursor,
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


class VerticalConnectionCursorTests(unittest.TestCase):
    def build(self):
        machine = build_scalar_partition_translation_machine(
            phase_graph(),
            start_nodes=(("a", 0),),
            phase_of=lambda node: node[1],
            period=3,
            width=32,
            seed_cache_entries=16,
        )
        return machine, ExactVerticalConnection(machine)

    def test_cursor_matches_direct_local_reverse(self):
        machine, connection = self.build()

        for final_time in range(1, 12):
            total = machine.oracle.total_count(final_time)
            for packed in range(total):
                direct = connection.unpack(
                    packed,
                    final_time,
                )
                cursor = VerticalConnectionBackwardCursor(
                    connection,
                    packed,
                    final_time,
                )
                self.assertEqual(
                    cursor.state,
                    direct,
                )

                while direct.time > 0:
                    direct, direct_edge = connection.reverse(
                        direct
                    )
                    cursor_edge = cursor.reverse()
                    self.assertEqual(
                        cursor_edge,
                        direct_edge,
                    )
                    self.assertEqual(
                        cursor.state,
                        direct,
                    )

    def test_forward_cursor_matches_direct_local_forward(self):
        machine, connection = self.build()
        start = ("a", 0)
        direct = connection.state(
            start,
            0,
            0,
        )
        cursor = VerticalConnectionForwardCursor(
            connection,
            start,
            0,
        )

        for _ in range(10):
            edges = machine.codec.outgoing[
                direct.node
            ]
            edge = edges[0]
            direct = connection.forward(
                direct,
                edge.label,
            )
            cursor_edge = cursor.forward(
                edge.label
            )
            self.assertEqual(
                cursor_edge,
                edge,
            )
            self.assertEqual(
                cursor.state,
                direct,
            )
            self.assertEqual(
                cursor.pack_current(),
                connection.pack(direct),
            )

    def test_forward_cursor_survives_forbidden_scalar_oracle(self):
        machine, connection = self.build()

        def forbidden(*args, **kwargs):
            raise AssertionError(
                "forward cursor requested scalar_at"
            )

        machine.oracle.scalar_at = forbidden
        cursor = VerticalConnectionForwardCursor(
            connection,
            ("a", 0),
            0,
        )
        for _ in range(12):
            edge = machine.codec.outgoing[
                cursor.state.node
            ][0]
            cursor.forward(edge.label)

        self.assertGreater(cursor.pack_current(), -1)

    def test_reverse_unifilar_fast_path_skips_previous_vector(self):
        machine, connection = self.build()

        start = ("a", 0)
        forward = VerticalConnectionForwardCursor(
            connection,
            start,
            0,
        )
        unique_edge = next(
            edge
            for edge in machine.codec.outgoing[start]
            if len(
                machine.codec.incoming[edge.target]
            ) == 1
        )
        forward.forward(unique_edge.label)
        packed = forward.pack_current()

        cursor = VerticalConnectionBackwardCursor(
            connection,
            packed,
            1,
        )

        def forbidden():
            raise AssertionError(
                "reverse-unifilar fast path requested previous_vector"
            )

        cursor.count_cursor.previous_vector = forbidden
        recovered = cursor.reverse()

        self.assertEqual(
            recovered,
            unique_edge,
        )
        self.assertEqual(
            cursor.state.node,
            start,
        )
        self.assertEqual(
            cursor.metrics.reverse_unifilar_steps,
            1,
        )
        self.assertEqual(
            cursor.metrics.partition_reverse_steps,
            0,
        )

    def test_cursor_reverse_survives_forbidden_scalar_oracle(self):
        machine, connection = self.build()
        final_time = 10
        total = machine.oracle.total_count(final_time)
        packed = total - 1

        def forbidden(*args, **kwargs):
            raise AssertionError(
                "cursor reverse requested scalar_at"
            )

        machine.oracle.scalar_at = forbidden
        cursor = VerticalConnectionBackwardCursor(
            connection,
            packed,
            final_time,
        )
        while cursor.state.time > 0:
            cursor.reverse()

        self.assertEqual(cursor.state.time, 0)
        self.assertEqual(cursor.state.rank, 0)

    def test_cursor_storage_is_horizon_independent(self):
        machine, connection = self.build()
        bounds = []

        for final_time in (20, 50, 100):
            # Pick address zero; only cursor storage is under test.
            cursor = VerticalConnectionBackwardCursor(
                connection,
                0,
                final_time,
            )
            metrics = cursor.metrics
            bounds.append(
                metrics.maximum_stored_count_integers
            )
            self.assertLessEqual(
                metrics.maximum_stored_floquet_rows,
                len(machine.field.reduced_coefficients),
            )

        self.assertEqual(
            len(set(bounds)),
            1,
        )


if __name__ == "__main__":
    unittest.main()

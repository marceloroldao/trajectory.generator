import unittest

from trajectory_generator.count_field_recurrence import (
    CountFieldRecurrence,
)
from trajectory_generator.floquet_count_field import (
    FloquetCountFieldRecurrence,
)
from trajectory_generator.floquet_path_trajectory import (
    build_floquet_path_codec,
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


class FloquetCountFieldTests(unittest.TestCase):
    def test_floquet_rows_match_full_recurrence(self):
        graph = phase_graph()
        starts = (("a", 0),)

        full = CountFieldRecurrence(
            graph,
            start_nodes=starts,
            cache_rows=1,
        )
        floquet = FloquetCountFieldRecurrence(
            graph,
            start_nodes=starts,
            phase_of=lambda node: node[1],
            period=3,
            base_phase=0,
            cache_rows=1,
        )

        for t in range(100):
            self.assertEqual(
                floquet.vector_at(t),
                full.vector_at(t),
            )

        self.assertTrue(floquet.validate_recurrence(20))
        self.assertEqual(floquet.basis_integer_count, 0)
        self.assertGreater(floquet.derived_basis_integer_count, 0)
        self.assertLessEqual(
            floquet.phase_state_count,
            floquet.reachable_state_count,
        )

    def test_floquet_backward_cursor_matches_every_row(self):
        graph = phase_graph()
        field = FloquetCountFieldRecurrence(
            graph,
            start_nodes=(("a", 0),),
            phase_of=lambda node: node[1],
            period=3,
            cache_rows=1,
        )

        final_time = 120
        direct = [field.initial_vector]
        for _ in range(final_time):
            direct.append(field.step_vector(direct[-1]))

        cursor = field.backward_cursor(final_time)
        while cursor.time >= 0:
            self.assertEqual(
                cursor.current_vector(),
                direct[cursor.time],
            )
            if cursor.time == 0:
                break
            self.assertEqual(
                cursor.previous_vector(),
                direct[cursor.time - 1],
            )
            cursor.step_back()

    def test_floquet_cursor_direct_lookback_and_jump(self):
        graph = phase_graph()
        field = FloquetCountFieldRecurrence(
            graph,
            start_nodes=(("a", 0),),
            phase_of=lambda node: node[1],
            period=3,
            cache_rows=1,
        )

        final_time = 120
        direct = [field.initial_vector]
        for _ in range(final_time):
            direct.append(
                field.step_vector(direct[-1])
            )

        cursor = field.backward_cursor(final_time)

        for distance in range(13):
            base, phase = (
                cursor.period_base_vector_at_back(
                    distance
                )
            )
            reconstructed = (
                field.expand_period_vector(
                    base,
                    phase,
                )
            )
            self.assertEqual(
                reconstructed,
                direct[final_time - distance],
            )
            self.assertEqual(
                cursor.vector_at_back(distance),
                direct[final_time - distance],
            )

        cursor.step_back_many(17)
        self.assertEqual(
            cursor.time,
            final_time - 17,
        )
        self.assertEqual(
            cursor.current_vector(),
            direct[final_time - 17],
        )

    def test_floquet_codec_roundtrip(self):
        graph = phase_graph()
        codec = build_floquet_path_codec(
            graph,
            start_nodes=(("a", 0),),
            phase_of=lambda node: node[1],
            period=3,
            width=32,
            cache_rows=1,
        )

        for steps in range(14):
            for state in range(codec.total_count(steps)):
                start, edges = codec.decode_edges(
                    state,
                    steps,
                )
                rebuilt, rebuilt_steps = codec.encode_edges(
                    start,
                    [edge.label for edge in edges],
                )
                self.assertEqual(
                    (rebuilt, rebuilt_steps),
                    (state, steps),
                )


if __name__ == "__main__":
    unittest.main()

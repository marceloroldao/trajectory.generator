import unittest

from trajectory_generator.count_field_recurrence import (
    CountFieldRecurrence,
)
from trajectory_generator.recurrence_path_trajectory import (
    build_recurrence_path_codec,
)


class CountFieldRecurrenceTests(unittest.TestCase):
    def test_exact_rows_match_direct_propagation(self):
        graph = {
            "s": ["a", "b"],
            "a": ["a", "c"],
            "b": ["c"],
            "c": ["a"],
        }
        field = CountFieldRecurrence(
            graph,
            start_nodes=("s",),
            cache_rows=3,
        )

        current = field.initial_vector
        for t in range(60):
            self.assertEqual(field.vector_at(t), current)
            current = field.step_vector(current)

        self.assertTrue(field.validate_recurrence(40))
        self.assertLessEqual(field.order, field.reachable_state_count)

    def test_cache_is_bounded(self):
        graph = {
            "s": ["a", "b"],
            "a": ["a", "b"],
            "b": ["a"],
        }
        field = CountFieldRecurrence(
            graph,
            start_nodes=("s",),
            cache_rows=2,
        )

        for t in range(100):
            field.vector_at(t)
            self.assertLessEqual(field.cached_row_count, 2)

    def test_recurrence_codec_roundtrips_complete_small_family(self):
        graph = {
            "s": ["a", "b"],
            "a": ["c"],
            "b": ["c"],
            "c": ["c", "d"],
            "d": ["c"],
        }

        codec = build_recurrence_path_codec(
            graph,
            start_nodes=("s",),
            width=32,
            cache_rows=2,
        )

        for steps in range(12):
            for state in range(codec.total_count(steps)):
                start, edges = codec.decode_edges(state, steps)
                rebuilt, rebuilt_steps = codec.encode_edges(
                    start,
                    [edge.label for edge in edges],
                )
                self.assertEqual(
                    (rebuilt, rebuilt_steps),
                    (state, steps),
                )

                path = codec.reconstruct_physical_path(
                    state,
                    steps,
                )
                self.assertEqual(len(path), steps + 1)



    def test_compact_mode_regenerates_basis_on_demand(self):
        graph = {
            "s": ["a", "b"],
            "a": ["a", "c"],
            "b": ["c"],
            "c": ["a", "b"],
        }
        retained = CountFieldRecurrence(
            graph,
            start_nodes=("s",),
            cache_rows=0,
            retain_basis=True,
        )
        compact = CountFieldRecurrence(
            graph,
            start_nodes=("s",),
            cache_rows=0,
            retain_basis=False,
        )

        self.assertEqual(retained.coefficients, compact.coefficients)
        self.assertEqual(compact.basis_integer_count, 0)
        self.assertEqual(
            compact.derived_basis_integer_count,
            retained.basis_integer_count,
        )

        for t in (0, 1, 5, 20, 75, 200):
            self.assertEqual(
                compact.vector_at(t),
                retained.vector_at(t),
            )

    def test_backward_cursor_reconstructs_every_count_row(self):
        graph = {
            "s": ["a", "b"],
            "a": ["a", "c"],
            "b": ["c"],
            "c": ["a", "b"],
        }
        field = CountFieldRecurrence(
            graph,
            start_nodes=("s",),
            cache_rows=1,
        )

        final_time = 80
        direct = [field.initial_vector]
        for _ in range(final_time):
            direct.append(field.step_vector(direct[-1]))

        cursor = field.backward_cursor(final_time)
        while cursor.time >= 0:
            self.assertEqual(
                cursor.current_vector(),
                direct[cursor.time],
            )
            if cursor.time > 0:
                self.assertEqual(
                    cursor.previous_vector(),
                    direct[cursor.time - 1],
                )
                cursor.step_back()
            else:
                break

        self.assertLessEqual(
            cursor.stored_row_count,
            len(field.reduced_coefficients),
        )

    def test_storage_is_horizon_independent(self):
        graph = {
            "a": ["a", "b"],
            "b": ["a"],
        }
        field = CountFieldRecurrence(
            graph,
            start_nodes=("a",),
            cache_rows=1,
        )

        fixed = field.basis_integer_count
        for t in (10, 100, 1000, 10000):
            field.vector_at(t)
            self.assertEqual(field.basis_integer_count, fixed)
            self.assertLessEqual(field.cached_row_count, 1)
            self.assertGreater(
                field.direct_table_integer_count(t),
                fixed,
            )


if __name__ == "__main__":
    unittest.main()

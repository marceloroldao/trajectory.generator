import unittest

from trajectory_generator.minimal_reversible_completion import (
    LiftedState,
    MinimalReversibleCompletion,
)


def identity(edge, time, vertical, size):
    return vertical


def reflection(edge, time, vertical, size):
    return (-vertical) % size


def phase_reflection(edge, time, vertical, size):
    sigma = -1 if (time % 3) == 1 else 1
    return (sigma * vertical) % size


class MinimalReversibleCompletionTests(unittest.TestCase):
    def graph(self):
        return {
            "a": ("b", "c"),
            "b": ("c", "a"),
            "c": ("a",),
        }

    def test_fiber_cardinality_equals_history_multiplicity(self):
        completion = MinimalReversibleCompletion(
            self.graph(),
            start_nodes=("a",),
        )

        for time in range(7):
            for node in completion.nodes:
                histories, minimum = completion.minimality_certificate(
                    node,
                    time,
                )
                self.assertEqual(histories, minimum)
                self.assertEqual(
                    histories,
                    len(completion.histories(node, time)),
                )

    def test_identity_and_reflection_are_both_exact_lifts(self):
        completion = MinimalReversibleCompletion(
            self.graph(),
            start_nodes=("a",),
        )

        saw_difference = False

        for time in range(6):
            for node in completion.nodes:
                size = completion.fiber_size(node, time)
                for vertical in range(size):
                    state = LiftedState(node, vertical)
                    for edge in completion.outgoing[node]:
                        nxt_identity = completion.advance(
                            state,
                            time,
                            edge.label,
                            gauge=identity,
                        )
                        prev_identity, recovered_identity = (
                            completion.rewind(
                                nxt_identity,
                                time + 1,
                                gauge=identity,
                            )
                        )
                        self.assertEqual(prev_identity, state)
                        self.assertEqual(
                            recovered_identity,
                            edge,
                        )

                        nxt_reflection = completion.advance(
                            state,
                            time,
                            edge.label,
                            gauge=reflection,
                        )
                        prev_reflection, recovered_reflection = (
                            completion.rewind(
                                nxt_reflection,
                                time + 1,
                                gauge=reflection,
                            )
                        )
                        self.assertEqual(prev_reflection, state)
                        self.assertEqual(
                            recovered_reflection,
                            edge,
                        )

                        if nxt_identity != nxt_reflection:
                            saw_difference = True

        self.assertTrue(saw_difference)

    def test_gauge_map_preserves_underlying_history(self):
        completion = MinimalReversibleCompletion(
            self.graph(),
            start_nodes=("a",),
        )

        for time in range(7):
            for node in completion.nodes:
                size = completion.fiber_size(node, time)
                for vertical in range(size):
                    identity_state = LiftedState(
                        node,
                        vertical,
                    )
                    reflected = completion.gauge_map(
                        identity_state,
                        time,
                        source_gauge=identity,
                        target_gauge=phase_reflection,
                    )

                    h1 = completion.history_at(
                        identity_state,
                        time,
                        gauge=identity,
                    )
                    h2 = completion.history_at(
                        reflected,
                        time,
                        gauge=phase_reflection,
                    )
                    self.assertEqual(h1, h2)


if __name__ == "__main__":
    unittest.main()

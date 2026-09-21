import unittest

from trajectory_generator.minimal_reversible_completion import (
    MinimalReversibleCompletion,
)
from trajectory_generator.reversible_natural_extension import (
    ReversibleNaturalExtension,
)


def identity(edge, time, vertical, size):
    return vertical


def alternating(edge, time, vertical, size):
    sigma = -1 if (time & 1) else 1
    shift = 1 if edge.label.endswith(".1") else 0
    return (sigma * vertical + shift) % size


class ReversibleNaturalExtensionTests(unittest.TestCase):
    def build(self):
        completion = MinimalReversibleCompletion(
            {
                0: (1, 2),
                1: (0, 2),
                2: (0,),
            },
            start_nodes=(0,),
        )
        return ReversibleNaturalExtension(
            completion
        )

    def test_history_forward_reverse_is_exact(self):
        extension = self.build()

        for time in range(6):
            for history in extension.histories_at(time):
                for edge in extension.completion.outgoing[
                    history.endpoint
                ]:
                    nxt = extension.advance_history(
                        history,
                        edge.label,
                    )
                    previous, recovered = (
                        extension.rewind_history(nxt)
                    )
                    self.assertEqual(previous, history)
                    self.assertEqual(recovered, edge)

    def test_each_gauge_is_bijective_chart(self):
        extension = self.build()

        for time in range(7):
            self.assertTrue(
                extension.chart_is_bijection(
                    time,
                    gauge=identity,
                )
            )
            self.assertTrue(
                extension.chart_is_bijection(
                    time,
                    gauge=alternating,
                )
            )

    def test_gauge_change_conjugates_dynamics(self):
        extension = self.build()

        for time in range(6):
            for history in extension.histories_at(time):
                for edge in extension.completion.outgoing[
                    history.endpoint
                ]:
                    self.assertTrue(
                        extension.transition_conjugacy_holds(
                            history,
                            time,
                            edge.label,
                            source_gauge=identity,
                            target_gauge=alternating,
                        )
                    )


if __name__ == "__main__":
    unittest.main()

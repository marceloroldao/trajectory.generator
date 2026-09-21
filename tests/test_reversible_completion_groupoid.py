import unittest

from trajectory_generator.minimal_reversible_completion import (
    MinimalReversibleCompletion,
)
from trajectory_generator.reversible_completion_groupoid import (
    GaugeChart,
    ReversibleCompletionGroupoid,
)


def identity(edge, time, vertical, size):
    return vertical


def reflection(edge, time, vertical, size):
    return (-vertical) % size


def alternating(edge, time, vertical, size):
    sigma = -1 if (time & 1) else 1
    shift = 1 if edge.label.endswith(".1") else 0
    return (sigma * vertical + shift) % size


class ReversibleCompletionGroupoidTests(unittest.TestCase):
    def build(self):
        completion = MinimalReversibleCompletion(
            {
                0: (1, 2),
                1: (0, 2),
                2: (0,),
            },
            start_nodes=(0,),
        )
        return ReversibleCompletionGroupoid(
            completion
        )

    def charts(self):
        return (
            GaugeChart("identity", identity),
            GaugeChart("reflection", reflection),
            GaugeChart("alternating", alternating),
        )

    def test_groupoid_identities(self):
        groupoid = self.build()
        charts = self.charts()

        for time in range(7):
            for history in groupoid.extension.histories_at(time):
                base = groupoid.state(
                    history,
                    time,
                    charts[0],
                )

                for chart in charts:
                    state = groupoid.change(
                        base,
                        time,
                        charts[0],
                        chart,
                    )
                    self.assertTrue(
                        groupoid.identity_holds(
                            state,
                            time,
                            chart,
                        )
                    )

                for source in charts:
                    source_state = groupoid.state(
                        history,
                        time,
                        source,
                    )
                    for target in charts:
                        self.assertTrue(
                            groupoid.inverse_holds(
                                source_state,
                                time,
                                source,
                                target,
                            )
                        )
                        for third in charts:
                            self.assertTrue(
                                groupoid.composition_holds(
                                    source_state,
                                    time,
                                    source,
                                    target,
                                    third,
                                )
                            )

    def test_transition_naturality(self):
        groupoid = self.build()
        charts = self.charts()

        for time in range(6):
            for history in groupoid.extension.histories_at(time):
                for source in charts:
                    state = groupoid.state(
                        history,
                        time,
                        source,
                    )
                    for edge in groupoid.completion.outgoing[
                        history.endpoint
                    ]:
                        for target in charts:
                            self.assertTrue(
                                groupoid.transition_naturality_holds(
                                    state,
                                    time,
                                    edge.label,
                                    source,
                                    target,
                                )
                            )


if __name__ == "__main__":
    unittest.main()

"""Gate coordinate-free natural extension and gauge conjugacy."""

from trajectory_generator.minimal_reversible_completion import (
    MinimalReversibleCompletion,
)
from trajectory_generator.reversible_natural_extension import (
    ReversibleNaturalExtension,
)


def identity(edge, time, vertical, size):
    return vertical


def reflect(edge, time, vertical, size):
    return (-vertical) % size


def phase_merge(edge, time, vertical, size):
    sigma = -1 if (time % 3) == 1 else 1
    incoming_index = int(edge.label.rsplit(".", 1)[-1])
    return (
        sigma * vertical + incoming_index
    ) % size


GRAPHS = {
    "merge": (
        {
            0: (1, 2),
            1: (2,),
            2: (1,),
        },
        (0,),
    ),
    "branch_merge": (
        {
            0: (1, 2),
            1: (0, 2),
            2: (0,),
        },
        (0,),
    ),
    "two_starts": (
        {
            0: (2,),
            1: (2,),
            2: (0, 1),
        },
        (0, 1),
    ),
}


def gate(name, adjacency, starts, horizon=7):
    completion = MinimalReversibleCompletion(
        adjacency,
        start_nodes=starts,
    )
    extension = ReversibleNaturalExtension(
        completion
    )

    gauges = (identity, reflect, phase_merge)

    bijective = True
    conjugate = True
    history_reversible = True
    coordinate_difference = False

    checked_histories = 0
    checked_transitions = 0

    for time in range(horizon + 1):
        for gauge in gauges:
            if not extension.chart_is_bijection(
                time,
                gauge=gauge,
            ):
                bijective = False

        histories = extension.histories_at(time)
        checked_histories += len(histories)

        for history in histories:
            states = [
                extension.chart(
                    history,
                    time,
                    gauge=gauge,
                )
                for gauge in gauges
            ]
            if len(set(states)) > 1:
                coordinate_difference = True

            if time == horizon:
                continue

            for edge in completion.outgoing[
                history.endpoint
            ]:
                checked_transitions += 1
                nxt = extension.advance_history(
                    history,
                    edge.label,
                )
                previous, recovered = (
                    extension.rewind_history(nxt)
                )
                if previous != history or recovered != edge:
                    history_reversible = False

                for source_gauge in gauges:
                    for target_gauge in gauges:
                        if not extension.transition_conjugacy_holds(
                            history,
                            time,
                            edge.label,
                            source_gauge=source_gauge,
                            target_gauge=target_gauge,
                        ):
                            conjugate = False

    passed = (
        bijective
        and conjugate
        and history_reversible
        and coordinate_difference
    )

    print(
        "NATURAL_EXTENSION_GAUGE_GATE",
        "name", name,
        "PASS", passed,
        "horizon", horizon,
        "histories_checked", checked_histories,
        "transitions_checked", checked_transitions,
        "charts_bijective", bijective,
        "history_reversible", history_reversible,
        "gauge_conjugacy", conjugate,
        "coordinate_difference", coordinate_difference,
    )
    return passed


def main():
    results = [
        gate(name, adjacency, starts)
        for name, (adjacency, starts)
        in GRAPHS.items()
    ]

    print(
        "NATURAL_EXTENSION_GAUGE_FULL_GATE",
        "PASS", all(results),
        "conclusion",
        "history space is invariant; vertical coordinates are gauge charts",
    )

    if not all(results):
        raise AssertionError(
            "natural extension gauge gate failed"
        )


if __name__ == "__main__":
    main()

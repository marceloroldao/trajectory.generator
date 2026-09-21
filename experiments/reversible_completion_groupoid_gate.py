"""Gate gauge-groupoid identities of minimal reversible completion."""

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


GRAPHS = {
    "merge": (
        {
            0: (1, 2),
            1: (0,),
            2: (0,),
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
    "parallel": (
        {
            0: (1, 1),
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


CHARTS = (
    GaugeChart("identity", identity),
    GaugeChart("reflection", reflection),
    GaugeChart("alternating", alternating),
)


def gate(name, adjacency, starts, horizon=7):
    completion = MinimalReversibleCompletion(
        adjacency,
        start_nodes=starts,
    )
    groupoid = ReversibleCompletionGroupoid(
        completion
    )

    identity_ok = True
    inverse_ok = True
    composition_ok = True
    naturality_ok = True
    history_invariant = True

    checked_states = 0
    checked_compositions = 0
    checked_transitions = 0

    for time in range(horizon + 1):
        histories = groupoid.extension.histories_at(time)

        for history in histories:
            for source in CHARTS:
                state = groupoid.state(
                    history,
                    time,
                    source,
                )
                checked_states += 1

                if not groupoid.identity_holds(
                    state,
                    time,
                    source,
                ):
                    identity_ok = False

                for target in CHARTS:
                    mapped = groupoid.change(
                        state,
                        time,
                        source,
                        target,
                    )

                    if not groupoid.inverse_holds(
                        state,
                        time,
                        source,
                        target,
                    ):
                        inverse_ok = False

                    if not groupoid.same_underlying_history(
                        state,
                        source,
                        mapped,
                        target,
                        time,
                    ):
                        history_invariant = False

                    for third in CHARTS:
                        checked_compositions += 1
                        if not groupoid.composition_holds(
                            state,
                            time,
                            source,
                            target,
                            third,
                        ):
                            composition_ok = False

                if time == horizon:
                    continue

                for edge in completion.outgoing[
                    history.endpoint
                ]:
                    for target in CHARTS:
                        checked_transitions += 1
                        if not groupoid.transition_naturality_holds(
                            state,
                            time,
                            edge.label,
                            source,
                            target,
                        ):
                            naturality_ok = False

    passed = (
        identity_ok
        and inverse_ok
        and composition_ok
        and naturality_ok
        and history_invariant
    )

    print(
        "REVERSIBLE_COMPLETION_GROUPOID",
        "name", name,
        "PASS", passed,
        "horizon", horizon,
        "states_checked", checked_states,
        "compositions_checked", checked_compositions,
        "transitions_checked", checked_transitions,
        "identity", identity_ok,
        "inverse", inverse_ok,
        "composition", composition_ok,
        "transition_naturality", naturality_ok,
        "history_invariant", history_invariant,
    )
    return passed


def main():
    results = [
        gate(name, adjacency, starts)
        for name, (adjacency, starts)
        in GRAPHS.items()
    ]

    passed = all(results)

    print(
        "REVERSIBLE_COMPLETION_GROUPOID_FULL_GATE",
        "PASS", passed,
        "conclusion",
        "minimal reversible lifts are unique up to history-preserving "
        "time-dependent fiber gauge isomorphism",
    )

    if not passed:
        raise AssertionError(
            "reversible completion groupoid gate failed"
        )


if __name__ == "__main__":
    main()

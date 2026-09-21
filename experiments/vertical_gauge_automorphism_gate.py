"""Gate automorphism invariance of candidate vertical gauges."""

from trajectory_generator.minimal_reversible_completion import (
    MinimalReversibleCompletion,
)


GRAPH = {
    0: (1, 2),
    1: (3,),
    2: (3,),
    3: (0,),
}

SWAP = {
    0: 0,
    1: 2,
    2: 1,
    3: 3,
}


def mapped_edge(completion, edge):
    source = SWAP[edge.source]
    target = SWAP[edge.target]
    matches = [
        candidate
        for candidate in completion.outgoing[source]
        if candidate.target == target
    ]
    if len(matches) != 1:
        raise AssertionError(
            "automorphism edge image is not unique"
        )
    return matches[0]


def incoming_index(completion, edge):
    return completion.incoming[edge.target].index(edge)


def phase_reflection(time, vertical, size):
    sigma = -1 if (time % 3) == 1 else 1
    return (sigma * vertical) % size


def phase_merge(completion, edge, time, vertical, size):
    sigma = -1 if (time % 3) == 1 else 1
    return (
        sigma * vertical
        + incoming_index(completion, edge)
    ) % size


def main():
    completion = MinimalReversibleCompletion(
        GRAPH,
        start_nodes=(0,),
    )

    reflection_equivariant = True
    ordered_merge_equivariant = True
    reflection_checks = 0
    merge_checks = 0
    first_order_witness = None

    for time in range(14):
        for edge in completion.edges:
            mapped = mapped_edge(completion, edge)

            source_size = completion.fiber_size(
                edge.source,
                time,
            )
            mapped_size = completion.fiber_size(
                mapped.source,
                time,
            )

            if source_size != mapped_size:
                raise AssertionError(
                    "graph automorphism did not preserve fiber size"
                )

            if source_size == 0:
                continue

            for vertical in range(source_size):
                reflection_checks += 1
                if (
                    phase_reflection(
                        time,
                        vertical,
                        source_size,
                    )
                    != phase_reflection(
                        time,
                        vertical,
                        mapped_size,
                    )
                ):
                    reflection_equivariant = False

                merge_checks += 1
                left = phase_merge(
                    completion,
                    edge,
                    time,
                    vertical,
                    source_size,
                )
                right = phase_merge(
                    completion,
                    mapped,
                    time,
                    vertical,
                    mapped_size,
                )
                if left != right:
                    ordered_merge_equivariant = False
                    if first_order_witness is None:
                        first_order_witness = (
                            time,
                            edge.label,
                            mapped.label,
                            source_size,
                            vertical,
                            incoming_index(completion, edge),
                            incoming_index(completion, mapped),
                            left,
                            right,
                        )

    passed = (
        reflection_equivariant
        and not ordered_merge_equivariant
        and first_order_witness is not None
    )

    print(
        "VERTICAL_GAUGE_AUTOMORPHISM_GATE",
        "PASS", passed,
        "reflection_equivariant",
        reflection_equivariant,
        "phase_merge_raw_equivariant",
        ordered_merge_equivariant,
        "reflection_checks",
        reflection_checks,
        "merge_checks",
        merge_checks,
        "first_order_witness",
        first_order_witness,
        "conclusion",
        "phase reflection is invariant under predecessor swap; "
        "incoming-index rotation is an ordered-chart convention",
    )

    if not passed:
        raise AssertionError(
            "vertical gauge automorphism gate failed"
        )


if __name__ == "__main__":
    main()

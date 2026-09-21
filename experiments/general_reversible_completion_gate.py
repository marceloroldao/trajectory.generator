"""Gate the general minimal reversible-completion theorem and gauge freedom."""

from itertools import product

from trajectory_generator.minimal_reversible_completion import (
    LiftedState,
    MinimalReversibleCompletion,
)


def identity(edge, time, vertical, size):
    return vertical


def reflection(edge, time, vertical, size):
    return (-vertical) % size


def alternating(edge, time, vertical, size):
    sigma = -1 if (time & 1) else 1
    return (sigma * vertical + (edge.label.endswith(".1"))) % size


def graph_family():
    # Small deterministic enumeration of different merge/branch geometries.
    yield "merge", {
        0: (1, 2),
        1: (2,),
        2: (1,),
    }, (0,)

    yield "branch_merge", {
        0: (1, 2),
        1: (0, 2),
        2: (0,),
    }, (0,)

    yield "two_starts", {
        0: (2,),
        1: (2,),
        2: (0, 1),
    }, (0, 1)

    yield "parallel_growth", {
        0: (1, 1),
        1: (0, 2),
        2: (0,),
    }, (0,)


def gate_graph(name, adjacency, starts, horizon=7):
    completion = MinimalReversibleCompletion(
        adjacency,
        start_nodes=starts,
    )

    minimality = True
    partition = True
    reversible = True
    projection = True
    gauge_equivalent = True
    nonunique = False

    gauges = (identity, reflection, alternating)

    checked_states = 0
    checked_edges = 0
    gauge_pairs = 0

    for time in range(horizon + 1):
        for node in completion.nodes:
            histories = completion.histories(node, time)
            count, minimum = completion.minimality_certificate(
                node,
                time,
            )
            if count != len(histories) or minimum != count:
                minimality = False

            if time < horizon:
                blocks = completion.incoming_blocks(
                    node,
                    time,
                )
                if blocks:
                    if blocks[0][1] != 0:
                        partition = False
                    for left, right in zip(blocks, blocks[1:]):
                        if left[2] != right[1]:
                            partition = False
                    expected = completion.fiber_size(
                        node,
                        time + 1,
                    )
                    if blocks[-1][2] != expected:
                        partition = False

            for vertical in range(count):
                state = LiftedState(node, vertical)
                checked_states += 1

                # All gauges represent the exact same underlying history set.
                base_history = completion.history_at(
                    state,
                    time,
                    gauge=identity,
                )
                for gauge in gauges[1:]:
                    mapped = completion.gauge_map(
                        state,
                        time,
                        source_gauge=identity,
                        target_gauge=gauge,
                    )
                    recovered_history = completion.history_at(
                        mapped,
                        time,
                        gauge=gauge,
                    )
                    gauge_pairs += 1
                    if recovered_history != base_history:
                        gauge_equivalent = False

                if time >= horizon:
                    continue

                for edge in completion.outgoing[node]:
                    checked_edges += 1
                    images = []

                    for gauge in gauges:
                        nxt = completion.advance(
                            state,
                            time,
                            edge.label,
                            gauge=gauge,
                        )
                        if nxt.node != edge.target:
                            projection = False

                        previous, recovered_edge = completion.rewind(
                            nxt,
                            time + 1,
                            gauge=gauge,
                        )
                        if (
                            previous != state
                            or recovered_edge != edge
                        ):
                            reversible = False
                        images.append(nxt)

                    if len(set(images)) > 1:
                        nonunique = True

    passed = (
        minimality
        and partition
        and reversible
        and projection
        and gauge_equivalent
        and nonunique
    )

    print(
        "GENERAL_REVERSIBLE_COMPLETION_GATE",
        "name", name,
        "PASS", passed,
        "horizon", horizon,
        "states_checked", checked_states,
        "edges_checked", checked_edges,
        "gauge_pairs_checked", gauge_pairs,
        "minimality", minimality,
        "partition", partition,
        "reversible", reversible,
        "projection", projection,
        "gauge_equivalent", gauge_equivalent,
        "vertical_law_nonunique", nonunique,
    )
    return passed


def main():
    results = [
        gate_graph(name, adjacency, starts)
        for name, adjacency, starts in graph_family()
    ]

    print(
        "GENERAL_REVERSIBLE_COMPLETION_FULL_GATE",
        "PASS", all(results),
        "graphs", len(results),
        "conclusion",
        "fiber sizes and edge-block cardinalities are forced; "
        "internal vertical permutations are gauge freedom",
    )

    if not all(results):
        raise AssertionError(
            "general reversible completion gate failed"
        )


if __name__ == "__main__":
    main()

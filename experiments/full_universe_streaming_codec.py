"""Full-universe streaming address for the phase-lifted topological universes."""

from recurrent_orbit_core import graph
from topological_transition_state import (
    counts as legacy_counts,
    initial_topology,
    make_codec as make_legacy_codec,
)

from trajectory_generator.public_graph_trajectory import (
    build_public_graph_codec,
    monotone_graph_frontier,
)


CANDIDATES = {
    "robust_208": ((1, 0, 0, 2), 208),
    "balanced_221": ((0, 2, 4, 4), 221),
    "long_239": ((3, 2, 4, 4), 239),
}


def initial_nodes():
    return tuple(
        (state, initial_topology(state), 0)
        for state in range(8)
    )


def bits_from_decoded_path(start, edges):
    history = start[0]
    bits = [
        (history >> 2) & 1,
        (history >> 1) & 1,
        history & 1,
    ]
    for edge in edges:
        bits.append(edge.target[0] & 1)
    return bits


def language_set_from_streaming(codec, steps):
    transition_steps = steps - 3
    out = set()
    for state in range(codec.total_count(transition_steps)):
        start, edges = codec.decode_edges(state, transition_steps)
        out.add(tuple(bits_from_decoded_path(start, edges)))
    return out


def language_set_from_legacy(params, steps):
    total, unrank, _ = make_legacy_codec(params)
    return {
        tuple(unrank(rank, steps))
        for rank in range(total(steps))
    }


def main():
    for name, (params, expected_frontier) in CANDIDATES.items():
        adjacency = graph(params)
        _, codec = build_public_graph_codec(
            adjacency,
            start_nodes=initial_nodes(),
            width=63,
        )

        historical = legacy_counts(
            params,
            max_steps=expected_frontier + 2,
        )

        count_match = True
        for steps in range(3, expected_frontier + 2):
            if codec.total_count(steps - 3) != historical[steps]:
                count_match = False
                break

        language_match = True
        for steps in range(3, 11):
            if (
                language_set_from_streaming(codec, steps)
                != language_set_from_legacy(params, steps)
            ):
                language_match = False
                break

        transition_frontier = monotone_graph_frontier(codec)
        trajectory_frontier = transition_frontier + 3

        final_state = codec.total_count(transition_frontier) - 1
        start, edges = codec.decode_edges(
            final_state,
            transition_frontier,
        )
        bits = bits_from_decoded_path(start, edges)

        total, _, validate = make_legacy_codec(params)
        rebuilt, rebuilt_steps = codec.encode_edges(
            start,
            [edge.label for edge in edges],
        )

        print(
            "FULL_UNIVERSE_STREAMING",
            "name", name,
            "PASS",
            count_match
            and language_match
            and trajectory_frontier == expected_frontier
            and validate(bits)
            and (rebuilt, rebuilt_steps)
                == (final_state, transition_frontier),
            "count_match", count_match,
            "language_match", language_match,
            "frontier", trajectory_frontier,
            "expected_frontier", expected_frontier,
            "count_frontier",
            codec.total_count(transition_frontier),
            "next_count",
            codec.total_count(transition_frontier + 1),
            "bits_recovered", len(bits),
        )

        print(
            "FULL_UNIVERSE_COUNT_IDENTITY",
            "name", name,
            "PASS",
            all(
                codec.total_count(steps - 3) == historical[steps]
                for steps in range(3, expected_frontier + 2)
            ),
            "checked_steps", expected_frontier - 1,
        )


if __name__ == "__main__":
    main()

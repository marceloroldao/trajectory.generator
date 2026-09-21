"""Streaming codec for the recurrent information-clock macrograph."""

from information_clock_macrograph import dominant_component, macro_edges
from trajectory_generator.weighted_path_trajectory import (
    WeightedEdge,
    WeightedPathCodec,
)


def build_codec(width=63):
    graph_edges, component = dominant_component()
    branches, macros = macro_edges(graph_edges, component)
    nodes = tuple(sorted(branches))

    ordered = sorted(
        macros,
        key=lambda row: (row[0], row[1], row[2], row[3]),
    )
    edges = []
    for i, (source, target, length, path) in enumerate(ordered):
        label = f"m{i}:{length}"
        edges.append(
            WeightedEdge(
                label=label,
                source=source,
                target=target,
                length=length,
                path=path,
            )
        )

    return WeightedPathCodec(nodes, edges, start_nodes=nodes, width=width)


def conservative_streaming_frontier(codec):
    t = 0
    while codec.capacity_ok(t + 1):
        t += 1
    return t


def exhaustive_small_gate(codec, max_steps=40):
    checked = 0
    for t in range(max_steps + 1):
        for state in range(codec.total_count(t)):
            start, edges = codec.decode_edges(state, t)
            got_state, got_t = codec.encode_edges(
                start,
                [edge.label for edge in edges],
            )
            if (got_state, got_t) != (state, t):
                return False, checked, (t, state)
            if len(codec.reconstruct_physical_path(state, t)) != t + 1:
                return False, checked, ("physical-length", t, state)
            checked += 1
    return True, checked, None


def main():
    codec = build_codec(width=63)

    ok, checked, error = exhaustive_small_gate(codec)
    print(
        "INFORMATION_CLOCK_STREAMING_EXHAUSTIVE",
        "PASS", ok,
        "checked", checked,
        "error", error,
    )

    frontier = conservative_streaming_frontier(codec)
    print(
        "INFORMATION_CLOCK_STREAMING_63BIT",
        "frontier", frontier,
        "count_frontier", codec.total_count(frontier),
        "occupancy_frontier", codec.total_count(frontier) / (1 << 63),
        "next_time", frontier + 1,
        "next_count", codec.total_count(frontier + 1),
        "next_fits", codec.capacity_ok(frontier + 1),
    )

    for t in range(frontier, frontier + 4):
        print(
            "INFORMATION_CLOCK_EXACT_LENGTH",
            "T", t,
            "count", codec.total_count(t),
            "fits63", codec.capacity_ok(t),
        )

    state = codec.total_count(frontier) - 1
    start, edges = codec.decode_edges(state, frontier)
    rebuilt_state, rebuilt_t = codec.encode_edges(
        start,
        [edge.label for edge in edges],
    )
    physical = codec.reconstruct_physical_path(state, frontier)
    print(
        "INFORMATION_CLOCK_FULL_REGEN",
        "PASS",
        (rebuilt_state, rebuilt_t) == (state, frontier)
        and len(physical) == frontier + 1,
        "macro_events", len(edges),
        "physical_steps", frontier,
        "start", start,
    )


if __name__ == "__main__":
    main()

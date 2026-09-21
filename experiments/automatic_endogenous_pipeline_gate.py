"""Automatic endogenous-universe -> recurrent-core -> reversible-address gate."""

from information_clock_macrograph import (
    dominant_component as legacy_dominant_component,
    macro_edges as legacy_macro_edges,
)
from recurrent_orbit_core import graph

from trajectory_generator.recurrent_macrograph import (
    build_physical_core_codec,
    derive_recurrent_structure,
    monotone_physical_frontier,
)


CANDIDATES = {
    "robust_208": (1, 0, 0, 2),
    "balanced_221": (0, 2, 4, 4),
    "long_239": (3, 2, 4, 4),
}


def macro_signature(structure):
    return sorted(
        (
            edge.source,
            edge.target,
            edge.length,
            edge.path,
        )
        for edge in structure.macro_edges
    )


def legacy_balanced_signature():
    edges, component = legacy_dominant_component()
    _, macros = legacy_macro_edges(edges, component)
    return sorted(macros)


def small_roundtrip_gate(codec, max_steps=18):
    checked = 0
    for steps in range(max_steps + 1):
        for state in range(codec.total_count(steps)):
            start, edges = codec.decode_edges(state, steps)
            rebuilt, rebuilt_steps = codec.encode_edges(
                start,
                [edge.label for edge in edges],
            )
            if (rebuilt, rebuilt_steps) != (state, steps):
                return False, checked, (steps, state)
            path = codec.reconstruct_physical_path(state, steps)
            if len(path) != steps + 1:
                return False, checked, ("path", steps, state)
            checked += 1
    return True, checked, None


def main():
    for name, params in CANDIDATES.items():
        adjacency = graph(params)
        structure, codec = build_physical_core_codec(
            adjacency,
            width=63,
        )

        ok, checked, error = small_roundtrip_gate(codec)
        frontier = monotone_physical_frontier(codec)

        print(
            "AUTO_RECURRENT_PIPELINE",
            "name", name,
            "PASS", ok,
            "checked", checked,
            "error", error,
            "core_nodes", len(structure.component),
            "branch_nodes", len(structure.branch_nodes),
            "macro_edges", len(structure.macro_edges),
            "macro_lengths", sorted(
                edge.length for edge in structure.macro_edges
            ),
            "growth_rate", f"{structure.growth_rate:.12f}",
            "frontier63", frontier,
            "count_frontier", codec.total_count(frontier),
            "occupancy", codec.total_count(frontier) / (1 << 63),
            "next_count", codec.total_count(frontier + 1),
        )

        final_state = codec.total_count(frontier) - 1
        start, path_edges = codec.decode_edges(final_state, frontier)
        rebuilt, rebuilt_steps = codec.encode_edges(
            start,
            [edge.label for edge in path_edges],
        )
        physical = codec.reconstruct_physical_path(
            final_state,
            frontier,
        )
        print(
            "AUTO_RECURRENT_FULL_REGEN",
            "name", name,
            "PASS",
            (rebuilt, rebuilt_steps) == (final_state, frontier)
            and len(physical) == frontier + 1,
            "physical_steps", frontier,
            "start", start,
        )

    balanced = derive_recurrent_structure(
        graph(CANDIDATES["balanced_221"])
    )
    print(
        "AUTO_VS_LEGACY_BALANCED_MACROGRAPH",
        "PASS",
        macro_signature(balanced) == legacy_balanced_signature(),
        "auto_core_nodes", len(balanced.component),
        "auto_branch_nodes", len(balanced.branch_nodes),
        "auto_lengths", sorted(
            edge.length for edge in balanced.macro_edges
        ),
    )


if __name__ == "__main__":
    main()

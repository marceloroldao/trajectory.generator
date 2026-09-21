"""Audit whether forward deterministic information-clock flights are reverse-unifilar.

A macro-flight is forward deterministic between branch nodes, but exact reverse
skipping is trivial only if each interior target on that flight has one internal
predecessor in the recurrent core.

If an interior node has multiple internal predecessors, the information-clock
flight contains a reverse merge. Then the vertical rank must still select a
predecessor, and a correct macro-runtime needs a composed vertical subfiber
embedding rather than a topology-only jump.
"""

from recurrent_orbit_core import graph

from trajectory_generator.recurrent_macrograph import (
    derive_recurrent_structure,
)


CANDIDATES = {
    "robust": (1, 0, 0, 2),
    "balanced": (0, 2, 4, 4),
    "long": (3, 2, 4, 4),
}


def main():
    for name, params in CANDIDATES.items():
        adjacency = graph(params)
        structure = derive_recurrent_structure(
            adjacency
        )
        comp = set(structure.component)

        internal_indegree = {
            node: 0
            for node in comp
        }
        for source in comp:
            for target in adjacency.get(source, ()):
                if target in comp:
                    internal_indegree[target] += 1

        total_interior_steps = 0
        reverse_unifilar_steps = 0
        merged_interior_steps = 0
        fully_reverse_unifilar_edges = 0
        rows = []

        for macro in structure.macro_edges:
            interior_targets = macro.path[1:-1]
            merged = [
                node
                for node in interior_targets
                if internal_indegree[node] != 1
            ]
            total_interior_steps += len(
                interior_targets
            )
            reverse_unifilar_steps += (
                len(interior_targets)
                - len(merged)
            )
            merged_interior_steps += len(merged)
            if not merged:
                fully_reverse_unifilar_edges += 1

            rows.append((
                macro.label,
                macro.length,
                len(interior_targets),
                len(merged),
            ))

        all_unifilar = (
            merged_interior_steps == 0
        )
        print(
            "INFORMATION_CLOCK_REVERSE_UNIFILAR_AUDIT",
            "name", name,
            "core_nodes", len(structure.component),
            "macro_edges", len(structure.macro_edges),
            "macro_lengths",
            tuple(edge.length for edge in structure.macro_edges),
            "fully_reverse_unifilar_macro_edges",
            fully_reverse_unifilar_edges,
            "interior_steps",
            total_interior_steps,
            "reverse_unifilar_interior_steps",
            reverse_unifilar_steps,
            "merged_interior_steps",
            merged_interior_steps,
            "all_macro_flights_reverse_unifilar",
            all_unifilar,
            "edge_rows",
            tuple(rows),
        )


if __name__ == "__main__":
    main()

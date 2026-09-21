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
from topological_transition_state import initial_topology

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

        starts = {
            (state, initial_topology(state), 0)
            for state in range(8)
        }
        reachable = set(starts)
        stack = list(starts)
        while stack:
            source = stack.pop()
            for target in adjacency.get(source, ()):
                if target not in reachable:
                    reachable.add(target)
                    stack.append(target)

        reachable_indegree = {
            node: 0
            for node in reachable
        }
        for source in reachable:
            for target in adjacency.get(source, ()):
                if target in reachable:
                    reachable_indegree[target] += 1

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
        fully_global_reverse_unifilar_edges = 0
        global_merged_interior_steps = 0
        rows = []

        final_predecessor_multiplicity = {}
        for macro in structure.macro_edges:
            if macro.length > 0:
                key = (
                    macro.target,
                    macro.path[-2],
                )
                final_predecessor_multiplicity[key] = (
                    final_predecessor_multiplicity.get(
                        key,
                        0,
                    )
                    + 1
                )

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

            global_merged = [
                node
                for node in interior_targets
                if reachable_indegree.get(node, 0) != 1
            ]
            global_merged_interior_steps += len(
                global_merged
            )
            final_key = (
                macro.target,
                macro.path[-2],
            )
            final_predecessor_unique = (
                final_predecessor_multiplicity[
                    final_key
                ]
                == 1
            )
            fully_global = (
                not global_merged
                and final_predecessor_unique
            )
            if fully_global:
                fully_global_reverse_unifilar_edges += 1

            rows.append((
                macro.label,
                macro.length,
                len(interior_targets),
                len(merged),
                len(global_merged),
                final_predecessor_unique,
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
            "reachable_nodes",
            len(reachable),
            "fully_global_reverse_unifilar_macro_edges",
            fully_global_reverse_unifilar_edges,
            "global_merged_interior_steps",
            global_merged_interior_steps,
            "all_macro_flights_global_reverse_unifilar",
            (
                fully_global_reverse_unifilar_edges
                == len(structure.macro_edges)
            ),
            "edge_rows",
            tuple(rows),
        )


if __name__ == "__main__":
    main()

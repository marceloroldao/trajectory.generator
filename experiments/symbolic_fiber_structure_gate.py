"""Gate symbol-induced canonical fiber order on topological universes."""

from recurrent_orbit_core import graph
from topological_transition_state import (
    initial_topology,
)

from trajectory_generator.symbolic_history_fiber import (
    SymbolicHistoryFibers,
)


CANDIDATES = {
    "robust_208": (1, 0, 0, 2),
    "balanced_221": (0, 2, 4, 4),
    "long_239": (3, 2, 4, 4),
}


def bootstrap_word(state):
    return (
        (state >> 2) & 1,
        (state >> 1) & 1,
        state & 1,
    )


def labeled_universe(params):
    raw = graph(params)
    adjacency = {}

    for source, targets in raw.items():
        rows = []
        for target in targets:
            bit = target[0] & 1
            rows.append((bit, target))
        adjacency[source] = tuple(rows)

    starts = {
        (state, initial_topology(state), 0):
        bootstrap_word(state)
        for state in range(8)
    }
    return adjacency, starts


def relabel_universe(adjacency, starts):
    nodes = set(adjacency)
    for rows in adjacency.values():
        nodes.update(target for _, target in rows)

    ordered = sorted(nodes, key=repr)
    rename = {
        node: ("renamed", len(ordered) - 1 - i)
        for i, node in enumerate(ordered)
    }

    relabeled = {
        rename[source]: tuple(
            (symbol, rename[target])
            for symbol, target in rows
        )
        for source, rows in adjacency.items()
    }
    relabeled_starts = {
        rename[node]: word
        for node, word in starts.items()
    }
    return relabeled, relabeled_starts, rename


def main():
    for name, params in CANDIDATES.items():
        adjacency, starts = labeled_universe(params)
        fibers = SymbolicHistoryFibers(
            adjacency,
            start_words=starts,
            alphabet_order=(0, 1),
        )

        relabeled, relabeled_starts, rename = (
            relabel_universe(adjacency, starts)
        )
        renamed_fibers = SymbolicHistoryFibers(
            relabeled,
            start_words=relabeled_starts,
            alphabet_order=(0, 1),
        )

        unique = True
        relabel_invariant = True
        cyclic_identity = True
        nontrivial_fibers = 0
        histories_checked = 0

        for time in range(10):
            if not fibers.words_are_unique(
                time=time,
                within_each_fiber=True,
            ):
                unique = False

            for node in fibers.nodes:
                first = fibers.chart_signature(
                    node,
                    time,
                )
                second = renamed_fibers.chart_signature(
                    rename[node],
                    time,
                )

                histories_checked += len(first)

                if first != second:
                    relabel_invariant = False

                if len(first) > 1:
                    nontrivial_fibers += 1
                    for rank in range(len(first)):
                        inverse = (
                            fibers.cyclic_inverse_rank(
                                node,
                                time,
                                rank,
                            )
                        )
                        if (
                            fibers.cyclic_add_ranks(
                                node,
                                time,
                                rank,
                                inverse,
                            )
                            != 0
                        ):
                            cyclic_identity = False

        passed = (
            unique
            and relabel_invariant
            and cyclic_identity
            and nontrivial_fibers > 0
        )

        print(
            "SYMBOLIC_FIBER_STRUCTURE_GATE",
            "name", name,
            "PASS", passed,
            "horizons", 10,
            "histories_checked", histories_checked,
            "symbol_words_unique", unique,
            "node_relabel_invariant",
            relabel_invariant,
            "nontrivial_fibers",
            nontrivial_fibers,
            "derived_Zn_inverse_identity",
            cyclic_identity,
            "extra_structure",
            "public ordered binary trajectory alphabet",
        )

        if not passed:
            raise AssertionError(
                f"symbolic fiber structure failed for {name}"
            )


if __name__ == "__main__":
    main()

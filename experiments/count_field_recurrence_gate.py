"""Gate the full-universe streaming codec with a fixed-memory count recurrence."""

from recurrent_orbit_core import graph
from topological_transition_state import (
    counts as legacy_counts,
    initial_topology,
)

from trajectory_generator.public_graph_trajectory import (
    build_public_graph_codec,
)
from trajectory_generator.recurrence_path_trajectory import (
    build_recurrence_path_codec,
)


CANDIDATES = {
    "robust_208": ((1, 0, 0, 2), 208, 31, 46),
    "balanced_221": ((0, 2, 4, 4), 221, 23, 37),
    "long_239": ((3, 2, 4, 4), 239, 22, 34),
}


def initial_nodes():
    return tuple(
        (state, initial_topology(state), 0)
        for state in range(8)
    )


def main():
    for name, (
        params,
        trajectory_frontier,
        expected_order,
        expected_reachable,
    ) in CANDIDATES.items():
        adjacency = graph(params)

        recurrence_codec = build_recurrence_path_codec(
            adjacency,
            start_nodes=initial_nodes(),
            width=63,
            cache_rows=3,
        )
        direct_structure, direct_codec = build_public_graph_codec(
            adjacency,
            start_nodes=initial_nodes(),
            width=63,
        )

        field = recurrence_codec.count_field
        transition_frontier = trajectory_frontier - 3
        historical = legacy_counts(
            params,
            max_steps=trajectory_frontier + 1,
        )

        count_identity = all(
            recurrence_codec.total_count(t)
            == direct_codec.total_count(t)
            == historical[t + 3]
            for t in range(transition_frontier + 2)
        )

        # Address identity: same node/edge ordering after zero-count unreachable
        # buckets are removed, so representative final addresses must decode to
        # the same physical node sequence.
        sample_states = {
            0,
            recurrence_codec.total_count(transition_frontier) // 2,
            recurrence_codec.total_count(transition_frontier) - 1,
        }
        address_identity = True
        for state in sorted(sample_states):
            rpath = recurrence_codec.reconstruct_physical_path(
                state,
                transition_frontier,
            )
            dpath = direct_codec.reconstruct_physical_path(
                state,
                transition_frontier,
            )
            if rpath != dpath:
                address_identity = False
                break

        fixed_entries = field.basis_integer_count
        direct_entries = field.direct_table_integer_count(
            transition_frontier
        )

        print(
            "COUNT_FIELD_RECURRENCE",
            "name", name,
            "PASS",
            count_identity
            and address_identity
            and field.validate_recurrence(32)
            and field.order == expected_order
            and field.reachable_state_count == expected_reachable,
            "reachable_states", field.reachable_state_count,
            "order", field.order,
            "transient_factor_power",
            field.transient_factor_power,
            "coefficients", field.coefficients,
            "fixed_basis_integers", fixed_entries,
            "direct_frontier_integers", direct_entries,
            "storage_reduction", direct_entries / fixed_entries,
            "cache_rows", field.cache_rows,
            "cache_rows_current", field.cached_row_count,
            "count_identity", count_identity,
            "address_identity", address_identity,
        )

        frontier_count = recurrence_codec.total_count(
            transition_frontier
        )
        next_count = recurrence_codec.total_count(
            transition_frontier + 1
        )

        print(
            "COUNT_FIELD_FRONTIER",
            "name", name,
            "PASS",
            frontier_count <= (1 << 63)
            and next_count > (1 << 63),
            "trajectory_frontier", trajectory_frontier,
            "frontier_count", frontier_count,
            "next_count", next_count,
        )


if __name__ == "__main__":
    main()

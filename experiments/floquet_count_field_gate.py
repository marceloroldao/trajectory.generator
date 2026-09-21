"""Gate phase/Floquet compression of the topological universe count field."""

from recurrent_orbit_core import graph
from topological_transition_state import (
    counts as legacy_counts,
    initial_topology,
)

from trajectory_generator.floquet_path_trajectory import (
    build_floquet_path_codec,
)
from trajectory_generator.recurrence_path_trajectory import (
    build_recurrence_path_codec,
)


CANDIDATES = {
    # params, trajectory frontier, full order, phase order, full reachable,
    # base-phase reachable, transient factor power in the phase recurrence
    "robust_208": ((1, 0, 0, 2), 208, 31, 11, 46, 16, 2),
    "balanced_221": ((0, 2, 4, 4), 221, 23, 8, 37, 13, 1),
    "long_239": ((3, 2, 4, 4), 239, 22, 8, 34, 12, 3),
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
        expected_full_order,
        expected_phase_order,
        expected_reachable,
        expected_phase_states,
        expected_transient,
    ) in CANDIDATES.items():
        adjacency = graph(params)

        full_codec = build_recurrence_path_codec(
            adjacency,
            start_nodes=initial_nodes(),
            width=63,
            cache_rows=1,
        )
        floquet_codec = build_floquet_path_codec(
            adjacency,
            start_nodes=initial_nodes(),
            phase_of=lambda node: node[2],
            period=3,
            base_phase=0,
            width=63,
            cache_rows=1,
        )

        full = full_codec.count_field
        field = floquet_codec.count_field
        transition_frontier = trajectory_frontier - 3

        historical = legacy_counts(
            params,
            max_steps=trajectory_frontier + 1,
        )

        count_identity = all(
            floquet_codec.total_count(t)
            == full_codec.total_count(t)
            == historical[t + 3]
            for t in range(transition_frontier + 2)
        )

        sample_states = {
            0,
            floquet_codec.total_count(transition_frontier) // 2,
            floquet_codec.total_count(transition_frontier) - 1,
        }
        address_identity = True
        for state in sorted(sample_states):
            fpath = floquet_codec.reconstruct_physical_path(
                state,
                transition_frontier,
            )
            rpath = full_codec.reconstruct_physical_path(
                state,
                transition_frontier,
            )
            if fpath != rpath:
                address_identity = False
                break

        phase_window_rows = len(field.reduced_coefficients)
        phase_window_integers = (
            field.phase_state_count * phase_window_rows
        )
        full_decode_pair_integers = (
            2 * field.reachable_state_count
        )
        cache_integers = (
            field.cache_rows * field.phase_state_count
        )
        persistent_seed_integers = (
            field.reachable_state_count
            + field.phase_state_count
            + field.order
        )
        floquet_resident_count_integers = (
            phase_window_integers
            + full_decode_pair_integers
            + cache_integers
            + persistent_seed_integers
        )
        direct_entries = (
            field.reachable_state_count
            * (transition_frontier + 1)
        )

        print(
            "FLOQUET_COUNT_FIELD",
            "name", name,
            "PASS",
            count_identity
            and address_identity
            and field.validate_recurrence(24)
            and full.order == expected_full_order
            and field.order == expected_phase_order
            and field.reachable_state_count == expected_reachable
            and field.phase_state_count == expected_phase_states
            and field.transient_factor_power == expected_transient,
            "full_reachable", field.reachable_state_count,
            "base_phase_states", field.phase_state_count,
            "full_order", full.order,
            "floquet_order", field.order,
            "transient_factor_power",
            field.transient_factor_power,
            "coefficients", field.coefficients,
            "retained_basis_integers",
            field.basis_integer_count,
            "derived_basis_integers",
            field.derived_basis_integer_count,
            "reverse_window_rows", phase_window_rows,
            "reverse_window_integers", phase_window_integers,
            "resident_count_integers_estimate",
            floquet_resident_count_integers,
            "direct_frontier_integers", direct_entries,
            "resident_count_storage_reduction",
            direct_entries / floquet_resident_count_integers,
            "count_identity", count_identity,
            "address_identity", address_identity,
        )

        frontier_count = floquet_codec.total_count(
            transition_frontier
        )
        next_count = floquet_codec.total_count(
            transition_frontier + 1
        )

        print(
            "FLOQUET_FRONTIER",
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

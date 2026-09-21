"""Gate scalar-only partition decoding for full topological universes."""

from recurrent_orbit_core import graph
from topological_transition_state import initial_topology

from trajectory_generator.floquet_path_trajectory import (
    build_floquet_path_codec,
)
from trajectory_generator.scalar_partition_trajectory import (
    build_scalar_partition_translation_machine,
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


def main():
    for name, (params, trajectory_frontier) in CANDIDATES.items():
        adjacency = graph(params)

        machine = build_scalar_partition_translation_machine(
            adjacency,
            start_nodes=initial_nodes(),
            phase_of=lambda node: node[2],
            period=3,
            base_phase=0,
            width=63,
            seed_cache_entries=512,
        )
        reference = build_floquet_path_codec(
            adjacency,
            start_nodes=initial_nodes(),
            phase_of=lambda node: node[2],
            period=3,
            base_phase=0,
            width=63,
            cache_rows=0,
        )

        transition_frontier = trajectory_frontier - 3
        total = machine.oracle.total_count(
            transition_frontier
        )

        count_identity = (
            total
            == reference.total_count(transition_frontier)
        )

        samples = {
            0,
            total // 4,
            total // 2,
            (3 * total) // 4,
            total - 1,
        }

        # Forbid full-vector reconstruction in the scalar decoder itself.
        def forbidden(*args, **kwargs):
            raise AssertionError(
                "full count-vector reconstruction requested"
            )

        machine.field.vector_at = forbidden

        path_identity = True
        for state in sorted(samples):
            scalar_path = machine.reconstruct_physical_path(
                state,
                transition_frontier,
            )
            reference_path = reference.reconstruct_physical_path(
                state,
                transition_frontier,
            )
            if scalar_path != reference_path:
                path_identity = False
                break

        # Exhaustive low-horizon address identity.
        exhaustive_identity = True
        checked = 0
        for t in range(18):
            for state in range(reference.total_count(t)):
                spath = machine.reconstruct_physical_path(
                    state,
                    t,
                )
                rpath = reference.reconstruct_physical_path(
                    state,
                    t,
                )
                checked += 1
                if spath != rpath:
                    exhaustive_identity = False
                    break
            if not exhaustive_identity:
                break

        print(
            "SCALAR_PARTITION_GATE",
            "name", name,
            "PASS",
            count_identity
            and path_identity
            and exhaustive_identity,
            "trajectory_frontier", trajectory_frontier,
            "count_identity", count_identity,
            "frontier_path_identity", path_identity,
            "exhaustive_identity", exhaustive_identity,
            "checked_small_addresses", checked,
            "floquet_order", machine.field.order,
            "base_phase_states",
            machine.field.phase_state_count,
            "scalar_seed_cache_limit",
            machine.oracle.seed_cache_entries,
            "scalar_seed_cache_current",
            machine.oracle.cached_functional_count,
            "full_vector_api_disabled", True,
        )


if __name__ == "__main__":
    main()

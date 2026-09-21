"""Gate variable-fiber geometry against a naive Cartesian H x V model."""

from recurrent_orbit_core import graph
from topological_transition_state import initial_topology

from trajectory_generator.branch_information_budget import (
    step_counts,
)
from trajectory_generator.fiber_bundle_geometry import (
    fiber_bundle_geometry,
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
    for name, (params, frontier) in CANDIDATES.items():
        adjacency = graph(params)

        nodes = set(adjacency)
        for targets in adjacency.values():
            nodes.update(targets)

        counts = {
            node: 0
            for node in nodes
        }
        for start in initial_nodes():
            counts[start] += 1

        for _ in range(frontier - 3):
            counts = step_counts(
                adjacency,
                counts,
            )

        geometry = fiber_bundle_geometry(
            counts,
            total_base_states=len(nodes),
        )

        exact_fits_63 = (
            geometry.total_histories <= (1 << 63)
            and geometry.optimal_integer_bits <= 63
        )
        active_rectangle_has_padding = (
            geometry.active_rectangular_slots
            > geometry.total_histories
        )
        full_rectangle_has_padding = (
            geometry.full_rectangular_slots
            > geometry.total_histories
        )

        passed = (
            geometry.fibers_are_nonuniform
            and exact_fits_63
            and active_rectangle_has_padding
            and full_rectangle_has_padding
            and geometry.active_rectangular_occupancy < 1.0
            and geometry.full_rectangular_occupancy < 1.0
        )

        print(
            "FIBER_BUNDLE_GEOMETRY_GATE",
            "name", name,
            "PASS", passed,
            "frontier", frontier,
            "total_base_states",
            geometry.total_base_states,
            "populated_base_states",
            geometry.populated_base_states,
            "total_histories",
            geometry.total_histories,
            "min_fiber",
            geometry.minimum_nonzero_fiber,
            "max_fiber",
            geometry.maximum_fiber,
            "nonuniform",
            geometry.fibers_are_nonuniform,
            "exact_family_bits",
            f"{geometry.exact_family_bits:.12f}",
            "optimal_integer_bits",
            geometry.optimal_integer_bits,
            "active_rectangle_occupancy",
            f"{geometry.active_rectangular_occupancy:.12f}",
            "active_rectangle_redundancy_bits",
            f"{geometry.active_rectangular_redundancy_bits:.12f}",
            "active_rectangle_integer_bits",
            geometry.active_rectangular_integer_bits,
            "full_rectangle_occupancy",
            f"{geometry.full_rectangular_occupancy:.12f}",
            "full_rectangle_redundancy_bits",
            f"{geometry.full_rectangular_redundancy_bits:.12f}",
            "full_rectangle_integer_bits",
            geometry.full_rectangular_integer_bits,
            "interpretation",
            "minimal reversible state is a variable fiber bundle, not a uniform Cartesian product",
        )

        if not passed:
            raise AssertionError(
                f"fiber bundle geometry failed for {name}"
            )


if __name__ == "__main__":
    main()

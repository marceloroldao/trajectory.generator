"""Gate the horizontal/vertical reversible fiber-lift interpretation."""

from recurrent_orbit_core import graph
from topological_transition_state import (
    initial_topology,
    counts as historical_counts,
)

from trajectory_generator.reversible_fiber_lift import (
    ReversibleFiberLift,
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
    for name, (params, frontier) in CANDIDATES.items():
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
        lift = ReversibleFiberLift(machine)

        t = frontier - 3
        fibers = lift.active_fibers(t)
        total = lift.total_states(t)
        expected = historical_counts(
            params,
            max_steps=frontier,
        )[frontier]

        fiber_partition_ok = total == expected
        max_fiber = max(size for _, size in fibers)

        # Representative states spanning every occupied fiber.
        samples = set()
        offset = 0
        for _, size in fibers:
            samples.add(offset)
            samples.add(offset + size - 1)
            offset += size

        coordinate_identity = True
        for state in sorted(samples):
            coordinate = lift.coordinate(state, t)
            if (
                lift.pack(
                    coordinate.node,
                    coordinate.rank,
                    t,
                )
                != state
            ):
                coordinate_identity = False
                break

        # Low-horizon exhaustive lifted-edge reversibility.
        edge_lift_ok = True
        checked_edges = 0
        for time in range(15):
            for state in range(lift.total_states(time)):
                coordinate = lift.coordinate(
                    state,
                    time,
                )
                for edge in machine.codec.outgoing[
                    coordinate.node
                ]:
                    nxt = lift.forward(
                        coordinate,
                        edge.label,
                    )
                    previous, recovered = lift.reverse(nxt)
                    checked_edges += 1
                    if (
                        previous != coordinate
                        or recovered != edge
                    ):
                        edge_lift_ok = False
                        break
                if not edge_lift_ok:
                    break
            if not edge_lift_ok:
                break

        print(
            "REVERSIBLE_FIBER_LIFT",
            "name", name,
            "PASS",
            fiber_partition_ok
            and coordinate_identity
            and edge_lift_ok,
            "frontier", frontier,
            "horizontal_active_nodes", len(fibers),
            "vertical_total_states", total,
            "max_vertical_fiber", max_fiber,
            "max_vertical_bits",
            (max_fiber - 1).bit_length(),
            "fiber_partition", fiber_partition_ok,
            "coordinate_identity", coordinate_identity,
            "edge_lift", edge_lift_ok,
            "checked_lifted_edges", checked_edges,
        )


if __name__ == "__main__":
    main()

"""Gate the finite-horizon minimal reversible causal lift."""

from recurrent_orbit_core import graph
from topological_transition_state import (
    initial_topology,
    counts as historical_counts,
)

from trajectory_generator.lifted_causal_universe import (
    LiftedCausalUniverse,
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


def build_universe(params):
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
    return LiftedCausalUniverse(
        ReversibleFiberLift(machine)
    )


def main():
    for name, (params, frontier) in CANDIDATES.items():
        universe = build_universe(params)
        t = frontier - 3

        fibers = universe.lift.active_fibers(t)
        total = sum(size for _, size in fibers)
        expected = historical_counts(
            params,
            max_steps=frontier,
        )[frontier]

        exact_size = total == expected

        # Fiberwise minimality is a counting theorem: above raw node v there
        # are exactly D(v,t) distinct admissible histories, so fewer than D(v,t)
        # lifted states must merge at least two histories by pigeonhole.
        local_minimal = all(
            universe.local_minimum_states(node, t) == size
            for node, size in fibers
        )

        worst_node, worst_size = max(
            fibers,
            key=lambda row: row[1],
        )

        # Exhaustive semiconjugacy/reversibility at early horizons.
        semiconjugacy = True
        reversible = True
        checked = 0
        for time in range(14):
            for packed in range(
                universe.lift.total_states(time)
            ):
                state = universe.from_packed(
                    packed,
                    time,
                )
                for edge in universe.machine.codec.outgoing[
                    state.node
                ]:
                    checked += 1
                    if not universe.semiconjugacy_holds(
                        state,
                        time,
                        edge.label,
                    ):
                        semiconjugacy = False
                        break
                    nxt = universe.advance(
                        state,
                        time,
                        edge.label,
                    )
                    previous, recovered = universe.rewind(
                        nxt,
                        time + 1,
                    )
                    if previous != state or recovered != edge:
                        reversible = False
                        break
                if not semiconjugacy or not reversible:
                    break
            if not semiconjugacy or not reversible:
                break

        # At frontier, verify every active target fiber is exactly partitioned
        # by its predecessor edge images.
        partition_complete = True
        for target, target_size in fibers:
            blocks = universe.fiber_partition(
                target,
                t - 1,
            )
            if not blocks:
                partition_complete = False
                break
            if blocks[0][1] != 0 or blocks[-1][2] != target_size:
                partition_complete = False
                break
            for left, right in zip(blocks, blocks[1:]):
                if left[2] != right[1]:
                    partition_complete = False
                    break
            if not partition_complete:
                break

        print(
            "MINIMAL_REVERSIBLE_CAUSAL_LIFT",
            "name", name,
            "PASS",
            exact_size
            and local_minimal
            and semiconjugacy
            and reversible
            and partition_complete,
            "frontier", frontier,
            "raw_active_nodes", len(fibers),
            "lifted_states", total,
            "worst_raw_node", worst_node,
            "worst_fiber_states", worst_size,
            "worst_fiber_bits",
            universe.local_minimum_bits(worst_node, t),
            "fiberwise_minimal", local_minimal,
            "semiconjugacy", semiconjugacy,
            "reversible", reversible,
            "target_fibers_partitioned",
            partition_complete,
            "checked_early_lifted_edges", checked,
        )


if __name__ == "__main__":
    main()

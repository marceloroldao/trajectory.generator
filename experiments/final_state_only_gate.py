"""End-to-end final-state-only gate for the topological universes."""

from recurrent_orbit_core import graph
from topological_transition_state import (
    initial_topology,
    make_codec as make_legacy_codec,
)

from trajectory_generator.scalar_partition_trajectory import (
    build_scalar_partition_translation_machine,
)
from trajectory_generator.seeded_graph_state_machine import (
    SeededGraphStateMachine,
)


CANDIDATES = {
    "robust_208": ((1, 0, 0, 2), 208),
    "balanced_221": ((0, 2, 4, 4), 221),
    "long_239": ((3, 2, 4, 4), 239),
}


def build_machine(params):
    adjacency = graph(params)
    starts = tuple(
        (state, initial_topology(state), 0)
        for state in range(8)
    )

    partition = build_scalar_partition_translation_machine(
        adjacency,
        start_nodes=starts,
        phase_of=lambda node: node[2],
        period=3,
        base_phase=0,
        width=63,
        seed_cache_entries=512,
    )

    return SeededGraphStateMachine(
        partition,
        seed_bits=3,
        seed_to_start_node={
            state: (
                state,
                initial_topology(state),
                0,
            )
            for state in range(8)
        },
        edge_symbol=lambda edge: edge.target[0] & 1,
    )


def main():
    for name, (params, frontier) in CANDIDATES.items():
        machine = build_machine(params)
        total, legacy_unrank, legacy_validate = make_legacy_codec(
            params
        )

        # Exact language/address roundtrip on small horizons.
        exhaustive_ok = True
        checked = 0
        for steps in range(0, 12):
            family = total(steps)
            seen = set()

            for rank in range(family):
                bits = legacy_unrank(rank, steps)
                state, got_steps = machine.encode(bits)
                if (
                    got_steps != steps
                    or state in seen
                    or machine.decode(state, steps) != bits
                ):
                    exhaustive_ok = False
                    break
                seen.add(state)
                checked += 1

            if not exhaustive_ok or len(seen) != family:
                exhaustive_ok = False
                break

        # Frontier addresses are used directly: decode receives only integer
        # final state + public trajectory length.
        frontier_total = total(frontier)
        sample_states = {
            0,
            frontier_total // 4,
            frontier_total // 2,
            (3 * frontier_total) // 4,
            frontier_total - 1,
        }

        frontier_ok = True
        for state in sorted(sample_states):
            bits = machine.decode(state, frontier)
            if (
                len(bits) != frontier
                or not legacy_validate(bits)
            ):
                frontier_ok = False
                break

            rebuilt, rebuilt_steps = machine.encode(bits)
            if (
                rebuilt != state
                or rebuilt_steps != frontier
            ):
                frontier_ok = False
                break

        next_over_capacity = total(frontier + 1) > (1 << 63)

        print(
            "FINAL_STATE_ONLY_GATE",
            "name", name,
            "PASS",
            exhaustive_ok
            and frontier_ok
            and next_over_capacity,
            "trajectory_frontier", frontier,
            "frontier_family", frontier_total,
            "next_family", total(frontier + 1),
            "small_addresses_checked", checked,
            "frontier_samples", len(sample_states),
            "decode_inputs",
            "(final_state,steps)+public_law_only",
            "exhaustive_roundtrip", exhaustive_ok,
            "frontier_roundtrip", frontier_ok,
            "next_over_capacity", next_over_capacity,
        )


if __name__ == "__main__":
    main()

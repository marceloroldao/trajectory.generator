"""Final-state-only gate using the canonical dynamic vertical coordinate."""

from recurrent_orbit_core import graph
from topological_transition_state import (
    initial_topology,
    make_codec as make_legacy_codec,
)

from trajectory_generator.canonical_vertical_state_machine import (
    CanonicalVerticalStateMachine,
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


def build_machine(params):
    adjacency = graph(params)
    partition = build_scalar_partition_translation_machine(
        adjacency,
        start_nodes=initial_nodes(),
        phase_of=lambda node: node[2],
        period=3,
        base_phase=0,
        width=63,
        seed_cache_entries=512,
    )

    return CanonicalVerticalStateMachine(
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

        exhaustive_ok = True
        checked = 0

        for steps in range(12):
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

            if (
                not exhaustive_ok
                or len(seen) != family
            ):
                exhaustive_ok = False
                break

        frontier_total = total(frontier)
        samples = {
            0,
            frontier_total // 4,
            frontier_total // 2,
            (3 * frontier_total) // 4,
            frontier_total - 1,
        }

        frontier_ok = True
        changed_from_rank_codec = 0

        for state in sorted(samples):
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

            # The dynamic vertical law generally changes which admissible
            # trajectory corresponds to a given integer versus the old static
            # rank address. Track this to prove we did not silently fall back.
            old_bits = legacy_unrank(state, frontier)
            if bits != old_bits:
                changed_from_rank_codec += 1

        print(
            "CANONICAL_VERTICAL_FINAL_STATE_GATE",
            "name", name,
            "PASS",
            exhaustive_ok
            and frontier_ok
            and changed_from_rank_codec > 0,
            "frontier", frontier,
            "frontier_family", frontier_total,
            "small_addresses_checked", checked,
            "frontier_samples", len(samples),
            "dynamic_mapping_differs_from_rank_samples",
            changed_from_rank_codec,
            "decode_inputs",
            "(final_state,steps)+public_law_only",
            "exhaustive_roundtrip", exhaustive_ok,
            "frontier_roundtrip", frontier_ok,
        )


if __name__ == "__main__":
    main()

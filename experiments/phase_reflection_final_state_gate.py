"""Gate final-state-only recovery with phase-reflection vertical dynamics."""

from recurrent_orbit_core import graph
from topological_transition_state import (
    initial_topology,
    make_codec as make_legacy_codec,
)

from trajectory_generator.canonical_vertical_state_machine import (
    CanonicalVerticalStateMachine,
)
from trajectory_generator.intrinsic_vertical_dynamics import (
    build_phase_reflection_lift,
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
        lift_builder=build_phase_reflection_lift,
    )


def main():
    for name, (params, frontier) in CANDIDATES.items():
        machine = build_machine(params)
        total, legacy_unrank, legacy_validate = make_legacy_codec(
            params
        )

        exhaustive = True
        checked = 0
        changed_small = 0

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
                    exhaustive = False
                    break
                if state != rank:
                    changed_small += 1
                seen.add(state)
                checked += 1

            if not exhaustive or len(seen) != family:
                exhaustive = False
                break

        family = total(frontier)
        samples = {
            0,
            family // 4,
            family // 2,
            (3 * family) // 4,
            family - 1,
        }

        frontier_ok = True
        changed_frontier = 0

        for final_state in sorted(samples):
            bits = machine.decode(
                final_state,
                frontier,
            )
            if (
                len(bits) != frontier
                or not legacy_validate(bits)
            ):
                frontier_ok = False
                break

            rebuilt, rebuilt_steps = machine.encode(bits)
            if (
                rebuilt != final_state
                or rebuilt_steps != frontier
            ):
                frontier_ok = False
                break

            if bits != legacy_unrank(
                final_state,
                frontier,
            ):
                changed_frontier += 1

        passed = (
            exhaustive
            and frontier_ok
            and changed_small > 0
            and changed_frontier > 0
        )

        print(
            "PHASE_REFLECTION_FINAL_STATE_GATE",
            "name", name,
            "PASS", passed,
            "frontier", frontier,
            "frontier_family", family,
            "small_addresses_checked", checked,
            "small_mapping_changes", changed_small,
            "frontier_samples", len(samples),
            "frontier_mapping_changes", changed_frontier,
            "exhaustive_roundtrip", exhaustive,
            "frontier_roundtrip", frontier_ok,
            "decode_inputs",
            "(final_state,steps)+public_law_only",
        )

        if not passed:
            raise AssertionError(
                f"phase-reflection final-state gate failed for {name}"
            )


if __name__ == "__main__":
    main()

"""Gate gauge equivalence of operational topological final-state charts."""

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
from trajectory_generator.seeded_graph_state_machine import (
    SeededGraphStateMachine,
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


def build_partition(params):
    return build_scalar_partition_translation_machine(
        graph(params),
        start_nodes=initial_nodes(),
        phase_of=lambda node: node[2],
        period=3,
        base_phase=0,
        width=63,
        seed_cache_entries=512,
    )


def build_charts(params):
    partition = build_partition(params)
    seed_map = {
        state: (
            state,
            initial_topology(state),
            0,
        )
        for state in range(8)
    }
    symbol = lambda edge: edge.target[0] & 1

    static = SeededGraphStateMachine(
        partition,
        seed_bits=3,
        seed_to_start_node=seed_map,
        edge_symbol=symbol,
    )
    phase = CanonicalVerticalStateMachine(
        partition,
        seed_bits=3,
        seed_to_start_node=seed_map,
        edge_symbol=symbol,
        lift_builder=build_phase_reflection_lift,
    )
    phase_merge = CanonicalVerticalStateMachine(
        partition,
        seed_bits=3,
        seed_to_start_node=seed_map,
        edge_symbol=symbol,
    )
    return static, phase, phase_merge


def main():
    for name, (params, frontier) in CANDIDATES.items():
        total, legacy_unrank, legacy_validate = make_legacy_codec(
            params
        )
        static, phase, phase_merge = build_charts(params)

        exhaustive = True
        coordinate_difference = False
        checked = 0

        for steps in range(12):
            family = total(steps)

            for static_state in range(family):
                bits = static.decode(
                    static_state,
                    steps,
                )

                phase_state, phase_steps = phase.encode(bits)
                merge_state, merge_steps = phase_merge.encode(bits)

                if (
                    phase_steps != steps
                    or merge_steps != steps
                    or phase.decode(phase_state, steps) != bits
                    or phase_merge.decode(merge_state, steps) != bits
                    or static.encode(bits) != (static_state, steps)
                ):
                    exhaustive = False
                    break

                if (
                    phase_state != static_state
                    or merge_state != static_state
                    or phase_state != merge_state
                ):
                    coordinate_difference = True

                # Gauge roundtrip through the common underlying trajectory.
                back_static_from_phase, _ = static.encode(
                    phase.decode(phase_state, steps)
                )
                back_static_from_merge, _ = static.encode(
                    phase_merge.decode(merge_state, steps)
                )

                if (
                    back_static_from_phase != static_state
                    or back_static_from_merge != static_state
                ):
                    exhaustive = False
                    break

                checked += 1

            if not exhaustive:
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
        frontier_coordinate_changes = 0

        for static_state in sorted(samples):
            bits = static.decode(
                static_state,
                frontier,
            )
            if (
                len(bits) != frontier
                or not legacy_validate(bits)
            ):
                frontier_ok = False
                break

            phase_state, _ = phase.encode(bits)
            merge_state, _ = phase_merge.encode(bits)

            if (
                phase.decode(phase_state, frontier) != bits
                or phase_merge.decode(merge_state, frontier) != bits
            ):
                frontier_ok = False
                break

            if (
                phase_state != static_state
                or merge_state != static_state
                or phase_state != merge_state
            ):
                frontier_coordinate_changes += 1

            # Return to static chart using only chart decode/encode.
            static_from_phase, _ = static.encode(
                phase.decode(phase_state, frontier)
            )
            static_from_merge, _ = static.encode(
                phase_merge.decode(merge_state, frontier)
            )
            if (
                static_from_phase != static_state
                or static_from_merge != static_state
            ):
                frontier_ok = False
                break

        passed = (
            exhaustive
            and coordinate_difference
            and frontier_ok
            and frontier_coordinate_changes > 0
        )

        print(
            "TOPOLOGICAL_GAUGE_EQUIVALENCE",
            "name", name,
            "PASS", passed,
            "frontier", frontier,
            "family", family,
            "small_addresses_checked", checked,
            "small_coordinate_difference", coordinate_difference,
            "frontier_samples", len(samples),
            "frontier_coordinate_changes",
            frontier_coordinate_changes,
            "history_identity_preserved", exhaustive and frontier_ok,
            "charts",
            "static_rank,phase_reflection,phase_merge",
        )

        if not passed:
            raise AssertionError(
                f"topological gauge equivalence failed for {name}"
            )


if __name__ == "__main__":
    main()

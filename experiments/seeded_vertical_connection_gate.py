"""Gate final-state-only bit recovery through local fiber connection."""

from recurrent_orbit_core import graph
from topological_transition_state import (
    initial_topology,
    make_codec as make_legacy_codec,
)

from trajectory_generator.exact_vertical_connection import (
    ExactVerticalConnection,
)
from trajectory_generator.scalar_partition_trajectory import (
    build_scalar_partition_translation_machine,
)
from trajectory_generator.seeded_graph_state_machine import (
    SeededGraphStateMachine,
)
from trajectory_generator.seeded_vertical_connection import (
    SeededVerticalConnectionMachine,
)


CANDIDATES = {
    "robust_208": ((1, 0, 0, 2), 208),
    "balanced_221": ((0, 2, 4, 4), 221),
    "long_239": ((3, 2, 4, 4), 239),
}


def build(params):
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
    mapping = {
        state: (
            state,
            initial_topology(state),
            0,
        )
        for state in range(8)
    }
    symbol = lambda edge: edge.target[0] & 1

    local = SeededVerticalConnectionMachine(
        ExactVerticalConnection(partition),
        seed_bits=3,
        seed_to_start_node=mapping,
        edge_symbol=symbol,
    )
    reference = SeededGraphStateMachine(
        partition,
        seed_bits=3,
        seed_to_start_node=mapping,
        edge_symbol=symbol,
    )
    return local, reference


def main():
    for name, (params, frontier) in CANDIDATES.items():
        total, legacy_unrank, legacy_validate = (
            make_legacy_codec(params)
        )
        local, reference = build(params)

        exhaustive = True
        checked = 0

        for steps in range(12):
            family = total(steps)
            for state in range(family):
                bits = legacy_unrank(
                    state,
                    steps,
                )
                local_state, local_steps = (
                    local.encode(bits)
                )
                reference_state, reference_steps = (
                    reference.encode(bits)
                )

                if (
                    local_steps != steps
                    or reference_steps != steps
                    or local_state != reference_state
                    or local.decode(
                        local_state,
                        steps,
                    ) != bits
                    or reference.decode(
                        reference_state,
                        steps,
                    ) != bits
                ):
                    exhaustive = False
                    break
                checked += 1

            if not exhaustive:
                break

        frontier_family = total(frontier)
        samples = sorted({
            0,
            frontier_family // 4,
            frontier_family // 2,
            (3 * frontier_family) // 4,
            frontier_family - 1,
        })

        frontier_ok = True
        frontier_bits_recovered = 0

        for final_state in samples:
            bits = local.decode(
                final_state,
                frontier,
            )
            if (
                len(bits) != frontier
                or not legacy_validate(bits)
                or reference.decode(
                    final_state,
                    frontier,
                ) != bits
            ):
                frontier_ok = False
                break

            rebuilt, rebuilt_steps = local.encode(
                bits
            )
            if (
                rebuilt != final_state
                or rebuilt_steps != frontier
            ):
                frontier_ok = False
                break

            frontier_bits_recovered += len(bits)

        passed = (
            exhaustive
            and frontier_ok
            and frontier_bits_recovered
            == len(samples) * frontier
        )

        print(
            "SEEDED_VERTICAL_CONNECTION_GATE",
            "name", name,
            "PASS", passed,
            "frontier", frontier,
            "frontier_family", frontier_family,
            "small_addresses_checked", checked,
            "frontier_samples", len(samples),
            "frontier_bits_recovered",
            frontier_bits_recovered,
            "decode_inputs",
            "(final_state,steps)+public_law_only",
            "packed_chart_operations_per_decode",
            1,
            "packed_state_internal_dynamics",
            False,
            "exact_match_reference_decoder",
            exhaustive and frontier_ok,
        )

        if not passed:
            raise AssertionError(
                f"seeded vertical connection failed for {name}"
            )


if __name__ == "__main__":
    main()

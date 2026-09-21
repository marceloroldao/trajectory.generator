"""Gate genuine native vertical state and quantify its 63-bit cost."""

from recurrent_orbit_core import graph
from topological_transition_state import (
    initial_topology,
    make_codec as make_legacy_codec,
)

from trajectory_generator.native_vertical_product import (
    NativeVerticalProductMachine,
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


def base_machine(params):
    partition = build_scalar_partition_translation_machine(
        graph(params),
        start_nodes=initial_nodes(),
        phase_of=lambda node: node[2],
        period=3,
        base_phase=0,
        width=None,
        seed_cache_entries=256,
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


def lifted_frontier(total, modulus, width=63):
    limit = 1 << width
    steps = 0
    while (
        total(steps + 1) * modulus
        <= limit
    ):
        steps += 1
    return steps


def main():
    for name, (params, original_frontier) in CANDIDATES.items():
        total, unrank, validate = make_legacy_codec(
            params
        )
        base = base_machine(params)

        for modulus in (2, 4, 8):
            machine = NativeVerticalProductMachine(
                base,
                vertical_modulus=modulus,
            )

            frontier = lifted_frontier(
                total,
                modulus,
            )
            family = total(frontier)
            lifted_family = (
                family * modulus
            )
            next_lifted = (
                total(frontier + 1)
                * modulus
            )

            # Full natural-symmetry check on a representative trajectory.
            probe_steps = min(frontier, 24)
            probe_rank = (
                total(probe_steps) // 2
            )
            bits = unrank(
                probe_rank,
                probe_steps,
            )

            state, steps = machine.encode(
                bits,
                initial_vertical=0,
            )

            symmetry = True
            current = machine.pack(0, 0)
            current_steps = 0
            for bit in bits:
                for offset in range(modulus):
                    if not machine.symmetry_commutes(
                        current,
                        current_steps,
                        bit,
                        offset,
                    ):
                        symmetry = False
                        break
                if not symmetry:
                    break
                current, current_steps = (
                    machine.advance(
                        current,
                        current_steps,
                        bit,
                    )
                )

            roundtrip = True
            for initial in range(modulus):
                encoded, got_steps = machine.encode(
                    bits,
                    initial_vertical=initial,
                )
                decoded = machine.decode(
                    encoded,
                    got_steps,
                )
                if (
                    list(decoded.bits) != bits
                    or decoded.initial_vertical
                    != initial
                ):
                    roundtrip = False
                    break

            capacity_exact = (
                lifted_family <= (1 << 63)
                and next_lifted > (1 << 63)
            )
            cost_steps = (
                original_frontier - frontier
            )

            passed = (
                symmetry
                and roundtrip
                and capacity_exact
                and validate(bits)
            )

            print(
                "NATIVE_VERTICAL_PRODUCT_GATE",
                "name", name,
                "PASS", passed,
                "vertical_modulus", modulus,
                "native_vertical_bits",
                modulus.bit_length() - 1,
                "original_frontier",
                original_frontier,
                "lifted_frontier",
                frontier,
                "frontier_step_cost",
                cost_steps,
                "lifted_family", lifted_family,
                "next_lifted_family",
                next_lifted,
                "translation_symmetry_natural",
                symmetry,
                "roundtrip_bits_and_initial_vertical",
                roundtrip,
                "interpretation",
                "genuine independent vertical state exists but consumes final-state capacity",
            )

            if not passed:
                raise AssertionError(
                    f"native vertical product failed for {name}, m={modulus}"
                )


if __name__ == "__main__":
    main()

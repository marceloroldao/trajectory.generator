"""Scale the cursor-based local fiber machine to wider final states.

The public causal universe is unchanged. Only the serialization width grows.

For each candidate and width:
- find the exact monotone trajectory frontier by forward public count evolution;
- require frontier family <= 2^W and next family > 2^W;
- decode representative final integers using only the backward Floquet cursor;
- re-encode through only the forward count cursor;
- require exact final-state identity;
- prohibit every ScalarFloquetPartitionOracle.scalar_at call.

The number of stored count *integers* should be horizon-independent for a fixed
universe. Python big-integer byte size still grows with numeric magnitude; this
gate does not claim constant byte memory as W increases.
"""

from math import log2

from recurrent_orbit_core import graph
from topological_transition_state import initial_topology

from trajectory_generator.exact_vertical_connection import (
    ExactVerticalConnection,
)
from trajectory_generator.scalar_partition_trajectory import (
    build_scalar_partition_translation_machine,
)
from trajectory_generator.seeded_vertical_connection import (
    SeededVerticalConnectionMachine,
)


CANDIDATES = {
    "robust": (1, 0, 0, 2),
    "balanced": (0, 2, 4, 4),
    "long": (3, 2, 4, 4),
}

WIDTHS = (63, 128, 256, 512)


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
        width=max(WIDTHS),
        seed_cache_entries=64,
    )
    mapping = {
        state: (
            state,
            initial_topology(state),
            0,
        )
        for state in range(8)
    }
    return SeededVerticalConnectionMachine(
        ExactVerticalConnection(partition),
        seed_bits=3,
        seed_to_start_node=mapping,
        edge_symbol=lambda edge: edge.target[0] & 1,
    )


def exact_transition_frontier(field, width):
    limit = 1 << width
    vector = field.initial_vector
    transition_time = 0
    total = sum(vector)

    if total > limit:
        raise AssertionError(
            "initial family already exceeds width"
        )

    while True:
        nxt = field.step_vector(vector)
        next_total = sum(nxt)
        if next_total > limit:
            return (
                transition_time,
                total,
                next_total,
            )
        vector = nxt
        total = next_total
        transition_time += 1


def main():
    for name, params in CANDIDATES.items():
        machine = build(params)
        field = machine.connection.machine.field
        oracle = machine.connection.machine.oracle

        def forbidden(*args, **kwargs):
            raise AssertionError(
                "wide cursor gate requested scalar_at"
            )

        oracle.scalar_at = forbidden

        reverse_storage = []
        forward_storage = []
        frontiers = []

        for width in WIDTHS:
            (
                transition_frontier,
                frontier_family,
                next_family,
            ) = exact_transition_frontier(
                field,
                width,
            )
            trajectory_frontier = (
                transition_frontier
                + machine.seed_bits
            )
            frontiers.append(
                trajectory_frontier
            )

            samples = sorted({
                0,
                frontier_family // 2,
                frontier_family - 1,
            })

            exact_roundtrip = True
            max_reverse_slots = 0
            max_forward_persistent = 0
            max_forward_peak = 0

            for final_state in samples:
                bits, reverse_metrics = (
                    machine.decode_with_cursor_metrics(
                        final_state,
                        trajectory_frontier,
                    )
                )
                (
                    rebuilt,
                    rebuilt_steps,
                    forward_metrics,
                ) = machine.encode_with_cursor_metrics(
                    bits
                )

                if (
                    rebuilt != final_state
                    or rebuilt_steps
                    != trajectory_frontier
                    or len(bits)
                    != trajectory_frontier
                    or reverse_metrics is None
                    or forward_metrics is None
                ):
                    exact_roundtrip = False
                    break

                max_reverse_slots = max(
                    max_reverse_slots,
                    reverse_metrics.maximum_stored_count_integers,
                )
                max_forward_persistent = max(
                    max_forward_persistent,
                    forward_metrics.persistent_count_integers,
                )
                max_forward_peak = max(
                    max_forward_peak,
                    forward_metrics.peak_count_integers_during_step,
                )

            reverse_storage.append(
                max_reverse_slots
            )
            forward_storage.append(
                max_forward_persistent
            )

            passed = (
                frontier_family <= (1 << width)
                and next_family > (1 << width)
                and exact_roundtrip
            )

            print(
                "WIDE_STATE_CURSOR_GATE",
                "name", name,
                "width", width,
                "PASS", passed,
                "trajectory_frontier",
                trajectory_frontier,
                "transition_frontier",
                transition_frontier,
                "frontier_family_bits",
                f"{log2(frontier_family):.12f}",
                "next_family_bits",
                f"{log2(next_family):.12f}",
                "samples", len(samples),
                "reverse_stored_count_integers",
                max_reverse_slots,
                "forward_persistent_count_integers",
                max_forward_persistent,
                "forward_peak_count_integers",
                max_forward_peak,
                "scalar_at_calls_allowed",
                False,
                "storage_measure",
                "integer_slots_not_bigint_bytes",
            )

            if not passed:
                raise AssertionError(
                    f"wide-state cursor gate failed for {name} W={width}"
                )

        storage_constant = (
            len(set(reverse_storage)) == 1
            and len(set(forward_storage)) == 1
        )
        frontier_monotone = all(
            right > left
            for left, right in zip(
                frontiers,
                frontiers[1:],
            )
        )

        print(
            "WIDE_STATE_CURSOR_SUMMARY",
            "name", name,
            "PASS",
            storage_constant and frontier_monotone,
            "widths", WIDTHS,
            "frontiers", tuple(frontiers),
            "reverse_storage", tuple(reverse_storage),
            "forward_storage", tuple(forward_storage),
            "storage_integer_slots_constant",
            storage_constant,
            "frontier_strictly_increases",
            frontier_monotone,
        )

        if not (
            storage_constant
            and frontier_monotone
        ):
            raise AssertionError(
                f"wide-state summary failed for {name}"
            )


if __name__ == "__main__":
    main()

"""Scale information-event final-state decoding across wider state widths.

The universe law is unchanged.  Only final-state serialization width grows.
For every candidate and width this gate:

- finds the exact trajectory frontier;
- decodes representative states from only (final_state, steps) + public law;
- re-encodes to the exact same final integer;
- verifies event-cursor physical-step accounting;
- requires at least one macro information-event jump;
- records how many physical reverse steps are collapsed into semantic reverse
  operations.

Timing is deliberately not a gate criterion.  Exactness and semantic operation
reduction are.
"""

from math import log2

from recurrent_orbit_core import graph
from topological_transition_state import initial_topology

from trajectory_generator.exact_vertical_connection import (
    ExactVerticalConnection,
)
from trajectory_generator.information_event_cursor import (
    InformationEventDecoder,
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
        decoder = InformationEventDecoder(machine)
        field = machine.connection.machine.field
        oracle = machine.connection.machine.oracle

        def forbidden(*args, **kwargs):
            raise AssertionError(
                "wide event decoder requested scalar_at"
            )

        oracle.scalar_at = forbidden

        ratios = []
        operations_per_sample = []
        macro_share = []
        stored_slots = []
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
            frontiers.append(trajectory_frontier)

            samples = sorted({
                0,
                frontier_family // 2,
                frontier_family - 1,
            })

            total_physical = 0
            total_logical = 0
            total_macro_jumps = 0
            total_macro_steps = 0
            max_stored_count_integers = 0

            for final_state in samples:
                trace, metrics = (
                    decoder.decode_trace_with_metrics(
                        final_state,
                        trajectory_frontier,
                    )
                )
                bits = decoder.trace_codec.expand_bits(
                    trace
                )

                rebuilt, rebuilt_steps = machine.encode(
                    bits
                )

                if (
                    rebuilt != final_state
                    or rebuilt_steps != trajectory_frontier
                    or len(bits) != trajectory_frontier
                    or metrics is None
                    or metrics.equivalent_physical_steps
                    != transition_frontier
                    or metrics.macro_probe_physical_steps != 0
                ):
                    raise AssertionError(
                        f"wide event roundtrip/accounting failed "
                        f"for {name} W={width}"
                    )

                total_physical += (
                    metrics.equivalent_physical_steps
                )
                total_logical += (
                    metrics.logical_reverse_operations
                )
                total_macro_jumps += metrics.macro_jumps
                total_macro_steps += (
                    metrics.macro_physical_steps
                )
                max_stored_count_integers = max(
                    max_stored_count_integers,
                    metrics.maximum_stored_count_integers,
                )

            if total_logical <= 0:
                raise AssertionError(
                    f"no event operations for {name} W={width}"
                )
            if total_macro_jumps <= 0:
                raise AssertionError(
                    f"no macro jumps for {name} W={width}"
                )
            if total_logical >= total_physical:
                raise AssertionError(
                    f"no semantic reduction for {name} W={width}"
                )

            ratio = total_physical / total_logical
            mean_ops = total_logical / len(samples)
            share = total_macro_steps / total_physical

            ratios.append(ratio)
            operations_per_sample.append(mean_ops)
            macro_share.append(share)
            stored_slots.append(
                max_stored_count_integers
            )

            passed = (
                frontier_family <= (1 << width)
                and next_family > (1 << width)
                and ratio > 1.0
                and share > 0.0
            )

            print(
                "WIDE_INFORMATION_EVENT_DECODER_GATE",
                "name", name,
                "width", width,
                "PASS", passed,
                "trajectory_frontier",
                trajectory_frontier,
                "frontier_family_bits",
                f"{log2(frontier_family):.12f}",
                "next_family_bits",
                f"{log2(next_family):.12f}",
                "samples", len(samples),
                "physical_reverse_steps",
                total_physical,
                "logical_reverse_operations",
                total_logical,
                "semantic_reduction_ratio",
                f"{ratio:.9f}",
                "macro_jumps",
                total_macro_jumps,
                "macro_physical_steps",
                total_macro_steps,
                "macro_step_share",
                f"{share:.9f}",
                "maximum_stored_count_integers",
                max_stored_count_integers,
                "decode_inputs",
                "(final_state,steps)+public_law_only",
                "scalar_at_calls_allowed",
                False,
            )

            if not passed:
                raise AssertionError(
                    f"wide information-event gate failed "
                    f"for {name} W={width}"
                )

        if not all(
            right > left
            for left, right in zip(
                frontiers,
                frontiers[1:],
            )
        ):
            raise AssertionError(
                f"frontier did not grow for {name}"
            )

        print(
            "WIDE_INFORMATION_EVENT_DECODER_SUMMARY",
            "name", name,
            "PASS", True,
            "widths", WIDTHS,
            "frontiers", tuple(frontiers),
            "semantic_reduction_ratios",
            tuple(round(value, 9) for value in ratios),
            "mean_logical_operations_per_sample",
            tuple(
                round(value, 3)
                for value in operations_per_sample
            ),
            "macro_step_shares",
            tuple(
                round(value, 9)
                for value in macro_share
            ),
            "maximum_stored_count_integers",
            tuple(stored_slots),
        )


if __name__ == "__main__":
    main()

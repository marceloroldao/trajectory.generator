"""Gate lossless full-universe information-clock traces at wide frontiers."""

from recurrent_orbit_core import graph
from topological_transition_state import (
    initial_topology,
    make_codec as make_legacy_codec,
)

from trajectory_generator.exact_vertical_connection import (
    ExactVerticalConnection,
)
from trajectory_generator.information_clock_trace import (
    InformationClockTraceCodec,
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

WIDTH = 512


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
        width=WIDTH,
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
    machine = SeededVerticalConnectionMachine(
        ExactVerticalConnection(partition),
        seed_bits=3,
        seed_to_start_node=mapping,
        edge_symbol=lambda edge: edge.target[0] & 1,
    )
    return machine, InformationClockTraceCodec(machine)


def frontier(field):
    limit = 1 << WIDTH
    vector = field.initial_vector
    t = 0
    total = sum(vector)

    while True:
        nxt = field.step_vector(vector)
        next_total = sum(nxt)
        if next_total > limit:
            return t, total
        vector = nxt
        total = next_total
        t += 1


def sample_states(family, count=17):
    if family <= count:
        return list(range(family))
    return sorted({
        (i * (family - 1)) // (count - 1)
        for i in range(count)
    })


def main():
    for name, params in CANDIDATES.items():
        _, _, legacy_validate = make_legacy_codec(
            params
        )
        machine, trace_codec = build(params)
        field = machine.connection.machine.field
        transition_frontier, family = frontier(
            field
        )
        steps = (
            transition_frontier
            + machine.seed_bits
        )

        def forbidden(*args, **kwargs):
            raise AssertionError(
                "event trace gate requested scalar_at"
            )

        machine.connection.machine.oracle.scalar_at = (
            forbidden
        )

        samples = sample_states(family)
        exact = True
        total_macro_events = 0
        total_macro_steps = 0
        total_fallback_steps = 0
        total_semantic_units = 0
        total_transition_steps = 0
        total_emitted_items = 0

        for final_state in samples:
            trace = trace_codec.decode_trace(
                final_state,
                steps,
            )
            bits = trace_codec.expand_bits(trace)

            if (
                len(bits) != steps
                or not legacy_validate(bits)
                or machine.encode(bits)
                != (final_state, steps)
                or trace.physical_reverse_steps
                != transition_frontier
            ):
                exact = False
                break

            semantic_units = (
                trace.macro_event_count
                + trace.fallback_physical_steps
            )

            total_macro_events += (
                trace.macro_event_count
            )
            total_macro_steps += (
                trace.macro_physical_steps
            )
            total_fallback_steps += (
                trace.fallback_physical_steps
            )
            total_semantic_units += (
                semantic_units
            )
            total_transition_steps += (
                trace.transition_steps
            )
            total_emitted_items += (
                trace.emitted_item_count
            )

        macro_coverage = (
            total_macro_steps / total_transition_steps
            if total_transition_steps
            else 0.0
        )
        semantic_reduction = (
            total_transition_steps / total_semantic_units
            if total_semantic_units
            else 1.0
        )
        average_macro_length = (
            total_macro_steps / total_macro_events
            if total_macro_events
            else 0.0
        )

        passed = (
            exact
            and total_transition_steps
            == len(samples) * transition_frontier
            and (
                total_macro_steps
                + total_fallback_steps
                == total_transition_steps
            )
            and total_macro_events > 0
        )

        print(
            "INFORMATION_CLOCK_TRACE_GATE",
            "name", name,
            "PASS", passed,
            "width", WIDTH,
            "trajectory_frontier", steps,
            "transition_frontier",
            transition_frontier,
            "samples", len(samples),
            "macro_events",
            total_macro_events,
            "macro_physical_steps",
            total_macro_steps,
            "fallback_physical_steps",
            total_fallback_steps,
            "macro_physical_coverage",
            f"{macro_coverage:.6f}",
            "average_macro_length",
            f"{average_macro_length:.6f}",
            "semantic_units",
            total_semantic_units,
            "physical_transition_steps",
            total_transition_steps,
            "semantic_reduction_ratio",
            f"{semantic_reduction:.6f}",
            "emitted_trace_items",
            total_emitted_items,
            "physical_reverse_steps_still_required",
            total_transition_steps,
            "scalar_at_calls_allowed",
            False,
            "interpretation",
            "lossless event trace established; recurrence skipping is next layer",
        )

        if not passed:
            raise AssertionError(
                f"information-clock trace failed for {name}"
            )


if __name__ == "__main__":
    main()

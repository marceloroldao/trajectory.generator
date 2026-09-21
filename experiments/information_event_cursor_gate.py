"""Gate exact information-event backward runtime against physical decoding.

This gate evaluates the first true information-clock runtime cursor.

Hard correctness conditions:
- input is only final_state + steps + public law;
- expanded event trace equals the exact physical decoder;
- historical trajectory validator accepts the recovered bits;
- re-encode reproduces exactly the original final_state;
- equivalent physical steps equal the requested transition horizon;
- optimized path performs zero scalar_at() calls;
- at least one macro jump occurs;
- logical reverse operations are fewer than physical reverse operations whenever
  macro coverage is present.

Wall-clock timing is reported only as instrumentation. This first event cursor
may be slower because every macro candidate currently regenerates exact
composed-block geometry and restarts a compact Floquet cursor.
"""

from time import perf_counter

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
from trajectory_generator.information_event_cursor import (
    InformationEventBackwardCursor,
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
SAMPLE_COUNT = 17


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


def transition_frontier(field):
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


def sample_states(family):
    if family <= SAMPLE_COUNT:
        return list(range(family))
    return sorted({
        (i * (family - 1)) // (SAMPLE_COUNT - 1)
        for i in range(SAMPLE_COUNT)
    })


def main():
    for name, params in CANDIDATES.items():
        _, _, legacy_validate = make_legacy_codec(params)
        machine, trace_codec = build(params)
        field = machine.connection.machine.field
        transition_steps, family = transition_frontier(field)
        steps = transition_steps + machine.seed_bits
        samples = sample_states(family)

        oracle = machine.connection.machine.oracle
        original_scalar_at = oracle.scalar_at
        scalar_calls = 0

        def counted_scalar_at(*args, **kwargs):
            nonlocal scalar_calls
            scalar_calls += 1
            return original_scalar_at(*args, **kwargs)

        oracle.scalar_at = counted_scalar_at

        exact = True
        total_logical = 0
        total_macro_jumps = 0
        total_macro_steps = 0
        total_fallback_steps = 0
        total_restarts = 0
        total_macro_probe_steps = 0
        maximum_stored_integers = 0

        event_start = perf_counter()
        event_bits = []

        for final_state in samples:
            cursor = InformationEventBackwardCursor(
                trace_codec,
                final_state,
                transition_steps,
            )
            trace = cursor.decode_trace(
                seed_bits=machine.seed_bits,
                start_node_to_seed=machine.start_node_to_seed,
            )
            bits = trace_codec.expand_bits(trace)
            metrics = cursor.metrics

            if (
                len(bits) != steps
                or not legacy_validate(bits)
                or machine.encode(bits) != (final_state, steps)
                or metrics.equivalent_physical_steps != transition_steps
            ):
                exact = False
                break

            event_bits.append(bits)
            total_logical += metrics.logical_reverse_operations
            total_macro_jumps += metrics.macro_jumps
            total_macro_steps += metrics.macro_physical_steps
            total_fallback_steps += metrics.fallback_physical_steps
            total_restarts += metrics.count_cursor_restarts
            total_macro_probe_steps += (
                metrics.macro_probe_physical_steps
            )
            maximum_stored_integers = max(
                maximum_stored_integers,
                metrics.maximum_stored_count_integers,
            )

        event_seconds = perf_counter() - event_start

        physical_start = perf_counter()
        physical_bits = [
            machine.decode(final_state, steps)
            for final_state in samples
        ]
        physical_seconds = perf_counter() - physical_start

        total_physical = len(samples) * transition_steps
        semantic_reduction = (
            total_physical / total_logical
            if total_logical
            else 1.0
        )
        timing_ratio = (
            physical_seconds / event_seconds
            if event_seconds > 0.0
            else float("inf")
        )

        hard_pass = (
            exact
            and event_bits == physical_bits
            and scalar_calls == 0
            and total_macro_jumps > 0
            and total_macro_steps > 0
            and total_macro_steps + total_fallback_steps == total_physical
            and total_logical < total_physical
            and total_restarts == 0
        )

        print(
            "INFORMATION_EVENT_CURSOR_GATE",
            "name", name,
            "PASS", hard_pass,
            "width", WIDTH,
            "trajectory_frontier", steps,
            "transition_frontier", transition_steps,
            "samples", len(samples),
            "physical_reverse_steps", total_physical,
            "logical_reverse_operations", total_logical,
            "macro_jumps", total_macro_jumps,
            "macro_physical_steps", total_macro_steps,
            "fallback_physical_steps", total_fallback_steps,
            "semantic_reduction_ratio",
            f"{semantic_reduction:.6f}",
            "count_cursor_restarts", total_restarts,
            "macro_probe_physical_steps",
            total_macro_probe_steps,
            "maximum_stored_count_integers",
            maximum_stored_integers,
            "scalar_at_calls", scalar_calls,
            "event_seconds", f"{event_seconds:.6f}",
            "physical_seconds", f"{physical_seconds:.6f}",
            "physical_over_event_timing_ratio",
            f"{timing_ratio:.6f}",
            "timing_is_gate", False,
            "interpretation",
            "exact event-level reverse runtime; timing remains diagnostic",
        )

        if not hard_pass:
            raise AssertionError(
                f"information-event cursor gate failed for {name}"
            )


if __name__ == "__main__":
    main()

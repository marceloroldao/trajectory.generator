"""Compare direct scalar local reverse with the Floquet cursor decoder.

Correctness and dependency elimination are hard gate criteria.
Wall-clock timing is informational only because CI hosts are noisy.
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
from trajectory_generator.scalar_partition_trajectory import (
    build_scalar_partition_translation_machine,
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
    return SeededVerticalConnectionMachine(
        ExactVerticalConnection(partition),
        seed_bits=3,
        seed_to_start_node=mapping,
        edge_symbol=lambda edge: edge.target[0] & 1,
    )


def timed_decode(method, states, steps):
    start = perf_counter()
    result = [
        method(state, steps)
        for state in states
    ]
    return result, perf_counter() - start


def main():
    for name, (params, frontier) in CANDIDATES.items():
        total, _, legacy_validate = make_legacy_codec(
            params
        )
        family = total(frontier)
        samples = sorted({
            0,
            family // 2,
            family - 1,
        })

        direct_machine = build(params)
        direct_oracle = direct_machine.connection.machine.oracle
        direct_original = direct_oracle.scalar_at
        direct_calls = 0

        def counted_direct(*args, **kwargs):
            nonlocal direct_calls
            direct_calls += 1
            return direct_original(*args, **kwargs)

        direct_oracle.scalar_at = counted_direct
        direct_bits, direct_seconds = timed_decode(
            direct_machine.decode_direct,
            samples,
            frontier,
        )

        cursor_machine = build(params)
        cursor_oracle = cursor_machine.connection.machine.oracle
        cursor_original = cursor_oracle.scalar_at
        cursor_calls = 0

        def counted_cursor(*args, **kwargs):
            nonlocal cursor_calls
            cursor_calls += 1
            return cursor_original(*args, **kwargs)

        cursor_oracle.scalar_at = counted_cursor
        cursor_bits, cursor_seconds = timed_decode(
            cursor_machine.decode,
            samples,
            frontier,
        )

        metric_bits, metrics = (
            cursor_machine.decode_with_cursor_metrics(
                samples[-1],
                frontier,
            )
        )

        same_bits = direct_bits == cursor_bits
        valid = all(
            len(bits) == frontier
            and legacy_validate(bits)
            for bits in cursor_bits
        )
        expected_reverse_steps = frontier - 3
        fixed_memory = (
            metrics is not None
            and metrics.reverse_steps
            == expected_reverse_steps
            and metrics.maximum_stored_floquet_rows
            <= len(
                cursor_machine.connection.machine.field.reduced_coefficients
            )
        )
        metric_identity = (
            metric_bits == cursor_bits[-1]
        )

        passed = (
            same_bits
            and valid
            and direct_calls > 0
            and cursor_calls == 0
            and fixed_memory
            and metric_identity
        )

        speedup = (
            direct_seconds / cursor_seconds
            if cursor_seconds > 0.0
            else float("inf")
        )

        direct_encode_machine = build(params)
        direct_encode_oracle = (
            direct_encode_machine.connection.machine.oracle
        )
        direct_encode_original = (
            direct_encode_oracle.scalar_at
        )
        direct_encode_calls = 0

        def counted_direct_encode(*args, **kwargs):
            nonlocal direct_encode_calls
            direct_encode_calls += 1
            return direct_encode_original(*args, **kwargs)

        direct_encode_oracle.scalar_at = (
            counted_direct_encode
        )
        start = perf_counter()
        direct_encoded = [
            direct_encode_machine.encode_direct(bits)
            for bits in direct_bits
        ]
        direct_encode_seconds = (
            perf_counter() - start
        )

        cursor_encode_machine = build(params)
        cursor_encode_oracle = (
            cursor_encode_machine.connection.machine.oracle
        )
        cursor_encode_original = (
            cursor_encode_oracle.scalar_at
        )
        cursor_encode_calls = 0

        def counted_cursor_encode(*args, **kwargs):
            nonlocal cursor_encode_calls
            cursor_encode_calls += 1
            return cursor_encode_original(*args, **kwargs)

        cursor_encode_oracle.scalar_at = (
            counted_cursor_encode
        )
        start = perf_counter()
        cursor_encoded = [
            cursor_encode_machine.encode(bits)
            for bits in cursor_bits
        ]
        cursor_encode_seconds = (
            perf_counter() - start
        )

        expected_encoded = [
            (state, frontier)
            for state in samples
        ]
        encode_identity = (
            direct_encoded
            == cursor_encoded
            == expected_encoded
        )

        _, _, forward_metrics = (
            cursor_encode_machine.encode_with_cursor_metrics(
                cursor_bits[-1]
            )
        )

        passed = (
            passed
            and direct_encode_calls > 0
            and cursor_encode_calls == 0
            and encode_identity
            and forward_metrics is not None
            and forward_metrics.forward_steps
            == expected_reverse_steps
        )

        encode_speedup = (
            direct_encode_seconds / cursor_encode_seconds
            if cursor_encode_seconds > 0.0
            else float("inf")
        )

        print(
            "CURSOR_VERTICAL_CONNECTION_PERF_GATE",
            "name", name,
            "PASS", passed,
            "frontier", frontier,
            "samples", len(samples),
            "direct_decode_scalar_at_calls", direct_calls,
            "cursor_decode_scalar_at_calls", cursor_calls,
            "direct_decode_seconds",
            f"{direct_seconds:.6f}",
            "cursor_decode_seconds",
            f"{cursor_seconds:.6f}",
            "decode_timing_speedup",
            f"{speedup:.3f}",
            "direct_encode_scalar_at_calls",
            direct_encode_calls,
            "cursor_encode_scalar_at_calls",
            cursor_encode_calls,
            "direct_encode_seconds",
            f"{direct_encode_seconds:.6f}",
            "cursor_encode_seconds",
            f"{cursor_encode_seconds:.6f}",
            "encode_timing_speedup",
            f"{encode_speedup:.3f}",
            "reverse_steps",
            metrics.reverse_steps if metrics else None,
            "reverse_unifilar_steps",
            (
                metrics.reverse_unifilar_steps
                if metrics
                else None
            ),
            "partition_reverse_steps",
            (
                metrics.partition_reverse_steps
                if metrics
                else None
            ),
            "stored_floquet_rows",
            (
                metrics.maximum_stored_floquet_rows
                if metrics
                else None
            ),
            "stored_count_integers",
            (
                metrics.maximum_stored_count_integers
                if metrics
                else None
            ),
            "reachable_states",
            (
                metrics.reachable_state_count
                if metrics
                else None
            ),
            "forward_persistent_count_integers",
            (
                forward_metrics.persistent_count_integers
                if forward_metrics
                else None
            ),
            "forward_peak_count_integers",
            (
                forward_metrics.peak_count_integers_during_step
                if forward_metrics
                else None
            ),
            "timing_is_gate",
            False,
        )

        if not passed:
            raise AssertionError(
                f"cursor performance/correctness gate failed for {name}"
            )


if __name__ == "__main__":
    main()

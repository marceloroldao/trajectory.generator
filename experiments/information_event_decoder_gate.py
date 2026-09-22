"""Gate reusable information-event decoding against the physical cursor.

This gate treats (final_state, steps) + public universe law as the only decode
input.  It verifies exact trajectory recovery at the historical 63-bit
frontiers while measuring semantic compression of the reverse walk.
"""

from recurrent_orbit_core import graph
from topological_transition_state import (
    initial_topology,
    make_codec as make_legacy_codec,
)

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


def main():
    for name, (params, frontier) in CANDIDATES.items():
        total, _, legacy_validate = make_legacy_codec(params)
        machine = build(params)
        decoder = InformationEventDecoder(machine)

        family = total(frontier)
        samples = sorted({
            0,
            family // 4,
            family // 2,
            (3 * family) // 4,
            family - 1,
        })

        physical_ops = 0
        logical_ops = 0
        macro_jumps = 0
        macro_steps = 0
        max_rows = 0

        for final_state in samples:
            expected = machine.decode(final_state, frontier)
            trace, metrics = decoder.decode_trace_with_metrics(
                final_state,
                frontier,
            )
            bits = decoder.trace_codec.expand_bits(trace)

            if bits != expected:
                raise AssertionError(
                    f"event decoder mismatch for {name}"
                )
            if len(bits) != frontier or not legacy_validate(bits):
                raise AssertionError(
                    f"invalid recovered trajectory for {name}"
                )

            rebuilt, rebuilt_steps = machine.encode(bits)
            if rebuilt != final_state or rebuilt_steps != frontier:
                raise AssertionError(
                    f"roundtrip mismatch for {name}"
                )

            if metrics is None:
                raise AssertionError(
                    f"missing event metrics for {name}"
                )
            if (
                metrics.equivalent_physical_steps
                != frontier - machine.seed_bits
            ):
                raise AssertionError(
                    f"physical-step accounting mismatch for {name}"
                )
            if metrics.macro_probe_physical_steps != 0:
                raise AssertionError(
                    f"macro path replay detected for {name}"
                )

            physical_ops += metrics.equivalent_physical_steps
            logical_ops += metrics.logical_reverse_operations
            macro_jumps += metrics.macro_jumps
            macro_steps += metrics.macro_physical_steps
            max_rows = max(
                max_rows,
                metrics.maximum_stored_floquet_rows,
            )

        if logical_ops <= 0:
            raise AssertionError(
                f"no logical reverse operations for {name}"
            )
        if macro_jumps <= 0 or macro_steps <= 0:
            raise AssertionError(
                f"no information-event macro jump for {name}"
            )
        if logical_ops >= physical_ops:
            raise AssertionError(
                f"event cursor did not reduce reverse operations for {name}"
            )

        ratio = physical_ops / logical_ops
        print(
            "INFORMATION_EVENT_DECODER_GATE",
            "name", name,
            "PASS", True,
            "frontier", frontier,
            "samples", len(samples),
            "physical_reverse_steps", physical_ops,
            "logical_reverse_operations", logical_ops,
            "semantic_reduction_ratio", f"{ratio:.6f}",
            "macro_jumps", macro_jumps,
            "macro_physical_steps", macro_steps,
            "maximum_stored_floquet_rows", max_rows,
            "decode_inputs",
            "(final_state,steps)+public_law_only",
            "roundtrip_exact", True,
            "macro_path_replay_steps", 0,
        )


if __name__ == "__main__":
    main()

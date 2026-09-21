"""Gate exact composed vertical macro-blocks against physical-step dynamics."""

from recurrent_orbit_core import graph
from topological_transition_state import initial_topology

from trajectory_generator.composed_vertical_connection import (
    ComposedVerticalConnection,
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

BASE_START_TIMES = (24, 48, 96, 192)


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
        width=512,
        seed_cache_entries=128,
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
    trace = InformationClockTraceCodec(machine)
    composed = ComposedVerticalConnection(
        machine.connection
    )
    return machine, trace, composed


def main():
    for name, params in CANDIDATES.items():
        machine, trace, composed = build(params)

        checked_blocks = 0
        checked_ranks = 0
        located_blocks = 0
        merge_crossing_blocks = 0

        reachable_indegree = {
            node: len(
                machine.connection.codec.incoming[node]
            )
            for node in machine.connection.codec.nodes
        }

        for macro in trace.structure.macro_edges:
            source_phase = (
                macro.source[2]
                if (
                    isinstance(macro.source, tuple)
                    and len(macro.source) >= 3
                    and isinstance(macro.source[2], int)
                )
                else 0
            )
            start_times = tuple(
                base
                + (
                    source_phase
                    - base
                )
                % 3
                for base in BASE_START_TIMES
            )

            for start_time in start_times:
                labels = trace.macro_edge_labels[
                    macro.label
                ]
                block = composed.embedding(
                    labels,
                    start_time,
                )
                if block.source_size <= 0:
                    continue

                checked_blocks += 1
                if any(
                    reachable_indegree[node] > 1
                    for node in macro.path[1:-1]
                ):
                    merge_crossing_blocks += 1

                ranks = sorted({
                    0,
                    block.source_size // 2,
                    block.source_size - 1,
                })

                for rank in ranks:
                    source = machine.connection.state(
                        block.source,
                        rank,
                        start_time,
                    )

                    sequential = source
                    for label in labels:
                        sequential = (
                            machine.connection.forward(
                                sequential,
                                label,
                            )
                        )

                    jumped = composed.forward(
                        source,
                        labels,
                    )
                    if jumped != sequential:
                        raise AssertionError(
                            f"composed forward mismatch for {name} {macro.label}"
                        )

                    recovered = composed.reverse(
                        jumped,
                        labels,
                    )
                    if recovered != source:
                        raise AssertionError(
                            f"composed reverse mismatch for {name} {macro.label}"
                        )

                    candidate_paths = [
                        trace.macro_edge_labels[
                            candidate.label
                        ]
                        for candidate in trace.structure.macro_edges
                        if candidate.target == macro.target
                    ]
                    located = composed.locate_predecessor(
                        jumped,
                        candidate_paths,
                    )
                    if (
                        located is None
                        or located.edge_labels != labels
                    ):
                        raise AssertionError(
                            f"macro predecessor locate mismatch for {name} {macro.label}"
                        )

                    located_blocks += 1
                    checked_ranks += 1

                if (
                    block.end - block.start
                    != block.source_size
                ):
                    raise AssertionError(
                        "composed block width changed source fiber cardinality"
                    )

        passed = (
            checked_blocks > 0
            and checked_ranks > 0
            and located_blocks == checked_ranks
            and merge_crossing_blocks > 0
        )

        print(
            "COMPOSED_VERTICAL_MACROBLOCK_GATE",
            "name", name,
            "PASS", passed,
            "base_start_times", BASE_START_TIMES,
            "macro_edges",
            len(trace.structure.macro_edges),
            "checked_blocks", checked_blocks,
            "checked_ranks", checked_ranks,
            "located_blocks", located_blocks,
            "merge_crossing_blocks",
            merge_crossing_blocks,
            "unit_slope_translation",
            True,
            "source_width_preserved",
            True,
            "interpretation",
            "entire information-clock flight is one exact contiguous vertical predecessor block",
        )

        if not passed:
            raise AssertionError(
                f"composed vertical macro-block gate failed for {name}"
            )


if __name__ == "__main__":
    main()

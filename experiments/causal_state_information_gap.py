"""Quantify the information lost by the raw causal node at 63-bit frontiers.

The operational final-state machine is reversible, but its integer trajectory
coordinate is richer than the old phase-lifted causal node:

    (history3, topology3, phase3).

This experiment measures how many distinct admissible histories merge into each
raw node at the frontier.

Under a uniform distribution over admissible trajectories, if C_v histories end
at node v then:

    H(history | raw_node=v) = log2(C_v)

and

    H(history | raw_node)
      = sum_v (C_v/N) * log2(C_v).

The worst-case additional coordinate must distinguish at least max_v C_v
histories that share one identical raw node.
"""

from math import ceil, log2

from recurrent_orbit_core import graph
from topological_transition_state import (
    initial_topology,
    counts as historical_counts,
)

from trajectory_generator.floquet_count_field import (
    FloquetCountFieldRecurrence,
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


def ceil_log2(value):
    if value <= 1:
        return 0
    return (value - 1).bit_length()


def main():
    for name, (params, frontier) in CANDIDATES.items():
        adjacency = graph(params)
        field = FloquetCountFieldRecurrence(
            adjacency,
            start_nodes=initial_nodes(),
            phase_of=lambda node: node[2],
            period=3,
            base_phase=0,
            cache_rows=0,
        )

        transition_time = frontier - 3
        vector = field.vector_at(transition_time)
        previous = field.vector_at(transition_time - 1)

        active = [
            (node, count)
            for node, count in zip(field.nodes, vector)
            if count
        ]
        total = sum(count for _, count in active)

        historical = historical_counts(
            params,
            max_steps=frontier + 1,
        )
        if total != historical[frontier]:
            raise AssertionError("frontier count mismatch")

        total_entropy = log2(total)
        endpoint_entropy = -sum(
            (count / total) * log2(count / total)
            for _, count in active
        )
        conditional_entropy = sum(
            (count / total) * log2(count)
            for _, count in active
        )

        # Numerical identity:
        # H(path) = H(raw endpoint) + H(path | raw endpoint).
        entropy_residual = (
            total_entropy
            - endpoint_entropy
            - conditional_entropy
        )

        max_node, max_count = max(
            active,
            key=lambda row: row[1],
        )
        worst_extra_bits = ceil_log2(max_count)

        # At known physical time phase is public. The raw causal payload has
        # only history3+topology3 = 6 non-phase bits, although the number of
        # actually populated endpoint nodes can be much smaller than 64.
        raw_fixed_time_capacity_bits = 6
        address_bits = ceil_log2(total)

        incoming = {node: [] for node in field.nodes}
        for source in field.nodes:
            source_count = previous[field.node_index[source]]
            if not source_count:
                continue
            for edge_index, target in enumerate(
                adjacency.get(source, ())
            ):
                if target in incoming:
                    incoming[target].append(
                        (source, edge_index, source_count)
                    )

        ambiguous_nodes = []
        ambiguous_path_count = 0
        max_predecessor_blocks = 0

        for node, count in active:
            blocks = incoming[node]
            choices = len(blocks)
            max_predecessor_blocks = max(
                max_predecessor_blocks,
                choices,
            )
            if choices > 1:
                ambiguous_nodes.append(node)
                ambiguous_path_count += count

        immediate_ambiguity_fraction = (
            ambiguous_path_count / total
        )

        print(
            "CAUSAL_STATE_INFORMATION_GAP",
            "name", name,
            "PASS",
            abs(entropy_residual) < 1e-9
            and max_count > 1
            and address_bits <= 63,
            "frontier", frontier,
            "trajectories", total,
            "address_bits", address_bits,
            "active_raw_nodes", len(active),
            "raw_fixed_time_capacity_bits",
            raw_fixed_time_capacity_bits,
            "endpoint_entropy_bits",
            f"{endpoint_entropy:.12f}",
            "history_given_raw_node_bits",
            f"{conditional_entropy:.12f}",
            "total_entropy_bits",
            f"{total_entropy:.12f}",
            "entropy_residual",
            f"{entropy_residual:.3e}",
            "max_histories_one_raw_node", max_count,
            "worst_case_extra_bits", worst_extra_bits,
            "max_merge_node", max_node,
            "immediately_ambiguous_raw_nodes",
            len(ambiguous_nodes),
            "max_predecessor_blocks",
            max_predecessor_blocks,
            "path_fraction_at_immediately_ambiguous_nodes",
            f"{immediate_ambiguity_fraction:.12f}",
        )

        next_total = historical[frontier + 1]
        print(
            "CAUSAL_STATE_FRONTIER_BOUND",
            "name", name,
            "PASS",
            total <= (1 << 63)
            and next_total > (1 << 63),
            "frontier_family", total,
            "next_family", next_total,
            "raw_node_cannot_be_unique",
            max_count > 1,
            "minimum_worst_case_auxiliary_states",
            max_count,
            "minimum_worst_case_auxiliary_bits",
            worst_extra_bits,
        )


if __name__ == "__main__":
    main()

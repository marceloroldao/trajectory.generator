"""Gate exact vertical information creation at causal branch events."""

from math import log2

from recurrent_orbit_core import graph
from topological_transition_state import initial_topology

from trajectory_generator.branch_information_budget import (
    budget_step,
    cumulative_created_bits,
    endpoint_information_gain,
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


def main():
    for name, (params, frontier) in CANDIDATES.items():
        adjacency = graph(params)
        starts = initial_nodes()

        field = FloquetCountFieldRecurrence(
            adjacency,
            start_nodes=starts,
            phase_of=lambda node: node[2],
            period=3,
            base_phase=0,
            cache_rows=0,
        )

        counts = {
            node: field.initial_vector[
                field.node_index[node]
            ]
            for node in field.nodes
        }

        # The 3-bit bootstrap already contributes 8 histories. The graph
        # transition horizon is frontier-3.
        transition_horizon = frontier - 3
        rows = []

        count_identity = True
        conservation = True

        for time in range(transition_horizon):
            row, nxt = budget_step(
                adjacency,
                counts,
                time=time,
            )
            rows.append(row)

            expected_after = field.total(time + 1)
            if row.total_after != expected_after:
                count_identity = False

            if (
                row.total_after
                != row.total_before
                + row.branch_excess
            ):
                conservation = False

            counts = nxt

        final_total = field.total(
            transition_horizon
        )
        expected_bits = (
            log2(final_total)
            - log2(len(starts))
        )
        created_bits = cumulative_created_bits(
            rows
        )
        telescope = abs(
            created_bits - expected_bits
        ) < 1e-9

        deterministic_rows = [
            row for row in rows
            if row.deterministic
        ]
        deterministic_zero = all(
            row.delta_bits == 0.0
            and row.total_after == row.total_before
            for row in deterministic_rows
        )

        branch_rows = [
            row for row in rows
            if not row.deterministic
        ]
        branch_positive = all(
            row.delta_bits > 0.0
            and row.branch_excess > 0
            for row in branch_rows
        )

        # Count weighted branch-event mass, not just physical rows.
        total_branch_excess = sum(
            row.branch_excess
            for row in rows
        )
        max_step_bits = max(
            (row.delta_bits for row in rows),
            default=0.0,
        )

        passed = (
            count_identity
            and conservation
            and telescope
            and deterministic_zero
            and branch_positive
            and len(branch_rows) > 0
        )

        print(
            "BRANCH_INFORMATION_BUDGET_GATE",
            "name", name,
            "PASS", passed,
            "frontier", frontier,
            "transition_horizon",
            transition_horizon,
            "initial_histories", len(starts),
            "final_histories", final_total,
            "created_information_bits",
            f"{created_bits:.12f}",
            "expected_information_gain_bits",
            f"{expected_bits:.12f}",
            "physical_rows", len(rows),
            "branching_rows", len(branch_rows),
            "deterministic_rows",
            len(deterministic_rows),
            "total_branch_excess",
            total_branch_excess,
            "max_single_step_created_bits",
            f"{max_step_bits:.12f}",
            "count_identity", count_identity,
            "conservation", conservation,
            "telescoping_identity", telescope,
            "deterministic_zero_cost",
            deterministic_zero,
            "branch_positive_cost",
            branch_positive,
        )

        if not passed:
            raise AssertionError(
                f"branch information budget failed for {name}"
            )


if __name__ == "__main__":
    main()

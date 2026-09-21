"""Gate exact horizontal/vertical information flow on topological universes."""

from math import log2

from recurrent_orbit_core import graph
from topological_transition_state import (
    initial_topology,
)

from trajectory_generator.branch_information_budget import (
    budget_step,
)
from trajectory_generator.horizontal_vertical_entropy import (
    decompose_counts,
    entropy_flow_step,
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

        nodes = set(adjacency)
        for targets in adjacency.values():
            nodes.update(targets)

        counts = {
            node: 0
            for node in nodes
        }
        for start in initial_nodes():
            counts[start] += 1

        transition_horizon = frontier - 3

        chain_rule = True
        flow_identity = True
        branch_budget_identity = True
        deterministic_conservation = True

        deterministic_rows = 0
        branch_rows = 0
        horizontal_to_vertical_rows = 0
        vertical_to_horizontal_rows = 0

        max_positive_vertical_flow = 0.0
        max_negative_vertical_flow = 0.0

        initial = decompose_counts(counts)
        final = initial

        for time in range(transition_horizon):
            budget, nxt = budget_step(
                adjacency,
                counts,
                time=time,
            )
            flow = entropy_flow_step(
                counts,
                nxt,
                time=time,
            )

            if (
                abs(flow.before.residual) > 1e-9
                or abs(flow.after.residual) > 1e-9
            ):
                chain_rule = False

            if abs(flow.flow_residual) > 1e-9:
                flow_identity = False

            if (
                abs(
                    flow.branch_created_bits
                    - budget.delta_bits
                )
                > 1e-9
            ):
                branch_budget_identity = False

            if flow.deterministic:
                deterministic_rows += 1
                if (
                    abs(flow.branch_created_bits) > 1e-12
                    or abs(
                        flow.delta_horizontal_bits
                        + flow.delta_vertical_bits
                    ) > 1e-9
                ):
                    deterministic_conservation = False
            else:
                branch_rows += 1

            if flow.delta_vertical_bits > 1e-12:
                horizontal_to_vertical_rows += 1
            elif flow.delta_vertical_bits < -1e-12:
                vertical_to_horizontal_rows += 1

            max_positive_vertical_flow = max(
                max_positive_vertical_flow,
                flow.delta_vertical_bits,
            )
            max_negative_vertical_flow = min(
                max_negative_vertical_flow,
                flow.delta_vertical_bits,
            )

            counts = nxt
            final = flow.after

        total_gain = (
            final.total_bits - initial.total_bits
        )
        total_gain_expected = log2(
            final.total_histories
            / initial.total_histories
        )

        endpoint_identity = (
            abs(
                final.total_bits
                - final.horizontal_bits
                - final.vertical_bits
            )
            < 1e-9
        )
        total_gain_identity = (
            abs(
                total_gain
                - total_gain_expected
            )
            < 1e-9
        )

        passed = (
            chain_rule
            and flow_identity
            and branch_budget_identity
            and deterministic_conservation
            and endpoint_identity
            and total_gain_identity
            and branch_rows > 0
        )

        print(
            "HORIZONTAL_VERTICAL_ENTROPY_GATE",
            "name", name,
            "PASS", passed,
            "frontier", frontier,
            "initial_total_bits",
            f"{initial.total_bits:.12f}",
            "final_total_bits",
            f"{final.total_bits:.12f}",
            "final_horizontal_bits",
            f"{final.horizontal_bits:.12f}",
            "final_vertical_bits",
            f"{final.vertical_bits:.12f}",
            "created_after_bootstrap_bits",
            f"{total_gain:.12f}",
            "deterministic_rows",
            deterministic_rows,
            "branch_rows", branch_rows,
            "vertical_gain_rows",
            horizontal_to_vertical_rows,
            "vertical_loss_rows",
            vertical_to_horizontal_rows,
            "max_positive_vertical_flow",
            f"{max_positive_vertical_flow:.12f}",
            "max_negative_vertical_flow",
            f"{max_negative_vertical_flow:.12f}",
            "chain_rule", chain_rule,
            "branch_budget_identity",
            branch_budget_identity,
            "deterministic_conservation",
            deterministic_conservation,
        )

        if not passed:
            raise AssertionError(
                f"horizontal/vertical entropy flow failed for {name}"
            )


if __name__ == "__main__":
    main()

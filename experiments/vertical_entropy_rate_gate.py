"""Gate vertical-memory rate against recurrent-core topological entropy."""

from recurrent_orbit_core import graph

from trajectory_generator.branch_information_budget import (
    step_counts,
)
from trajectory_generator.horizontal_vertical_entropy import (
    decompose_counts,
)
from trajectory_generator.recurrent_macrograph import (
    derive_recurrent_structure,
)
from trajectory_generator.vertical_entropy_rate import (
    entropy_rate_from_growth,
    rate_bound_holds,
    vertical_rate_bound,
)


CANDIDATES = {
    "robust_208": (1, 0, 0, 2),
    "balanced_221": (0, 2, 4, 4),
    "long_239": (3, 2, 4, 4),
}


HORIZONS = (96, 192, 384)


def core_adjacency(adjacency, component):
    comp = set(component)
    return {
        node: tuple(
            target
            for target in adjacency[node]
            if target in comp
        )
        for node in component
    }


def main():
    for name, params in CANDIDATES.items():
        adjacency = graph(params)
        structure = derive_recurrent_structure(
            adjacency
        )
        core = core_adjacency(
            adjacency,
            structure.component,
        )

        counts = {
            node: 1
            for node in structure.component
        }

        rows = {}
        max_horizon = max(HORIZONS)

        for time in range(max_horizon + 1):
            if time in HORIZONS:
                decomposition = decompose_counts(
                    counts
                )
                rows[time] = vertical_rate_bound(
                    decomposition,
                    time=time,
                    causal_state_count=len(
                        structure.component
                    ),
                )

            if time < max_horizon:
                counts = step_counts(
                    core,
                    counts,
                )

        target_rate = entropy_rate_from_growth(
            structure.growth_rate
        )

        identities = all(
            rate_bound_holds(row)
            for row in rows.values()
        )

        gap_bounds_shrink = all(
            rows[right].maximum_rate_gap
            < rows[left].maximum_rate_gap
            for left, right in zip(
                HORIZONS,
                HORIZONS[1:],
            )
        )

        final = rows[HORIZONS[-1]]
        vertical_matches_entropy = (
            abs(
                final.vertical_rate
                - target_rate
            )
            < 5e-4
        )

        # The vertical estimate should be closer to h than the raw total rate,
        # because the O(1) horizontal endpoint entropy has been removed.
        vertical_is_better_estimator = (
            abs(final.vertical_rate - target_rate)
            < abs(final.total_rate - target_rate)
        )

        passed = (
            structure.growth_rate > 1.0
            and identities
            and gap_bounds_shrink
            and vertical_matches_entropy
            and vertical_is_better_estimator
        )

        print(
            "VERTICAL_ENTROPY_RATE_GATE",
            "name", name,
            "PASS", passed,
            "core_nodes",
            len(structure.component),
            "growth_rate",
            f"{structure.growth_rate:.12f}",
            "target_log2_lambda",
            f"{target_rate:.12f}",
            "horizons", HORIZONS,
            "total_rate",
            tuple(
                round(rows[t].total_rate, 12)
                for t in HORIZONS
            ),
            "vertical_rate",
            tuple(
                round(rows[t].vertical_rate, 12)
                for t in HORIZONS
            ),
            "horizontal_rate",
            tuple(
                round(rows[t].horizontal_rate, 12)
                for t in HORIZONS
            ),
            "max_rate_gap_bound",
            tuple(
                round(
                    rows[t].maximum_rate_gap,
                    12,
                )
                for t in HORIZONS
            ),
            "final_vertical_error",
            f"{abs(final.vertical_rate - target_rate):.12f}",
            "vertical_is_better_entropy_estimator",
            vertical_is_better_estimator,
        )

        if not passed:
            raise AssertionError(
                f"vertical entropy-rate gate failed for {name}"
            )


if __name__ == "__main__":
    main()

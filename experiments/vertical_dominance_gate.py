"""Gate asymptotic vertical-information dominance on recurrent cores."""

from recurrent_orbit_core import graph

from trajectory_generator.branch_information_budget import (
    step_counts,
)
from trajectory_generator.recurrent_macrograph import (
    derive_recurrent_structure,
)
from trajectory_generator.vertical_dominance import (
    bound_identity_holds,
    dominance_bound,
)


CANDIDATES = {
    "robust_208": (1, 0, 0, 2),
    "balanced_221": (0, 2, 4, 4),
    "long_239": (3, 2, 4, 4),
}


HORIZONS = (24, 48, 96, 192, 384)


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

        # One distinct initial history at every recurrent core node.
        counts = {
            node: 1
            for node in structure.component
        }

        rows = {}
        max_horizon = max(HORIZONS)

        for time in range(max_horizon + 1):
            if time in HORIZONS:
                rows[time] = dominance_bound(
                    counts,
                    causal_state_count=len(
                        structure.component
                    ),
                )

            if time < max_horizon:
                counts = step_counts(
                    core,
                    counts,
                )

        identities = all(
            bound_identity_holds(row)
            for row in rows.values()
        )

        lower_bounds = [
            rows[t].lower_bound_vertical_fraction
            for t in HORIZONS
        ]
        total_bits = [
            rows[t].total_bits
            for t in HORIZONS
        ]

        # Positive entropy makes H_total grow. The theorem's lower bound must
        # therefore improve strictly over this long-window sample.
        bound_improves = all(
            right > left
            for left, right in zip(
                lower_bounds,
                lower_bounds[1:],
            )
        )
        total_grows = all(
            right > left
            for left, right in zip(
                total_bits,
                total_bits[1:],
            )
        )

        last = rows[HORIZONS[-1]]
        actual_dominant = (
            last.actual_vertical_fraction > 0.95
        )
        theorem_dominant = (
            last.lower_bound_vertical_fraction > 0.95
        )

        passed = (
            structure.growth_rate > 1.0
            and identities
            and bound_improves
            and total_grows
            and actual_dominant
            and theorem_dominant
        )

        print(
            "VERTICAL_DOMINANCE_GATE",
            "name", name,
            "PASS", passed,
            "core_nodes",
            len(structure.component),
            "growth_rate",
            f"{structure.growth_rate:.12f}",
            "horizons", HORIZONS,
            "total_bits",
            tuple(
                round(rows[t].total_bits, 12)
                for t in HORIZONS
            ),
            "horizontal_bits",
            tuple(
                round(rows[t].horizontal_bits, 12)
                for t in HORIZONS
            ),
            "vertical_bits",
            tuple(
                round(rows[t].vertical_bits, 12)
                for t in HORIZONS
            ),
            "actual_vertical_fraction",
            tuple(
                round(
                    rows[t].actual_vertical_fraction,
                    12,
                )
                for t in HORIZONS
            ),
            "theorem_lower_bound",
            tuple(
                round(
                    rows[t].lower_bound_vertical_fraction,
                    12,
                )
                for t in HORIZONS
            ),
            "final_actual_vertical_fraction",
            f"{last.actual_vertical_fraction:.12f}",
            "final_theorem_lower_bound",
            f"{last.lower_bound_vertical_fraction:.12f}",
        )

        if not passed:
            raise AssertionError(
                f"vertical dominance failed for {name}"
            )


if __name__ == "__main__":
    main()

"""Gate normalized vertical block geometry and reverse Parry limit."""

from recurrent_orbit_core import graph

from trajectory_generator.branch_information_budget import (
    step_counts,
)
from trajectory_generator.information_clock_statistics import (
    information_clock_statistics,
)
from trajectory_generator.normalized_vertical_dynamics import (
    exact_normalized_block_width,
    exact_target_partition_residual,
    reverse_parry_geometry,
)
from trajectory_generator.recurrent_macrograph import (
    derive_recurrent_structure,
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

        stats = information_clock_statistics(
            structure.component,
            structure.physical_edges,
            growth_rate=structure.growth_rate,
        )
        reverse = reverse_parry_geometry(
            structure.component,
            stats,
        )
        limit_by_label = {
            row.label: row.probability
            for row in reverse.reverse_probabilities
        }

        counts = {
            node: 1
            for node in structure.component
        }

        errors = {}
        partition_residuals = {}
        max_horizon = max(HORIZONS)

        for time in range(max_horizon + 1):
            nxt = step_counts(
                core,
                counts,
            )

            if time in HORIZONS:
                maximum_error = 0.0
                for edge in structure.physical_edges:
                    exact = exact_normalized_block_width(
                        counts,
                        nxt,
                        edge,
                    )
                    maximum_error = max(
                        maximum_error,
                        abs(
                            exact
                            - limit_by_label[edge.label]
                        ),
                    )
                errors[time] = maximum_error
                partition_residuals[time] = (
                    exact_target_partition_residual(
                        counts,
                        nxt,
                        structure.physical_edges,
                    )
                )

            counts = nxt

        error_improves = (
            errors[HORIZONS[-1]]
            < errors[HORIZONS[0]]
        )
        final_close = (
            errors[HORIZONS[-1]] < 1e-6
        )
        partitions_exact = all(
            residual < 1e-12
            for residual in partition_residuals.values()
        )
        entropy_identity = (
            abs(
                reverse.expected_reverse_information_bits
                - stats.bits_per_physical_step
            )
            < 1e-10
        )

        passed = (
            reverse.maximum_target_normalization_residual
            < 1e-10
            and partitions_exact
            and error_improves
            and final_close
            and entropy_identity
        )

        print(
            "NORMALIZED_VERTICAL_DYNAMICS_GATE",
            "name", name,
            "PASS", passed,
            "core_nodes",
            len(structure.component),
            "lambda",
            f"{structure.growth_rate:.12f}",
            "log2_lambda",
            f"{stats.bits_per_physical_step:.12f}",
            "horizons", HORIZONS,
            "max_block_width_error",
            tuple(
                f"{errors[t]:.3e}"
                for t in HORIZONS
            ),
            "max_partition_residual",
            f"{max(partition_residuals.values()):.3e}",
            "reverse_parry_normalization_residual",
            f"{reverse.maximum_target_normalization_residual:.3e}",
            "expected_minus_log2_reverse_width",
            f"{reverse.expected_reverse_information_bits:.12f}",
            "entropy_identity_residual",
            f"{abs(reverse.expected_reverse_information_bits - stats.bits_per_physical_step):.3e}",
            "interpretation",
            "normalized vertical fibers converge to a stationary piecewise-affine reverse geometry",
        )

        if not passed:
            raise AssertionError(
                f"normalized vertical dynamics failed for {name}"
            )


if __name__ == "__main__":
    main()

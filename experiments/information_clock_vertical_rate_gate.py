"""Gate exact equivalence of information-clock and vertical-memory rates."""

from recurrent_orbit_core import graph

from trajectory_generator.branch_information_budget import (
    step_counts,
)
from trajectory_generator.horizontal_vertical_entropy import (
    decompose_counts,
)
from trajectory_generator.information_clock_statistics import (
    information_clock_statistics,
)
from trajectory_generator.recurrent_macrograph import (
    derive_recurrent_structure,
)
from trajectory_generator.vertical_entropy_rate import (
    vertical_rate_bound,
)


CANDIDATES = {
    "robust_208": (1, 0, 0, 2),
    "balanced_221": (0, 2, 4, 4),
    "long_239": (3, 2, 4, 4),
}


VERTICAL_RATE_HORIZON = 384


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

        stats = information_clock_statistics(
            structure.branch_nodes,
            structure.macro_edges,
            growth_rate=structure.growth_rate,
        )

        core = core_adjacency(
            adjacency,
            structure.component,
        )
        counts = {
            node: 1
            for node in structure.component
        }
        for _ in range(VERTICAL_RATE_HORIZON):
            counts = step_counts(core, counts)

        decomposition = decompose_counts(counts)
        vertical = vertical_rate_bound(
            decomposition,
            time=VERTICAL_RATE_HORIZON,
            causal_state_count=len(
                structure.component
            ),
        )

        clock_identity = (
            abs(stats.identity_residual) < 1e-10
            and stats.maximum_row_probability_residual
            < 1e-10
            and stats.stationary_residual < 1e-10
        )

        vertical_convergence = (
            abs(
                vertical.vertical_rate
                - stats.bits_per_physical_step
            )
            < 5e-4
        )

        passed = (
            structure.growth_rate > 1.0
            and clock_identity
            and vertical_convergence
        )

        print(
            "INFORMATION_CLOCK_VERTICAL_RATE_GATE",
            "name", name,
            "PASS", passed,
            "core_nodes",
            len(structure.component),
            "branch_nodes",
            len(structure.branch_nodes),
            "macro_edges",
            len(structure.macro_edges),
            "lambda",
            f"{structure.growth_rate:.12f}",
            "log2_lambda",
            f"{stats.bits_per_physical_step:.12f}",
            "avg_physical_steps_per_event",
            f"{stats.average_physical_steps_per_event:.12f}",
            "bits_per_information_event",
            f"{stats.bits_per_information_event:.12f}",
            "events_per_physical_step",
            f"{stats.events_per_physical_step:.12f}",
            "event_entropy_times_event_rate",
            f"{stats.reconstructed_bits_per_physical_step:.12f}",
            "clock_identity_residual",
            f"{stats.identity_residual:.3e}",
            "vertical_rate_t384",
            f"{vertical.vertical_rate:.12f}",
            "vertical_vs_clock_error",
            f"{abs(vertical.vertical_rate - stats.bits_per_physical_step):.12f}",
        )

        if not passed:
            raise AssertionError(
                f"information-clock/vertical-rate equivalence failed for {name}"
            )


if __name__ == "__main__":
    main()

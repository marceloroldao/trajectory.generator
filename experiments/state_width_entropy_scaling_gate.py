"""Gate state-width frontier scaling against topological entropy.

For a positive-entropy finite public universe with dominant growth

    |A_n| ~ C * lambda^n,

the width-W exact-address frontier satisfies asymptotically

    n(W) / W -> 1 / log2(lambda).

Finite transients contribute an O(1) offset in n(W).  Dyadic frontier
increments cancel most of that offset:

    (n(W2)-n(W1)) / (W2-W1)
        -> 1 / log2(lambda).

This experiment checks the relation using exact whole-universe path counts and
the independently derived recurrent-core Perron spectral radius.
"""

from math import log2

from recurrent_orbit_core import graph
from topological_transition_state import initial_topology

from trajectory_generator.floquet_count_field import (
    FloquetCountFieldRecurrence,
)
from trajectory_generator.recurrent_macrograph import (
    derive_recurrent_structure,
)


CANDIDATES = {
    "robust": (1, 0, 0, 2),
    "balanced": (0, 2, 4, 4),
    "long": (3, 2, 4, 4),
}

WIDTHS = (63, 128, 256, 512)
SEED_BITS = 3


def initial_nodes():
    return tuple(
        (state, initial_topology(state), 0)
        for state in range(8)
    )


def transition_frontier(field, width):
    limit = 1 << width
    vector = field.initial_vector
    t = 0
    total = sum(vector)

    while True:
        nxt = field.step_vector(vector)
        next_total = sum(nxt)
        if next_total > limit:
            return t, total, next_total
        vector = nxt
        total = next_total
        t += 1


def main():
    for name, params in CANDIDATES.items():
        adjacency = graph(params)
        structure = derive_recurrent_structure(
            adjacency
        )
        entropy_rate = log2(
            structure.growth_rate
        )
        target_steps_per_bit = (
            1.0 / entropy_rate
        )

        field = FloquetCountFieldRecurrence(
            adjacency,
            start_nodes=initial_nodes(),
            phase_of=lambda node: node[2],
            period=3,
            base_phase=0,
            cache_rows=0,
        )

        frontiers = []
        ratios = []
        ratio_errors = []

        for width in WIDTHS:
            t, family, next_family = (
                transition_frontier(
                    field,
                    width,
                )
            )
            frontier = t + SEED_BITS
            frontiers.append(frontier)

            ratio = frontier / width
            relative_error = (
                abs(
                    ratio
                    - target_steps_per_bit
                )
                / target_steps_per_bit
            )
            ratios.append(ratio)
            ratio_errors.append(
                relative_error
            )

            print(
                "STATE_WIDTH_ENTROPY_POINT",
                "name", name,
                "width", width,
                "frontier", frontier,
                "frontier_family_bits",
                f"{log2(family):.12f}",
                "next_family_bits",
                f"{log2(next_family):.12f}",
                "frontier_steps_per_bit",
                f"{ratio:.12f}",
                "target_steps_per_bit",
                f"{target_steps_per_bit:.12f}",
                "relative_error",
                f"{relative_error:.12f}",
            )

        increment_slopes = []
        increment_errors = []
        for left, right in zip(
            range(len(WIDTHS) - 1),
            range(1, len(WIDTHS)),
        ):
            delta_width = (
                WIDTHS[right]
                - WIDTHS[left]
            )
            delta_frontier = (
                frontiers[right]
                - frontiers[left]
            )
            slope = (
                delta_frontier
                / delta_width
            )
            relative_error = (
                abs(
                    slope
                    - target_steps_per_bit
                )
                / target_steps_per_bit
            )
            increment_slopes.append(slope)
            increment_errors.append(
                relative_error
            )

        ratio_convergence = all(
            right < left
            for left, right in zip(
                ratio_errors,
                ratio_errors[1:],
            )
        )

        final_increment_error = (
            increment_errors[-1]
        )

        passed = (
            structure.growth_rate > 1.0
            and ratio_convergence
            and ratio_errors[-1] < 0.03
            and final_increment_error < 0.02
        )

        print(
            "STATE_WIDTH_ENTROPY_SCALING_GATE",
            "name", name,
            "PASS", passed,
            "lambda",
            f"{structure.growth_rate:.12f}",
            "log2_lambda",
            f"{entropy_rate:.12f}",
            "target_steps_per_bit",
            f"{target_steps_per_bit:.12f}",
            "widths", WIDTHS,
            "frontiers", tuple(frontiers),
            "frontier_ratios",
            tuple(
                f"{value:.9f}"
                for value in ratios
            ),
            "frontier_relative_errors",
            tuple(
                f"{value:.6e}"
                for value in ratio_errors
            ),
            "increment_slopes",
            tuple(
                f"{value:.9f}"
                for value in increment_slopes
            ),
            "increment_relative_errors",
            tuple(
                f"{value:.6e}"
                for value in increment_errors
            ),
            "final_increment_relative_error",
            f"{final_increment_error:.6e}",
            "interpretation",
            "state-width frontier slope converges to inverse topological entropy rate",
        )

        if not passed:
            raise AssertionError(
                f"state-width entropy scaling failed for {name}"
            )


if __name__ == "__main__":
    main()

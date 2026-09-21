"""Gate the stationary finite reversible-cover no-go on recurrent cores."""

from recurrent_orbit_core import graph

from trajectory_generator.recurrent_macrograph import (
    derive_recurrent_structure,
)
from trajectory_generator.stationary_reversible_cover_no_go import (
    maximum_fiber_demand,
    total_path_count,
)


CANDIDATES = {
    "robust_208": (1, 0, 0, 2),
    "balanced_221": (0, 2, 4, 4),
    "long_239": (3, 2, 4, 4),
}


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
    all_pass = True

    # Negative control: deterministic 3-cycle has lambda=1 and constant demand.
    deterministic = {
        0: (1,),
        1: (2,),
        2: (0,),
    }
    deterministic_max = [
        maximum_fiber_demand(
            deterministic,
            start_nodes=(0,),
            steps=t,
        )
        for t in range(12)
    ]
    deterministic_ok = (
        max(deterministic_max) == 1
    )

    print(
        "STATIONARY_COVER_CONTROL",
        "PASS", deterministic_ok,
        "max_demands", tuple(deterministic_max),
        "interpretation",
        "zero-entropy deterministic cycle admits fixed fiber demand",
    )

    all_pass = all_pass and deterministic_ok

    for name, params in CANDIDATES.items():
        adjacency = graph(params)
        structure = derive_recurrent_structure(
            adjacency
        )
        core = core_adjacency(
            adjacency,
            structure.component,
        )

        # Start from every recurrent node with one distinct initial history.
        starts = tuple(structure.component)

        totals = [
            total_path_count(
                core,
                start_nodes=starts,
                steps=t,
            )
            for t in range(0, 49)
        ]
        maxima = [
            maximum_fiber_demand(
                core,
                start_nodes=starts,
                steps=t,
            )
            for t in range(0, 49)
        ]

        positive_entropy = (
            structure.growth_rate > 1.0 + 1e-9
        )
        total_growth = totals[-1] > totals[0]
        fiber_growth = maxima[-1] > maxima[0]

        # If a fixed finite full-domain cover existed, its capacities would
        # bound these exact history multiplicities for every time. Continued
        # recurrent growth is the constructive witness of the obstruction.
        passed = (
            positive_entropy
            and total_growth
            and fiber_growth
        )
        all_pass = all_pass and passed

        print(
            "STATIONARY_REVERSIBLE_COVER_NO_GO",
            "name", name,
            "PASS", passed,
            "core_nodes", len(structure.component),
            "growth_rate",
            f"{structure.growth_rate:.12f}",
            "initial_total_paths", totals[0],
            "paths_t48", totals[-1],
            "initial_max_fiber", maxima[0],
            "max_fiber_t48", maxima[-1],
            "positive_entropy", positive_entropy,
            "fiber_demand_grows", fiber_growth,
            "conclusion",
            "no finite time-independent full-domain fiber vector can "
            "support exact reversible branching indefinitely",
        )

    print(
        "STATIONARY_REVERSIBLE_COVER_FULL_GATE",
        "PASS", all_pass,
        "structural_bound",
        "m >= A^T m impossible on irreducible lambda>1 core",
        "implication",
        "vertical capacity must grow with history entropy or the language "
        "must be restricted",
    )

    if not all_pass:
        raise AssertionError(
            "stationary reversible-cover no-go gate failed"
        )


if __name__ == "__main__":
    main()

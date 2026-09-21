"""Gate the gauge-invariance no-go theorem on generic and project fibers."""

from recurrent_orbit_core import graph
from topological_transition_state import initial_topology

from trajectory_generator.floquet_count_field import (
    FloquetCountFieldRecurrence,
)
from trajectory_generator.gauge_invariant_vertical_law import (
    certificate,
    center_by_transpositions,
    identity_permutation,
    theorem_holds_through,
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
    small_group_theorem = theorem_holds_through(6)

    for size in range(1, 7):
        cert = certificate(size)
        print(
            "SYMMETRIC_GROUP_CENTER",
            "size", size,
            "PASS",
            cert.center_size
            == cert.expected_center_size,
            "center_size", cert.center_size,
            "expected", cert.expected_center_size,
            "phase_reflection_central",
            cert.phase_reflection_is_central,
            "reflection_chart_witness",
            cert.phase_reflection_witness_exists,
        )

    project_ok = True

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
        active_sizes = [
            count
            for count in vector
            if count
        ]
        max_fiber = max(active_sizes)
        fibers_ge_3 = sum(
            1
            for size in active_sizes
            if size >= 3
        )

        # We do not enumerate S_n for frontier-sized n.  The exact group
        # theorem established above applies symbolically to every n>=3.
        applies = max_fiber >= 3 and fibers_ge_3 > 0
        project_ok = project_ok and applies

        print(
            "PROJECT_GAUGE_NO_GO",
            "name", name,
            "PASS", applies,
            "frontier", frontier,
            "active_fibers", len(active_sizes),
            "fibers_ge_3", fibers_ge_3,
            "max_fiber", max_fiber,
            "conclusion",
            "nontrivial numeric vertical permutation cannot be invariant "
            "under all internal fiber relabelings without extra structure",
        )

    passed = small_group_theorem and project_ok

    print(
        "GAUGE_INVARIANCE_NO_GO_FULL_GATE",
        "PASS", passed,
        "small_exact_group_gate", small_group_theorem,
        "project_frontiers_apply", project_ok,
        "intrinsic_object",
        "admissible-history natural extension",
        "numeric_vertical_law",
        "gauge representation unless extra fiber structure is declared",
    )

    if not passed:
        raise AssertionError(
            "gauge-invariance no-go gate failed"
        )


if __name__ == "__main__":
    main()

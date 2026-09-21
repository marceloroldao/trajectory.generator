"""Gate the natural-automorphism no-go theorem.

The theorem says that for the complete edge-labelled history extension with
singleton initial fibers, every base-fixing natural automorphism is identity.
"""

from trajectory_generator.history_naturality_no_go import (
    certificate,
)
from trajectory_generator.minimal_reversible_completion import (
    MinimalReversibleCompletion,
)


GRAPHS = {
    "merge": (
        {
            0: (1, 2),
            1: (0,),
            2: (0,),
        },
        (0,),
    ),
    "branch_merge": (
        {
            0: (1, 2),
            1: (0, 2),
            2: (0,),
        },
        (0,),
    ),
    "parallel": (
        {
            0: (1, 1),
            1: (0, 2),
            2: (0,),
        },
        (0,),
    ),
    "two_distinct_starts": (
        {
            0: (2,),
            1: (2,),
            2: (0, 1),
        },
        (0, 1),
    ),
}


def main():
    all_pass = True

    for name, (adjacency, starts) in GRAPHS.items():
        completion = MinimalReversibleCompletion(
            adjacency,
            start_nodes=starts,
        )
        cert = certificate(
            completion,
            horizon=7,
        )

        passed = (
            cert.singleton_initial_fibers
            and cert.identity_forced
            and cert.histories_checked
            == cert.forced_fixed_histories
        )
        all_pass = all_pass and passed

        print(
            "HISTORY_NATURALITY_NO_GO",
            "name", name,
            "PASS", passed,
            "horizon", cert.horizon,
            "singleton_initial_fibers",
            cert.singleton_initial_fibers,
            "histories_checked",
            cert.histories_checked,
            "forced_fixed_histories",
            cert.forced_fixed_histories,
            "identity_forced",
            cert.identity_forced,
        )

    # Negative-control boundary: if one base node begins with multiple histories,
    # a nontrivial permutation may already exist at t=0 and propagate naturally.
    duplicate_start = MinimalReversibleCompletion(
        {0: (0,)},
        start_nodes=(0, 0),
    )
    boundary = certificate(
        duplicate_start,
        horizon=4,
    )
    boundary_ok = (
        not boundary.singleton_initial_fibers
        and not boundary.identity_forced
    )

    print(
        "HISTORY_NATURALITY_BOUNDARY",
        "PASS", boundary_ok,
        "singleton_initial_fibers",
        boundary.singleton_initial_fibers,
        "identity_forced",
        boundary.identity_forced,
        "interpretation",
        "extra initial vertical multiplicity can support intrinsic natural "
        "automorphisms; bare singleton history extension cannot",
    )

    passed = all_pass and boundary_ok

    print(
        "HISTORY_NATURALITY_NO_GO_FULL_GATE",
        "PASS", passed,
        "conclusion",
        "with singleton initial fibers and fixed labelled causal edges, "
        "the only natural automorphism of the history extension is identity",
        "implication",
        "nontrivial vertical laws in current construction are gauge unless "
        "new native vertical structure/state is introduced",
    )

    if not passed:
        raise AssertionError(
            "history naturality no-go gate failed"
        )


if __name__ == "__main__":
    main()

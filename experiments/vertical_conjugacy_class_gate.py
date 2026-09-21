"""Gate gauge-invariant conjugacy classes of branch vertical actions."""

from recurrent_orbit_core import graph
from topological_transition_state import initial_topology

from trajectory_generator.scalar_partition_trajectory import (
    build_scalar_partition_translation_machine,
)
from trajectory_generator.vertical_conjugacy_class import (
    cycle_type,
    information_event_action_class,
    reflection_cycle_type,
    reflection_representative,
)
from trajectory_generator.gauge_invariant_vertical_law import (
    conjugate,
    transposition,
)


CANDIDATES = {
    "robust_208": (1, 0, 0, 2),
    "balanced_221": (0, 2, 4, 4),
    "long_239": (3, 2, 4, 4),
}


def initial_nodes():
    return tuple(
        (state, initial_topology(state), 0)
        for state in range(8)
    )


def main():
    # Exact small-fiber conjugacy checks.
    small_ok = True
    conjugacy_checks = 0

    for size in range(1, 10):
        representative = reflection_representative(
            size
        )
        expected = reflection_cycle_type(size)

        if cycle_type(representative) != expected:
            small_ok = False

        for i in range(size):
            for j in range(i + 1, size):
                gauge = transposition(size, i, j)
                transformed = conjugate(
                    representative,
                    gauge,
                )
                conjugacy_checks += 1
                if cycle_type(transformed) != expected:
                    small_ok = False

    project_ok = True

    for name, params in CANDIDATES.items():
        machine = build_scalar_partition_translation_machine(
            graph(params),
            start_nodes=initial_nodes(),
            phase_of=lambda node: node[2],
            period=3,
            base_phase=0,
            width=63,
            seed_cache_entries=256,
        )

        branch_actions = 0
        nontrivial_branch_classes = 0
        deterministic_actions = 0
        deterministic_identity_classes = 0

        # Early horizons are enough to observe fibers grow beyond singleton
        # while checking both entropy-bearing and deterministic source states.
        for time in range(24):
            phase = (
                machine.field.base_phase + time
            ) % machine.field.period

            for node in machine.nodes:
                if (
                    machine.field.phase_of(node)
                    % machine.field.period
                    != phase
                ):
                    continue

                size = machine.endpoint_count(
                    node,
                    time,
                )
                if size <= 0:
                    continue

                is_branch = (
                    len(machine.codec.outgoing[node]) > 1
                )
                action = information_event_action_class(
                    fiber_size=size,
                    is_branch=is_branch,
                )

                for _edge in machine.codec.outgoing[node]:
                    if is_branch:
                        branch_actions += 1
                        if action.nontrivial:
                            nontrivial_branch_classes += 1
                    else:
                        deterministic_actions += 1
                        if not action.nontrivial:
                            deterministic_identity_classes += 1

        passed = (
            branch_actions > 0
            and nontrivial_branch_classes > 0
            and deterministic_actions > 0
            and deterministic_identity_classes
            == deterministic_actions
        )
        project_ok = project_ok and passed

        print(
            "VERTICAL_CONJUGACY_CLASS_GATE",
            "name", name,
            "PASS", passed,
            "branch_actions", branch_actions,
            "nontrivial_branch_classes",
            nontrivial_branch_classes,
            "deterministic_actions",
            deterministic_actions,
            "deterministic_identity_classes",
            deterministic_identity_classes,
            "intrinsic_branch_signature",
            "reflection involution cycle type",
            "chart_representative",
            "y -> -y mod n",
        )

    passed = small_ok and project_ok

    print(
        "VERTICAL_CONJUGACY_CLASS_FULL_GATE",
        "PASS", passed,
        "small_conjugacy_checks", conjugacy_checks,
        "small_cycle_type_invariant", small_ok,
        "project_event_classes", project_ok,
        "conclusion",
        "specific vertical permutation is gauge; conjugacy class is invariant",
    )

    if not passed:
        raise AssertionError(
            "vertical conjugacy class gate failed"
        )


if __name__ == "__main__":
    main()

"""Gate gauge-covariant maximal-pairing dynamics at information events."""

from math import factorial

from recurrent_orbit_core import graph
from topological_transition_state import (
    initial_topology,
    make_codec as make_legacy_codec,
)

from trajectory_generator.canonical_vertical_state_machine import (
    CanonicalVerticalStateMachine,
)
from trajectory_generator.gauge_covariant_vertical_event import (
    build_maximal_pairing_branch_lift,
    cycle_type,
    derive_maximal_pairing_cycle_type,
    fixed_point_count,
    maximal_pairing_cycle_type,
    maximal_pairing_involutions,
    reversal_involution,
)
from trajectory_generator.scalar_partition_trajectory import (
    build_scalar_partition_translation_machine,
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


def build_machine(params):
    adjacency = graph(params)
    partition = build_scalar_partition_translation_machine(
        adjacency,
        start_nodes=initial_nodes(),
        phase_of=lambda node: node[2],
        period=3,
        base_phase=0,
        width=63,
        seed_cache_entries=512,
    )
    return CanonicalVerticalStateMachine(
        partition,
        seed_bits=3,
        seed_to_start_node={
            state: (
                state,
                initial_topology(state),
                0,
            )
            for state in range(8)
        },
        edge_symbol=lambda edge: edge.target[0] & 1,
        lift_builder=build_maximal_pairing_branch_lift,
    )


def small_group_gate():
    ok = True
    rows = []

    for size in range(1, 7):
        representative = reversal_involution(size)
        members = maximal_pairing_involutions(size)
        types = {
            cycle_type(value)
            for value in members
        }

        expected_type = maximal_pairing_cycle_type(
            size
        )
        derived_type = derive_maximal_pairing_cycle_type(
            size
        )
        passed = (
            derived_type == expected_type
            and
            fixed_point_count(representative)
            == size % 2
            and cycle_type(representative)
            == expected_type
            and types == {expected_type}
        )
        ok = ok and passed

        rows.append(
            (
                size,
                passed,
                len(members),
                expected_type,
                fixed_point_count(representative),
            )
        )

        print(
            "MAXIMAL_PAIRING_CLASS",
            "size", size,
            "PASS", passed,
            "class_members", len(members),
            "cycle_type", expected_type,
            "axiomatically_derived", derived_type,
            "fixed_points",
            fixed_point_count(representative),
        )

    return ok, rows


def candidate_gate(name, params, frontier):
    machine = build_machine(params)
    lift = machine.lift
    total, legacy_unrank, legacy_validate = make_legacy_codec(
        params
    )

    structural = True
    branch_edges = 0
    deterministic_edges = 0

    for edge in lift.machine.codec.edges:
        is_branch = lift.is_information_event(edge)
        if is_branch:
            branch_edges += 1
        else:
            deterministic_edges += 1

        # Representative class is checked whenever source fiber is non-empty in
        # the small operational window below.

    exhaustive = True
    checked = 0
    changed_small = 0

    for steps in range(12):
        family = total(steps)
        seen = set()

        for rank in range(family):
            bits = legacy_unrank(rank, steps)
            state, got_steps = machine.encode(bits)

            if (
                got_steps != steps
                or state in seen
                or machine.decode(state, steps) != bits
            ):
                exhaustive = False
                break

            if state != rank:
                changed_small += 1

            seen.add(state)
            checked += 1

        if not exhaustive or len(seen) != family:
            exhaustive = False
            break

    class_checks = 0
    class_ok = True
    deterministic_identity = True
    branch_nontrivial = 0

    for time in range(18):
        for node, size in lift.active_fibers(time):
            for edge in lift.machine.codec.outgoing[node]:
                drive = lift.drive(edge, time)
                perm = tuple(
                    lift.permute_local(
                        y,
                        size,
                        drive,
                    )
                    for y in range(size)
                )
                class_checks += 1

                if lift.is_information_event(edge):
                    if (
                        cycle_type(perm)
                        != maximal_pairing_cycle_type(size)
                    ):
                        class_ok = False
                    if any(
                        perm[y] != y
                        for y in range(size)
                    ):
                        branch_nontrivial += 1
                else:
                    if perm != tuple(range(size)):
                        deterministic_identity = False

    family = total(frontier)
    samples = {
        0,
        family // 4,
        family // 2,
        (3 * family) // 4,
        family - 1,
    }

    frontier_ok = True
    changed_frontier = 0

    for final_state in sorted(samples):
        bits = machine.decode(
            final_state,
            frontier,
        )

        if (
            len(bits) != frontier
            or not legacy_validate(bits)
        ):
            frontier_ok = False
            break

        rebuilt, rebuilt_steps = machine.encode(
            bits
        )
        if (
            rebuilt != final_state
            or rebuilt_steps != frontier
        ):
            frontier_ok = False
            break

        if bits != legacy_unrank(
            final_state,
            frontier,
        ):
            changed_frontier += 1

    passed = (
        structural
        and branch_edges > 0
        and deterministic_edges > 0
        and exhaustive
        and class_ok
        and deterministic_identity
        and branch_nontrivial > 0
        and frontier_ok
        and changed_small > 0
        and changed_frontier > 0
    )

    print(
        "GAUGE_COVARIANT_EVENT_GATE",
        "name", name,
        "PASS", passed,
        "frontier", frontier,
        "frontier_family", family,
        "branch_public_edges", branch_edges,
        "deterministic_public_edges",
        deterministic_edges,
        "class_checks", class_checks,
        "maximal_pairing_class", class_ok,
        "deterministic_identity",
        deterministic_identity,
        "nontrivial_branch_classes",
        branch_nontrivial,
        "small_addresses_checked", checked,
        "small_mapping_changes", changed_small,
        "frontier_mapping_changes", changed_frontier,
        "exhaustive_roundtrip", exhaustive,
        "frontier_roundtrip", frontier_ok,
    )

    return passed


def main():
    group_ok, _ = small_group_gate()

    results = [
        candidate_gate(name, params, frontier)
        for name, (params, frontier)
        in CANDIDATES.items()
    ]

    passed = group_ok and all(results)

    print(
        "GAUGE_COVARIANT_EVENT_FULL_GATE",
        "PASS", passed,
        "coordinate_free_event",
        "causal branch / information event",
        "coordinate_free_action",
        "maximal-pairing involution conjugacy class",
        "chart_representative",
        "reversal y -> n-1-y",
        "conclusion",
        "nontrivial vertical dynamics can be gauge-covariant "
        "as a conjugacy class without violating the no-go theorem",
    )

    if not passed:
        raise AssertionError(
            "gauge-covariant event gate failed"
        )


if __name__ == "__main__":
    main()

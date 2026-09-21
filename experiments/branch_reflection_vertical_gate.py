"""Gate information-event-driven vertical reflection on topological universes."""

from recurrent_orbit_core import graph
from topological_transition_state import (
    initial_topology,
    make_codec as make_legacy_codec,
)

from trajectory_generator.branch_reflection_vertical_dynamics import (
    build_branch_reflection_lift,
)
from trajectory_generator.canonical_vertical_state_machine import (
    CanonicalVerticalStateMachine,
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
        lift_builder=build_branch_reflection_lift,
    )


def main():
    for name, (params, frontier) in CANDIDATES.items():
        machine = build_machine(params)
        lift = machine.lift
        total, legacy_unrank, legacy_validate = make_legacy_codec(
            params
        )

        # Structural law check across every public edge.
        law_exact = True
        branch_public_edges = 0
        deterministic_public_edges = 0

        for edge in lift.machine.codec.edges:
            is_branch = (
                len(
                    lift.machine.codec.outgoing[
                        edge.source
                    ]
                ) > 1
            )
            drive = lift.drive(edge, 0)

            if is_branch:
                branch_public_edges += 1
            else:
                deterministic_public_edges += 1

            expected = -1 if is_branch else 1
            if (
                drive.orientation != expected
                or drive.shift_seed != 0
            ):
                law_exact = False
                break

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

            rebuilt, rebuilt_steps = machine.encode(bits)
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

        # Count actual nontrivial vertical actions at early horizons.
        nontrivial_actions = 0
        identity_deterministic_actions = True
        checked_lifted_edges = 0

        for time in range(18):
            for packed in range(lift.total_states(time)):
                state = lift.from_packed(
                    packed,
                    time,
                )
                for edge in lift.machine.codec.outgoing[
                    state.node
                ]:
                    checked_lifted_edges += 1
                    size = lift.fiber_size(
                        state.node,
                        time,
                    )
                    drive = lift.drive(edge, time)
                    mapped = lift.permute_local(
                        state.vertical,
                        size,
                        drive,
                    )

                    if drive.orientation == 1:
                        if mapped != state.vertical:
                            identity_deterministic_actions = False
                    elif mapped != state.vertical:
                        nontrivial_actions += 1

        passed = (
            law_exact
            and branch_public_edges > 0
            and deterministic_public_edges > 0
            and exhaustive
            and frontier_ok
            and changed_small > 0
            and changed_frontier > 0
            and nontrivial_actions > 0
            and identity_deterministic_actions
        )

        print(
            "BRANCH_REFLECTION_VERTICAL_GATE",
            "name", name,
            "PASS", passed,
            "frontier", frontier,
            "frontier_family", family,
            "branch_public_edges", branch_public_edges,
            "deterministic_public_edges",
            deterministic_public_edges,
            "law_exact", law_exact,
            "checked_small_addresses", checked,
            "small_mapping_changes", changed_small,
            "frontier_mapping_changes", changed_frontier,
            "checked_lifted_edges", checked_lifted_edges,
            "nontrivial_branch_actions",
            nontrivial_actions,
            "deterministic_actions_identity",
            identity_deterministic_actions,
            "exhaustive_roundtrip", exhaustive,
            "frontier_roundtrip", frontier_ok,
            "decode_inputs",
            "(final_state,steps)+public_law_only",
        )

        if not passed:
            raise AssertionError(
                f"branch-reflection gate failed for {name}"
            )


if __name__ == "__main__":
    main()

"""Search the smallest coefficient-free canonical vertical law."""

from recurrent_orbit_core import graph
from topological_transition_state import (
    initial_topology,
    counts as historical_counts,
)

from trajectory_generator.canonical_vertical_law import (
    CanonicalPeriodicVerticalLift,
    canonical_law_specs,
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
    return build_scalar_partition_translation_machine(
        adjacency,
        start_nodes=initial_nodes(),
        phase_of=lambda node: node[2],
        period=3,
        base_phase=0,
        width=63,
        seed_cache_entries=512,
    )


def activity(lift, horizon=18):
    flips = 0
    nonzero_rotations = 0
    nontrivial_maps = 0
    checked = 0

    for time in range(horizon):
        for node, size in lift.active_fibers(time):
            if size <= 0:
                continue
            for edge in lift.machine.codec.outgoing[node]:
                drive = lift.drive(edge, time)
                checked += 1

                if drive.orientation == -1:
                    flips += 1
                if drive.shift_seed % size:
                    nonzero_rotations += 1

                probes = {0, size - 1, size // 2}
                if any(
                    lift.permute_local(
                        y,
                        size,
                        drive,
                    ) != y
                    for y in probes
                ):
                    nontrivial_maps += 1

    return {
        "flips": flips,
        "nonzero_rotations": nonzero_rotations,
        "nontrivial_maps": nontrivial_maps,
        "checked": checked,
    }


def law_is_active_for_all(spec, machines):
    stats = {}
    for name, machine in machines.items():
        lift = CanonicalPeriodicVerticalLift(
            machine,
            spec,
        )
        row = activity(lift)
        stats[name] = row

        # Require genuine orientation and rotation activity, plus a nontrivial
        # map. This rejects passive-rank transport and reflection-only laws.
        if (
            row["flips"] == 0
            or row["nonzero_rotations"] == 0
            or row["nontrivial_maps"] == 0
        ):
            return False, stats

    return True, stats


def full_gate(name, params, frontier, machine, spec):
    lift = CanonicalPeriodicVerticalLift(
        machine,
        spec,
    )

    transition_frontier = frontier - 3
    expected = historical_counts(
        params,
        max_steps=frontier,
    )[frontier]
    total = lift.total_states(transition_frontier)

    periodic = all(
        lift.drive_is_periodic(edge, time)
        for edge in lift.machine.codec.edges
        for time in range(2 * lift.vertical_period)
    )

    reversible = True
    projection = True
    checked_edges = 0

    for time in range(15):
        for packed in range(lift.total_states(time)):
            state = lift.from_packed(packed, time)
            for edge in lift.machine.codec.outgoing[state.node]:
                checked_edges += 1
                nxt = lift.advance(
                    state,
                    time,
                    edge.label,
                )
                if lift.project(nxt) != edge.target:
                    projection = False
                    break
                previous, recovered = lift.rewind(
                    nxt,
                    time + 1,
                )
                if previous != state or recovered != edge:
                    reversible = False
                    break
            if not reversible or not projection:
                break
        if not reversible or not projection:
            break

    # Verify complete predecessor sub-fiber partition at the frontier.
    partition = True
    previous_time = transition_frontier - 1
    for target, target_size in lift.active_fibers(
        transition_frontier
    ):
        blocks = []
        for edge in lift.machine.codec.incoming[target]:
            start, end = lift.edge_image_interval(
                edge,
                previous_time,
            )
            if end > start:
                blocks.append((start, end))
        blocks.sort()

        if (
            not blocks
            or blocks[0][0] != 0
            or blocks[-1][1] != target_size
        ):
            partition = False
            break

        if any(
            left[1] != right[0]
            for left, right in zip(blocks, blocks[1:])
        ):
            partition = False
            break

    samples = {
        0,
        total // 4,
        total // 2,
        (3 * total) // 4,
        total - 1,
    }
    frontier_roundtrip = True

    for packed_final in sorted(samples):
        current = lift.from_packed(
            packed_final,
            transition_frontier,
        )
        time = transition_frontier
        reverse_edges = []

        while time > 0:
            current, edge = lift.rewind(
                current,
                time,
            )
            reverse_edges.append(edge)
            time -= 1

        rebuilt = current
        time = 0
        for edge in reversed(reverse_edges):
            rebuilt = lift.advance(
                rebuilt,
                time,
                edge.label,
            )
            time += 1

        if (
            lift.to_packed(
                rebuilt,
                transition_frontier,
            )
            != packed_final
        ):
            frontier_roundtrip = False
            break

    row = activity(lift)

    passed = (
        total == expected
        and periodic
        and reversible
        and projection
        and partition
        and frontier_roundtrip
        and row["flips"] > 0
        and row["nonzero_rotations"] > 0
        and row["nontrivial_maps"] > 0
    )

    print(
        "CANONICAL_VERTICAL_GATE",
        "name", name,
        "PASS", passed,
        "frontier", frontier,
        "period_multiple", spec.period_multiple,
        "vertical_period", lift.vertical_period,
        "orientation_features",
        spec.orientation_features,
        "shift_features",
        spec.shift_features,
        "frontier_states", total,
        "periodic", periodic,
        "reversible", reversible,
        "causal_projection", projection,
        "frontier_partition", partition,
        "frontier_roundtrip", frontier_roundtrip,
        "activity_flips", row["flips"],
        "activity_nonzero_rotations",
        row["nonzero_rotations"],
        "activity_nontrivial_maps",
        row["nontrivial_maps"],
        "checked_early_edges", checked_edges,
    )
    return passed


def main():
    machines = {
        name: build_machine(params)
        for name, (params, _) in CANDIDATES.items()
    }

    selected = None
    selected_stats = None
    checked_specs = 0

    for spec in canonical_law_specs():
        checked_specs += 1
        ok, stats = law_is_active_for_all(
            spec,
            machines,
        )
        if ok:
            selected = spec
            selected_stats = stats
            break

    if selected is None:
        raise AssertionError(
            "no active coefficient-free canonical law found"
        )

    print(
        "CANONICAL_VERTICAL_SEARCH",
        "PASS", True,
        "checked_specs", checked_specs,
        "period_multiple", selected.period_multiple,
        "orientation_features",
        selected.orientation_features,
        "shift_features",
        selected.shift_features,
        "term_count", selected.term_count,
        "description_cost", selected.description_cost,
        "activity", selected_stats,
    )

    all_pass = True
    for name, (params, frontier) in CANDIDATES.items():
        if not full_gate(
            name,
            params,
            frontier,
            machines[name],
            selected,
        ):
            all_pass = False

    print(
        "CANONICAL_VERTICAL_FULL_GATE",
        "PASS", all_pass,
        "selected", selected,
    )

    if not all_pass:
        raise AssertionError(
            "selected canonical vertical law failed full gate"
        )


if __name__ == "__main__":
    main()

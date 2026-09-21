"""Gate periodic endogenous vertical dynamics on full topological universes."""

from recurrent_orbit_core import graph
from topological_transition_state import (
    initial_topology,
    counts as historical_counts,
)

from trajectory_generator.endogenous_vertical_dynamics import (
    EndogenousPeriodicVerticalLift,
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


def build_lift(params):
    adjacency = graph(params)
    machine = build_scalar_partition_translation_machine(
        adjacency,
        start_nodes=initial_nodes(),
        phase_of=lambda node: node[2],
        period=3,
        base_phase=0,
        width=63,
        seed_cache_entries=512,
    )
    return EndogenousPeriodicVerticalLift(machine)


def main():
    for name, (params, frontier) in CANDIDATES.items():
        lift = build_lift(params)
        transition_frontier = frontier - 3

        expected = historical_counts(
            params,
            max_steps=frontier,
        )[frontier]
        frontier_size = lift.total_states(
            transition_frontier
        )
        count_identity = frontier_size == expected

        periodic = True
        checked_drives = 0
        orientation_flips = 0

        for edge in lift.machine.codec.edges:
            for time in range(
                2 * lift.vertical_period
            ):
                checked_drives += 1
                drive = lift.drive(edge, time)
                if drive.orientation == -1:
                    orientation_flips += 1
                if not lift.drive_is_periodic(edge, time):
                    periodic = False
                    break
            if not periodic:
                break

        # Exhaustive early-horizon gate over every lifted state and every
        # admissible public outgoing edge.
        reversible = True
        projection = True
        nontrivial_maps = 0
        checked_edges = 0

        for time in range(15):
            total = lift.total_states(time)
            for packed in range(total):
                state = lift.from_packed(
                    packed,
                    time,
                )
                for edge in lift.machine.codec.outgoing[
                    state.node
                ]:
                    checked_edges += 1

                    drive = lift.drive(edge, time)
                    source_size = lift.fiber_size(
                        state.node,
                        time,
                    )
                    if source_size > 1:
                        mapped = lift.permute_local(
                            state.vertical,
                            source_size,
                            drive,
                        )
                        if mapped != state.vertical:
                            nontrivial_maps += 1

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

        # Frontier partition: every target fiber is exactly the disjoint union
        # of its incoming edge-image intervals.  The endogenous permutation acts
        # inside each interval and therefore cannot destroy horizontal causal
        # projection or injectivity.
        frontier_partition = True
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

            if not blocks:
                frontier_partition = False
                break

            blocks.sort()
            if blocks[0][0] != 0:
                frontier_partition = False
                break

            for left, right in zip(
                blocks,
                blocks[1:],
            ):
                if left[1] != right[0]:
                    frontier_partition = False
                    break
            if not frontier_partition:
                break

            if blocks[-1][1] != target_size:
                frontier_partition = False
                break

        # Strong full-frontier sample: begin from arbitrary packed lifted states,
        # reverse all the way to t=0, then replay the recovered edge sequence.
        samples = {
            0,
            frontier_size // 4,
            frontier_size // 2,
            (3 * frontier_size) // 4,
            frontier_size - 1,
        }
        frontier_roundtrip = True

        for packed_final in sorted(samples):
            current = lift.from_packed(
                packed_final,
                transition_frontier,
            )
            time = transition_frontier
            reversed_edges = []

            while time > 0:
                current, edge = lift.rewind(
                    current,
                    time,
                )
                reversed_edges.append(edge)
                time -= 1

            rebuilt = current
            time = 0
            for edge in reversed(reversed_edges):
                rebuilt = lift.advance(
                    rebuilt,
                    time,
                    edge.label,
                )
                time += 1

            if (
                time != transition_frontier
                or lift.to_packed(
                    rebuilt,
                    transition_frontier,
                )
                != packed_final
            ):
                frontier_roundtrip = False
                break

        print(
            "ENDOGENOUS_PERIODIC_VERTICAL_GATE",
            "name", name,
            "PASS",
            count_identity
            and periodic
            and reversible
            and projection
            and frontier_partition
            and frontier_roundtrip
            and nontrivial_maps > 0
            and orientation_flips > 0,
            "frontier", frontier,
            "vertical_period", lift.vertical_period,
            "causal_period", lift.causal_period,
            "frontier_states", frontier_size,
            "count_identity", count_identity,
            "drive_periodic", periodic,
            "checked_drives", checked_drives,
            "orientation_flips", orientation_flips,
            "nontrivial_vertical_maps", nontrivial_maps,
            "checked_early_lifted_edges", checked_edges,
            "reversible", reversible,
            "causal_projection", projection,
            "frontier_partition", frontier_partition,
            "frontier_samples", len(samples),
            "frontier_roundtrip", frontier_roundtrip,
        )


if __name__ == "__main__":
    main()

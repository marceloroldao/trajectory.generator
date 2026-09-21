"""Gate direct horizontal/vertical connection against packed scalar chart."""

from recurrent_orbit_core import graph
from topological_transition_state import (
    initial_topology,
    make_codec as make_legacy_codec,
)

from trajectory_generator.exact_vertical_connection import (
    ExactVerticalConnection,
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


def build(params):
    machine = build_scalar_partition_translation_machine(
        graph(params),
        start_nodes=initial_nodes(),
        phase_of=lambda node: node[2],
        period=3,
        base_phase=0,
        width=63,
        seed_cache_entries=512,
    )
    return machine, ExactVerticalConnection(machine)


def main():
    for name, (params, frontier) in CANDIDATES.items():
        total, _, _ = make_legacy_codec(params)
        machine, connection = build(params)

        exhaustive = True
        local_steps_checked = 0
        partitions_checked = 0

        for time in range(10):
            family = total(time + 3)
            # Scalar machine time excludes the 3-bit bootstrap.
            transition_time = time
            expected_family = machine.oracle.total_count(
                transition_time
            )
            if expected_family != family:
                exhaustive = False
                break

            for packed in range(expected_family):
                local = connection.unpack(
                    packed,
                    transition_time,
                )
                if connection.pack(local) != packed:
                    exhaustive = False
                    break

                for edge in machine.codec.outgoing[
                    local.node
                ]:
                    nxt = connection.forward(
                        local,
                        edge.label,
                    )
                    packed_nxt = machine.forward_step(
                        packed,
                        transition_time,
                        edge.label,
                    )
                    if connection.pack(nxt) != packed_nxt:
                        exhaustive = False
                        break

                    prev, recovered = connection.reverse(
                        nxt
                    )
                    if (
                        prev != local
                        or recovered != edge
                    ):
                        exhaustive = False
                        break
                    local_steps_checked += 1

                if not exhaustive:
                    break

            if not exhaustive:
                break

            next_time = transition_time + 1
            phase = (
                machine.field.base_phase + next_time
            ) % machine.field.period
            for target in machine.nodes:
                if (
                    machine.field.phase_of(target)
                    % machine.field.period
                    != phase
                ):
                    continue
                if machine.endpoint_count(
                    target,
                    next_time,
                ) <= 0:
                    continue
                partitions_checked += 1
                if not connection.partition_is_exact(
                    target,
                    next_time,
                ):
                    exhaustive = False
                    break

            if not exhaustive:
                break

        transition_frontier = frontier - 3
        family = machine.oracle.total_count(
            transition_frontier
        )
        samples = sorted({
            0,
            family // 4,
            family // 2,
            (3 * family) // 4,
            family - 1,
        })

        frontier_ok = True
        frontier_edges_reversed = 0

        for packed in samples:
            local = connection.unpack(
                packed,
                transition_frontier,
            )
            if connection.pack(local) != packed:
                frontier_ok = False
                break

            origin, edges = connection.decode_edges(
                local
            )
            rebuilt = origin
            for edge in edges:
                rebuilt = connection.forward(
                    rebuilt,
                    edge.label,
                )
            if (
                rebuilt != local
                or connection.pack(rebuilt) != packed
            ):
                frontier_ok = False
                break

            frontier_edges_reversed += len(edges)

        passed = (
            exhaustive
            and frontier_ok
            and local_steps_checked > 0
            and partitions_checked > 0
            and frontier_edges_reversed
            == len(samples) * transition_frontier
        )

        print(
            "EXACT_VERTICAL_CONNECTION_GATE",
            "name", name,
            "PASS", passed,
            "frontier", frontier,
            "transition_frontier",
            transition_frontier,
            "frontier_family", family,
            "small_local_steps_checked",
            local_steps_checked,
            "partitions_checked",
            partitions_checked,
            "frontier_samples",
            len(samples),
            "frontier_edges_reversed",
            frontier_edges_reversed,
            "packed_state_used_as_dynamics",
            False,
            "interpretation",
            "packed final_state is a chart over direct horizontal plus vertical fiber dynamics",
        )

        if not passed:
            raise AssertionError(
                f"exact vertical connection failed for {name}"
            )


if __name__ == "__main__":
    main()

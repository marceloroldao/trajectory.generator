"""Gate affine translation dynamics of the full-universe address."""

from recurrent_orbit_core import graph
from topological_transition_state import initial_topology

from trajectory_generator.floquet_path_trajectory import (
    build_floquet_path_codec,
)
from trajectory_generator.translation_address_trajectory import (
    TranslationAddressMachine,
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


def sequence_obeys_recurrence(values, coefficients):
    order = len(coefficients)
    for n in range(order, len(values)):
        expected = sum(
            coefficients[i] * values[n - order + i]
            for i in range(order)
        )
        if values[n] != expected:
            return False
    return True


def main():
    for name, (params, trajectory_frontier) in CANDIDATES.items():
        adjacency = graph(params)
        codec = build_floquet_path_codec(
            adjacency,
            start_nodes=initial_nodes(),
            phase_of=lambda node: node[2],
            period=3,
            base_phase=0,
            width=63,
            cache_rows=1,
        )
        machine = TranslationAddressMachine(codec)
        field = codec.count_field
        coefficients = field.coefficients

        transition_frontier = trajectory_frontier - 3

        # Every reachable physical edge has one public translation sequence,
        # sampled at the edge source phase every three physical steps.
        delta_recurrence_ok = True
        checked_edges = 0
        for edge in codec.edges:
            phase = edge.source[2]
            values = []
            for q in range(field.order + 24):
                t = phase + 3 * q
                values.append(
                    machine.translation(edge.label, t)
                )

            checked_edges += 1
            if not sequence_obeys_recurrence(
                values,
                coefficients,
            ):
                delta_recurrence_ok = False
                break

        # Full-frontier representative addresses must regenerate exactly the
        # same path under affine translation reverse and rank-block reverse.
        total = codec.total_count(transition_frontier)
        samples = {0, total // 2, total - 1}
        path_identity = True
        for state in sorted(samples):
            translated_path = machine.reconstruct_physical_path(
                state,
                transition_frontier,
            )
            reference_path = codec.reconstruct_physical_path(
                state,
                transition_frontier,
            )
            if translated_path != reference_path:
                path_identity = False
                break

        # Rank-independence on representative populated source buckets.
        rank_independent = True
        checked_rank_pairs = 0
        max_t = min(transition_frontier, 48)
        for t in range(max_t + 1):
            vector = field.vector_at(t)
            for edge in codec.edges:
                count = vector[
                    field.node_index[edge.source]
                ]
                if count < 2:
                    continue

                source_offset = machine._node_offset_from_vector(
                    edge.source,
                    vector,
                )
                first = source_offset
                last = source_offset + count - 1

                first_next = machine.forward_step(
                    first,
                    t,
                    edge.label,
                )
                last_next = machine.forward_step(
                    last,
                    t,
                    edge.label,
                )
                checked_rank_pairs += 1

                if (
                    first_next - first
                    != last_next - last
                ):
                    rank_independent = False
                    break
            if not rank_independent:
                break

        print(
            "TRANSLATION_ADDRESS_GATE",
            "name", name,
            "PASS",
            delta_recurrence_ok
            and path_identity
            and rank_independent,
            "checked_edges", checked_edges,
            "checked_rank_pairs", checked_rank_pairs,
            "floquet_order", field.order,
            "delta_recurrence", delta_recurrence_ok,
            "rank_independent", rank_independent,
            "path_identity", path_identity,
            "trajectory_frontier", trajectory_frontier,
        )


if __name__ == "__main__":
    main()

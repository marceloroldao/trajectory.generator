"""Gate functorial cyclic-group compatibility of topological history fibers."""

from recurrent_orbit_core import graph
from topological_transition_state import initial_topology

from trajectory_generator.cyclic_fiber_functor import (
    cyclic_injection_homomorphism_exists,
)
from trajectory_generator.scalar_partition_trajectory import (
    build_scalar_partition_translation_machine,
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
    any_obstruction = False

    for name, params in CANDIDATES.items():
        machine = build_scalar_partition_translation_machine(
            graph(params),
            start_nodes=initial_nodes(),
            phase_of=lambda node: node[2],
            period=3,
            base_phase=0,
            width=63,
            seed_cache_entries=512,
        )

        checked = 0
        compatible = 0
        obstructions = 0
        first = None

        # A modest horizon is sufficient for an impossibility certificate.
        # We count each public edge with a nonempty source fiber.
        for time in range(36):
            for node in machine.nodes:
                source_size = machine.endpoint_count(
                    node,
                    time,
                )
                if source_size <= 0:
                    continue

                for edge in machine.codec.outgoing[node]:
                    target_size = machine.endpoint_count(
                        edge.target,
                        time + 1,
                    )
                    if target_size <= 0:
                        raise AssertionError(
                            "reachable edge landed in empty target fiber"
                        )

                    checked += 1
                    if cyclic_injection_homomorphism_exists(
                        source_size,
                        target_size,
                    ):
                        compatible += 1
                    else:
                        obstructions += 1
                        if first is None:
                            first = (
                                time,
                                edge.label,
                                edge.source,
                                edge.target,
                                source_size,
                                target_size,
                            )

        has_obstruction = obstructions > 0
        any_obstruction = (
            any_obstruction or has_obstruction
        )

        print(
            "CYCLIC_FIBER_FUNCTOR_GATE",
            "name", name,
            "PASS", has_obstruction,
            "edges_checked", checked,
            "cyclic_homomorphic_edges", compatible,
            "divisibility_obstructions", obstructions,
            "first_obstruction", first,
            "conclusion",
            "per-fiber Z_n may be a gauge structure, but current causal "
            "edge injections cannot all be cyclic-group homomorphisms",
        )

    print(
        "CYCLIC_FIBER_FUNCTOR_FULL_GATE",
        "PASS", any_obstruction,
        "strong_claim_rejected",
        "current history fibers form a Z_n group functor under every causal edge",
        "conditional_result_preserved",
        "inversion is natural if a cyclic structure is separately declared",
    )

    if not any_obstruction:
        raise AssertionError(
            "no cyclic-functor divisibility obstruction found"
        )


if __name__ == "__main__":
    main()

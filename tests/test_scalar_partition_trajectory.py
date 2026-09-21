import unittest

from trajectory_generator.floquet_path_trajectory import (
    build_floquet_path_codec,
)
from trajectory_generator.scalar_partition_trajectory import (
    build_scalar_partition_translation_machine,
)


def phase_graph():
    return {
        ("a", 0): [("a", 1), ("b", 1)],
        ("b", 0): [("a", 1)],
        ("a", 1): [("a", 2)],
        ("b", 1): [("a", 2), ("b", 2)],
        ("a", 2): [("a", 0), ("b", 0)],
        ("b", 2): [("a", 0)],
    }


class ScalarPartitionTrajectoryTests(unittest.TestCase):
    def test_scalar_decoder_never_needs_full_vector_at(self):
        graph = phase_graph()
        machine = build_scalar_partition_translation_machine(
            graph,
            start_nodes=(("a", 0),),
            phase_of=lambda node: node[1],
            period=3,
            width=32,
            seed_cache_entries=8,
        )
        codec = machine.codec

        reference = build_floquet_path_codec(
            graph,
            start_nodes=(("a", 0),),
            phase_of=lambda node: node[1],
            period=3,
            width=32,
            cache_rows=0,
        )

        # Prohibit the target-time full-vector API after construction.
        def forbidden(*args, **kwargs):
            raise AssertionError(
                "full count-vector reconstruction was requested"
            )

        machine.field.vector_at = forbidden

        for steps in range(12):
            for state in range(reference.total_count(steps)):
                scalar_path = machine.reconstruct_physical_path(
                    state,
                    steps,
                )
                reference_path = reference.reconstruct_physical_path(
                    state,
                    steps,
                )
                self.assertEqual(
                    scalar_path,
                    reference_path,
                )

    def test_scalar_forward_addresses_match_reference(self):
        graph = phase_graph()
        machine = build_scalar_partition_translation_machine(
            graph,
            start_nodes=(("a", 0),),
            phase_of=lambda node: node[1],
            period=3,
            width=32,
        )
        codec = machine.codec

        for t in range(8):
            total = machine.oracle.total_count(t)
            for state in range(total):
                node, _ = machine.locate_endpoint(
                    state,
                    t,
                )
                for edge in codec.outgoing[node]:
                    scalar_next = machine.forward_step(
                        state,
                        t,
                        edge.label,
                    )
                    reference_next, got_t = codec.forward_step(
                        state,
                        t,
                        edge.label,
                    )
                    self.assertEqual(got_t, t + 1)
                    self.assertEqual(
                        scalar_next,
                        reference_next,
                    )

    def test_seed_cache_is_bounded(self):
        graph = phase_graph()
        machine = build_scalar_partition_translation_machine(
            graph,
            start_nodes=(("a", 0),),
            phase_of=lambda node: node[1],
            period=3,
            width=32,
            seed_cache_entries=3,
        )

        for t in range(30):
            machine.oracle.total_count(t)
            for node in machine.nodes:
                machine.endpoint_count(node, t)
            self.assertLessEqual(
                machine.oracle.cached_functional_count,
                3,
            )


if __name__ == "__main__":
    unittest.main()

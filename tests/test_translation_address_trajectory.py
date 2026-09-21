import unittest

from trajectory_generator.floquet_path_trajectory import (
    build_floquet_path_codec,
)
from trajectory_generator.translation_address_trajectory import (
    TranslationAddressMachine,
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


class TranslationAddressTrajectoryTests(unittest.TestCase):
    def test_translation_matches_codec_for_all_small_states(self):
        graph = phase_graph()
        codec = build_floquet_path_codec(
            graph,
            start_nodes=(("a", 0),),
            phase_of=lambda node: node[1],
            period=3,
            width=32,
            cache_rows=1,
        )
        machine = TranslationAddressMachine(codec)

        for t in range(10):
            vector = codec.count_field.vector_at(t)
            for state in range(codec.total_count(t)):
                node, _ = codec._unpack_with_vector(
                    state,
                    vector,
                )
                for edge in codec.outgoing[node]:
                    translated = machine.forward_step(
                        state,
                        t,
                        edge.label,
                    )
                    reference, got_t = codec.forward_step(
                        state,
                        t,
                        edge.label,
                    )
                    self.assertEqual(got_t, t + 1)
                    self.assertEqual(translated, reference)

                    previous, recovered_edge = machine.reverse_step(
                        translated,
                        t + 1,
                    )
                    self.assertEqual(previous, state)
                    self.assertEqual(recovered_edge, edge)

    def test_delta_is_rank_independent(self):
        graph = phase_graph()
        codec = build_floquet_path_codec(
            graph,
            start_nodes=(("a", 0),),
            phase_of=lambda node: node[1],
            period=3,
            width=32,
        )
        machine = TranslationAddressMachine(codec)

        for t in range(8):
            vector = codec.count_field.vector_at(t)
            for edge in codec.edges:
                count = vector[
                    codec.count_field.node_index[edge.source]
                ]
                if count < 2:
                    continue

                source_offset = machine._node_offset_from_vector(
                    edge.source,
                    vector,
                )
                states = (
                    source_offset,
                    source_offset + count - 1,
                )
                deltas = []
                for state in states:
                    nxt = machine.forward_step(
                        state,
                        t,
                        edge.label,
                    )
                    deltas.append(nxt - state)
                self.assertEqual(deltas[0], deltas[1])

    def test_full_translation_roundtrip(self):
        graph = phase_graph()
        codec = build_floquet_path_codec(
            graph,
            start_nodes=(("a", 0),),
            phase_of=lambda node: node[1],
            period=3,
            width=32,
        )
        machine = TranslationAddressMachine(codec)

        for steps in range(12):
            for state in range(codec.total_count(steps)):
                mpath = machine.reconstruct_physical_path(
                    state,
                    steps,
                )
                cpath = codec.reconstruct_physical_path(
                    state,
                    steps,
                )
                self.assertEqual(mpath, cpath)


if __name__ == "__main__":
    unittest.main()

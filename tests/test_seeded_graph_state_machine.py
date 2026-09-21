import unittest

from trajectory_generator.scalar_partition_trajectory import (
    build_scalar_partition_translation_machine,
)
from trajectory_generator.seeded_graph_state_machine import (
    SeededGraphStateMachine,
)


def phase_graph():
    # Two-bit bootstrap mapped to four phase-0 nodes.
    graph = {}
    starts = []
    for seed in range(4):
        start = (seed, 0)
        starts.append(start)
        graph[start] = [
            ((seed << 1) & 3, 1),
            (((seed << 1) | 1) & 3, 1),
        ]
    for history in range(4):
        node = (history, 1)
        graph[node] = [
            ((history << 1) & 3, 0),
            (((history << 1) | 1) & 3, 0),
        ]
    return graph, tuple(starts)


class SeededGraphStateMachineTests(unittest.TestCase):
    def build_machine(self):
        graph, starts = phase_graph()
        partition = build_scalar_partition_translation_machine(
            graph,
            start_nodes=starts,
            phase_of=lambda node: node[1],
            period=2,
            base_phase=0,
            width=32,
            seed_cache_entries=32,
        )
        return SeededGraphStateMachine(
            partition,
            seed_bits=2,
            seed_to_start_node={
                seed: (seed, 0)
                for seed in range(4)
            },
            edge_symbol=lambda edge: edge.target[0] & 1,
        )

    def test_all_binary_words_roundtrip(self):
        machine = self.build_machine()

        for steps in range(10):
            for word in range(1 << steps):
                bits = [
                    (word >> (steps - 1 - i)) & 1
                    for i in range(steps)
                ] if steps else []
                state, got_steps = machine.encode(bits)
                self.assertEqual(got_steps, steps)
                self.assertEqual(
                    machine.decode(state, steps),
                    bits,
                )

    def test_stepwise_rewind_matches_prefixes(self):
        machine = self.build_machine()
        bits = [1, 0, 1, 1, 0, 1, 0]

        state = 0
        steps = 0
        history = [(state, steps)]
        for bit in bits:
            state, steps = machine.advance(
                state,
                steps,
                bit,
            )
            history.append((state, steps))

        for i in range(len(bits) - 1, -1, -1):
            state, steps, recovered = machine.rewind(
                state,
                steps,
            )
            self.assertEqual(recovered, bits[i])
            self.assertEqual(
                (state, steps),
                history[i],
            )


if __name__ == "__main__":
    unittest.main()

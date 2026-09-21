import unittest

from trajectory_generator.native_vertical_product import (
    NativeVerticalProductMachine,
)
from trajectory_generator.seeded_graph_state_machine import (
    SeededGraphStateMachine,
)
from trajectory_generator.scalar_partition_trajectory import (
    build_scalar_partition_translation_machine,
)


def graph():
    rows = {}
    starts = []

    for seed in range(4):
        node = (seed, 0)
        starts.append(node)
        rows[node] = [
            ((seed << 1) & 3, 1),
            (((seed << 1) | 1) & 3, 1),
        ]

    for history in range(4):
        rows[(history, 1)] = [
            ((history << 1) & 3, 0),
            (((history << 1) | 1) & 3, 0),
        ]

    return rows, tuple(starts)


def base_machine():
    rows, starts = graph()
    partition = build_scalar_partition_translation_machine(
        rows,
        start_nodes=starts,
        phase_of=lambda node: node[1],
        period=2,
        base_phase=0,
        width=32,
        seed_cache_entries=64,
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


class NativeVerticalProductTests(unittest.TestCase):
    def test_roundtrip_recovers_bits_and_initial_vertical(self):
        for modulus in (2, 3, 4, 7):
            machine = NativeVerticalProductMachine(
                base_machine(),
                vertical_modulus=modulus,
            )

            bits = (1, 0, 1, 1, 0, 1)
            for initial in range(modulus):
                state, steps = machine.encode(
                    bits,
                    initial_vertical=initial,
                )
                decoded = machine.decode(
                    state,
                    steps,
                )
                self.assertEqual(
                    decoded.bits,
                    bits,
                )
                self.assertEqual(
                    decoded.initial_vertical,
                    initial,
                )

    def test_vertical_translations_are_true_natural_symmetries(self):
        machine = NativeVerticalProductMachine(
            base_machine(),
            vertical_modulus=5,
        )

        state = machine.pack(0, 2)
        steps = 0

        bits = (1, 0, 1, 1, 0)
        for bit in bits:
            for offset in range(5):
                self.assertTrue(
                    machine.symmetry_commutes(
                        state,
                        steps,
                        bit,
                        offset,
                    )
                )
            state, steps = machine.advance(
                state,
                steps,
                bit,
            )

    def test_family_cardinality_multiplies_exactly(self):
        machine = NativeVerticalProductMachine(
            base_machine(),
            vertical_modulus=8,
        )
        self.assertEqual(
            machine.lifted_family_size(12345),
            8 * 12345,
        )


if __name__ == "__main__":
    unittest.main()

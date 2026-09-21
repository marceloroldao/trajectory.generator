"""One-integer reversible trajectory state over a seeded public graph.

This is the operational wrapper around the scalar-partition translation machine.

The public universe may require a fixed binary seed before its lifted graph state
is defined. For example, the current topological universe uses a 3-bit history
seed. The seed itself is encoded directly while it is being formed; once the
seed is complete, it is mapped to one public initial graph node and the same
integer becomes the enumerative graph address.

After bootstrap, each input bit selects one public outgoing edge and the state
evolves by the public affine translation law.

The public API is intentionally minimal:

    advance(state, steps, bit) -> (new_state, new_steps)
    rewind(state, steps)       -> (prev_state, prev_steps, recovered_bit)
    encode(bits)               -> (final_state, steps)
    decode(final_state, steps) -> bits

No causal node, trajectory rank, core-entry state, or path history is passed to
decode. Those are recovered from the integer address and public laws.
"""

from __future__ import annotations

from typing import Callable, Hashable, Mapping, Sequence

from .scalar_partition_trajectory import ScalarPartitionTranslationMachine
from .weighted_path_trajectory import WeightedEdge


Node = Hashable
EdgeSymbol = Callable[[WeightedEdge], int]


class SeededGraphStateMachine:
    def __init__(
        self,
        partition_machine: ScalarPartitionTranslationMachine,
        *,
        seed_bits: int,
        seed_to_start_node: Mapping[int, Node],
        edge_symbol: EdgeSymbol,
    ) -> None:
        if seed_bits < 0:
            raise ValueError("seed_bits must be >= 0")

        self.partition_machine = partition_machine
        self.seed_bits = seed_bits
        self.edge_symbol = edge_symbol

        expected = 1 << seed_bits
        if len(seed_to_start_node) != expected:
            raise ValueError(
                "seed_to_start_node must cover every binary seed"
            )

        self.seed_to_start_node = dict(seed_to_start_node)
        self.start_node_to_seed = {}

        for seed in range(expected):
            if seed not in self.seed_to_start_node:
                raise ValueError("missing binary seed")
            node = self.seed_to_start_node[seed]
            if node in self.start_node_to_seed:
                raise ValueError(
                    "seed mapping must be one-to-one"
                )
            if node not in partition_machine.codec.start_set:
                raise ValueError(
                    "seed node is not a public graph start node"
                )
            self.start_node_to_seed[node] = seed

        # A bit must identify at most one public outgoing edge from a node.
        for node in partition_machine.codec.nodes:
            seen = {}
            for edge in partition_machine.codec.outgoing[node]:
                symbol = int(edge_symbol(edge))
                if symbol not in (0, 1):
                    raise ValueError(
                        "edge_symbol must return binary values"
                    )
                if symbol in seen:
                    raise ValueError(
                        "two outgoing edges share the same public bit"
                    )
                seen[symbol] = edge

    def _validate_literal_prefix(
        self,
        state: int,
        steps: int,
    ) -> None:
        if state < 0:
            raise ValueError("state must be non-negative")
        if steps < 0:
            raise ValueError("steps must be >= 0")
        if steps < self.seed_bits and state >= (1 << steps):
            raise ValueError(
                "literal bootstrap state exceeds prefix width"
            )

    def advance(
        self,
        state: int,
        steps: int,
        bit: int,
    ) -> tuple[int, int]:
        bit = int(bit)
        if bit not in (0, 1):
            raise ValueError("bit must be 0 or 1")
        self._validate_literal_prefix(state, steps)

        if steps < self.seed_bits:
            seed = (state << 1) | bit
            new_steps = steps + 1

            if new_steps < self.seed_bits:
                return seed, new_steps

            node = self.seed_to_start_node[seed]
            address = self.partition_machine.endpoint_offset(
                node,
                0,
            )
            count = self.partition_machine.endpoint_count(
                node,
                0,
            )
            if count != 1:
                raise AssertionError(
                    "each bootstrap seed must identify one initial path"
                )
            return address, new_steps

        transition_time = steps - self.seed_bits
        node, _ = self.partition_machine.locate_endpoint(
            state,
            transition_time,
        )

        chosen = None
        for edge in self.partition_machine.codec.outgoing[node]:
            if int(self.edge_symbol(edge)) == bit:
                chosen = edge
                break

        if chosen is None:
            raise ValueError(
                "bit is not admissible from current public state"
            )

        return (
            self.partition_machine.forward_step(
                state,
                transition_time,
                chosen.label,
            ),
            steps + 1,
        )

    def rewind(
        self,
        state: int,
        steps: int,
    ) -> tuple[int, int, int]:
        if steps <= 0:
            raise ValueError("cannot rewind an empty trajectory")

        if steps < self.seed_bits:
            self._validate_literal_prefix(state, steps)
            bit = state & 1
            return state >> 1, steps - 1, bit

        if steps == self.seed_bits:
            node, rank = self.partition_machine.locate_endpoint(
                state,
                0,
            )
            if rank != 0:
                raise ValueError("invalid bootstrap address")
            try:
                seed = self.start_node_to_seed[node]
            except KeyError as exc:
                raise ValueError(
                    "address does not terminate in a seed node"
                ) from exc
            bit = seed & 1
            return seed >> 1, steps - 1, bit

        transition_time = steps - self.seed_bits
        predecessor, edge = self.partition_machine.reverse_step(
            state,
            transition_time,
        )
        bit = int(self.edge_symbol(edge))
        return predecessor, steps - 1, bit

    def encode(
        self,
        bits: Sequence[int],
    ) -> tuple[int, int]:
        state = 0
        steps = 0
        for bit in bits:
            state, steps = self.advance(
                state,
                steps,
                int(bit),
            )
        return state, steps

    def decode(
        self,
        final_state: int,
        steps: int,
    ) -> list[int]:
        if steps < 0:
            raise ValueError("steps must be >= 0")
        if steps == 0:
            if final_state != 0:
                raise ValueError(
                    "empty trajectory has only state 0"
                )
            return []

        current = final_state
        n = steps
        reversed_bits = []

        while n:
            current, n, bit = self.rewind(
                current,
                n,
            )
            reversed_bits.append(bit)

        if current != 0:
            raise AssertionError(
                "rewind did not return to zero origin"
            )

        reversed_bits.reverse()
        return reversed_bits

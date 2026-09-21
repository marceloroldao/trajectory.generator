"""Final-state-only machine using the canonical dynamic vertical coordinate.

This wrapper is parallel to SeededGraphStateMachine, but after bootstrap the
single integer state is interpreted through CanonicalPeriodicVerticalLift.

The vertical coordinate therefore evolves by the frozen coefficient-free law:

    sigma(t) = (-1)^(t mod 3)
    b(e)     = incoming_index(e)

rather than passive rank transport.

Public API:

    advance(state, steps, bit) -> (new_state, new_steps)
    rewind(state, steps)       -> (prev_state, prev_steps, bit)
    encode(bits)               -> (final_state, steps)
    decode(final_state, steps) -> bits

The decoder receives no causal node, edge history, rank history, or auxiliary
trajectory metadata.
"""

from __future__ import annotations

from typing import Callable, Hashable, Mapping, Sequence

from .canonical_vertical_law import (
    build_canonical_phase_merge_lift,
)
from .weighted_path_trajectory import WeightedEdge


Node = Hashable
EdgeSymbol = Callable[[WeightedEdge], int]


class CanonicalVerticalStateMachine:
    def __init__(
        self,
        partition_machine,
        *,
        seed_bits: int,
        seed_to_start_node: Mapping[int, Node],
        edge_symbol: EdgeSymbol,
        lift_builder=build_canonical_phase_merge_lift,
    ) -> None:
        if seed_bits < 0:
            raise ValueError("seed_bits must be >= 0")

        self.partition_machine = partition_machine
        self.lift = lift_builder(partition_machine)
        self.seed_bits = seed_bits
        self.edge_symbol = edge_symbol

        expected = 1 << seed_bits
        if len(seed_to_start_node) != expected:
            raise ValueError(
                "seed_to_start_node must cover every seed"
            )

        self.seed_to_start_node = dict(seed_to_start_node)
        self.start_node_to_seed = {}

        for seed in range(expected):
            if seed not in self.seed_to_start_node:
                raise ValueError("missing seed")
            node = self.seed_to_start_node[seed]
            if node in self.start_node_to_seed:
                raise ValueError("seed mapping must be one-to-one")
            if node not in partition_machine.codec.start_set:
                raise ValueError("seed node is not public start node")
            self.start_node_to_seed[node] = seed

        for node in partition_machine.codec.nodes:
            seen = set()
            for edge in partition_machine.codec.outgoing[node]:
                symbol = int(edge_symbol(edge))
                if symbol not in (0, 1):
                    raise ValueError(
                        "edge_symbol must be binary"
                    )
                if symbol in seen:
                    raise ValueError(
                        "outgoing edges must have unique symbols"
                    )
                seen.add(symbol)

    def _validate_prefix(self, state: int, steps: int) -> None:
        if state < 0 or steps < 0:
            raise ValueError("state and steps must be non-negative")
        if steps < self.seed_bits and state >= (1 << steps):
            raise ValueError("bootstrap prefix outside width")

    def advance(
        self,
        state: int,
        steps: int,
        bit: int,
    ) -> tuple[int, int]:
        bit = int(bit)
        if bit not in (0, 1):
            raise ValueError("bit must be 0 or 1")

        self._validate_prefix(state, steps)

        if steps < self.seed_bits:
            seed = (state << 1) | bit
            new_steps = steps + 1

            if new_steps < self.seed_bits:
                return seed, new_steps

            node = self.seed_to_start_node[seed]
            initial = self.lift.from_packed(
                self.partition_machine.endpoint_offset(node, 0),
                0,
            )
            if initial.node != node or initial.vertical != 0:
                raise AssertionError(
                    "bootstrap did not land at vertical origin"
                )
            return self.lift.to_packed(initial, 0), new_steps

        t = steps - self.seed_bits
        current = self.lift.from_packed(state, t)

        chosen = None
        for edge in self.partition_machine.codec.outgoing[current.node]:
            if int(self.edge_symbol(edge)) == bit:
                chosen = edge
                break

        if chosen is None:
            raise ValueError(
                "bit is not admissible from current causal state"
            )

        nxt = self.lift.advance(
            current,
            t,
            chosen.label,
        )
        return self.lift.to_packed(nxt, t + 1), steps + 1

    def rewind(
        self,
        state: int,
        steps: int,
    ) -> tuple[int, int, int]:
        if steps <= 0:
            raise ValueError("cannot rewind empty trajectory")

        if steps < self.seed_bits:
            self._validate_prefix(state, steps)
            return state >> 1, steps - 1, state & 1

        if steps == self.seed_bits:
            current = self.lift.from_packed(state, 0)
            if current.vertical != 0:
                raise ValueError(
                    "bootstrap state is not vertical origin"
                )
            try:
                seed = self.start_node_to_seed[current.node]
            except KeyError as exc:
                raise ValueError(
                    "bootstrap node is not a public seed"
                ) from exc
            return seed >> 1, steps - 1, seed & 1

        t = steps - self.seed_bits
        current = self.lift.from_packed(state, t)
        previous, edge = self.lift.rewind(current, t)
        bit = int(self.edge_symbol(edge))

        return (
            self.lift.to_packed(previous, t - 1),
            steps - 1,
            bit,
        )

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
                    "empty trajectory has only state zero"
                )
            return []

        state = final_state
        n = steps
        reversed_bits = []

        while n:
            state, n, bit = self.rewind(
                state,
                n,
            )
            reversed_bits.append(bit)

        if state != 0:
            raise AssertionError(
                "dynamic vertical rewind did not return to origin"
            )

        reversed_bits.reverse()
        return reversed_bits

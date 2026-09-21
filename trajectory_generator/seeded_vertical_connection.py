"""Seeded trajectory machine driven by the exact local vertical connection.

This is the final-state-only wrapper for the horizontal/vertical formulation.

After the public seed is complete, the dynamical state is NOT the packed scalar
address. It is the local reversible coordinate:

    (time, horizontal causal node, vertical fiber rank).

Encoding:
- read the public seed bits;
- enter the corresponding singleton initial fiber;
- evolve locally by edge-specific vertical embeddings;
- pack once at the final boundary.

Decoding:
- unpack the supplied final integer once;
- reverse locally through vertical predecessor blocks until time zero;
- recover the public seed from the initial horizontal node;
- concatenate seed bits with recovered edge symbols.

Thus final_state + steps + public law still recovers the trajectory, while the
packed integer is explicitly only a boundary chart rather than the internal
dynamical representation.
"""

from __future__ import annotations

from typing import Callable, Hashable, Mapping, Sequence

from .exact_vertical_connection import (
    ExactVerticalConnection,
    LocalFiberState,
)
from .weighted_path_trajectory import WeightedEdge
from .vertical_connection_cursor import (
    VerticalConnectionBackwardCursor,
    VerticalConnectionForwardCursor,
)


Node = Hashable
EdgeSymbol = Callable[[WeightedEdge], int]


class SeededVerticalConnectionMachine:
    def __init__(
        self,
        connection: ExactVerticalConnection,
        *,
        seed_bits: int,
        seed_to_start_node: Mapping[int, Node],
        edge_symbol: EdgeSymbol,
    ) -> None:
        if seed_bits < 0:
            raise ValueError("seed_bits must be >= 0")

        self.connection = connection
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
            if node not in connection.codec.start_set:
                raise ValueError(
                    "seed node is not a public graph start node"
                )
            if (
                connection.machine.endpoint_count(node, 0)
                != 1
            ):
                raise ValueError(
                    "each seed node must have singleton initial fiber"
                )
            self.start_node_to_seed[node] = seed

        self.outgoing_by_symbol = {}
        for node in connection.codec.nodes:
            row = {}
            for edge in connection.codec.outgoing[node]:
                symbol = int(edge_symbol(edge))
                if symbol not in (0, 1):
                    raise ValueError(
                        "edge_symbol must return binary values"
                    )
                if symbol in row:
                    raise ValueError(
                        "two outgoing edges share the same public bit"
                    )
                row[symbol] = edge
            self.outgoing_by_symbol[node] = row

    @staticmethod
    def _bits_from_integer(
        value: int,
        width: int,
    ) -> list[int]:
        if width < 0:
            raise ValueError("width must be non-negative")
        if value < 0 or value >= (1 << width):
            raise ValueError("integer outside fixed-width bit range")
        return [
            (value >> shift) & 1
            for shift in range(width - 1, -1, -1)
        ]

    @staticmethod
    def _integer_from_bits(
        bits: Sequence[int],
    ) -> int:
        value = 0
        for bit in bits:
            bit = int(bit)
            if bit not in (0, 1):
                raise ValueError("bit must be 0 or 1")
            value = (value << 1) | bit
        return value

    def _seed_state(
        self,
        seed: int,
    ) -> LocalFiberState:
        try:
            node = self.seed_to_start_node[seed]
        except KeyError as exc:
            raise ValueError("unknown seed") from exc
        return self.connection.state(
            node,
            0,
            0,
        )

    def encode_direct(
        self,
        bits: Sequence[int],
    ) -> tuple[int, int]:
        """Reference local encoder using scalar partition functionals."""
        values = [int(bit) for bit in bits]
        if any(bit not in (0, 1) for bit in values):
            raise ValueError("bits must be binary")

        steps = len(values)
        if steps < self.seed_bits:
            return (
                self._integer_from_bits(values),
                steps,
            )

        seed = self._integer_from_bits(
            values[: self.seed_bits]
        )
        local = self._seed_state(seed)

        for bit in values[self.seed_bits :]:
            edge = self.outgoing_by_symbol[
                local.node
            ].get(bit)
            if edge is None:
                raise ValueError(
                    "bit is not admissible from current public state"
                )
            local = self.connection.forward(
                local,
                edge.label,
            )

        return self.connection.pack(local), steps

    def encode(
        self,
        bits: Sequence[int],
    ) -> tuple[int, int]:
        """Optimized encode using one forward public count vector."""
        values = [int(bit) for bit in bits]
        if any(bit not in (0, 1) for bit in values):
            raise ValueError("bits must be binary")

        steps = len(values)
        if steps < self.seed_bits:
            return (
                self._integer_from_bits(values),
                steps,
            )

        seed = self._integer_from_bits(
            values[: self.seed_bits]
        )
        start_node = self.seed_to_start_node[seed]
        cursor = VerticalConnectionForwardCursor(
            self.connection,
            start_node,
            0,
        )

        for bit in values[self.seed_bits :]:
            edge = self.outgoing_by_symbol[
                cursor.state.node
            ].get(bit)
            if edge is None:
                raise ValueError(
                    "bit is not admissible from current public state"
                )
            cursor.forward(edge.label)

        return cursor.pack_current(), steps

    def encode_with_cursor_metrics(
        self,
        bits: Sequence[int],
    ):
        values = [int(bit) for bit in bits]
        if any(bit not in (0, 1) for bit in values):
            raise ValueError("bits must be binary")

        steps = len(values)
        if steps < self.seed_bits:
            return (
                self._integer_from_bits(values),
                steps,
                None,
            )

        seed = self._integer_from_bits(
            values[: self.seed_bits]
        )
        start_node = self.seed_to_start_node[seed]
        cursor = VerticalConnectionForwardCursor(
            self.connection,
            start_node,
            0,
        )

        for bit in values[self.seed_bits :]:
            edge = self.outgoing_by_symbol[
                cursor.state.node
            ].get(bit)
            if edge is None:
                raise ValueError(
                    "bit is not admissible from current public state"
                )
            cursor.forward(edge.label)

        return (
            cursor.pack_current(),
            steps,
            cursor.metrics,
        )

    def _finish_seeded_decode(
        self,
        local: LocalFiberState,
        reversed_symbols: list[int],
        steps: int,
    ) -> list[int]:
        if local.rank != 0:
            raise AssertionError(
                "local reverse did not reach singleton seed fiber"
            )
        try:
            seed = self.start_node_to_seed[
                local.node
            ]
        except KeyError as exc:
            raise ValueError(
                "local reverse did not reach a public seed node"
            ) from exc

        seed_values = self._bits_from_integer(
            seed,
            self.seed_bits,
        )
        reversed_symbols.reverse()

        result = seed_values + reversed_symbols
        if len(result) != steps:
            raise AssertionError(
                "decoded trajectory has wrong length"
            )
        return result

    def _validate_decode_inputs(
        self,
        final_state: int,
        steps: int,
    ):
        if steps < 0:
            raise ValueError("steps must be >= 0")
        if final_state < 0:
            raise ValueError("final_state must be non-negative")

        if steps == 0:
            if final_state != 0:
                raise ValueError(
                    "empty trajectory has only state 0"
                )
            return []

        if steps < self.seed_bits:
            return self._bits_from_integer(
                final_state,
                steps,
            )
        return None

    def decode_direct(
        self,
        final_state: int,
        steps: int,
    ) -> list[int]:
        """Reference local decoder using scalar partition functionals."""
        early = self._validate_decode_inputs(
            final_state,
            steps,
        )
        if early is not None:
            return early

        transition_time = steps - self.seed_bits
        local = self.connection.unpack(
            final_state,
            transition_time,
        )

        reversed_symbols = []
        while local.time > 0:
            local, edge = self.connection.reverse(
                local
            )
            reversed_symbols.append(
                int(self.edge_symbol(edge))
            )

        return self._finish_seeded_decode(
            local,
            reversed_symbols,
            steps,
        )

    def decode(
        self,
        final_state: int,
        steps: int,
    ) -> list[int]:
        """Optimized final-state decode using a fixed-memory Floquet cursor."""
        early = self._validate_decode_inputs(
            final_state,
            steps,
        )
        if early is not None:
            return early

        transition_time = steps - self.seed_bits
        cursor = VerticalConnectionBackwardCursor(
            self.connection,
            final_state,
            transition_time,
        )

        reversed_symbols = []
        while cursor.state.time > 0:
            edge = cursor.reverse()
            reversed_symbols.append(
                int(self.edge_symbol(edge))
            )

        return self._finish_seeded_decode(
            cursor.state,
            reversed_symbols,
            steps,
        )

    def decode_with_cursor_metrics(
        self,
        final_state: int,
        steps: int,
    ):
        """Return decoded bits plus fixed-memory cursor metrics."""
        early = self._validate_decode_inputs(
            final_state,
            steps,
        )
        if early is not None:
            return early, None

        transition_time = steps - self.seed_bits
        cursor = VerticalConnectionBackwardCursor(
            self.connection,
            final_state,
            transition_time,
        )

        reversed_symbols = []
        while cursor.state.time > 0:
            edge = cursor.reverse()
            reversed_symbols.append(
                int(self.edge_symbol(edge))
            )

        bits = self._finish_seeded_decode(
            cursor.state,
            reversed_symbols,
            steps,
        )
        return bits, cursor.metrics

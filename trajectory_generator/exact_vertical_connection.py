"""Exact local connection on variable-cardinality reversible history fibers.

This module exposes the horizontal/vertical geometry without using the packed
scalar address as the dynamical state.

A local reversible state is

    (time, horizontal causal node, vertical rank).

For a public physical edge e:u->v at transition time t, the source fiber has
size D_t(u).  Exact reversibility embeds it into one predecessor-specific block
inside the target fiber D_(t+1)(v):

    [start_e(t), start_e(t) + D_t(u)).

Forward local evolution is therefore

    (u, r) -> (v, start_e(t) + r).

Reverse local evolution inspects the current vertical rank, identifies the
unique incoming block containing it, and subtracts that block's start.

The scalar final_state is only a chart:

    pack_t(v,r) = endpoint_offset_t(v) + r.

No packed integer is needed by local forward/reverse once the fiber coordinate
has been obtained.

Normalized offsets and widths are returned as exact Fraction values, avoiding
floating-point ambiguity at finite time.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from math import log2
from typing import Hashable

from .scalar_partition_trajectory import (
    ScalarPartitionTranslationMachine,
)
from .weighted_path_trajectory import WeightedEdge


Node = Hashable


@dataclass(frozen=True)
class LocalFiberState:
    time: int
    node: Node
    rank: int
    fiber_size: int


@dataclass(frozen=True)
class ExactSubfiberEmbedding:
    time: int
    edge: WeightedEdge
    source_size: int
    target_size: int
    start: int
    end: int
    normalized_offset: Fraction
    normalized_width: Fraction

    @property
    def information_bits(self) -> float:
        if self.source_size <= 0:
            raise ValueError("empty source block has no information width")
        return log2(self.target_size / self.source_size)


class ExactVerticalConnection:
    """Integer-exact horizontal transition plus vertical subfiber embedding."""

    def __init__(
        self,
        machine: ScalarPartitionTranslationMachine,
    ) -> None:
        self.machine = machine
        self.codec = machine.codec

    def state(
        self,
        node: Node,
        rank: int,
        time: int,
    ) -> LocalFiberState:
        if time < 0:
            raise ValueError("time must be >= 0")
        size = self.machine.endpoint_count(node, time)
        if size <= 0:
            raise ValueError("horizontal node has empty fiber at this time")
        if not 0 <= rank < size:
            raise ValueError("rank outside vertical fiber")
        return LocalFiberState(
            time=time,
            node=node,
            rank=rank,
            fiber_size=size,
        )

    def unpack(
        self,
        packed_state: int,
        time: int,
    ) -> LocalFiberState:
        node, rank = self.machine.locate_endpoint(
            packed_state,
            time,
        )
        return self.state(node, rank, time)

    def pack(
        self,
        state: LocalFiberState,
    ) -> int:
        checked = self.state(
            state.node,
            state.rank,
            state.time,
        )
        if checked.fiber_size != state.fiber_size:
            raise ValueError("stale or inconsistent fiber_size")
        return (
            self.machine.endpoint_offset(
                state.node,
                state.time,
            )
            + state.rank
        )

    def embedding(
        self,
        edge: WeightedEdge | str,
        time: int,
    ) -> ExactSubfiberEmbedding:
        if time < 0:
            raise ValueError("time must be >= 0")

        if isinstance(edge, str):
            resolved = self.codec.edge_by_label.get(edge)
            if resolved is None:
                raise ValueError("unknown edge label")
            edge = resolved

        source_size = self.machine.endpoint_count(
            edge.source,
            time,
        )
        target_size = self.machine.endpoint_count(
            edge.target,
            time + 1,
        )
        if target_size <= 0:
            raise ValueError("target fiber is empty")

        start = self.machine.incoming_offset(
            edge,
            time,
        )
        end = start + source_size

        if not 0 <= start <= end <= target_size:
            raise AssertionError(
                "incoming block lies outside target fiber"
            )

        return ExactSubfiberEmbedding(
            time=time,
            edge=edge,
            source_size=source_size,
            target_size=target_size,
            start=start,
            end=end,
            normalized_offset=Fraction(
                start,
                target_size,
            ),
            normalized_width=Fraction(
                source_size,
                target_size,
            ),
        )

    def incoming_embeddings(
        self,
        target: Node,
        next_time: int,
        *,
        include_empty: bool = False,
    ) -> tuple[ExactSubfiberEmbedding, ...]:
        if next_time <= 0:
            raise ValueError("next_time must be > 0")
        time = next_time - 1

        rows = []
        for edge in self.codec.incoming[target]:
            item = self.embedding(edge, time)
            if include_empty or item.source_size > 0:
                rows.append(item)
        return tuple(rows)

    def partition_is_exact(
        self,
        target: Node,
        next_time: int,
    ) -> bool:
        target_size = self.machine.endpoint_count(
            target,
            next_time,
        )
        if target_size <= 0:
            return True

        rows = self.incoming_embeddings(
            target,
            next_time,
        )
        if not rows:
            return False

        cursor = 0
        for row in rows:
            if row.start != cursor:
                return False
            cursor = row.end
        return cursor == target_size

    def forward(
        self,
        state: LocalFiberState,
        edge_label: str,
    ) -> LocalFiberState:
        checked = self.state(
            state.node,
            state.rank,
            state.time,
        )
        if checked.fiber_size != state.fiber_size:
            raise ValueError("stale or inconsistent fiber_size")

        edge = self.codec.edge_by_label.get(
            edge_label
        )
        if edge is None:
            raise ValueError("unknown edge label")
        if edge.source != state.node:
            raise ValueError(
                "edge does not leave horizontal causal node"
            )

        block = self.embedding(
            edge,
            state.time,
        )
        if block.source_size <= 0:
            raise ValueError("source edge block is unreachable")
        if state.rank >= block.source_size:
            raise AssertionError(
                "source rank exceeds predecessor block"
            )

        return self.state(
            edge.target,
            block.start + state.rank,
            state.time + 1,
        )

    def reverse(
        self,
        state: LocalFiberState,
    ) -> tuple[LocalFiberState, WeightedEdge]:
        checked = self.state(
            state.node,
            state.rank,
            state.time,
        )
        if checked.fiber_size != state.fiber_size:
            raise ValueError("stale or inconsistent fiber_size")
        if state.time <= 0:
            raise ValueError("cannot reverse t=0")

        for block in self.incoming_embeddings(
            state.node,
            state.time,
        ):
            if block.start <= state.rank < block.end:
                previous = self.state(
                    block.edge.source,
                    state.rank - block.start,
                    state.time - 1,
                )
                return previous, block.edge

        raise ValueError(
            "vertical rank belongs to no predecessor subfiber"
        )

    def decode_edges(
        self,
        final_state: LocalFiberState,
    ) -> tuple[LocalFiberState, list[WeightedEdge]]:
        current = final_state
        reversed_edges = []

        while current.time > 0:
            current, edge = self.reverse(current)
            reversed_edges.append(edge)

        if (
            current.rank != 0
            or current.node not in self.codec.start_set
        ):
            raise AssertionError(
                "reverse did not terminate in an initial fiber state"
            )

        reversed_edges.reverse()
        return current, reversed_edges

    def normalized_rank_interval(
        self,
        state: LocalFiberState,
    ) -> tuple[Fraction, Fraction]:
        checked = self.state(
            state.node,
            state.rank,
            state.time,
        )
        if checked.fiber_size != state.fiber_size:
            raise ValueError("stale or inconsistent fiber_size")
        return (
            Fraction(state.rank, state.fiber_size),
            Fraction(state.rank + 1, state.fiber_size),
        )

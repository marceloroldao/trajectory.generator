"""Reversible fiber lift of a non-injective public causal graph.

A finite causal graph generally merges many admissible histories into one raw
node. The final-state-only address resolves this by lifting each raw node v at
time t into a vertical fiber:

    F(v,t) = {0, 1, ..., D(v,t)-1}

where D(v,t) is the number of admissible histories ending at v.

A lifted state is therefore:

    (horizontal causal node v, vertical fiber rank r)

with packed integer:

    S = endpoint_offset(v,t) + r.

The public graph is the horizontal projection. The fiber coordinate carries the
historical information that the raw causal node discarded.

For public edge e: u -> v, forward evolution is injective between fibers:

    r' = incoming_offset(e,t) + r

and the packed state obeys the affine law:

    S' = S + Delta(e,t).

Different incoming edges occupy disjoint vertical sub-fibers of the same target
raw node. Reverse first identifies the target sub-fiber, then subtracts its
offset and recovers the unique predecessor.

This module makes that geometry explicit without changing address semantics.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Hashable

from .scalar_partition_trajectory import (
    ScalarPartitionTranslationMachine,
)
from .weighted_path_trajectory import WeightedEdge


Node = Hashable


@dataclass(frozen=True)
class FiberCoordinate:
    time: int
    node: Node
    rank: int
    fiber_size: int
    packed_state: int


class ReversibleFiberLift:
    def __init__(
        self,
        machine: ScalarPartitionTranslationMachine,
    ) -> None:
        self.machine = machine

    def coordinate(
        self,
        packed_state: int,
        time: int,
    ) -> FiberCoordinate:
        node, rank = self.machine.locate_endpoint(
            packed_state,
            time,
        )
        size = self.machine.endpoint_count(node, time)
        return FiberCoordinate(
            time=time,
            node=node,
            rank=rank,
            fiber_size=size,
            packed_state=packed_state,
        )

    def pack(
        self,
        node: Node,
        rank: int,
        time: int,
    ) -> int:
        size = self.machine.endpoint_count(node, time)
        if not 0 <= rank < size:
            raise ValueError("rank outside node fiber")
        return (
            self.machine.endpoint_offset(node, time)
            + rank
        )

    def incoming_subfiber(
        self,
        edge: WeightedEdge,
        time: int,
    ) -> tuple[int, int]:
        """Return [start,end) of edge e inside target fiber at time+1."""
        start = self.machine.incoming_offset(
            edge,
            time,
        )
        size = self.machine.endpoint_count(
            edge.source,
            time,
        )
        return start, start + size

    def forward(
        self,
        coordinate: FiberCoordinate,
        edge_label: str,
    ) -> FiberCoordinate:
        if coordinate.time < 0:
            raise ValueError("time must be >= 0")

        edge = self.machine.codec.edge_by_label.get(
            edge_label
        )
        if edge is None:
            raise ValueError("unknown edge label")
        if edge.source != coordinate.node:
            raise ValueError(
                "edge does not leave horizontal causal node"
            )

        packed = self.machine.forward_step(
            coordinate.packed_state,
            coordinate.time,
            edge_label,
        )
        nxt = self.coordinate(
            packed,
            coordinate.time + 1,
        )

        subfiber_start, _ = self.incoming_subfiber(
            edge,
            coordinate.time,
        )
        expected_rank = (
            subfiber_start + coordinate.rank
        )

        if nxt.node != edge.target:
            raise AssertionError(
                "horizontal projection does not follow public edge"
            )
        if nxt.rank != expected_rank:
            raise AssertionError(
                "vertical fiber map is not offset-preserving"
            )

        return nxt

    def reverse(
        self,
        coordinate: FiberCoordinate,
    ) -> tuple[FiberCoordinate, WeightedEdge]:
        if coordinate.time <= 0:
            raise ValueError("cannot reverse t=0")

        previous_state, edge = self.machine.reverse_step(
            coordinate.packed_state,
            coordinate.time,
        )
        previous = self.coordinate(
            previous_state,
            coordinate.time - 1,
        )

        start, end = self.incoming_subfiber(
            edge,
            previous.time,
        )

        if not start <= coordinate.rank < end:
            raise AssertionError(
                "current vertical rank is outside predecessor sub-fiber"
            )
        if coordinate.rank - start != previous.rank:
            raise AssertionError(
                "sub-fiber reverse did not recover predecessor rank"
            )

        return previous, edge

    def active_fibers(
        self,
        time: int,
    ) -> tuple[tuple[Node, int], ...]:
        active = []
        phase = (
            self.machine.field.base_phase + time
        ) % self.machine.field.period

        for node in self.machine.nodes:
            if (
                self.machine.field.phase_of(node)
                % self.machine.field.period
                != phase
            ):
                continue
            size = self.machine.endpoint_count(
                node,
                time,
            )
            if size:
                active.append((node, size))

        return tuple(active)

    def total_states(
        self,
        time: int,
    ) -> int:
        return sum(
            size
            for _, size in self.active_fibers(time)
        )

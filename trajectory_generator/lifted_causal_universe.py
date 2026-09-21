"""Minimal reversible lift of a finite public causal universe.

A raw causal graph can be non-injective: many admissible histories may arrive at
one causal node.  At a fixed public time t, let D(v,t) be the number of
admissible histories ending at node v.

The finite-horizon reversible completion replaces raw node v by the fiber

    {v} x {0, ..., D(v,t)-1}.

This is not an arbitrary enlargement.  It is fiberwise minimal: any exact
reversible lift that projects onto the same raw causal graph and distinguishes
all admissible histories must contain at least D(v,t) lifted states above v.

The ReversibleFiberLift already supplies the exact coordinates and edge maps.
This module promotes that geometry to a causal-universe interface and exposes
the projection/semiconjugacy laws explicitly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Hashable

from .reversible_fiber_lift import (
    FiberCoordinate,
    ReversibleFiberLift,
)
from .weighted_path_trajectory import WeightedEdge


Node = Hashable


@dataclass(frozen=True)
class LiftedCausalState:
    """Native coordinate of the finite-horizon reversible lift."""

    node: Node
    vertical_rank: int


class LiftedCausalUniverse:
    def __init__(self, lift: ReversibleFiberLift) -> None:
        self.lift = lift
        self.machine = lift.machine

    def project(self, state: LiftedCausalState) -> Node:
        """Horizontal projection onto the original causal universe."""
        return state.node

    def fiber_size(self, node: Node, time: int) -> int:
        return self.machine.endpoint_count(node, time)

    def validate(
        self,
        state: LiftedCausalState,
        time: int,
    ) -> bool:
        if time < 0:
            return False
        size = self.fiber_size(state.node, time)
        return 0 <= state.vertical_rank < size

    def from_packed(
        self,
        packed_state: int,
        time: int,
    ) -> LiftedCausalState:
        coordinate = self.lift.coordinate(
            packed_state,
            time,
        )
        return LiftedCausalState(
            node=coordinate.node,
            vertical_rank=coordinate.rank,
        )

    def to_packed(
        self,
        state: LiftedCausalState,
        time: int,
    ) -> int:
        if not self.validate(state, time):
            raise ValueError("invalid lifted causal state")
        return self.lift.pack(
            state.node,
            state.vertical_rank,
            time,
        )

    def advance(
        self,
        state: LiftedCausalState,
        time: int,
        edge_label: str,
    ) -> LiftedCausalState:
        """Advance one public causal edge in the reversible lift."""
        if not self.validate(state, time):
            raise ValueError("invalid lifted causal state")

        packed = self.to_packed(state, time)
        coordinate = self.lift.coordinate(
            packed,
            time,
        )
        nxt = self.lift.forward(
            coordinate,
            edge_label,
        )
        return LiftedCausalState(
            node=nxt.node,
            vertical_rank=nxt.rank,
        )

    def rewind(
        self,
        state: LiftedCausalState,
        time: int,
    ) -> tuple[LiftedCausalState, WeightedEdge]:
        """Recover the unique predecessor lifted state and public edge."""
        if time <= 0:
            raise ValueError("cannot rewind t=0")
        if not self.validate(state, time):
            raise ValueError("invalid lifted causal state")

        packed = self.to_packed(state, time)
        coordinate = self.lift.coordinate(
            packed,
            time,
        )
        previous, edge = self.lift.reverse(coordinate)
        return (
            LiftedCausalState(
                node=previous.node,
                vertical_rank=previous.rank,
            ),
            edge,
        )

    def edge_image_interval(
        self,
        edge: WeightedEdge,
        time: int,
    ) -> tuple[int, int]:
        """Vertical target interval occupied by one incoming public edge."""
        return self.lift.incoming_subfiber(edge, time)

    def fiber_partition(
        self,
        target: Node,
        time: int,
    ) -> tuple[tuple[WeightedEdge, int, int], ...]:
        """Partition target fiber at time+1 by predecessor edge."""
        blocks = []
        for edge in self.machine.codec.incoming[target]:
            start, end = self.edge_image_interval(edge, time)
            if end > start:
                blocks.append((edge, start, end))
        return tuple(blocks)

    def semiconjugacy_holds(
        self,
        state: LiftedCausalState,
        time: int,
        edge_label: str,
    ) -> bool:
        """Check pi(F_e(x)) == f_e(pi(x)) for one lifted state."""
        edge = self.machine.codec.edge_by_label.get(edge_label)
        if edge is None or edge.source != state.node:
            return False
        nxt = self.advance(state, time, edge_label)
        return self.project(nxt) == edge.target

    def local_minimum_states(
        self,
        node: Node,
        time: int,
    ) -> int:
        """Information-theoretic lower bound for any exact lift above node."""
        return self.fiber_size(node, time)

    def local_minimum_bits(
        self,
        node: Node,
        time: int,
    ) -> int:
        size = self.local_minimum_states(node, time)
        return 0 if size <= 1 else (size - 1).bit_length()

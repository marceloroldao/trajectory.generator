"""Periodic endogenous dynamics for the vertical coordinate of a causal fiber lift.

The earlier reversible fiber lift used an offset-preserving vertical map:

    y_target = incoming_offset(edge,t) + y_source.

That makes the vertical coordinate operationally equivalent to a path rank.

This module replaces that identity map by a public, endogenous, periodic
permutation of the source fiber before insertion into the target sub-fiber.

For source fiber size n > 0:

    local' = (sigma(edge,t) * y + b(edge,t)) mod n

where:

    sigma in {+1, -1}

and b is a public integer drive.  The target vertical coordinate is:

    y' = incoming_offset(edge,t) + local'.

The drive is derived only from:

- local causal graph invariants of the edge;
- the public causal phase;
- a vertical phase of period 2*P, where P is the causal graph period.

No trajectory-specific metadata, rank history, random seed, or stored drive
sequence is used.

Using sigma in {+1,-1} is deliberate: every map is a permutation for every
positive fiber size, so reversibility does not depend on number-theoretic
properties of the dynamically changing fiber cardinality.

The inverse is exact:

    y = sigma * (local' - b) mod n.

The horizontal projection remains the original public causal dynamics.
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
class PeriodicVerticalState:
    """Native lifted coordinate: causal node plus dynamic vertical position."""

    node: Node
    vertical: int


@dataclass(frozen=True)
class VerticalDrive:
    """Public phase-local drive before reduction modulo the fiber size."""

    vertical_phase: int
    orientation: int
    shift_seed: int
    outgoing_index: int
    incoming_index: int


class EndogenousPeriodicVerticalLift:
    """Reversible causal lift with a phase-driven vertical dynamics."""

    def __init__(
        self,
        machine: ScalarPartitionTranslationMachine,
        *,
        vertical_period: int | None = None,
    ) -> None:
        self.machine = machine
        self.causal_period = machine.field.period

        if vertical_period is None:
            vertical_period = 2 * self.causal_period
        if vertical_period < 1:
            raise ValueError("vertical_period must be >= 1")
        if vertical_period % self.causal_period:
            raise ValueError(
                "vertical_period must be a multiple of causal period"
            )

        self.vertical_period = vertical_period

        self._outgoing_index: dict[str, int] = {}
        self._incoming_index: dict[str, int] = {}

        for node in machine.nodes:
            for i, edge in enumerate(machine.codec.outgoing[node]):
                self._outgoing_index[edge.label] = i
            for i, edge in enumerate(machine.codec.incoming[node]):
                self._incoming_index[edge.label] = i

    def fiber_size(self, node: Node, time: int) -> int:
        return self.machine.endpoint_count(node, time)

    def validate(
        self,
        state: PeriodicVerticalState,
        time: int,
    ) -> bool:
        if time < 0:
            return False
        size = self.fiber_size(state.node, time)
        return 0 <= state.vertical < size

    def project(self, state: PeriodicVerticalState) -> Node:
        return state.node

    def from_packed(
        self,
        packed_state: int,
        time: int,
    ) -> PeriodicVerticalState:
        node, vertical = self.machine.locate_endpoint(
            packed_state,
            time,
        )
        return PeriodicVerticalState(
            node=node,
            vertical=vertical,
        )

    def to_packed(
        self,
        state: PeriodicVerticalState,
        time: int,
    ) -> int:
        if not self.validate(state, time):
            raise ValueError("invalid periodic vertical state")
        return (
            self.machine.endpoint_offset(state.node, time)
            + state.vertical
        )

    def _edge_invariants(
        self,
        edge: WeightedEdge,
    ) -> tuple[int, int, int, int, int, int]:
        outgoing_index = self._outgoing_index[edge.label]
        incoming_index = self._incoming_index[edge.label]
        source_out_degree = len(
            self.machine.codec.outgoing[edge.source]
        )
        source_in_degree = len(
            self.machine.codec.incoming[edge.source]
        )
        target_out_degree = len(
            self.machine.codec.outgoing[edge.target]
        )
        target_in_degree = len(
            self.machine.codec.incoming[edge.target]
        )
        return (
            outgoing_index,
            incoming_index,
            source_out_degree,
            source_in_degree,
            target_out_degree,
            target_in_degree,
        )

    def drive(
        self,
        edge: WeightedEdge,
        time: int,
    ) -> VerticalDrive:
        """Return the public endogenous drive for one edge and physical time."""
        if time < 0:
            raise ValueError("time must be >= 0")

        (
            outgoing_index,
            incoming_index,
            source_out_degree,
            source_in_degree,
            target_out_degree,
            target_in_degree,
        ) = self._edge_invariants(edge)

        vertical_phase = time % self.vertical_period

        # The causal phase is part of the public state geometry.  The cycle
        # phase distinguishes repeated visits to the same causal phase when the
        # vertical period is longer than the horizontal causal period.
        causal_phase = (
            self.machine.field.phase_of(edge.source)
            % self.causal_period
        )
        cycle_phase = (
            vertical_phase // self.causal_period
        )

        mix = (
            1
            + 3 * (outgoing_index + 1)
            + 5 * (incoming_index + 1)
            + 7 * source_out_degree
            + 11 * source_in_degree
            + 13 * target_out_degree
            + 17 * target_in_degree
            + 19 * causal_phase
            + 23 * cycle_phase
        )

        orientation = -1 if (mix & 1) else 1

        # A non-negative public seed.  The actual rotation is reduced modulo
        # the current source-fiber size only when the map is applied.
        shift_seed = (
            mix * mix
            + 29 * (vertical_phase + 1)
            + 31 * (outgoing_index + 1) * (incoming_index + 1)
        )

        return VerticalDrive(
            vertical_phase=vertical_phase,
            orientation=orientation,
            shift_seed=shift_seed,
            outgoing_index=outgoing_index,
            incoming_index=incoming_index,
        )

    def permute_local(
        self,
        vertical: int,
        fiber_size: int,
        drive: VerticalDrive,
    ) -> int:
        if fiber_size <= 0:
            raise ValueError("fiber_size must be positive")
        if not 0 <= vertical < fiber_size:
            raise ValueError("vertical outside source fiber")

        shift = drive.shift_seed % fiber_size
        return (
            drive.orientation * vertical + shift
        ) % fiber_size

    def invert_local(
        self,
        local: int,
        fiber_size: int,
        drive: VerticalDrive,
    ) -> int:
        if fiber_size <= 0:
            raise ValueError("fiber_size must be positive")
        if not 0 <= local < fiber_size:
            raise ValueError("local coordinate outside edge image")

        shift = drive.shift_seed % fiber_size

        # orientation is +/-1 and is its own multiplicative inverse.
        return (
            drive.orientation * (local - shift)
        ) % fiber_size

    def edge_image_interval(
        self,
        edge: WeightedEdge,
        time: int,
    ) -> tuple[int, int]:
        start = self.machine.incoming_offset(edge, time)
        size = self.fiber_size(edge.source, time)
        return start, start + size

    def advance(
        self,
        state: PeriodicVerticalState,
        time: int,
        edge_label: str,
    ) -> PeriodicVerticalState:
        """Advance one causal edge using endogenous vertical permutation."""
        if not self.validate(state, time):
            raise ValueError("invalid periodic vertical state")

        edge = self.machine.codec.edge_by_label.get(edge_label)
        if edge is None:
            raise ValueError("unknown edge label")
        if edge.source != state.node:
            raise ValueError(
                "edge does not leave current horizontal causal node"
            )

        source_size = self.fiber_size(edge.source, time)
        drive = self.drive(edge, time)
        local = self.permute_local(
            state.vertical,
            source_size,
            drive,
        )

        start, end = self.edge_image_interval(edge, time)
        target_vertical = start + local

        if not start <= target_vertical < end:
            raise AssertionError(
                "periodic vertical map left its edge sub-fiber"
            )

        nxt = PeriodicVerticalState(
            node=edge.target,
            vertical=target_vertical,
        )
        if not self.validate(nxt, time + 1):
            raise AssertionError(
                "periodic vertical map produced invalid target state"
            )
        return nxt

    def rewind(
        self,
        state: PeriodicVerticalState,
        time: int,
    ) -> tuple[PeriodicVerticalState, WeightedEdge]:
        """Recover unique predecessor state and causal edge."""
        if time <= 0:
            raise ValueError("cannot rewind t=0")
        if not self.validate(state, time):
            raise ValueError("invalid periodic vertical state")

        previous_time = time - 1

        chosen = None
        local = None
        for edge in self.machine.codec.incoming[state.node]:
            start, end = self.edge_image_interval(
                edge,
                previous_time,
            )
            if start <= state.vertical < end:
                chosen = edge
                local = state.vertical - start
                break

        if chosen is None or local is None:
            raise ValueError(
                "vertical state is outside every predecessor edge image"
            )

        source_size = self.fiber_size(
            chosen.source,
            previous_time,
        )
        drive = self.drive(chosen, previous_time)
        previous_vertical = self.invert_local(
            local,
            source_size,
            drive,
        )

        previous = PeriodicVerticalState(
            node=chosen.source,
            vertical=previous_vertical,
        )
        if not self.validate(previous, previous_time):
            raise AssertionError(
                "inverse vertical map produced invalid predecessor"
            )

        return previous, chosen

    def semiconjugacy_holds(
        self,
        state: PeriodicVerticalState,
        time: int,
        edge_label: str,
    ) -> bool:
        edge = self.machine.codec.edge_by_label.get(edge_label)
        if edge is None or edge.source != state.node:
            return False
        nxt = self.advance(state, time, edge_label)
        return self.project(nxt) == edge.target

    def active_fibers(
        self,
        time: int,
    ) -> tuple[tuple[Node, int], ...]:
        phase = (
            self.machine.field.base_phase + time
        ) % self.causal_period

        active = []
        for node in self.machine.nodes:
            if (
                self.machine.field.phase_of(node)
                % self.causal_period
                != phase
            ):
                continue
            size = self.fiber_size(node, time)
            if size:
                active.append((node, size))
        return tuple(active)

    def total_states(self, time: int) -> int:
        return sum(
            size
            for _, size in self.active_fibers(time)
        )

    def drive_is_periodic(
        self,
        edge: WeightedEdge,
        time: int,
    ) -> bool:
        return (
            self.drive(edge, time)
            == self.drive(
                edge,
                time + self.vertical_period,
            )
        )

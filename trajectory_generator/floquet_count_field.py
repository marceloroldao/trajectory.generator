"""Phase/Floquet compression of the public graph count field.

Many trajectory.generator universes are phase-lifted: every public transition
advances phase by exactly one modulo a fixed period P.

If all public initial nodes lie on one base phase, then at physical time t only
one phase slice can have non-zero count. Instead of deriving a recurrence on all
reachable lifted nodes, this module builds the P-step Floquet multigraph on the
base-phase slice and derives the minimal recurrence there.

For physical time

    t = P*q + r

the exact count field is reconstructed as:

1. regenerate the base-phase count vector at period q from the compact
   recurrence;
2. embed it into the full reachable graph;
3. apply r public one-step transitions.

A backward physical cursor wraps the recurrence cursor of the period graph. It
moves inside a period by deterministic public transitions and crosses period
boundaries by one reverse step of the compact Floquet count recurrence.

The stored recurrence state therefore depends on the base-phase reachable
dimension and Floquet Krylov order, not on the physical horizon T.
"""

from __future__ import annotations

from typing import Callable, Hashable, Mapping, Sequence

from .count_field_recurrence import (
    CountFieldRecurrence,
    reachable_nodes,
)


Node = Hashable
PhaseFunction = Callable[[Node], int]


def _step_vector(
    outgoing: Sequence[Sequence[int]],
    vector: Sequence[int],
) -> tuple[int, ...]:
    out = [0] * len(vector)
    for source, count in enumerate(vector):
        if not count:
            continue
        for target in outgoing[source]:
            out[target] += count
    return tuple(out)


class FloquetBackwardCountCursor:
    def __init__(
        self,
        field: "FloquetCountFieldRecurrence",
        final_time: int,
    ) -> None:
        if final_time < 0:
            raise ValueError("final_time must be >= 0")

        self.field = field
        self.time = final_time
        period_index, phase_offset = divmod(
            final_time,
            field.period,
        )
        self.phase_offset = phase_offset
        self.period_cursor = field.period_field.backward_cursor(
            period_index
        )

    def clone(self) -> "FloquetBackwardCountCursor":
        clone = object.__new__(FloquetBackwardCountCursor)
        clone.field = self.field
        clone.time = self.time
        clone.phase_offset = self.phase_offset
        clone.period_cursor = self.period_cursor.clone()
        return clone

    @property
    def stored_row_count(self) -> int:
        return self.period_cursor.stored_row_count

    def current_vector(self) -> tuple[int, ...]:
        base = self.period_cursor.current_vector()
        return self.field.expand_period_vector(
            base,
            self.phase_offset,
        )

    def previous_vector(self) -> tuple[int, ...]:
        if self.time <= 0:
            raise ValueError("t=0 has no previous count row")

        if self.phase_offset > 0:
            base = self.period_cursor.current_vector()
            return self.field.expand_period_vector(
                base,
                self.phase_offset - 1,
            )

        previous_period = self.period_cursor.previous_vector()
        return self.field.expand_period_vector(
            previous_period,
            self.field.period - 1,
        )

    def step_back(self) -> None:
        if self.time <= 0:
            raise ValueError("cannot step before t=0")

        if self.phase_offset > 0:
            self.phase_offset -= 1
        else:
            self.period_cursor.step_back()
            self.phase_offset = self.field.period - 1

        self.time -= 1


class FloquetCountFieldRecurrence:
    """Exact count oracle compressed onto one public phase slice."""

    def __init__(
        self,
        adjacency: Mapping[Node, Sequence[Node]],
        *,
        start_nodes: Sequence[Node],
        phase_of: PhaseFunction,
        period: int,
        base_phase: int = 0,
        cache_rows: int = 2,
    ) -> None:
        if period < 1:
            raise ValueError("period must be >= 1")

        self.period = period
        self.base_phase = base_phase % period
        self.phase_of = phase_of
        self.start_nodes = tuple(start_nodes)

        if not self.start_nodes:
            raise ValueError("start_nodes must be non-empty")
        if any(
            phase_of(node) % period != self.base_phase
            for node in self.start_nodes
        ):
            raise ValueError(
                "all start nodes must lie on the base phase"
            )

        self.nodes = reachable_nodes(
            adjacency,
            self.start_nodes,
        )
        self.node_index = {
            node: i
            for i, node in enumerate(self.nodes)
        }

        self.outgoing = tuple(
            tuple(
                self.node_index[target]
                for target in adjacency.get(source, ())
            )
            for source in self.nodes
        )

        # Validate strict cyclic phase advancement on the reachable graph.
        for source in self.nodes:
            source_phase = phase_of(source) % period
            expected = (source_phase + 1) % period
            for target in adjacency.get(source, ()):
                if phase_of(target) % period != expected:
                    raise ValueError(
                        "reachable edge does not advance public phase by one"
                    )

        initial = [0] * len(self.nodes)
        for node in self.start_nodes:
            initial[self.node_index[node]] += 1
        self.initial_vector = tuple(initial)

        base_nodes = tuple(
            node
            for node in self.nodes
            if phase_of(node) % period == self.base_phase
        )

        # Build the exact P-step multigraph. Duplicate targets are retained:
        # each duplicate represents a distinct public P-edge path.
        period_adjacency: dict[Node, list[Node]] = {}
        for source in base_nodes:
            frontier = [source]
            for _ in range(period):
                nxt = []
                for node in frontier:
                    nxt.extend(adjacency.get(node, ()))
                frontier = nxt

            if any(
                phase_of(target) % period != self.base_phase
                for target in frontier
            ):
                raise AssertionError(
                    "period walk did not return to base phase"
                )
            period_adjacency[source] = frontier

        self.period_field = CountFieldRecurrence(
            period_adjacency,
            start_nodes=self.start_nodes,
            cache_rows=cache_rows,
            retain_basis=False,
        )

        self.base_nodes = self.period_field.nodes
        self.base_full_indices = tuple(
            self.node_index[node]
            for node in self.base_nodes
        )

    @property
    def reachable_state_count(self) -> int:
        return len(self.nodes)

    @property
    def phase_state_count(self) -> int:
        return len(self.base_nodes)

    @property
    def order(self) -> int:
        return self.period_field.order

    @property
    def coefficients(self) -> tuple[int, ...]:
        return self.period_field.coefficients

    @property
    def transient_factor_power(self) -> int:
        return self.period_field.transient_factor_power

    @property
    def reduced_coefficients(self) -> tuple[int, ...]:
        return self.period_field.reduced_coefficients

    @property
    def basis_integer_count(self) -> int:
        return self.period_field.basis_integer_count

    @property
    def derived_basis_integer_count(self) -> int:
        return self.period_field.derived_basis_integer_count

    @property
    def cache_rows(self) -> int:
        return self.period_field.cache_rows

    @property
    def cached_row_count(self) -> int:
        return self.period_field.cached_row_count

    def direct_table_integer_count(self, horizon: int) -> int:
        if horizon < 0:
            raise ValueError("horizon must be >= 0")
        return self.reachable_state_count * (horizon + 1)

    def step_vector(
        self,
        vector: Sequence[int],
    ) -> tuple[int, ...]:
        if len(vector) != self.reachable_state_count:
            raise ValueError("count vector has wrong dimension")
        return _step_vector(self.outgoing, vector)

    def expand_period_vector(
        self,
        base_vector: Sequence[int],
        phase_offset: int,
    ) -> tuple[int, ...]:
        if not 0 <= phase_offset < self.period:
            raise ValueError("phase_offset outside period")
        if len(base_vector) != self.phase_state_count:
            raise ValueError("base-phase vector has wrong dimension")

        full = [0] * self.reachable_state_count
        for value, index in zip(
            base_vector,
            self.base_full_indices,
        ):
            full[index] = value

        vector = tuple(full)
        for _ in range(phase_offset):
            vector = self.step_vector(vector)
        return vector

    def vector_at(self, t: int) -> tuple[int, ...]:
        if t < 0:
            raise ValueError("t must be >= 0")
        period_index, phase_offset = divmod(t, self.period)
        base = self.period_field.vector_at(period_index)
        return self.expand_period_vector(
            base,
            phase_offset,
        )

    def count(self, node: Node, t: int) -> int:
        index = self.node_index.get(node)
        if index is None:
            return 0
        return self.vector_at(t)[index]

    def total(self, t: int) -> int:
        return sum(self.vector_at(t))

    def backward_cursor(
        self,
        final_time: int,
    ) -> FloquetBackwardCountCursor:
        return FloquetBackwardCountCursor(
            self,
            final_time,
        )

    def validate_recurrence(
        self,
        extra_periods: int = 32,
    ) -> bool:
        if not self.period_field.validate_recurrence(
            extra_periods
        ):
            return False

        limit = self.period * (
            self.order + extra_periods
        )
        current = self.initial_vector
        for t in range(limit + 1):
            if self.vector_at(t) != current:
                return False
            current = self.step_vector(current)

        return True

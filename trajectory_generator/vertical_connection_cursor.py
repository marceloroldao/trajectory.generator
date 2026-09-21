"""Fixed-memory backward cursor for exact local vertical fiber decoding.

The scalar partition decoder answers many separate count-function queries while
walking backward.  The Floquet count field already provides a stronger object:
an exact backward cursor carrying a compact recurrence window.

This module combines that public count cursor with the local horizontal/vertical
fiber state.

At current transition time t:

- current_vector contains all D_t(v);
- previous_vector contains all D_(t-1)(u);
- incoming predecessor blocks of target v have sizes D_(t-1)(u).

Therefore reverse block selection needs no ScalarFloquetPartitionOracle query.

The cursor retains only the compact Floquet recurrence window plus one local
fiber state.  Memory is independent of the decoded horizon.
"""

from __future__ import annotations

from dataclasses import dataclass

from .exact_vertical_connection import (
    ExactVerticalConnection,
    LocalFiberState,
)
from .weighted_path_trajectory import WeightedEdge


@dataclass(frozen=True)
class CursorMetrics:
    reverse_steps: int
    maximum_stored_floquet_rows: int
    phase_state_count: int
    reachable_state_count: int

    @property
    def maximum_stored_count_integers(self) -> int:
        return (
            self.maximum_stored_floquet_rows
            * self.phase_state_count
        )


class VerticalConnectionBackwardCursor:
    """Reverse a packed final chart through exact local fibers."""

    def __init__(
        self,
        connection: ExactVerticalConnection,
        final_state: int,
        final_time: int,
    ) -> None:
        if final_state < 0:
            raise ValueError("final_state must be non-negative")
        if final_time < 0:
            raise ValueError("final_time must be non-negative")

        self.connection = connection
        self.machine = connection.machine
        self.field = self.machine.field
        self.count_cursor = self.field.backward_cursor(
            final_time
        )
        self._reverse_steps = 0
        self._maximum_stored_rows = (
            self.count_cursor.stored_row_count
        )

        vector = self.count_cursor.current_vector()
        node, rank = self._locate_from_vector(
            final_state,
            vector,
        )
        size = vector[
            self.field.node_index[node]
        ]
        self.state = LocalFiberState(
            time=final_time,
            node=node,
            rank=rank,
            fiber_size=size,
        )

    def _locate_from_vector(
        self,
        packed_state: int,
        vector,
    ):
        total = sum(vector)
        if packed_state >= total:
            raise ValueError(
                "state outside exact-length path family"
            )

        lower = 0
        for node in self.machine.nodes:
            count = vector[
                self.field.node_index[node]
            ]
            if count <= 0:
                continue
            upper = lower + count
            if packed_state < upper:
                return node, packed_state - lower
            lower = upper

        raise AssertionError(
            "packed address endpoint bucket not found"
        )

    @property
    def metrics(self) -> CursorMetrics:
        return CursorMetrics(
            reverse_steps=self._reverse_steps,
            maximum_stored_floquet_rows=(
                self._maximum_stored_rows
            ),
            phase_state_count=(
                self.field.phase_state_count
            ),
            reachable_state_count=(
                self.field.reachable_state_count
            ),
        )

    def reverse(
        self,
    ) -> WeightedEdge:
        current = self.state
        if current.time <= 0:
            raise ValueError("cannot reverse t=0")
        if self.count_cursor.time != current.time:
            raise AssertionError(
                "count cursor and local state time diverged"
            )

        previous_vector = (
            self.count_cursor.previous_vector()
        )
        offset = 0
        chosen = None
        previous_rank = None
        previous_size = None

        for edge in self.connection.codec.incoming[
            current.node
        ]:
            source_index = self.field.node_index[
                edge.source
            ]
            block = previous_vector[source_index]
            if block <= 0:
                continue

            if current.rank < offset + block:
                chosen = edge
                previous_rank = (
                    current.rank - offset
                )
                previous_size = block
                break
            offset += block

        if (
            chosen is None
            or previous_rank is None
            or previous_size is None
        ):
            raise ValueError(
                "vertical rank belongs to no predecessor subfiber"
            )

        self.count_cursor.step_back()
        self._maximum_stored_rows = max(
            self._maximum_stored_rows,
            self.count_cursor.stored_row_count,
        )
        self._reverse_steps += 1

        self.state = LocalFiberState(
            time=current.time - 1,
            node=chosen.source,
            rank=previous_rank,
            fiber_size=previous_size,
        )
        return chosen



@dataclass(frozen=True)
class ForwardCursorMetrics:
    forward_steps: int
    reachable_state_count: int

    @property
    def persistent_count_integers(self) -> int:
        return self.reachable_state_count

    @property
    def peak_count_integers_during_step(self) -> int:
        return 2 * self.reachable_state_count


class VerticalConnectionForwardCursor:
    """Advance exact local fibers from one public singleton start state."""

    def __init__(
        self,
        connection: ExactVerticalConnection,
        start_node,
        start_rank: int = 0,
    ) -> None:
        self.connection = connection
        self.machine = connection.machine
        self.field = self.machine.field
        self.vector = self.field.initial_vector
        self._forward_steps = 0

        index = self.field.node_index.get(start_node)
        if index is None:
            raise ValueError("start node outside reachable graph")
        size = self.vector[index]
        if size <= 0:
            raise ValueError("start node has empty initial fiber")
        if not 0 <= start_rank < size:
            raise ValueError("start rank outside initial fiber")

        self.state = LocalFiberState(
            time=0,
            node=start_node,
            rank=start_rank,
            fiber_size=size,
        )

    @property
    def metrics(self) -> ForwardCursorMetrics:
        return ForwardCursorMetrics(
            forward_steps=self._forward_steps,
            reachable_state_count=(
                self.field.reachable_state_count
            ),
        )

    def forward(
        self,
        edge_label: str,
    ) -> WeightedEdge:
        edge = self.connection.codec.edge_by_label.get(
            edge_label
        )
        if edge is None:
            raise ValueError("unknown edge label")
        if edge.source != self.state.node:
            raise ValueError(
                "edge does not leave horizontal causal node"
            )

        source_index = self.field.node_index[
            edge.source
        ]
        source_size = self.vector[source_index]
        if source_size != self.state.fiber_size:
            raise AssertionError(
                "forward cursor source fiber size diverged"
            )
        if not 0 <= self.state.rank < source_size:
            raise AssertionError(
                "forward cursor rank outside source fiber"
            )

        offset = 0
        found = False
        for incoming in self.connection.codec.incoming[
            edge.target
        ]:
            if incoming == edge:
                found = True
                break
            offset += self.vector[
                self.field.node_index[incoming.source]
            ]
        if not found:
            raise ValueError(
                "edge is not incoming to its target"
            )

        next_vector = self.field.step_vector(
            self.vector
        )
        target_size = next_vector[
            self.field.node_index[edge.target]
        ]
        next_rank = offset + self.state.rank

        if not 0 <= next_rank < target_size:
            raise AssertionError(
                "forward embedding lies outside target fiber"
            )

        self.vector = next_vector
        self._forward_steps += 1
        self.state = LocalFiberState(
            time=self.state.time + 1,
            node=edge.target,
            rank=next_rank,
            fiber_size=target_size,
        )
        return edge

    def pack_current(self) -> int:
        offset = 0
        for node in self.machine.nodes:
            if node == self.state.node:
                break
            offset += self.vector[
                self.field.node_index[node]
            ]
        else:
            raise AssertionError(
                "current node missing from public node order"
            )

        packed = offset + self.state.rank
        total = sum(self.vector)
        if not 0 <= packed < total:
            raise AssertionError(
                "packed forward cursor state outside family"
            )
        return packed

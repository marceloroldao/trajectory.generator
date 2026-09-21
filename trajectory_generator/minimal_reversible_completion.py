"""General finite-horizon minimal reversible completion of a causal graph.

This module separates what is FORCED by exact reversibility from what is only a
choice of vertical coordinates.

For a finite directed multigraph with public start nodes, let H_t(v) be the set
of length-t edge histories ending at causal node v.

Any exact reversible lift projecting onto the same causal graph must have at
least |H_t(v)| lifted states above v, because distinct histories ending at the
same raw node must remain distinguishable.

A minimal lift therefore has fiber cardinality exactly:

    |F_t(v)| = |H_t(v)|.

Furthermore, for each target v at time t+1, predecessor edge images have forced
cardinalities:

    |image(e:u->v)| = |H_t(u)|

and those images partition F_(t+1)(v).

What is NOT forced is the labeling inside each image.  Any permutation of the
source fiber before embedding into its target edge block preserves exact
reversibility and the horizontal causal projection.

This internal permutation freedom is a vertical gauge freedom.

The module provides an explicit history model and compares arbitrary gauge laws
without relying on trajectory.generator's Floquet implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Hashable, Mapping, Sequence


Node = Hashable


@dataclass(frozen=True)
class CausalEdge:
    label: str
    source: Node
    target: Node


@dataclass(frozen=True)
class History:
    start: Node
    edges: tuple[str, ...]
    endpoint: Node


@dataclass(frozen=True)
class LiftedState:
    node: Node
    vertical: int


PermutationLaw = Callable[
    [CausalEdge, int, int, int],
    int,
]
# args: edge, time, vertical, fiber_size -> permuted vertical


class MinimalReversibleCompletion:
    """Exact finite-horizon history lift with pluggable vertical gauge."""

    def __init__(
        self,
        adjacency: Mapping[Node, Sequence[Node]],
        *,
        start_nodes: Sequence[Node],
        edge_order: Mapping[Node, Sequence[Node]] | None = None,
    ) -> None:
        if not start_nodes:
            raise ValueError("start_nodes must be non-empty")

        self.start_nodes = tuple(start_nodes)

        nodes = set(adjacency)
        for targets in adjacency.values():
            nodes.update(targets)
        self.nodes = tuple(sorted(nodes, key=repr))

        order = adjacency if edge_order is None else edge_order

        edges: list[CausalEdge] = []
        outgoing: dict[Node, list[CausalEdge]] = {
            node: [] for node in self.nodes
        }
        incoming: dict[Node, list[CausalEdge]] = {
            node: [] for node in self.nodes
        }

        for source in self.nodes:
            targets = tuple(order.get(source, adjacency.get(source, ())))
            actual = tuple(adjacency.get(source, ()))
            if sorted(map(repr, targets)) != sorted(map(repr, actual)):
                raise ValueError(
                    "edge_order must contain the same target multiset"
                )
            for i, target in enumerate(targets):
                edge = CausalEdge(
                    label=f"e{self.nodes.index(source)}.{i}",
                    source=source,
                    target=target,
                )
                edges.append(edge)
                outgoing[source].append(edge)
                incoming[target].append(edge)

        self.edges = tuple(edges)
        self.outgoing = {
            node: tuple(value)
            for node, value in outgoing.items()
        }
        self.incoming = {
            node: tuple(value)
            for node, value in incoming.items()
        }
        self.edge_by_label = {
            edge.label: edge
            for edge in self.edges
        }

        self._histories: list[
            dict[Node, tuple[History, ...]]
        ] = []

        initial: dict[Node, list[History]] = {
            node: [] for node in self.nodes
        }
        for start in self.start_nodes:
            if start not in initial:
                raise ValueError("start node absent from graph")
            initial[start].append(
                History(
                    start=start,
                    edges=(),
                    endpoint=start,
                )
            )
        self._histories.append(
            {
                node: tuple(rows)
                for node, rows in initial.items()
            }
        )

    def ensure_horizon(self, time: int) -> None:
        if time < 0:
            raise ValueError("time must be >= 0")

        while len(self._histories) <= time:
            previous = self._histories[-1]
            nxt: dict[Node, list[History]] = {
                node: [] for node in self.nodes
            }

            # The ordered predecessor blocks are part of this concrete
            # coordinatization.  Histories are grouped by target incoming edge.
            for target in self.nodes:
                for edge in self.incoming[target]:
                    for history in previous[edge.source]:
                        nxt[target].append(
                            History(
                                start=history.start,
                                edges=history.edges + (edge.label,),
                                endpoint=target,
                            )
                        )

            self._histories.append(
                {
                    node: tuple(rows)
                    for node, rows in nxt.items()
                }
            )

    def histories(
        self,
        node: Node,
        time: int,
    ) -> tuple[History, ...]:
        self.ensure_horizon(time)
        return self._histories[time][node]

    def fiber_size(self, node: Node, time: int) -> int:
        return len(self.histories(node, time))

    def total_histories(self, time: int) -> int:
        self.ensure_horizon(time)
        return sum(
            len(rows)
            for rows in self._histories[time].values()
        )

    def incoming_blocks(
        self,
        target: Node,
        time: int,
    ) -> tuple[tuple[CausalEdge, int, int], ...]:
        """Return forced-cardinality edge blocks in one target fiber at t+1."""
        self.ensure_horizon(time)

        blocks = []
        offset = 0
        for edge in self.incoming[target]:
            size = self.fiber_size(edge.source, time)
            if size:
                blocks.append((edge, offset, offset + size))
                offset += size
        return tuple(blocks)

    def minimality_certificate(
        self,
        node: Node,
        time: int,
    ) -> tuple[int, int]:
        """Return (distinct histories, required minimum lifted states)."""
        count = self.fiber_size(node, time)
        return count, count

    def history_at(
        self,
        state: LiftedState,
        time: int,
        *,
        gauge: PermutationLaw | None = None,
    ) -> History:
        """Interpret a vertical coordinate as the underlying history.

        Gauge coordinates are defined recursively through edge-block maps.  For
        time zero the vertical coordinate directly indexes start multiplicity.
        For later times, locate the incoming edge block, invert its source-fiber
        permutation by exhaustive finite lookup, then recurse.
        """
        if state.vertical < 0:
            raise ValueError("vertical must be non-negative")
        size = self.fiber_size(state.node, time)
        if state.vertical >= size:
            raise ValueError("vertical outside fiber")

        if time == 0:
            return self.histories(state.node, 0)[state.vertical]

        for edge, start, end in self.incoming_blocks(
            state.node,
            time - 1,
        ):
            if start <= state.vertical < end:
                local = state.vertical - start
                source_size = end - start

                if gauge is None:
                    previous_vertical = local
                else:
                    inverse = [
                        candidate
                        for candidate in range(source_size)
                        if gauge(
                            edge,
                            time - 1,
                            candidate,
                            source_size,
                        ) == local
                    ]
                    if len(inverse) != 1:
                        raise ValueError(
                            "gauge law is not a permutation"
                        )
                    previous_vertical = inverse[0]

                previous_history = self.history_at(
                    LiftedState(
                        edge.source,
                        previous_vertical,
                    ),
                    time - 1,
                    gauge=gauge,
                )
                return History(
                    start=previous_history.start,
                    edges=(
                        previous_history.edges
                        + (edge.label,)
                    ),
                    endpoint=edge.target,
                )

        raise AssertionError("no predecessor block found")

    def state_for_history(
        self,
        history: History,
        time: int,
        *,
        gauge: PermutationLaw | None = None,
    ) -> LiftedState:
        """Return the vertical coordinate of one concrete history."""
        if len(history.edges) != time:
            raise ValueError("history length does not match time")

        if time == 0:
            rows = self.histories(history.endpoint, 0)
            for i, candidate in enumerate(rows):
                if candidate == history:
                    return LiftedState(history.endpoint, i)
            raise ValueError("history is not admissible")

        last_label = history.edges[-1]
        edge = self.edge_by_label.get(last_label)
        if edge is None or edge.target != history.endpoint:
            raise ValueError("history has invalid final edge")

        prefix_endpoint = edge.source
        prefix = History(
            start=history.start,
            edges=history.edges[:-1],
            endpoint=prefix_endpoint,
        )
        previous = self.state_for_history(
            prefix,
            time - 1,
            gauge=gauge,
        )

        block_start = None
        block_end = None
        for candidate, start, end in self.incoming_blocks(
            edge.target,
            time - 1,
        ):
            if candidate == edge:
                block_start = start
                block_end = end
                break

        if block_start is None or block_end is None:
            raise AssertionError("edge block not found")

        size = block_end - block_start
        local = previous.vertical
        if gauge is not None:
            local = gauge(edge, time - 1, local, size)
            if not 0 <= local < size:
                raise ValueError(
                    "gauge law mapped outside source fiber"
                )

        return LiftedState(
            node=edge.target,
            vertical=block_start + local,
        )

    def advance(
        self,
        state: LiftedState,
        time: int,
        edge_label: str,
        *,
        gauge: PermutationLaw | None = None,
    ) -> LiftedState:
        edge = self.edge_by_label.get(edge_label)
        if edge is None:
            raise ValueError("unknown edge")
        if edge.source != state.node:
            raise ValueError("edge does not leave state node")

        size = self.fiber_size(state.node, time)
        if not 0 <= state.vertical < size:
            raise ValueError("vertical outside source fiber")

        block = next(
            (
                (start, end)
                for candidate, start, end
                in self.incoming_blocks(edge.target, time)
                if candidate == edge
            ),
            None,
        )
        if block is None:
            raise ValueError("edge has empty source fiber")

        start, end = block
        local = state.vertical
        if gauge is not None:
            local = gauge(edge, time, local, size)

        if not 0 <= local < size:
            raise ValueError("gauge is not fiber-preserving")

        target = LiftedState(
            node=edge.target,
            vertical=start + local,
        )
        if target.vertical >= self.fiber_size(
            edge.target,
            time + 1,
        ):
            raise AssertionError("target outside target fiber")
        return target

    def rewind(
        self,
        state: LiftedState,
        time: int,
        *,
        gauge: PermutationLaw | None = None,
    ) -> tuple[LiftedState, CausalEdge]:
        if time <= 0:
            raise ValueError("cannot rewind t=0")

        if not 0 <= state.vertical < self.fiber_size(
            state.node,
            time,
        ):
            raise ValueError("vertical outside target fiber")

        for edge, start, end in self.incoming_blocks(
            state.node,
            time - 1,
        ):
            if start <= state.vertical < end:
                local = state.vertical - start
                size = end - start

                if gauge is None:
                    previous_vertical = local
                else:
                    inverse = [
                        candidate
                        for candidate in range(size)
                        if gauge(
                            edge,
                            time - 1,
                            candidate,
                            size,
                        ) == local
                    ]
                    if len(inverse) != 1:
                        raise ValueError(
                            "gauge law is not a permutation"
                        )
                    previous_vertical = inverse[0]

                return (
                    LiftedState(
                        node=edge.source,
                        vertical=previous_vertical,
                    ),
                    edge,
                )

        raise AssertionError("target state has no predecessor block")

    def gauge_map(
        self,
        state: LiftedState,
        time: int,
        *,
        source_gauge: PermutationLaw | None,
        target_gauge: PermutationLaw | None,
    ) -> LiftedState:
        """Map coordinates between two gauge choices via underlying history."""
        history = self.history_at(
            state,
            time,
            gauge=source_gauge,
        )
        return self.state_for_history(
            history,
            time,
            gauge=target_gauge,
        )

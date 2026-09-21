"""Streaming enumerative address for a public weighted macrograph.

A path evolves only at entropy-bearing macro-events. Each public macro-edge has
an integer physical length and may carry the deterministic physical path that it
represents.

For each physical time t and endpoint node v, let D[v,t] be the number of public
macro-paths that start in an allowed initial node, consume exactly t physical
steps, and end at v.

Paths ending at v are partitioned into public blocks by their final incoming
edge. The block for e=(u->v,length=L) has exactly D[u,t-L] members.

Forward:
    append edge e and place the predecessor rank inside e's block.

Reverse:
    inspect the current endpoint bucket and rank; the incoming-edge block that
    contains the rank identifies the unique final macro-edge.

This is the weighted-graph analogue of streaming colex. The DP counts depend
only on the public graph and physical time; no trajectory history is stored.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Hashable, Iterable, Sequence


Node = Hashable


@dataclass(frozen=True)
class WeightedEdge:
    label: str
    source: Node
    target: Node
    length: int
    path: tuple[Any, ...] = ()


class WeightedPathCodec:
    def __init__(
        self,
        nodes: Sequence[Node],
        edges: Sequence[WeightedEdge],
        *,
        start_nodes: Sequence[Node] | None = None,
        width: int | None = None,
    ) -> None:
        self.nodes = tuple(nodes)
        if not self.nodes or len(set(self.nodes)) != len(self.nodes):
            raise ValueError("nodes must be non-empty and unique")
        self.node_set = set(self.nodes)

        self.edges = tuple(edges)
        labels = set()
        for edge in self.edges:
            if edge.label in labels:
                raise ValueError("edge labels must be globally unique")
            labels.add(edge.label)
            if edge.source not in self.node_set or edge.target not in self.node_set:
                raise ValueError("edge endpoint outside node set")
            if edge.length <= 0:
                raise ValueError("edge length must be positive")
            if edge.path:
                if len(edge.path) != edge.length + 1:
                    raise ValueError("edge path length does not match physical length")
                if edge.path[0] != edge.source or edge.path[-1] != edge.target:
                    raise ValueError("edge path endpoints do not match edge")

        self.edge_by_label = {edge.label: edge for edge in self.edges}
        self.incoming = {node: [] for node in self.nodes}
        self.outgoing = {node: [] for node in self.nodes}
        for edge in self.edges:
            self.incoming[edge.target].append(edge)
            self.outgoing[edge.source].append(edge)

        self.start_nodes = tuple(self.nodes if start_nodes is None else start_nodes)
        if not self.start_nodes or any(node not in self.node_set for node in self.start_nodes):
            raise ValueError("start_nodes must be a non-empty subset of nodes")
        if len(set(self.start_nodes)) != len(self.start_nodes):
            raise ValueError("start_nodes must be unique")
        self.start_set = set(self.start_nodes)

        if width is not None and width < 1:
            raise ValueError("width must be >= 1")
        self.width = width

        self._counts: list[dict[Node, int]] = [
            {node: int(node in self.start_set) for node in self.nodes}
        ]

    def _ensure_counts(self, physical_steps: int) -> None:
        if physical_steps < 0:
            return
        while len(self._counts) <= physical_steps:
            t = len(self._counts)
            row = {}
            for target in self.nodes:
                total = 0
                for edge in self.incoming[target]:
                    prev_t = t - edge.length
                    if prev_t >= 0:
                        total += self._counts[prev_t][edge.source]
                row[target] = total
            self._counts.append(row)

    def count_node(self, node: Node, physical_steps: int) -> int:
        if node not in self.node_set:
            raise KeyError(node)
        if physical_steps < 0:
            return 0
        self._ensure_counts(physical_steps)
        return self._counts[physical_steps][node]

    def total_count(self, physical_steps: int) -> int:
        if physical_steps < 0:
            raise ValueError("physical_steps must be >= 0")
        self._ensure_counts(physical_steps)
        return sum(self._counts[physical_steps].values())

    def capacity_ok(self, physical_steps: int) -> bool:
        if self.width is None:
            return True
        return self.total_count(physical_steps) <= (1 << self.width)

    def _pack(self, node: Node, rank: int, physical_steps: int) -> int:
        if node not in self.node_set:
            raise KeyError(node)
        offset = 0
        for candidate in self.nodes:
            count = self.count_node(candidate, physical_steps)
            if candidate == node:
                if not 0 <= rank < count:
                    raise ValueError("rank outside endpoint bucket")
                state = offset + rank
                if self.width is not None and state >= (1 << self.width):
                    raise ValueError("state exceeds configured width")
                return state
            offset += count
        raise AssertionError("unreachable node bucket")

    def _unpack(self, state: int, physical_steps: int) -> tuple[Node, int]:
        if state < 0:
            raise ValueError("state must be non-negative")
        total = self.total_count(physical_steps)
        if state >= total:
            raise ValueError("state outside exact-length path family")
        remaining = state
        for node in self.nodes:
            count = self.count_node(node, physical_steps)
            if remaining < count:
                return node, remaining
            remaining -= count
        raise AssertionError("unreachable endpoint bucket")

    def initial_state(self, node: Node) -> int:
        if node not in self.start_set:
            raise ValueError("node is not an allowed start")
        return self._pack(node, 0, 0)

    def forward_step(
        self,
        state: int,
        physical_steps: int,
        edge_label: str,
    ) -> tuple[int, int]:
        source, rank = self._unpack(state, physical_steps)
        try:
            edge = self.edge_by_label[edge_label]
        except KeyError as exc:
            raise ValueError("unknown edge label") from exc
        if edge.source != source:
            raise ValueError("edge does not leave current endpoint")

        new_steps = physical_steps + edge.length
        if not self.capacity_ok(new_steps):
            raise ValueError("new exact-length family exceeds configured width")

        offset = 0
        for incoming in self.incoming[edge.target]:
            prev_t = new_steps - incoming.length
            block = self.count_node(incoming.source, prev_t) if prev_t >= 0 else 0
            if incoming == edge:
                if prev_t != physical_steps:
                    raise AssertionError("edge timing mismatch")
                if rank >= block:
                    raise AssertionError("predecessor rank outside incoming block")
                return self._pack(edge.target, offset + rank, new_steps), new_steps
            offset += block
        raise AssertionError("edge missing from target incoming list")

    def reverse_step(
        self,
        state: int,
        physical_steps: int,
    ) -> tuple[int, int, WeightedEdge]:
        if physical_steps <= 0:
            raise ValueError("cannot reverse an initial state")
        target, rank = self._unpack(state, physical_steps)

        offset = 0
        for edge in self.incoming[target]:
            prev_t = physical_steps - edge.length
            if prev_t < 0:
                continue
            block = self.count_node(edge.source, prev_t)
            if rank < offset + block:
                prev_rank = rank - offset
                prev_state = self._pack(edge.source, prev_rank, prev_t)
                return prev_state, prev_t, edge
            offset += block

        raise ValueError("state has no valid predecessor macro-edge")

    def encode_edges(
        self,
        start_node: Node,
        edge_labels: Iterable[str],
    ) -> tuple[int, int]:
        state = self.initial_state(start_node)
        physical_steps = 0
        for label in edge_labels:
            state, physical_steps = self.forward_step(state, physical_steps, label)
        return state, physical_steps

    def decode_edges(
        self,
        final_state: int,
        physical_steps: int,
    ) -> tuple[Node, list[WeightedEdge]]:
        current = final_state
        t = physical_steps
        reversed_edges = []
        while t > 0:
            current, t, edge = self.reverse_step(current, t)
            reversed_edges.append(edge)
        start, rank = self._unpack(current, 0)
        if rank != 0 or start not in self.start_set:
            raise AssertionError("reverse did not terminate in an initial state")
        reversed_edges.reverse()
        return start, reversed_edges

    def reconstruct_physical_path(
        self,
        final_state: int,
        physical_steps: int,
    ) -> tuple[Any, ...]:
        start, edges = self.decode_edges(final_state, physical_steps)
        path = [start]
        for edge in edges:
            if not edge.path:
                raise ValueError("physical path metadata missing for edge")
            if edge.path[0] != path[-1]:
                raise AssertionError("macro-edge path is discontinuous")
            path.extend(edge.path[1:])
        if len(path) != physical_steps + 1:
            raise AssertionError("reconstructed physical path has wrong length")
        return tuple(path)

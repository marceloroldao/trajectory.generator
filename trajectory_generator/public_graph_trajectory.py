"""Exact streaming path address for a complete public transition graph.

This is the most general finite-state construction currently used by
trajectory.generator.

Given:
- a public directed multigraph;
- a public set of allowed initial nodes;
- a final address width;

every admissible graph path of a fixed physical length is assigned one integer
address. The address evolves online one edge at a time and reverses one edge at
a time.

For each node v and time t, D(v,t) is the number of admissible paths that start
from the public initial-node set and end at v after exactly t edges. Incoming
edges partition D(v,t) into public contiguous rank blocks. A forward step places
the predecessor rank into the selected edge block. A reverse step identifies
the predecessor edge from the block containing the current rank.

This is an enumerative address state derived from the public universe graph. It
must not be confused with a claim that the universe's raw causal node alone
contains the complete trajectory history.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Hashable, Mapping, Sequence

from .weighted_path_trajectory import WeightedEdge, WeightedPathCodec


Node = Hashable


def _stable_key(value: Node) -> str:
    return repr(value)


@dataclass(frozen=True)
class PublicGraphStructure:
    nodes: tuple[Node, ...]
    edges: tuple[WeightedEdge, ...]


def derive_public_graph_structure(
    adjacency: Mapping[Node, Sequence[Node]],
) -> PublicGraphStructure:
    nodes_set = set(adjacency)
    for targets in adjacency.values():
        nodes_set.update(targets)

    if not nodes_set:
        raise ValueError("public graph must contain at least one node")

    nodes = tuple(sorted(nodes_set, key=_stable_key))
    node_index = {node: i for i, node in enumerate(nodes)}
    edges: list[WeightedEdge] = []

    for source in nodes:
        for outgoing_index, target in enumerate(adjacency.get(source, ())):
            edges.append(
                WeightedEdge(
                    label=f"g{node_index[source]}.{outgoing_index}",
                    source=source,
                    target=target,
                    length=1,
                    path=(source, target),
                )
            )

    return PublicGraphStructure(
        nodes=nodes,
        edges=tuple(edges),
    )


def build_public_graph_codec(
    adjacency: Mapping[Node, Sequence[Node]],
    *,
    start_nodes: Sequence[Node],
    width: int | None = 63,
) -> tuple[PublicGraphStructure, WeightedPathCodec]:
    structure = derive_public_graph_structure(adjacency)

    starts = tuple(start_nodes)
    if not starts:
        raise ValueError("start_nodes must be non-empty")
    unknown = set(starts) - set(structure.nodes)
    if unknown:
        raise ValueError(f"start node outside public graph: {unknown!r}")

    codec = WeightedPathCodec(
        structure.nodes,
        structure.edges,
        start_nodes=starts,
        width=width,
    )
    return structure, codec


def monotone_graph_frontier(codec: WeightedPathCodec) -> int:
    """Largest consecutive transition horizon fitting the configured width."""
    if codec.width is None:
        raise ValueError("frontier requires a finite codec width")

    t = 0
    while codec.capacity_ok(t + 1):
        t += 1
    return t

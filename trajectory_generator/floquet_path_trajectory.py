"""Public graph path codec backed by a phase/Floquet count recurrence."""

from __future__ import annotations

from typing import Callable, Hashable, Mapping, Sequence

from .floquet_count_field import FloquetCountFieldRecurrence
from .recurrence_path_trajectory import RecurrencePathCodec
from .weighted_path_trajectory import WeightedEdge


Node = Hashable
PhaseFunction = Callable[[Node], int]


def build_floquet_path_codec(
    adjacency: Mapping[Node, Sequence[Node]],
    *,
    start_nodes: Sequence[Node],
    phase_of: PhaseFunction,
    period: int,
    base_phase: int = 0,
    width: int | None = 63,
    cache_rows: int = 2,
) -> RecurrencePathCodec:
    field = FloquetCountFieldRecurrence(
        adjacency,
        start_nodes=start_nodes,
        phase_of=phase_of,
        period=period,
        base_phase=base_phase,
        cache_rows=cache_rows,
    )

    nodes = field.nodes
    node_index = {
        node: i
        for i, node in enumerate(nodes)
    }

    edges: list[WeightedEdge] = []
    for source in nodes:
        for outgoing_index, target in enumerate(
            adjacency.get(source, ())
        ):
            if target not in node_index:
                raise AssertionError(
                    "reachable subgraph is not forward-closed"
                )
            edges.append(
                WeightedEdge(
                    label=f"f{node_index[source]}.{outgoing_index}",
                    source=source,
                    target=target,
                    length=1,
                    path=(source, target),
                )
            )

    return RecurrencePathCodec(
        nodes,
        edges,
        start_nodes=tuple(start_nodes),
        width=width,
        count_field=field,
    )

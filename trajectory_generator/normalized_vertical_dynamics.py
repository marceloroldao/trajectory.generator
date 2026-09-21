"""Normalized vertical fiber dynamics and reverse Parry geometry.

At physical time t, the exact history fiber over causal state v has D_t(v)
discrete states. Normalize its rank coordinate to the unit interval.

For a causal edge e:u->v, exact reversibility assigns a target sub-fiber of
size D_t(u) inside the full target fiber D_(t+1)(v). Its normalized width is

    q_t(e) = D_t(u) / D_(t+1)(v).

Inside a chosen incoming-edge ordering, forward transport is an affine map

    x' = offset_t(e) + q_t(e) * x,

and reverse transport identifies the block and expands

    x = (x' - offset_t(e)) / q_t(e).

The offset depends on the chart ordering of incoming edges, but the block width
does not.

On an irreducible recurrent core, along one periodic phase class, q_t(e)
converges to the reverse Parry edge probability

    q(e | v) = pi(u) p(e | u) / pi(v),

where p is the maximum-entropy forward transition law and pi its stationary
distribution.

The stationary mean vertical contraction information is

    E[-log2 q(e | v)] = log2(lambda)

per physical step. Thus the normalized fiber geometry gives a local geometric
form of the same topological/vertical entropy rate.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import log2
from typing import Hashable, Mapping, Sequence

from .information_clock_statistics import (
    InformationClockStatistics,
)
from .weighted_path_trajectory import WeightedEdge


Node = Hashable


@dataclass(frozen=True)
class ReverseEdgeProbability:
    label: str
    source: Node
    target: Node
    probability: float
    stationary_edge_flow: float
    information_bits: float


@dataclass(frozen=True)
class ReverseParryGeometry:
    reverse_probabilities: tuple[ReverseEdgeProbability, ...]
    maximum_target_normalization_residual: float
    expected_reverse_information_bits: float


def reverse_parry_geometry(
    nodes: Sequence[Node],
    statistics: InformationClockStatistics,
) -> ReverseParryGeometry:
    nodes = tuple(nodes)
    if len(nodes) != len(statistics.branch_stationary):
        raise ValueError(
            "node order must match the information-clock statistics"
        )

    index = {node: i for i, node in enumerate(nodes)}
    stationary = statistics.branch_stationary

    rows = []
    target_sums = {
        node: 0.0
        for node in nodes
    }
    expected_bits = 0.0

    for edge in statistics.event_probabilities:
        i = index[edge.source]
        j = index[edge.target]
        flow = stationary[i] * edge.probability
        if stationary[j] <= 0.0:
            raise ValueError(
                "target has zero stationary probability"
            )

        reverse_probability = (
            flow / stationary[j]
        )
        reverse_probability = max(
            0.0,
            reverse_probability,
        )
        target_sums[edge.target] += (
            reverse_probability
        )

        information = (
            -log2(reverse_probability)
            if reverse_probability > 0.0
            else float("inf")
        )
        expected_bits += flow * information

        rows.append(
            ReverseEdgeProbability(
                label=edge.label,
                source=edge.source,
                target=edge.target,
                probability=reverse_probability,
                stationary_edge_flow=flow,
                information_bits=information,
            )
        )

    residual = max(
        abs(value - 1.0)
        for value in target_sums.values()
    )

    return ReverseParryGeometry(
        reverse_probabilities=tuple(rows),
        maximum_target_normalization_residual=residual,
        expected_reverse_information_bits=expected_bits,
    )


def exact_normalized_block_width(
    counts_before: Mapping[Node, int],
    counts_after: Mapping[Node, int],
    edge: WeightedEdge,
) -> float:
    source_count = counts_before.get(
        edge.source,
        0,
    )
    target_count = counts_after.get(
        edge.target,
        0,
    )
    if source_count < 0 or target_count < 0:
        raise ValueError("counts must be non-negative")
    if target_count <= 0:
        raise ValueError(
            "target fiber must be populated"
        )
    return source_count / target_count


def exact_target_partition_residual(
    counts_before: Mapping[Node, int],
    counts_after: Mapping[Node, int],
    edges: Sequence[WeightedEdge],
) -> float:
    sums: dict[Node, float] = {}
    targets = {
        edge.target
        for edge in edges
        if counts_after.get(edge.target, 0) > 0
    }

    for target in targets:
        sums[target] = 0.0

    for edge in edges:
        if edge.target not in sums:
            continue
        sums[edge.target] += (
            exact_normalized_block_width(
                counts_before,
                counts_after,
                edge,
            )
        )

    if not sums:
        return 0.0
    return max(
        abs(value - 1.0)
        for value in sums.values()
    )


def normalized_forward(
    local_coordinate: float,
    *,
    block_offset: float,
    block_width: float,
) -> float:
    if not 0.0 <= local_coordinate <= 1.0:
        raise ValueError(
            "local_coordinate must lie in [0,1]"
        )
    if block_width <= 0.0:
        raise ValueError(
            "block_width must be positive"
        )
    return (
        block_offset
        + block_width * local_coordinate
    )


def normalized_reverse(
    target_coordinate: float,
    *,
    block_offset: float,
    block_width: float,
) -> float:
    if block_width <= 0.0:
        raise ValueError(
            "block_width must be positive"
        )
    return (
        target_coordinate - block_offset
    ) / block_width

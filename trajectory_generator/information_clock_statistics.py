"""Maximum-entropy statistics of a weighted information-clock macrograph.

For a weighted recurrent macrograph, each macro-edge e has physical length L_e.
Let lambda > 1 be the physical-time Perron growth factor and define the weighted
transfer matrix

    W_ij(lambda) = sum_{e:i->j} lambda^(-L_e).

At the correct lambda, rho(W)=1. Let r,l be positive right/left Perron
eigenvectors:

    W r = r
    l W = l.

Then the maximum-entropy macroevent transition probability is

    p(e | i) = lambda^(-L_e) * r_j / r_i.

The stationary branch-state probability is proportional to l_i*r_i.

Two averages follow:

    <L> = mean physical steps per information event
    H_event = mean Shannon entropy per information event.

Using stationarity,

    H_event = <L> * log2(lambda),

so:

    H_event / <L> = log2(lambda).

This is the exact bridge between the information clock and the asymptotic
vertical-memory rate. The event clock decides *when* entropy is created; the
vertical history fiber is where that entropy is retained for exact reversal.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import log2
from typing import Hashable, Sequence

from .weighted_path_trajectory import WeightedEdge


Node = Hashable


@dataclass(frozen=True)
class EventProbability:
    label: str
    source: Node
    target: Node
    length: int
    probability: float


@dataclass(frozen=True)
class InformationClockStatistics:
    growth_rate: float
    bits_per_physical_step: float
    average_physical_steps_per_event: float
    bits_per_information_event: float
    events_per_physical_step: float
    reconstructed_bits_per_physical_step: float
    identity_residual: float
    branch_stationary: tuple[float, ...]
    event_probabilities: tuple[EventProbability, ...]
    maximum_row_probability_residual: float
    stationary_residual: float


def _transfer_matrix(
    nodes: Sequence[Node],
    edges: Sequence[WeightedEdge],
    growth_rate: float,
) -> list[list[float]]:
    index = {node: i for i, node in enumerate(nodes)}
    matrix = [
        [0.0 for _ in nodes]
        for _ in nodes
    ]
    for edge in edges:
        matrix[index[edge.source]][index[edge.target]] += (
            growth_rate ** (-edge.length)
        )
    return matrix


def _transpose(matrix: list[list[float]]) -> list[list[float]]:
    return [
        [matrix[j][i] for j in range(len(matrix))]
        for i in range(len(matrix))
    ]


def _solve_linear_system(
    matrix: list[list[float]],
    vector: list[float],
) -> list[float]:
    n = len(matrix)
    if n == 0 or any(len(row) != n for row in matrix):
        raise ValueError("matrix must be non-empty and square")
    if len(vector) != n:
        raise ValueError("vector size mismatch")

    a = [
        [float(value) for value in row]
        + [float(vector[i])]
        for i, row in enumerate(matrix)
    ]

    for col in range(n):
        pivot = max(
            range(col, n),
            key=lambda row: abs(a[row][col]),
        )
        if abs(a[pivot][col]) < 1e-15:
            raise ValueError("singular normalization system")
        if pivot != col:
            a[col], a[pivot] = a[pivot], a[col]

        scale = a[col][col]
        for j in range(col, n + 1):
            a[col][j] /= scale

        for row in range(n):
            if row == col:
                continue
            factor = a[row][col]
            if factor == 0.0:
                continue
            for j in range(col, n + 1):
                a[row][j] -= factor * a[col][j]

    return [a[i][n] for i in range(n)]


def _unit_eigenvector(
    matrix: list[list[float]],
) -> list[float]:
    n = len(matrix)
    if n == 0:
        raise ValueError("matrix must be non-empty")

    system = [
        [
            matrix[i][j] - (1.0 if i == j else 0.0)
            for j in range(n)
        ]
        for i in range(n)
    ]
    target = [0.0] * n

    # Replace one dependent eigen-equation by sum(x)=1.
    system[-1] = [1.0] * n
    target[-1] = 1.0

    value = _solve_linear_system(system, target)

    if sum(value) < 0.0:
        value = [-item for item in value]

    if min(value) < -1e-10:
        raise ValueError("Perron vector is not positive")

    value = [max(0.0, item) for item in value]
    norm = sum(value)
    if norm <= 0.0:
        raise ValueError("zero Perron vector")
    return [item / norm for item in value]


def information_clock_statistics(
    nodes: Sequence[Node],
    edges: Sequence[WeightedEdge],
    *,
    growth_rate: float,
) -> InformationClockStatistics:
    nodes = tuple(nodes)
    edges = tuple(edges)

    if not nodes:
        raise ValueError("nodes must be non-empty")
    if growth_rate <= 0.0:
        raise ValueError("growth_rate must be positive")

    node_set = set(nodes)
    if len(node_set) != len(nodes):
        raise ValueError("nodes must be unique")
    if not edges:
        raise ValueError("edges must be non-empty")
    if any(
        edge.source not in node_set
        or edge.target not in node_set
        for edge in edges
    ):
        raise ValueError("edge endpoint outside node set")

    matrix = _transfer_matrix(
        nodes,
        edges,
        growth_rate,
    )
    right = _unit_eigenvector(matrix)
    left = _unit_eigenvector(_transpose(matrix))

    stationary_raw = [
        left[i] * right[i]
        for i in range(len(nodes))
    ]
    stationary_norm = sum(stationary_raw)
    if stationary_norm <= 0.0:
        raise ValueError("invalid stationary normalization")
    stationary = [
        value / stationary_norm
        for value in stationary_raw
    ]

    index = {node: i for i, node in enumerate(nodes)}
    probabilities: list[EventProbability] = []
    row_sums = [0.0] * len(nodes)

    average_length = 0.0
    event_entropy = 0.0

    # State transition matrix under the event process.
    transition = [
        [0.0 for _ in nodes]
        for _ in nodes
    ]

    for edge in edges:
        i = index[edge.source]
        j = index[edge.target]
        probability = (
            growth_rate ** (-edge.length)
            * right[j]
            / right[i]
        )
        if probability < -1e-12:
            raise ValueError("negative event probability")
        probability = max(0.0, probability)

        row_sums[i] += probability
        transition[i][j] += probability
        probabilities.append(
            EventProbability(
                label=edge.label,
                source=edge.source,
                target=edge.target,
                length=edge.length,
                probability=probability,
            )
        )

        weighted = stationary[i] * probability
        average_length += weighted * edge.length
        if probability > 0.0:
            event_entropy += (
                weighted * -log2(probability)
            )

    row_residual = max(
        abs(value - 1.0)
        for value in row_sums
    )

    stationary_after = [0.0] * len(nodes)
    for i in range(len(nodes)):
        for j in range(len(nodes)):
            stationary_after[j] += (
                stationary[i] * transition[i][j]
            )
    stationary_residual = max(
        abs(stationary_after[i] - stationary[i])
        for i in range(len(nodes))
    )

    if average_length <= 0.0:
        raise ValueError("average event length must be positive")

    event_rate = 1.0 / average_length
    reconstructed = event_entropy / average_length
    target = log2(growth_rate)

    return InformationClockStatistics(
        growth_rate=growth_rate,
        bits_per_physical_step=target,
        average_physical_steps_per_event=average_length,
        bits_per_information_event=event_entropy,
        events_per_physical_step=event_rate,
        reconstructed_bits_per_physical_step=reconstructed,
        identity_residual=reconstructed - target,
        branch_stationary=tuple(stationary),
        event_probabilities=tuple(probabilities),
        maximum_row_probability_residual=row_residual,
        stationary_residual=stationary_residual,
    )

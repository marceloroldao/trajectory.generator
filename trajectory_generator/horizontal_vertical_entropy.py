"""Exact horizontal/vertical entropy decomposition of reversible history space.

At physical time t, let D_t(v) be the number of admissible histories ending at
raw causal node v and let:

    N_t = sum_v D_t(v).

Under the uniform measure on the exact admissible history family, the endpoint
probability is:

    p_t(v) = D_t(v) / N_t.

Define:

    H_total(t)      = log2 N_t
    H_horizontal(t) = H(endpoint node)
    H_vertical(t)   = H(history | endpoint node).

Because each history is equiprobable and the conditional distribution within a
fiber has D_t(v) equiprobable members:

    H_vertical(t)
      = sum_v p_t(v) log2 D_t(v).

Therefore the chain rule is exact:

    H_total = H_horizontal + H_vertical.

The branch-information budget gives:

    Delta H_total
      = log2(N_(t+1)/N_t).

Thus:

    Delta H_horizontal + Delta H_vertical
      = branch-created information.

When no populated state branches, Delta H_total=0.  Horizontal and vertical
information may still exchange, but their changes are equal and opposite.

This supplies an information-theoretic interpretation of the project's
multilayer geometry:
- horizontal coordinate: current causal state;
- vertical coordinate: unresolved history inside the current causal fiber.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import log2
from typing import Hashable, Mapping


Node = Hashable


@dataclass(frozen=True)
class EntropyDecomposition:
    total_histories: int
    populated_nodes: int
    total_bits: float
    horizontal_bits: float
    vertical_bits: float
    residual: float


@dataclass(frozen=True)
class EntropyFlowStep:
    time: int
    before: EntropyDecomposition
    after: EntropyDecomposition
    branch_created_bits: float
    delta_horizontal_bits: float
    delta_vertical_bits: float
    flow_residual: float
    deterministic: bool


def decompose_counts(
    counts: Mapping[Node, int],
) -> EntropyDecomposition:
    total = sum(counts.values())
    if total <= 0:
        raise ValueError(
            "entropy decomposition requires histories"
        )

    horizontal = 0.0
    vertical = 0.0
    populated = 0

    for count in counts.values():
        if count <= 0:
            continue

        populated += 1
        probability = count / total
        horizontal -= probability * log2(
            probability
        )
        vertical += probability * log2(count)

    total_bits = log2(total)
    residual = (
        total_bits - horizontal - vertical
    )

    return EntropyDecomposition(
        total_histories=total,
        populated_nodes=populated,
        total_bits=total_bits,
        horizontal_bits=horizontal,
        vertical_bits=vertical,
        residual=residual,
    )


def entropy_flow_step(
    before_counts: Mapping[Node, int],
    after_counts: Mapping[Node, int],
    *,
    time: int,
) -> EntropyFlowStep:
    if time < 0:
        raise ValueError("time must be >= 0")

    before = decompose_counts(before_counts)
    after = decompose_counts(after_counts)

    created = (
        after.total_bits - before.total_bits
    )
    delta_horizontal = (
        after.horizontal_bits
        - before.horizontal_bits
    )
    delta_vertical = (
        after.vertical_bits
        - before.vertical_bits
    )

    residual = (
        created
        - delta_horizontal
        - delta_vertical
    )

    return EntropyFlowStep(
        time=time,
        before=before,
        after=after,
        branch_created_bits=created,
        delta_horizontal_bits=delta_horizontal,
        delta_vertical_bits=delta_vertical,
        flow_residual=residual,
        deterministic=(
            after.total_histories
            == before.total_histories
        ),
    )

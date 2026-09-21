"""Asymptotic vertical dominance in finite positive-entropy causal graphs.

Let a finite public causal graph have at most M reachable endpoint nodes.  For
the uniform distribution over all admissible histories of physical length t:

    H_total(t) = log2 N_t

where N_t is the total number of histories, and the exact chain rule gives:

    H_total(t) = H_horizontal(t) + H_vertical(t).

The horizontal variable is only the current causal endpoint, so:

    0 <= H_horizontal(t) <= log2 M.

Therefore:

    H_vertical(t)
      >= H_total(t) - log2 M

and, whenever H_total(t) > 0:

    H_vertical(t) / H_total(t)
      >= 1 - log2(M) / H_total(t).

If the admissible history family has positive asymptotic entropy rate h>0, then
H_total(t) grows without bound (asymptotically h*t up to bounded/periodic
terms), while log2 M is constant. Hence:

    H_vertical(t) / H_total(t) -> 1.

This theorem is coordinate-free. It concerns the amount of history information
hidden inside causal fibers, not any particular numeric vertical chart.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import log2
from typing import Hashable, Mapping

from .horizontal_vertical_entropy import (
    EntropyDecomposition,
    decompose_counts,
)


Node = Hashable


@dataclass(frozen=True)
class VerticalDominanceBound:
    causal_state_count: int
    total_bits: float
    horizontal_bits: float
    vertical_bits: float
    actual_vertical_fraction: float
    lower_bound_vertical_fraction: float
    horizontal_capacity_bits: float


def dominance_bound(
    counts: Mapping[Node, int],
    *,
    causal_state_count: int | None = None,
) -> VerticalDominanceBound:
    decomposition = decompose_counts(counts)

    if causal_state_count is None:
        causal_state_count = len(counts)
    if causal_state_count < 1:
        raise ValueError(
            "causal_state_count must be >= 1"
        )

    horizontal_capacity = log2(
        causal_state_count
    )

    if decomposition.total_bits == 0.0:
        actual_fraction = 0.0
        lower_bound = 0.0
    else:
        actual_fraction = (
            decomposition.vertical_bits
            / decomposition.total_bits
        )
        lower_bound = max(
            0.0,
            1.0
            - horizontal_capacity
            / decomposition.total_bits,
        )

    return VerticalDominanceBound(
        causal_state_count=causal_state_count,
        total_bits=decomposition.total_bits,
        horizontal_bits=decomposition.horizontal_bits,
        vertical_bits=decomposition.vertical_bits,
        actual_vertical_fraction=actual_fraction,
        lower_bound_vertical_fraction=lower_bound,
        horizontal_capacity_bits=horizontal_capacity,
    )


def bound_identity_holds(
    value: VerticalDominanceBound,
    *,
    tolerance: float = 1e-12,
) -> bool:
    return (
        value.horizontal_bits
        <= value.horizontal_capacity_bits
        + tolerance
        and value.vertical_bits
        + tolerance
        >= (
            value.total_bits
            - value.horizontal_capacity_bits
        )
        and value.actual_vertical_fraction
        + tolerance
        >= value.lower_bound_vertical_fraction
    )


def asymptotic_vertical_fraction_lower_bound(
    *,
    causal_state_count: int,
    total_bits: float,
) -> float:
    if causal_state_count < 1:
        raise ValueError(
            "causal_state_count must be >= 1"
        )
    if total_bits <= 0.0:
        return 0.0

    return max(
        0.0,
        1.0
        - log2(causal_state_count)
        / total_bits,
    )


def bits_needed_for_vertical_fraction(
    *,
    causal_state_count: int,
    target_fraction: float,
) -> float:
    """Sufficient total history bits for theorem lower bound >= target."""
    if causal_state_count < 1:
        raise ValueError(
            "causal_state_count must be >= 1"
        )
    if not 0.0 <= target_fraction < 1.0:
        raise ValueError(
            "target_fraction must be in [0,1)"
        )
    if target_fraction == 1.0:
        raise ValueError(
            "finite total bits cannot force exact fraction 1"
        )

    return (
        log2(causal_state_count)
        / (1.0 - target_fraction)
    )

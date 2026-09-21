"""Asymptotic equality of vertical-memory rate and topological entropy rate.

For a finite causal graph with M horizontal states:

    H_total(t) = H_horizontal(t) + H_vertical(t)

and:

    0 <= H_horizontal(t) <= log2 M.

Divide by physical time t > 0:

    0 <= H_total(t)/t - H_vertical(t)/t
       <= log2(M)/t.

Therefore, whenever the path entropy rate exists,

    h = lim H_total(t)/t,

the vertical-memory rate has the same limit:

    lim H_vertical(t)/t = h.

For an irreducible finite recurrent core with Perron growth factor lambda:

    h = log2(lambda).

Thus the topological entropy rate is also the asymptotic rate at which exact
history information accumulates in the vertical fibers.  The horizontal causal
coordinate contributes zero asymptotic information rate because its state
space is finite.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import log2

from .horizontal_vertical_entropy import EntropyDecomposition


@dataclass(frozen=True)
class VerticalRateBound:
    time: int
    total_rate: float
    horizontal_rate: float
    vertical_rate: float
    maximum_rate_gap: float
    actual_rate_gap: float


def vertical_rate_bound(
    decomposition: EntropyDecomposition,
    *,
    time: int,
    causal_state_count: int,
) -> VerticalRateBound:
    if time <= 0:
        raise ValueError("time must be > 0")
    if causal_state_count < 1:
        raise ValueError(
            "causal_state_count must be >= 1"
        )

    total_rate = (
        decomposition.total_bits / time
    )
    horizontal_rate = (
        decomposition.horizontal_bits / time
    )
    vertical_rate = (
        decomposition.vertical_bits / time
    )
    max_gap = log2(causal_state_count) / time
    actual_gap = total_rate - vertical_rate

    return VerticalRateBound(
        time=time,
        total_rate=total_rate,
        horizontal_rate=horizontal_rate,
        vertical_rate=vertical_rate,
        maximum_rate_gap=max_gap,
        actual_rate_gap=actual_gap,
    )


def rate_bound_holds(
    row: VerticalRateBound,
    *,
    tolerance: float = 1e-12,
) -> bool:
    return (
        abs(
            row.actual_rate_gap
            - row.horizontal_rate
        )
        <= tolerance
        and row.actual_rate_gap
        <= row.maximum_rate_gap + tolerance
        and row.actual_rate_gap >= -tolerance
    )


def entropy_rate_from_growth(
    growth_rate: float,
) -> float:
    if growth_rate <= 0.0:
        raise ValueError(
            "growth_rate must be positive"
        )
    return log2(growth_rate)

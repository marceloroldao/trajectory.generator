"""Cardinality geometry of horizontal causal states and vertical history fibers.

At time t the minimal reversible completion is the disjoint union

    X_t = coproduct_v {v} x F_t(v),

where |F_t(v)| = D(v,t), the number of admissible histories ending at causal
state v.

This is generally not a Cartesian product H x V because the fiber cardinality
depends on the horizontal base state.

A uniform rectangular representation pads every populated fiber to

    D_max(t) = max_v D(v,t),

creating

    M_t * D_max(t)

slots for only

    sum_v D(v,t)

actual histories.

The scalar enumerative address used by trajectory.generator is simply a compact
chart of the disjoint union and pays no rectangular padding.  This module
quantifies the difference.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import log2
from typing import Hashable, Mapping


Node = Hashable


def ceil_log2_int(value: int) -> int:
    if value < 1:
        raise ValueError("value must be >= 1")
    return (value - 1).bit_length()


@dataclass(frozen=True)
class FiberBundleGeometry:
    total_base_states: int
    populated_base_states: int
    total_histories: int
    minimum_nonzero_fiber: int
    maximum_fiber: int
    fibers_are_nonuniform: bool
    exact_family_bits: float
    optimal_integer_bits: int
    active_rectangular_slots: int
    active_rectangular_occupancy: float
    active_rectangular_redundancy_bits: float
    active_rectangular_integer_bits: int
    full_rectangular_slots: int
    full_rectangular_occupancy: float
    full_rectangular_redundancy_bits: float
    full_rectangular_integer_bits: int


def fiber_bundle_geometry(
    counts: Mapping[Node, int],
    *,
    total_base_states: int | None = None,
) -> FiberBundleGeometry:
    if not counts:
        raise ValueError("counts must be non-empty")

    nonzero = [
        int(value)
        for value in counts.values()
        if value > 0
    ]
    if not nonzero:
        raise ValueError("at least one fiber must be populated")
    if any(value < 0 for value in counts.values()):
        raise ValueError("fiber counts must be non-negative")

    if total_base_states is None:
        total_base_states = len(counts)
    if total_base_states < len(nonzero):
        raise ValueError(
            "total_base_states cannot be smaller than populated states"
        )

    populated = len(nonzero)
    total = sum(nonzero)
    minimum = min(nonzero)
    maximum = max(nonzero)

    active_slots = populated * maximum
    full_slots = total_base_states * maximum

    exact_bits = log2(total)
    active_redundancy = log2(active_slots) - exact_bits
    full_redundancy = log2(full_slots) - exact_bits

    return FiberBundleGeometry(
        total_base_states=total_base_states,
        populated_base_states=populated,
        total_histories=total,
        minimum_nonzero_fiber=minimum,
        maximum_fiber=maximum,
        fibers_are_nonuniform=minimum != maximum,
        exact_family_bits=exact_bits,
        optimal_integer_bits=ceil_log2_int(total),
        active_rectangular_slots=active_slots,
        active_rectangular_occupancy=total / active_slots,
        active_rectangular_redundancy_bits=active_redundancy,
        active_rectangular_integer_bits=(
            ceil_log2_int(populated)
            + ceil_log2_int(maximum)
        ),
        full_rectangular_slots=full_slots,
        full_rectangular_occupancy=total / full_slots,
        full_rectangular_redundancy_bits=full_redundancy,
        full_rectangular_integer_bits=(
            ceil_log2_int(total_base_states)
            + ceil_log2_int(maximum)
        ),
    )

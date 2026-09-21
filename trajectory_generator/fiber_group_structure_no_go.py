"""No-go theorem for deriving a canonical group law from fiber cardinality alone.

A cyclic-group structure would make inversion y -> -y natural under
group-preserving automorphisms.  But an abstract finite set of histories does
not come with such a group structure for free.

Every group structure needs a distinguished identity element.  If the only
known property of a fiber is that it has n elements, its full symmetry group is
S_n.  A canonically selected identity would have to be fixed by every
permutation in S_n.

For n > 1 no element has that property.

Therefore a canonical Z_n structure cannot be derived from cardinality alone.
Any intrinsic group structure must be induced by additional public structure of
the histories or universe (symbol labels, a distinguished trajectory, algebraic
composition, etc.).
"""

from __future__ import annotations

from itertools import permutations

from .gauge_invariant_vertical_law import (
    Permutation,
)


def common_fixed_points(
    gauges: tuple[Permutation, ...],
) -> tuple[int, ...]:
    if not gauges:
        return ()

    size = len(gauges[0])
    if any(len(gauge) != size for gauge in gauges):
        raise ValueError("all gauges must have the same size")

    return tuple(
        point
        for point in range(size)
        if all(
            gauge[point] == point
            for gauge in gauges
        )
    )


def all_set_relabelings(size: int) -> tuple[Permutation, ...]:
    if size < 1:
        raise ValueError("size must be >= 1")
    return tuple(
        tuple(value)
        for value in permutations(range(size))
    )


def canonical_origin_exists_from_cardinality(
    size: int,
) -> bool:
    gauges = all_set_relabelings(size)
    return bool(common_fixed_points(gauges))


def cardinality_only_group_structure_possible(
    size: int,
) -> bool:
    """Necessary-condition test: a natural group identity must exist."""
    return canonical_origin_exists_from_cardinality(
        size
    )

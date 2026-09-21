"""Gauge-invariance no-go result for unstructured vertical fibers.

A minimal reversible completion fixes only the *set* of histories above each
causal node.  If no additional structure is declared on a fiber of size n, then
any bijection of its n elements is an admissible change of vertical chart.

A vertical permutation f is coordinate-free only if it is unchanged by every
such relabeling:

    g o f o g^-1 = f    for every g in S_n.

Equivalently, f must lie in the center Z(S_n).

For n >= 3:

    Z(S_n) = {identity}.

Therefore no nontrivial numerical vertical permutation can be intrinsic on a
generic unstructured fiber of size >= 3.  A nontrivial vertical law can still
be a perfectly valid *gauge representation* of the reversible history dynamics,
but to promote it to intrinsic physics the fiber must carry additional public
structure preserved by the allowed coordinate changes.

This module implements the finite permutation statement directly and exposes
small exact certificates used by the project gates.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import permutations
from typing import Iterable


Permutation = tuple[int, ...]


def identity_permutation(size: int) -> Permutation:
    if size < 0:
        raise ValueError("size must be non-negative")
    return tuple(range(size))


def validate_permutation(value: Permutation) -> None:
    if sorted(value) != list(range(len(value))):
        raise ValueError("value is not a permutation")


def compose(left: Permutation, right: Permutation) -> Permutation:
    """Return left o right."""
    validate_permutation(left)
    validate_permutation(right)
    if len(left) != len(right):
        raise ValueError("permutations must have equal size")
    return tuple(left[right[i]] for i in range(len(left)))


def inverse(value: Permutation) -> Permutation:
    validate_permutation(value)
    out = [0] * len(value)
    for i, target in enumerate(value):
        out[target] = i
    return tuple(out)


def conjugate(
    law: Permutation,
    gauge: Permutation,
) -> Permutation:
    """Return gauge o law o gauge^-1."""
    return compose(
        gauge,
        compose(law, inverse(gauge)),
    )


def commutes(left: Permutation, right: Permutation) -> bool:
    return compose(left, right) == compose(right, left)


def transposition(
    size: int,
    i: int,
    j: int,
) -> Permutation:
    if not 0 <= i < size or not 0 <= j < size:
        raise ValueError("transposition index outside permutation")
    out = list(range(size))
    out[i], out[j] = out[j], out[i]
    return tuple(out)


def commutes_with_all_transpositions(
    law: Permutation,
) -> bool:
    """Transpositions generate S_n, so this is equivalent to centrality."""
    validate_permutation(law)
    size = len(law)
    return all(
        commutes(law, transposition(size, i, j))
        for i in range(size)
        for j in range(i + 1, size)
    )


def center_by_transpositions(size: int) -> tuple[Permutation, ...]:
    """Exact center of S_n by exhaustive candidate enumeration.

    Intended for small theorem gates.  Centrality itself is checked only against
    transpositions because they generate the complete symmetric group.
    """
    if size < 0:
        raise ValueError("size must be non-negative")

    return tuple(
        candidate
        for candidate in permutations(range(size))
        if commutes_with_all_transpositions(candidate)
    )


def expected_center_size(size: int) -> int:
    """Known exact size of Z(S_n)."""
    if size <= 1:
        return 1
    if size == 2:
        return 2
    return 1


def phase_reflection_permutation(
    size: int,
    phase: int,
) -> Permutation:
    if size < 1:
        raise ValueError("size must be positive")
    sigma = -1 if (phase & 1) else 1
    return tuple(
        (sigma * vertical) % size
        for vertical in range(size)
    )


def first_gauge_witness(
    law: Permutation,
) -> tuple[Permutation, Permutation] | None:
    """Return (gauge, conjugated_law) witnessing chart dependence."""
    validate_permutation(law)
    size = len(law)

    for i in range(size):
        for j in range(i + 1, size):
            gauge = transposition(size, i, j)
            changed = conjugate(law, gauge)
            if changed != law:
                return gauge, changed
    return None


@dataclass(frozen=True)
class GaugeInvarianceCertificate:
    size: int
    center_size: int
    expected_center_size: int
    only_identity_for_generic_size: bool
    phase_reflection_is_central: bool
    phase_reflection_witness_exists: bool


def certificate(size: int) -> GaugeInvarianceCertificate:
    if size < 1:
        raise ValueError("size must be >= 1")

    center = center_by_transpositions(size)
    reflection = phase_reflection_permutation(
        size,
        phase=1,
    )
    reflection_central = commutes_with_all_transpositions(
        reflection
    )
    witness = first_gauge_witness(reflection)

    return GaugeInvarianceCertificate(
        size=size,
        center_size=len(center),
        expected_center_size=expected_center_size(size),
        only_identity_for_generic_size=(
            size < 3
            or center == (identity_permutation(size),)
        ),
        phase_reflection_is_central=reflection_central,
        phase_reflection_witness_exists=witness is not None,
    )


def theorem_holds_through(max_size: int = 7) -> bool:
    if max_size < 1:
        raise ValueError("max_size must be >= 1")

    for size in range(1, max_size + 1):
        center = center_by_transpositions(size)
        if len(center) != expected_center_size(size):
            return False
        if size >= 3 and center != (
            identity_permutation(size),
        ):
            return False

    return True

"""Naturality of vertical dynamics under declared fiber structure.

The gauge no-go theorem applies when a fiber is only an unlabeled finite set:
its admissible chart group is the full symmetric group S_n, whose center is
trivial for n>=3.

If the universe supplies additional structure, the admissible gauge group
shrinks to structure-preserving automorphisms.  Nontrivial natural vertical
operations may then exist.

This module studies the simplest candidate relevant to trajectory.generator:

    fiber = cyclic group Z_n.

A group automorphism is multiplication by a unit u modulo n:

    phi_u(y) = u*y mod n, gcd(u,n)=1.

The group inversion map

    I(y) = -y mod n

is canonical and natural:

    phi_u(I(y)) = -u*y = I(phi_u(y)).

Thus inversion commutes with every automorphism of Z_n for every n.  This is a
conditional theorem: it identifies a sufficient extra structure that would make
the project's vertical reflection intrinsic.  It does NOT establish that the
history fibers currently possess a canonically derived cyclic-group law.
"""

from __future__ import annotations

from math import gcd

from .gauge_invariant_vertical_law import (
    Permutation,
    commutes,
    identity_permutation,
    phase_reflection_permutation,
)


def units_modulo(size: int) -> tuple[int, ...]:
    if size < 1:
        raise ValueError("size must be >= 1")
    return tuple(
        value
        for value in range(size)
        if gcd(value, size) == 1
    )


def cyclic_group_automorphism(
    size: int,
    unit: int,
) -> Permutation:
    if size < 1:
        raise ValueError("size must be >= 1")
    if gcd(unit, size) != 1:
        raise ValueError("unit must be invertible modulo size")
    return tuple(
        (unit * value) % size
        for value in range(size)
    )


def cyclic_group_automorphisms(
    size: int,
) -> tuple[Permutation, ...]:
    return tuple(
        cyclic_group_automorphism(size, unit)
        for unit in units_modulo(size)
    )


def inversion_permutation(size: int) -> Permutation:
    if size < 1:
        raise ValueError("size must be >= 1")
    return phase_reflection_permutation(
        size,
        phase=1,
    )


def inversion_is_natural_for_cyclic_group(
    size: int,
) -> bool:
    inversion = inversion_permutation(size)
    return all(
        commutes(inversion, automorphism)
        for automorphism in cyclic_group_automorphisms(
            size
        )
    )


def identity_is_natural_for_cyclic_group(
    size: int,
) -> bool:
    identity = identity_permutation(size)
    return all(
        commutes(identity, automorphism)
        for automorphism in cyclic_group_automorphisms(
            size
        )
    )


def branch_inversion_is_natural(
    size: int,
    *,
    is_branch: bool,
) -> bool:
    """Identity on deterministic states, inversion on branch states."""
    if is_branch:
        return inversion_is_natural_for_cyclic_group(
            size
        )
    return identity_is_natural_for_cyclic_group(
        size
    )

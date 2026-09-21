"""Gauge-invariant conjugacy-class description of vertical dynamics.

A concrete vertical permutation depends on the chart used to label a fiber.
Under a gauge relabeling g, the represented law transforms by conjugation:

    f -> g f g^-1.

The permutation itself is therefore not gauge-invariant, but its conjugacy class
is.  For finite symmetric groups, the conjugacy class is completely determined
by cycle type.

This module uses cycle type as the intrinsic signature of a vertical action.

For the project's branch-reflection gauge representative

    R_n(y) = -y mod n,

the invariant cycle type is:

n odd:
    1 fixed point + (n-1)/2 transpositions

n even:
    2 fixed points + (n-2)/2 transpositions.

At deterministic causal states the intrinsic action class is identity.  At
entropy-bearing branch states the proposed intrinsic action class is the
reflection involution class.  A numerical chart may choose any representative
of that class; all such representatives are gauge-conjugate.
"""

from __future__ import annotations

from dataclasses import dataclass

from .gauge_invariant_vertical_law import (
    Permutation,
    conjugate,
    identity_permutation,
    phase_reflection_permutation,
    validate_permutation,
)


CycleType = tuple[int, ...]


def cycle_type(value: Permutation) -> CycleType:
    validate_permutation(value)
    size = len(value)
    seen = [False] * size
    lengths = []

    for start in range(size):
        if seen[start]:
            continue
        current = start
        length = 0
        while not seen[current]:
            seen[current] = True
            length += 1
            current = value[current]
        lengths.append(length)

    return tuple(sorted(lengths))


def identity_cycle_type(size: int) -> CycleType:
    if size < 0:
        raise ValueError("size must be non-negative")
    return tuple(1 for _ in range(size))


def reflection_cycle_type(size: int) -> CycleType:
    if size < 1:
        raise ValueError("size must be >= 1")

    fixed = 1 if size & 1 else 2
    pairs = (size - fixed) // 2
    return tuple(sorted(
        (1,) * fixed + (2,) * pairs
    ))


def reflection_representative(size: int) -> Permutation:
    return phase_reflection_permutation(
        size,
        phase=1,
    )


def is_involution(value: Permutation) -> bool:
    validate_permutation(value)
    identity = identity_permutation(len(value))
    return tuple(value[value[i]] for i in range(len(value))) == identity


def conjugacy_signature_is_invariant(
    law: Permutation,
    gauge: Permutation,
) -> bool:
    return (
        cycle_type(law)
        == cycle_type(conjugate(law, gauge))
    )


@dataclass(frozen=True)
class VerticalActionClass:
    kind: str
    fiber_size: int
    signature: CycleType

    @property
    def nontrivial(self) -> bool:
        return self.signature != identity_cycle_type(
            self.fiber_size
        )


def information_event_action_class(
    *,
    fiber_size: int,
    is_branch: bool,
) -> VerticalActionClass:
    if fiber_size < 1:
        raise ValueError("fiber_size must be >= 1")

    if is_branch:
        return VerticalActionClass(
            kind="reflection_involution",
            fiber_size=fiber_size,
            signature=reflection_cycle_type(
                fiber_size
            ),
        )

    return VerticalActionClass(
        kind="identity",
        fiber_size=fiber_size,
        signature=identity_cycle_type(
            fiber_size
        ),
    )

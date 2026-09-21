"""Gauge-covariant information-event dynamics by conjugacy class.

The gauge-invariance no-go theorem rules out a nontrivial *numerical*
permutation that is fixed under every relabeling of an unstructured fiber.

The coordinate-free object can nevertheless specify a conjugacy class of
permutations. Conjugation changes the representative but preserves cycle type.

This module selects a canonical conjugacy class using only fiber cardinality and
the causal information-event predicate:

- deterministic source node: identity class;
- branch source node: fixed-point-minimal involution class.

For a fiber of size n, a fixed-point-minimal involution has

    floor(n/2) transpositions
    n mod 2 fixed points.

This cycle type is unique for each n. All representatives with this type are
conjugate in S_n.

The default chart representative is reversal:

    R_n(y) = n - 1 - y.

For even n it has no fixed points. For odd n it has exactly the middle point
fixed. It is self-inverse for every n.

The physical statement is the conjugacy class, not this particular numeric
representative.
"""

from __future__ import annotations

from collections import Counter
from itertools import permutations

from .endogenous_vertical_dynamics import (
    EndogenousPeriodicVerticalLift,
    VerticalDrive,
)
from .gauge_invariant_vertical_law import (
    Permutation,
    conjugate,
    validate_permutation,
)


def cycle_type(value: Permutation) -> tuple[int, ...]:
    """Return sorted cycle lengths, including 1-cycles."""
    validate_permutation(value)
    seen = set()
    lengths = []

    for start in range(len(value)):
        if start in seen:
            continue
        current = start
        length = 0
        while current not in seen:
            seen.add(current)
            current = value[current]
            length += 1
        lengths.append(length)

    return tuple(sorted(lengths))


def fixed_point_count(value: Permutation) -> int:
    validate_permutation(value)
    return sum(
        1
        for i, target in enumerate(value)
        if i == target
    )


def is_involution(value: Permutation) -> bool:
    validate_permutation(value)
    return all(
        value[value[i]] == i
        for i in range(len(value))
    )


def reversal_involution(size: int) -> Permutation:
    if size < 1:
        raise ValueError("size must be >= 1")
    return tuple(
        size - 1 - i
        for i in range(size)
    )


def maximal_pairing_cycle_type(size: int) -> tuple[int, ...]:
    if size < 1:
        raise ValueError("size must be >= 1")
    return tuple(
        sorted(
            (1,) * (size % 2)
            + (2,) * (size // 2)
        )
    )


def is_maximal_pairing_involution(
    value: Permutation,
) -> bool:
    return (
        is_involution(value)
        and cycle_type(value)
        == maximal_pairing_cycle_type(len(value))
    )


def conjugacy_class_preserved(
    law: Permutation,
    gauge: Permutation,
) -> bool:
    return (
        cycle_type(conjugate(law, gauge))
        == cycle_type(law)
    )


def maximal_pairing_involutions(
    size: int,
) -> tuple[Permutation, ...]:
    """Enumerate small-n representatives for theorem gates."""
    if size < 1:
        raise ValueError("size must be >= 1")
    return tuple(
        value
        for value in permutations(range(size))
        if is_maximal_pairing_involution(value)
    )


class MaximalPairingBranchLift(
    EndogenousPeriodicVerticalLift
):
    """Chart representative of gauge-covariant branch-event pairing."""

    def __init__(self, machine) -> None:
        super().__init__(
            machine,
            vertical_period=machine.field.period,
        )

    def is_information_event(self, edge) -> bool:
        return (
            len(self.machine.codec.outgoing[edge.source])
            > 1
        )

    def drive(self, edge, time: int) -> VerticalDrive:
        if time < 0:
            raise ValueError("time must be >= 0")

        return VerticalDrive(
            vertical_phase=0,
            orientation=(
                -1
                if self.is_information_event(edge)
                else 1
            ),
            shift_seed=0,
            outgoing_index=self._outgoing_index[edge.label],
            incoming_index=self._incoming_index[edge.label],
        )

    def permute_local(
        self,
        vertical: int,
        fiber_size: int,
        drive: VerticalDrive,
    ) -> int:
        if fiber_size <= 0:
            raise ValueError("fiber_size must be positive")
        if not 0 <= vertical < fiber_size:
            raise ValueError("vertical outside source fiber")

        if drive.orientation == 1:
            return vertical
        if drive.orientation != -1:
            raise ValueError("orientation must be +/-1")

        return fiber_size - 1 - vertical

    def invert_local(
        self,
        local: int,
        fiber_size: int,
        drive: VerticalDrive,
    ) -> int:
        # Identity and reversal are both self-inverse.
        return self.permute_local(
            local,
            fiber_size,
            drive,
        )

    def representative_permutation(
        self,
        edge,
        time: int,
    ) -> Permutation:
        size = self.fiber_size(
            edge.source,
            time,
        )
        if size <= 0:
            raise ValueError(
                "edge source fiber is empty at this time"
            )

        drive = self.drive(edge, time)
        return tuple(
            self.permute_local(
                y,
                size,
                drive,
            )
            for y in range(size)
        )


def build_maximal_pairing_branch_lift(machine):
    return MaximalPairingBranchLift(machine)

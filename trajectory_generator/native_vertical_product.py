"""Native vertical product extension with an independent cyclic state.

The minimal history lift uses vertical multiplicity to distinguish pasts.  Its
numeric vertical laws are gauge because no independent vertical degree of
freedom exists at t=0.

This module adds one explicitly independent public vertical factor Z_m:

    state = (trajectory_address, z),  z in Z_m.

The factor is present from the beginning and evolves by the public skew-product
law:

    z' = z + bit mod m.

Because each causal bit is recovered during reverse, the inverse is exact:

    z = z' - bit mod m.

Global translations

    T_c(z) = z + c mod m

commute with every transition, so they are genuine nontrivial natural
automorphisms of the extended system rather than time-dependent history-chart
changes.

The price is exact: the state family is multiplied by m.  At a fixed final
width this consumes log2(m) bits of address capacity.  This module makes that
tradeoff operational.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class NativeVerticalDecoded:
    bits: tuple[int, ...]
    initial_vertical: int


class NativeVerticalProductMachine:
    def __init__(
        self,
        trajectory_machine,
        *,
        vertical_modulus: int,
    ) -> None:
        if vertical_modulus < 2:
            raise ValueError(
                "vertical_modulus must be >= 2"
            )
        self.trajectory_machine = trajectory_machine
        self.vertical_modulus = vertical_modulus

    def pack(
        self,
        trajectory_state: int,
        vertical: int,
    ) -> int:
        if trajectory_state < 0:
            raise ValueError(
                "trajectory_state must be non-negative"
            )
        if not 0 <= vertical < self.vertical_modulus:
            raise ValueError(
                "vertical outside native cyclic factor"
            )
        return (
            trajectory_state * self.vertical_modulus
            + vertical
        )

    def unpack(
        self,
        state: int,
    ) -> tuple[int, int]:
        if state < 0:
            raise ValueError("state must be non-negative")
        return divmod(
            state,
            self.vertical_modulus,
        )

    def translate_vertical(
        self,
        state: int,
        offset: int,
    ) -> int:
        trajectory_state, vertical = self.unpack(
            state
        )
        return self.pack(
            trajectory_state,
            (
                vertical + offset
            ) % self.vertical_modulus,
        )

    def advance(
        self,
        state: int,
        steps: int,
        bit: int,
    ) -> tuple[int, int]:
        trajectory_state, vertical = self.unpack(
            state
        )

        next_trajectory, next_steps = (
            self.trajectory_machine.advance(
                trajectory_state,
                steps,
                bit,
            )
        )
        next_vertical = (
            vertical + int(bit)
        ) % self.vertical_modulus

        return (
            self.pack(
                next_trajectory,
                next_vertical,
            ),
            next_steps,
        )

    def rewind(
        self,
        state: int,
        steps: int,
    ) -> tuple[int, int, int]:
        trajectory_state, vertical = self.unpack(
            state
        )

        (
            previous_trajectory,
            previous_steps,
            bit,
        ) = self.trajectory_machine.rewind(
            trajectory_state,
            steps,
        )

        previous_vertical = (
            vertical - bit
        ) % self.vertical_modulus

        return (
            self.pack(
                previous_trajectory,
                previous_vertical,
            ),
            previous_steps,
            bit,
        )

    def encode(
        self,
        bits: Sequence[int],
        *,
        initial_vertical: int = 0,
    ) -> tuple[int, int]:
        if not 0 <= initial_vertical < self.vertical_modulus:
            raise ValueError(
                "initial_vertical outside native cyclic factor"
            )

        state = self.pack(0, initial_vertical)
        steps = 0

        for bit in bits:
            state, steps = self.advance(
                state,
                steps,
                int(bit),
            )

        return state, steps

    def decode(
        self,
        final_state: int,
        steps: int,
    ) -> NativeVerticalDecoded:
        state = final_state
        n = steps
        reversed_bits = []

        while n:
            state, n, bit = self.rewind(
                state,
                n,
            )
            reversed_bits.append(bit)

        trajectory_origin, initial_vertical = (
            self.unpack(state)
        )
        if trajectory_origin != 0:
            raise AssertionError(
                "trajectory component did not return to origin"
            )

        reversed_bits.reverse()
        return NativeVerticalDecoded(
            bits=tuple(reversed_bits),
            initial_vertical=initial_vertical,
        )

    def symmetry_commutes(
        self,
        state: int,
        steps: int,
        bit: int,
        offset: int,
    ) -> bool:
        shifted_before = self.translate_vertical(
            state,
            offset,
        )
        left, left_steps = self.advance(
            shifted_before,
            steps,
            bit,
        )

        advanced, right_steps = self.advance(
            state,
            steps,
            bit,
        )
        right = self.translate_vertical(
            advanced,
            offset,
        )

        return (
            left_steps == right_steps
            and left == right
        )

    def lifted_family_size(
        self,
        trajectory_family_size: int,
    ) -> int:
        if trajectory_family_size < 0:
            raise ValueError(
                "trajectory_family_size must be non-negative"
            )
        return (
            trajectory_family_size
            * self.vertical_modulus
        )

"""Order-free intrinsic vertical permutation: public phase reflection only.

Minimal reversible completion forces predecessor edge blocks inside each target
fiber, but it does not force an internal numerical coordinate on those blocks.

This lift chooses the smallest nontrivial periodic internal gauge that does not
use incoming/outgoing edge order. The public phase is read from the current
causal source node itself:

    sigma(source) = (-1)^phase(source)
    b             = 0

    local' = sigma(source) * y mod |F(source,t)|

The target edge block is still selected by the causal predecessor edge.  Any
integer packing of those tagged blocks needs an ordering convention, but that
ordering belongs to the chart/serialization layer, not to the intrinsic
vertical permutation.
"""

from __future__ import annotations

from .endogenous_vertical_dynamics import (
    EndogenousPeriodicVerticalLift,
    VerticalDrive,
)


class PhaseReflectionVerticalLift(
    EndogenousPeriodicVerticalLift
):
    def __init__(self, machine) -> None:
        super().__init__(
            machine,
            vertical_period=machine.field.period,
        )

    def drive(self, edge, time: int) -> VerticalDrive:
        if time < 0:
            raise ValueError("time must be >= 0")

        # Phase is an endogenous coordinate of the phase-lifted causal node.
        # The drive therefore does not need the absolute time to choose its
        # orientation. On every reachable transition phase(source) == t mod P.
        phase = (
            self.machine.field.phase_of(edge.source)
            % self.causal_period
        )
        orientation = -1 if (phase & 1) else 1

        return VerticalDrive(
            vertical_phase=phase,
            orientation=orientation,
            shift_seed=0,
            outgoing_index=self._outgoing_index[edge.label],
            incoming_index=self._incoming_index[edge.label],
        )


def build_phase_reflection_lift(machine):
    return PhaseReflectionVerticalLift(machine)

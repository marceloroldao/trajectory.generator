"""Intrinsic vertical reflection driven by causal information events.

Minimal reversible completion leaves a gauge freedom inside each predecessor
edge image.  A particularly natural nontrivial gauge can be driven by the
same local event that defines the information clock:

    branch(source) = out_degree(source) > 1.

The internal vertical law is

    sigma(source) = -1  if source is an entropy-bearing branch node
                    +1  otherwise

    local' = sigma(source) * y mod |F(source,t)|.

No absolute time, phase number, incoming-edge order, outgoing-edge order,
numeric coefficient, or trajectory-specific parameter enters this internal
permutation.

The target predecessor block is still selected by the public causal edge; its
integer serialization remains a chart convention.
"""

from __future__ import annotations

from .endogenous_vertical_dynamics import (
    EndogenousPeriodicVerticalLift,
    VerticalDrive,
)


class BranchReflectionVerticalLift(
    EndogenousPeriodicVerticalLift
):
    """State-local reflection exactly at entropy-bearing branch nodes."""

    def __init__(self, machine) -> None:
        # The parent requires a positive public period for bookkeeping, but
        # drive() below does not depend on time or phase.
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

        orientation = (
            -1
            if self.is_information_event(edge)
            else 1
        )

        return VerticalDrive(
            vertical_phase=0,
            orientation=orientation,
            shift_seed=0,
            # Indices are retained only as diagnostic metadata inherited from
            # VerticalDrive; they do not enter the branch-reflection law.
            outgoing_index=self._outgoing_index[edge.label],
            incoming_index=self._incoming_index[edge.label],
        )


def build_branch_reflection_lift(machine):
    return BranchReflectionVerticalLift(machine)

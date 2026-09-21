"""Canonical endogenous vertical laws without arbitrary mixing constants.

The first periodic vertical lift proved that a nontrivial endogenous vertical
coordinate can remain exactly reversible, but its drive used hand-chosen
numerical mixing constants.

This module restricts the law grammar to canonical unit-coefficient features.

Temporal features may control orientation only:
    phase       = t mod P
    cycle       = floor((t mod P_vertical) / P)

Causal-geometry features may control rotation only:
    incoming_index
    outgoing_index
    source_branch_excess = max(out_degree(source)-1, 0)
    target_merge_excess  = max(in_degree(target)-1, 0)

For a LawSpec:

    sigma = (-1) ** (sum(selected temporal features) mod 2)
    b     = sum(selected structural features)

and:

    local' = (sigma*y + b) mod |F(source,t)|.

All selected features have coefficient exactly one.  There are no fitted
integers, hashes, random seeds, or candidate-specific parameters.

Period multipliers P, 2P, and 4P are supported.  The search uses a fixed
minimum-description ordering and requires both temporal and causal dependence.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Iterable

from .endogenous_vertical_dynamics import (
    EndogenousPeriodicVerticalLift,
    VerticalDrive,
)
from .weighted_path_trajectory import WeightedEdge


TEMPORAL_FEATURES = ("phase", "cycle")
STRUCTURAL_FEATURES = (
    "incoming_index",
    "outgoing_index",
    "source_branch_excess",
    "target_merge_excess",
)


@dataclass(frozen=True, order=True)
class CanonicalVerticalLawSpec:
    period_multiple: int
    orientation_features: tuple[str, ...]
    shift_features: tuple[str, ...]

    @property
    def term_count(self) -> int:
        return (
            len(self.orientation_features)
            + len(self.shift_features)
        )

    @property
    def description_cost(self) -> tuple:
        # A period with more public cycle states costs more before feature count.
        return (
            self.period_multiple,
            self.term_count,
            self.orientation_features,
            self.shift_features,
        )

    def validate(self) -> None:
        if self.period_multiple not in (1, 2, 4):
            raise ValueError(
                "period_multiple must be one of 1, 2, 4"
            )
        if not self.orientation_features:
            raise ValueError(
                "orientation must use at least one temporal feature"
            )
        if not self.shift_features:
            raise ValueError(
                "shift must use at least one structural feature"
            )
        if any(
            name not in TEMPORAL_FEATURES
            for name in self.orientation_features
        ):
            raise ValueError("unknown temporal feature")
        if any(
            name not in STRUCTURAL_FEATURES
            for name in self.shift_features
        ):
            raise ValueError("unknown structural feature")
        if (
            self.period_multiple == 1
            and "cycle" in self.orientation_features
        ):
            raise ValueError(
                "cycle is identically zero for period P"
            )


class CanonicalPeriodicVerticalLift(
    EndogenousPeriodicVerticalLift
):
    """Periodic lift driven by a unit-coefficient canonical law spec."""

    def __init__(self, machine, spec: CanonicalVerticalLawSpec):
        spec.validate()
        self.spec = spec
        super().__init__(
            machine,
            vertical_period=(
                machine.field.period
                * spec.period_multiple
            ),
        )

    def _feature_values(
        self,
        edge: WeightedEdge,
        time: int,
    ) -> dict[str, int]:
        outgoing_index = self._outgoing_index[edge.label]
        incoming_index = self._incoming_index[edge.label]

        source_out_degree = len(
            self.machine.codec.outgoing[edge.source]
        )
        target_in_degree = len(
            self.machine.codec.incoming[edge.target]
        )

        vertical_phase = time % self.vertical_period
        phase = time % self.causal_period
        cycle = (
            vertical_phase // self.causal_period
        )

        return {
            "phase": phase,
            "cycle": cycle,
            "incoming_index": incoming_index,
            "outgoing_index": outgoing_index,
            "source_branch_excess": max(
                source_out_degree - 1,
                0,
            ),
            "target_merge_excess": max(
                target_in_degree - 1,
                0,
            ),
        }

    def drive(
        self,
        edge: WeightedEdge,
        time: int,
    ) -> VerticalDrive:
        if time < 0:
            raise ValueError("time must be >= 0")

        values = self._feature_values(edge, time)

        parity = sum(
            values[name]
            for name in self.spec.orientation_features
        ) & 1
        orientation = -1 if parity else 1

        shift_seed = sum(
            values[name]
            for name in self.spec.shift_features
        )

        return VerticalDrive(
            vertical_phase=(
                time % self.vertical_period
            ),
            orientation=orientation,
            shift_seed=shift_seed,
            outgoing_index=self._outgoing_index[
                edge.label
            ],
            incoming_index=self._incoming_index[
                edge.label
            ],
        )


def _nonempty_subsets(
    names: tuple[str, ...],
) -> Iterable[tuple[str, ...]]:
    for size in range(1, len(names) + 1):
        yield from combinations(names, size)


def canonical_law_specs():
    """Yield the complete small law grammar in minimum-description order."""
    specs = []

    for period_multiple in (1, 2, 4):
        temporal = (
            ("phase",)
            if period_multiple == 1
            else TEMPORAL_FEATURES
        )

        for orientation in _nonempty_subsets(
            tuple(temporal)
        ):
            for shift in _nonempty_subsets(
                STRUCTURAL_FEATURES
            ):
                spec = CanonicalVerticalLawSpec(
                    period_multiple=period_multiple,
                    orientation_features=orientation,
                    shift_features=shift,
                )
                specs.append(spec)

    specs.sort(key=lambda spec: spec.description_cost)
    return tuple(specs)

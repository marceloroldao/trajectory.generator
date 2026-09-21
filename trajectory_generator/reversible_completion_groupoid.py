"""Gauge groupoid of minimal reversible completions.

The coordinate-free reversible object is the natural extension: admissible
histories with append/remove-edge dynamics.

Any minimal vertical chart assigns each history ending at node v and time t a
coordinate in a fiber of the same cardinality.  Two such charts A and B are
related by the unique history-preserving change of coordinates

    G_AB(t) = chart_B(t) o chart_A(t)^-1.

These changes form a groupoid:

    G_AA = id
    G_BA o G_AB = id
    G_BC o G_AB = G_AC

and they conjugate the represented dynamics:

    G_AB(t+1) o F_A(e,t)
      = F_B(e,t) o G_AB(t).

This module packages those identities as executable certificates.  It does not
claim a preferred gauge; rather, it makes gauge non-uniqueness explicit while
showing that the underlying reversible history dynamics is unique.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .minimal_reversible_completion import (
    History,
    LiftedState,
    MinimalReversibleCompletion,
    PermutationLaw,
)
from .reversible_natural_extension import (
    ReversibleNaturalExtension,
)


@dataclass(frozen=True)
class GaugeChart:
    name: str
    law: PermutationLaw | None


class ReversibleCompletionGroupoid:
    def __init__(
        self,
        completion: MinimalReversibleCompletion,
    ) -> None:
        self.completion = completion
        self.extension = ReversibleNaturalExtension(
            completion
        )

    def state(
        self,
        history: History,
        time: int,
        chart: GaugeChart,
    ) -> LiftedState:
        return self.extension.chart(
            history,
            time,
            gauge=chart.law,
        )

    def history(
        self,
        state: LiftedState,
        time: int,
        chart: GaugeChart,
    ) -> History:
        return self.extension.unchart(
            state,
            time,
            gauge=chart.law,
        )

    def change(
        self,
        state: LiftedState,
        time: int,
        source: GaugeChart,
        target: GaugeChart,
    ) -> LiftedState:
        return self.extension.gauge_change(
            state,
            time,
            source_gauge=source.law,
            target_gauge=target.law,
        )

    def identity_holds(
        self,
        state: LiftedState,
        time: int,
        chart: GaugeChart,
    ) -> bool:
        return self.change(
            state,
            time,
            chart,
            chart,
        ) == state

    def inverse_holds(
        self,
        state: LiftedState,
        time: int,
        source: GaugeChart,
        target: GaugeChart,
    ) -> bool:
        mapped = self.change(
            state,
            time,
            source,
            target,
        )
        recovered = self.change(
            mapped,
            time,
            target,
            source,
        )
        return recovered == state

    def composition_holds(
        self,
        state: LiftedState,
        time: int,
        first: GaugeChart,
        second: GaugeChart,
        third: GaugeChart,
    ) -> bool:
        via_second = self.change(
            state,
            time,
            first,
            second,
        )
        via_third = self.change(
            via_second,
            time,
            second,
            third,
        )
        direct = self.change(
            state,
            time,
            first,
            third,
        )
        return via_third == direct

    def transition_naturality_holds(
        self,
        state: LiftedState,
        time: int,
        edge_label: str,
        source: GaugeChart,
        target: GaugeChart,
    ) -> bool:
        edge = self.completion.edge_by_label.get(
            edge_label
        )
        if edge is None or edge.source != state.node:
            return False

        # Evolve in source chart, then change coordinates at t+1.
        source_next = self.completion.advance(
            state,
            time,
            edge_label,
            gauge=source.law,
        )
        left = self.change(
            source_next,
            time + 1,
            source,
            target,
        )

        # Change coordinates at t, then evolve in target chart.
        target_state = self.change(
            state,
            time,
            source,
            target,
        )
        right = self.completion.advance(
            target_state,
            time,
            edge_label,
            gauge=target.law,
        )

        return left == right

    def same_underlying_history(
        self,
        state_a: LiftedState,
        chart_a: GaugeChart,
        state_b: LiftedState,
        chart_b: GaugeChart,
        time: int,
    ) -> bool:
        return (
            self.history(state_a, time, chart_a)
            == self.history(state_b, time, chart_b)
        )

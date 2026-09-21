"""Coordinate-free natural extension of a finite causal graph.

The intrinsic reversible object associated with a non-injective causal graph is
its admissible history space.

At time t, a natural-extension state is a complete admissible edge history of
length t together with its endpoint.  Forward appends one public edge; reverse
removes the last edge.  This state evolution is exactly reversible.

A minimal fiber lift is a coordinate chart on this history space:

    chart_t : histories ending at v <-> {0, ..., D(v,t)-1}.

Different vertical laws correspond to different chart families.  They are
physically equivalent at the level of history dynamics when related by the
time-dependent fiber bijection:

    G_t = chart'_t o chart_t^{-1}.

The corresponding lifted edge maps satisfy the conjugacy equation:

    G_(t+1) o F_e = F'_e o G_t.

Thus exact minimal reversibility canonically fixes the history space and fiber
cardinalities, but not a unique integer coordinate inside each fiber.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Hashable

from .minimal_reversible_completion import (
    CausalEdge,
    History,
    LiftedState,
    MinimalReversibleCompletion,
    PermutationLaw,
)


Node = Hashable


class ReversibleNaturalExtension:
    def __init__(
        self,
        completion: MinimalReversibleCompletion,
    ) -> None:
        self.completion = completion

    def histories_at(self, time: int) -> tuple[History, ...]:
        self.completion.ensure_horizon(time)
        out = []
        for node in self.completion.nodes:
            out.extend(
                self.completion.histories(node, time)
            )
        return tuple(out)

    def advance_history(
        self,
        history: History,
        edge_label: str,
    ) -> History:
        edge = self.completion.edge_by_label.get(
            edge_label
        )
        if edge is None:
            raise ValueError("unknown edge")
        if edge.source != history.endpoint:
            raise ValueError(
                "edge does not leave history endpoint"
            )
        return History(
            start=history.start,
            edges=history.edges + (edge.label,),
            endpoint=edge.target,
        )

    def rewind_history(
        self,
        history: History,
    ) -> tuple[History, CausalEdge]:
        if not history.edges:
            raise ValueError(
                "initial history has no predecessor"
            )

        edge = self.completion.edge_by_label.get(
            history.edges[-1]
        )
        if edge is None or edge.target != history.endpoint:
            raise ValueError(
                "history has invalid final edge"
            )

        previous_endpoint = edge.source
        previous = History(
            start=history.start,
            edges=history.edges[:-1],
            endpoint=previous_endpoint,
        )
        return previous, edge

    def chart(
        self,
        history: History,
        time: int,
        *,
        gauge: PermutationLaw | None,
    ) -> LiftedState:
        return self.completion.state_for_history(
            history,
            time,
            gauge=gauge,
        )

    def unchart(
        self,
        state: LiftedState,
        time: int,
        *,
        gauge: PermutationLaw | None,
    ) -> History:
        return self.completion.history_at(
            state,
            time,
            gauge=gauge,
        )

    def gauge_change(
        self,
        state: LiftedState,
        time: int,
        *,
        source_gauge: PermutationLaw | None,
        target_gauge: PermutationLaw | None,
    ) -> LiftedState:
        return self.completion.gauge_map(
            state,
            time,
            source_gauge=source_gauge,
            target_gauge=target_gauge,
        )

    def transition_conjugacy_holds(
        self,
        history: History,
        time: int,
        edge_label: str,
        *,
        source_gauge: PermutationLaw | None,
        target_gauge: PermutationLaw | None,
    ) -> bool:
        """Check G_(t+1) F = F' G_t for one history/edge."""
        edge = self.completion.edge_by_label.get(
            edge_label
        )
        if edge is None or edge.source != history.endpoint:
            return False

        source_state = self.chart(
            history,
            time,
            gauge=source_gauge,
        )

        # Left: evolve in source coordinates, then change gauge.
        source_next = self.completion.advance(
            source_state,
            time,
            edge_label,
            gauge=source_gauge,
        )
        left = self.gauge_change(
            source_next,
            time + 1,
            source_gauge=source_gauge,
            target_gauge=target_gauge,
        )

        # Right: change gauge first, then evolve in target coordinates.
        target_state = self.gauge_change(
            source_state,
            time,
            source_gauge=source_gauge,
            target_gauge=target_gauge,
        )
        right = self.completion.advance(
            target_state,
            time,
            edge_label,
            gauge=target_gauge,
        )

        return left == right

    def chart_is_bijection(
        self,
        time: int,
        *,
        gauge: PermutationLaw | None,
    ) -> bool:
        histories = self.histories_at(time)
        states = [
            self.chart(
                history,
                time,
                gauge=gauge,
            )
            for history in histories
        ]
        if len(set(states)) != len(histories):
            return False

        for history, state in zip(histories, states):
            if self.unchart(
                state,
                time,
                gauge=gauge,
            ) != history:
                return False

        return True

"""Exact composed vertical embeddings for deterministic physical flights.

Every unit physical edge acts on the vertical rank as a translation:

    r_(k+1) = offset_k + r_k.

Therefore any fixed public physical path of length L acts as one exact affine
translation with unit slope:

    r_(t+L) = C_path(t) + r_t,

where C_path(t) is the sum of the edge offsets evaluated against the public
count field at the corresponding physical times.

The image of the source fiber is consequently one contiguous integer block,
even if the physical path crosses reverse merges.  This is the exact object
needed for an information-clock macro jump.

No trajectory log is used.  All offsets are regenerated from the public graph,
public initial family, start time, and path.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .exact_vertical_connection import (
    ExactVerticalConnection,
    LocalFiberState,
)


@dataclass(frozen=True)
class CompiledComposedPath:
    edge_labels: tuple[str, ...]
    source: object
    target: object
    physical_steps: int
    source_index: int
    offset_weights: tuple[int, ...]


@dataclass(frozen=True)
class ComposedVerticalEmbedding:
    start_time: int
    edge_labels: tuple[str, ...]
    source: object
    target: object
    physical_steps: int
    source_size: int
    target_size: int
    start: int
    end: int

    @property
    def empty(self) -> bool:
        return self.source_size == 0


class ComposedVerticalConnection:
    def __init__(
        self,
        connection: ExactVerticalConnection,
    ) -> None:
        self.connection = connection
        self.machine = connection.machine
        self.codec = connection.codec
        self.field = self.machine.field

    def _validated_edges(
        self,
        edge_labels: Sequence[str],
    ):
        labels = tuple(edge_labels)
        if not labels:
            raise ValueError(
                "composed path must contain at least one physical edge"
            )

        edges = []
        previous_target = None
        for label in labels:
            edge = self.codec.edge_by_label.get(label)
            if edge is None:
                raise ValueError(
                    f"unknown physical edge label: {label}"
                )
            if edge.length != 1:
                raise ValueError(
                    "composed vertical connection requires unit physical edges"
                )
            if (
                previous_target is not None
                and edge.source != previous_target
            ):
                raise ValueError(
                    "physical edge labels do not form a continuous path"
                )
            edges.append(edge)
            previous_target = edge.target
        return labels, tuple(edges)

    def compile_path(
        self,
        edge_labels: Sequence[str],
    ) -> CompiledComposedPath:
        """Compile the composed offset into one linear functional of D_start."""
        labels, edges = self._validated_edges(
            edge_labels
        )
        dimension = self.field.reachable_state_count
        weights = []

        for basis_index in range(dimension):
            vector = [0] * dimension
            vector[basis_index] = 1
            vector = tuple(vector)
            offset_total = 0

            for edge in edges:
                offset = 0
                found = False
                for incoming in self.codec.incoming[
                    edge.target
                ]:
                    if incoming == edge:
                        found = True
                        break
                    offset += vector[
                        self.field.node_index[
                            incoming.source
                        ]
                    ]
                if not found:
                    raise AssertionError(
                        "path edge missing from target incoming partition"
                    )
                offset_total += offset
                vector = self.field.step_vector(
                    vector
                )

            weights.append(offset_total)

        source = edges[0].source
        target = edges[-1].target
        return CompiledComposedPath(
            edge_labels=labels,
            source=source,
            target=target,
            physical_steps=len(edges),
            source_index=self.field.node_index[source],
            offset_weights=tuple(weights),
        )

    def embedding_from_source_vector(
        self,
        plan: CompiledComposedPath,
        *,
        start_time: int,
        source_vector: Sequence[int],
        target_size: int,
    ) -> ComposedVerticalEmbedding:
        """Evaluate a compiled macro-block without walking its physical path."""
        if start_time < 0:
            raise ValueError("start_time must be >= 0")
        if len(source_vector) != self.field.reachable_state_count:
            raise ValueError(
                "source_vector has wrong reachable-state dimension"
            )
        if target_size < 0:
            raise ValueError("target_size must be non-negative")

        source_size = int(
            source_vector[plan.source_index]
        )
        start = sum(
            weight * value
            for weight, value in zip(
                plan.offset_weights,
                source_vector,
            )
            if weight and value
        )
        end = start + source_size

        if not 0 <= start <= end <= target_size:
            raise AssertionError(
                "compiled composed subfiber lies outside target fiber"
            )

        return ComposedVerticalEmbedding(
            start_time=start_time,
            edge_labels=plan.edge_labels,
            source=plan.source,
            target=plan.target,
            physical_steps=plan.physical_steps,
            source_size=source_size,
            target_size=target_size,
            start=start,
            end=end,
        )

    def embedding(
        self,
        edge_labels: Sequence[str],
        start_time: int,
    ) -> ComposedVerticalEmbedding:
        labels = tuple(edge_labels)
        if not labels:
            raise ValueError(
                "composed path must contain at least one physical edge"
            )
        if start_time < 0:
            raise ValueError("start_time must be >= 0")

        edges = []
        previous_target = None
        for label in labels:
            edge = self.codec.edge_by_label.get(label)
            if edge is None:
                raise ValueError(
                    f"unknown physical edge label: {label}"
                )
            if edge.length != 1:
                raise ValueError(
                    "composed vertical connection requires unit physical edges"
                )
            if (
                previous_target is not None
                and edge.source != previous_target
            ):
                raise ValueError(
                    "physical edge labels do not form a continuous path"
                )
            edges.append(edge)
            previous_target = edge.target

        vector = self.field.vector_at(
            start_time
        )
        source = edges[0].source
        source_size = vector[
            self.field.node_index[source]
        ]
        offset_total = 0

        for edge in edges:
            offset = 0
            found = False
            for incoming in self.codec.incoming[
                edge.target
            ]:
                if incoming == edge:
                    found = True
                    break
                offset += vector[
                    self.field.node_index[
                        incoming.source
                    ]
                ]
            if not found:
                raise AssertionError(
                    "path edge missing from target incoming partition"
                )

            offset_total += offset
            vector = self.field.step_vector(
                vector
            )

        target = edges[-1].target
        target_size = vector[
            self.field.node_index[target]
        ]
        end = offset_total + source_size

        if not 0 <= offset_total <= end <= target_size:
            raise AssertionError(
                "composed subfiber lies outside target fiber"
            )

        return ComposedVerticalEmbedding(
            start_time=start_time,
            edge_labels=labels,
            source=source,
            target=target,
            physical_steps=len(edges),
            source_size=source_size,
            target_size=target_size,
            start=offset_total,
            end=end,
        )

    def forward(
        self,
        state: LocalFiberState,
        edge_labels: Sequence[str],
    ) -> LocalFiberState:
        block = self.embedding(
            edge_labels,
            state.time,
        )
        if state.node != block.source:
            raise ValueError(
                "composed path does not leave local horizontal node"
            )
        if state.fiber_size != block.source_size:
            raise ValueError(
                "local source fiber size does not match public count field"
            )
        if not 0 <= state.rank < block.source_size:
            raise ValueError(
                "local rank outside composed source fiber"
            )

        return LocalFiberState(
            time=state.time + block.physical_steps,
            node=block.target,
            rank=block.start + state.rank,
            fiber_size=block.target_size,
        )

    def reverse(
        self,
        state: LocalFiberState,
        edge_labels: Sequence[str],
    ) -> LocalFiberState:
        labels = tuple(edge_labels)
        if not labels:
            raise ValueError(
                "composed path must contain at least one physical edge"
            )
        start_time = state.time - len(labels)
        if start_time < 0:
            raise ValueError(
                "composed path is longer than current trajectory time"
            )

        block = self.embedding(
            labels,
            start_time,
        )
        if state.node != block.target:
            raise ValueError(
                "composed path does not end at local horizontal node"
            )
        if state.fiber_size != block.target_size:
            raise ValueError(
                "local target fiber size does not match public count field"
            )
        if not block.start <= state.rank < block.end:
            raise ValueError(
                "local rank is outside composed predecessor subfiber"
            )

        return LocalFiberState(
            time=start_time,
            node=block.source,
            rank=state.rank - block.start,
            fiber_size=block.source_size,
        )

    def locate_predecessor(
        self,
        state: LocalFiberState,
        candidate_paths: Sequence[Sequence[str]],
    ):
        matches = []
        for labels in candidate_paths:
            labels = tuple(labels)
            if not labels or len(labels) > state.time:
                continue
            block = self.embedding(
                labels,
                state.time - len(labels),
            )
            if (
                block.target == state.node
                and block.target_size
                == state.fiber_size
                and block.start
                <= state.rank
                < block.end
            ):
                matches.append(block)

        if len(matches) > 1:
            raise AssertionError(
                "composed predecessor blocks overlap"
            )
        return matches[0] if matches else None

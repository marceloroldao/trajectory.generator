"""Affine translation view of the streaming trajectory address.

For a public graph path address, let the packed state at time t be

    S_t = endpoint_bucket_offset_t(u) + rank_t

for current endpoint u.

Appending public edge e: u -> v preserves the predecessor rank inside the
incoming-edge block of v. Therefore:

    S_(t+1) = S_t + Delta(e,t)

with

    Delta(e,t) =
        endpoint_offset_(t+1)(v)
      + incoming_edge_offset_t(e)
      - endpoint_offset_t(u).

Delta depends only on the public edge, public time, node ordering, and public
count field. It is independent of the trajectory-specific rank.

Reverse decoding identifies the incoming-edge block containing S_(t+1), then
subtracts the same public translation.

For phase-lifted universes backed by FloquetCountFieldRecurrence, each
phase-aligned Delta(e, p+P*q) is an integer linear functional of the Floquet
count vector and therefore obeys the same Floquet recurrence.
"""

from __future__ import annotations

from typing import Hashable, Sequence

from .recurrence_path_trajectory import RecurrencePathCodec
from .weighted_path_trajectory import WeightedEdge


Node = Hashable


class TranslationAddressMachine:
    def __init__(
        self,
        codec: RecurrencePathCodec,
    ) -> None:
        self.codec = codec
        self.field = codec.count_field

    def _node_offset_from_vector(
        self,
        node: Node,
        vector: Sequence[int],
    ) -> int:
        offset = 0
        for candidate in self.codec.nodes:
            if candidate == node:
                return offset
            offset += vector[
                self.field.node_index[candidate]
            ]
        raise KeyError(node)

    def _incoming_offset_from_vector(
        self,
        edge: WeightedEdge,
        predecessor_vector: Sequence[int],
    ) -> int:
        offset = 0
        for incoming in self.codec.incoming[edge.target]:
            if incoming == edge:
                return offset
            offset += predecessor_vector[
                self.field.node_index[incoming.source]
            ]
        raise ValueError("edge is not incoming to its target")

    def translation(
        self,
        edge_label: str,
        t: int,
    ) -> int:
        """Return the public additive address translation for one edge."""
        if t < 0:
            raise ValueError("t must be >= 0")

        try:
            edge = self.codec.edge_by_label[edge_label]
        except KeyError as exc:
            raise ValueError("unknown edge label") from exc

        if edge.length != 1:
            raise ValueError(
                "translation machine currently requires unit physical edges"
            )

        current = self.field.vector_at(t)
        nxt = self.field.vector_at(t + 1)

        source_offset = self._node_offset_from_vector(
            edge.source,
            current,
        )
        target_offset = self._node_offset_from_vector(
            edge.target,
            nxt,
        )
        incoming_offset = self._incoming_offset_from_vector(
            edge,
            current,
        )

        return (
            target_offset
            + incoming_offset
            - source_offset
        )

    def forward_step(
        self,
        state: int,
        t: int,
        edge_label: str,
    ) -> int:
        """Advance by adding the public edge translation."""
        current = self.field.vector_at(t)
        source, _ = self.codec._unpack_with_vector(
            state,
            current,
        )

        edge = self.codec.edge_by_label.get(edge_label)
        if edge is None:
            raise ValueError("unknown edge label")
        if edge.source != source:
            raise ValueError("edge does not leave current endpoint")

        new_state = state + self.translation(
            edge_label,
            t,
        )

        # Validate the translated address against the next public family.
        nxt = self.field.vector_at(t + 1)
        target, _ = self.codec._unpack_with_vector(
            new_state,
            nxt,
        )
        if target != edge.target:
            raise AssertionError(
                "public translation landed in wrong endpoint bucket"
            )

        return new_state

    def reverse_step(
        self,
        state: int,
        next_time: int,
    ) -> tuple[int, WeightedEdge]:
        """Identify the previous edge block and subtract its translation."""
        if next_time <= 0:
            raise ValueError("cannot reverse t=0")

        t = next_time - 1
        current = self.field.vector_at(next_time)
        previous = self.field.vector_at(t)

        target, rank = self.codec._unpack_with_vector(
            state,
            current,
        )

        offset = 0
        chosen = None
        previous_rank = None

        for edge in self.codec.incoming[target]:
            block = previous[
                self.field.node_index[edge.source]
            ]
            if rank < offset + block:
                chosen = edge
                previous_rank = rank - offset
                break
            offset += block

        if chosen is None or previous_rank is None:
            raise ValueError("address has no valid predecessor edge")

        translated = state - self.translation(
            chosen.label,
            t,
        )

        expected = self.codec._pack_with_vector(
            chosen.source,
            previous_rank,
            previous,
        )
        if translated != expected:
            raise AssertionError(
                "translation reverse disagrees with rank-block reverse"
            )

        return translated, chosen

    def encode_edges(
        self,
        start_node: Node,
        edge_labels,
    ) -> tuple[int, int]:
        state = self.codec._pack_with_vector(
            start_node,
            0,
            self.field.initial_vector,
        )
        t = 0

        for label in edge_labels:
            state = self.forward_step(
                state,
                t,
                label,
            )
            t += 1

        return state, t

    def decode_edges(
        self,
        final_state: int,
        physical_steps: int,
    ) -> tuple[Node, list[WeightedEdge]]:
        if physical_steps < 0:
            raise ValueError("physical_steps must be >= 0")

        state = final_state
        t = physical_steps
        reversed_edges = []

        while t > 0:
            state, edge = self.reverse_step(
                state,
                t,
            )
            reversed_edges.append(edge)
            t -= 1

        start, rank = self.codec._unpack_with_vector(
            state,
            self.field.initial_vector,
        )
        if rank != 0 or start not in self.codec.start_set:
            raise AssertionError(
                "reverse did not terminate in an initial state"
            )

        reversed_edges.reverse()
        return start, reversed_edges

    def reconstruct_physical_path(
        self,
        final_state: int,
        physical_steps: int,
    ):
        start, edges = self.decode_edges(
            final_state,
            physical_steps,
        )
        path = [start]
        for edge in edges:
            path.append(edge.target)
        return tuple(path)

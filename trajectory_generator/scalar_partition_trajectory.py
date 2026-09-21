"""Full-universe translation address decoded from scalar partition oracles.

This codec removes full endpoint-count-vector reconstruction from the reverse
path. Address evolution remains

    S_(t+1) = S_t + Delta(edge,t)

but endpoint buckets, incoming-edge blocks, and Delta itself are evaluated from
scalar Floquet functionals only.

The implementation wraps the same public graph/edge ordering as
RecurrencePathCodec so addresses are bit-for-bit identical.
"""

from __future__ import annotations

from typing import Hashable

from .floquet_path_trajectory import build_floquet_path_codec
from .scalar_floquet_partition import ScalarFloquetPartitionOracle
from .weighted_path_trajectory import WeightedEdge


Node = Hashable


class ScalarPartitionTranslationMachine:
    def __init__(
        self,
        codec,
        *,
        seed_cache_entries: int = 64,
    ) -> None:
        self.codec = codec
        self.field = codec.count_field
        self.oracle = ScalarFloquetPartitionOracle(
            self.field,
            seed_cache_entries=seed_cache_entries,
        )

        self.nodes = codec.nodes
        self.node_position = {
            node: i
            for i, node in enumerate(self.nodes)
        }

    def _prefix_weights_before(
        self,
        node: Node,
    ):
        position = self.node_position[node]
        return tuple(
            (candidate, 1)
            for candidate in self.nodes[:position]
        )

    def endpoint_offset(
        self,
        node: Node,
        t: int,
    ) -> int:
        return self.oracle.scalar_at(
            t,
            self._prefix_weights_before(node),
        )

    def endpoint_count(
        self,
        node: Node,
        t: int,
    ) -> int:
        return self.oracle.node_count(node, t)

    def locate_endpoint(
        self,
        state: int,
        t: int,
    ) -> tuple[Node, int]:
        if state < 0:
            raise ValueError("state must be non-negative")

        total = self.oracle.total_count(t)
        if state >= total:
            raise ValueError(
                "state outside exact-length path family"
            )

        # Only one public phase can be populated at time t.
        active_phase = (
            self.field.base_phase + t
        ) % self.field.period

        lower = 0
        for node in self.nodes:
            if (
                self.field.phase_of(node) % self.field.period
                != active_phase
            ):
                continue

            count = self.endpoint_count(node, t)
            if not count:
                continue

            # lower is the sum of all populated active-phase nodes preceding
            # this node in the global public node ordering.
            upper = lower + count
            if state < upper:
                return node, state - lower
            lower = upper

        raise AssertionError("address endpoint bucket not found")

    def incoming_offset(
        self,
        edge: WeightedEdge,
        t: int,
    ) -> int:
        offset_weights: dict[Node, int] = {}
        for incoming in self.codec.incoming[edge.target]:
            if incoming == edge:
                break
            offset_weights[incoming.source] = (
                offset_weights.get(incoming.source, 0) + 1
            )
        else:
            raise ValueError(
                "edge is not incoming to its target"
            )

        return self.oracle.scalar_at(
            t,
            offset_weights,
        )

    def translation(
        self,
        edge: WeightedEdge,
        t: int,
    ) -> int:
        return (
            self.endpoint_offset(edge.target, t + 1)
            + self.incoming_offset(edge, t)
            - self.endpoint_offset(edge.source, t)
        )

    def forward_step(
        self,
        state: int,
        t: int,
        edge_label: str,
    ) -> int:
        source, _ = self.locate_endpoint(state, t)
        edge = self.codec.edge_by_label.get(edge_label)
        if edge is None:
            raise ValueError("unknown edge label")
        if edge.source != source:
            raise ValueError(
                "edge does not leave current endpoint"
            )

        result = state + self.translation(edge, t)
        target, _ = self.locate_endpoint(
            result,
            t + 1,
        )
        if target != edge.target:
            raise AssertionError(
                "scalar translation landed in wrong endpoint"
            )
        return result

    def reverse_step(
        self,
        state: int,
        next_time: int,
    ) -> tuple[int, WeightedEdge]:
        if next_time <= 0:
            raise ValueError("cannot reverse t=0")

        t = next_time - 1
        target, rank = self.locate_endpoint(
            state,
            next_time,
        )

        offset = 0
        chosen = None
        previous_rank = None

        for edge in self.codec.incoming[target]:
            block = self.endpoint_count(
                edge.source,
                t,
            )
            if rank < offset + block:
                chosen = edge
                previous_rank = rank - offset
                break
            offset += block

        if chosen is None or previous_rank is None:
            raise ValueError(
                "address has no valid predecessor edge"
            )

        predecessor = state - self.translation(
            chosen,
            t,
        )

        source, got_rank = self.locate_endpoint(
            predecessor,
            t,
        )
        if (
            source != chosen.source
            or got_rank != previous_rank
        ):
            raise AssertionError(
                "scalar reverse disagrees with predecessor block"
            )

        return predecessor, chosen

    def decode_edges(
        self,
        final_state: int,
        physical_steps: int,
    ) -> tuple[Node, list[WeightedEdge]]:
        if physical_steps < 0:
            raise ValueError("physical_steps must be >= 0")

        current = final_state
        t = physical_steps
        reversed_edges = []

        while t > 0:
            current, edge = self.reverse_step(
                current,
                t,
            )
            reversed_edges.append(edge)
            t -= 1

        start, rank = self.locate_endpoint(
            current,
            0,
        )
        if (
            rank != 0
            or start not in self.codec.start_set
        ):
            raise AssertionError(
                "reverse did not terminate in an initial node"
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


def build_scalar_partition_translation_machine(
    adjacency,
    *,
    start_nodes,
    phase_of,
    period,
    base_phase=0,
    width=63,
    seed_cache_entries=64,
):
    codec = build_floquet_path_codec(
        adjacency,
        start_nodes=start_nodes,
        phase_of=phase_of,
        period=period,
        base_phase=base_phase,
        width=width,
        cache_rows=0,
    )
    return ScalarPartitionTranslationMachine(
        codec,
        seed_cache_entries=seed_cache_entries,
    )

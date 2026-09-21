"""Lossless information-clock trace layered over the exact fiber decoder.

The optimized final-state decoder already recovers one exact physical edge per
transition.  This module adds a second, coarser representation:

- recurrent deterministic flights are represented by one public macro-edge;
- everything not covered by such a macro-edge is retained in exact fallback
  physical-edge segments.

The trace is therefore lossless for the full public universe, including
transient prefixes, trajectories outside the dominant recurrent core, and
arbitrary transitions around the core.

This first event layer intentionally does *not* claim fewer count-recurrence
steps.  It establishes exact event segmentation and lazy physical expansion.
A later macro-block cursor can use the same trace contract to skip recurrence
work once composed vertical embeddings are available.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Hashable

from .recurrent_macrograph import (
    RecurrentStructure,
    derive_recurrent_structure,
)
from .seeded_vertical_connection import (
    SeededVerticalConnectionMachine,
)
from .vertical_connection_cursor import (
    VerticalConnectionBackwardCursor,
)
from .weighted_path_trajectory import WeightedEdge


Node = Hashable


@dataclass(frozen=True)
class MacroTraceItem:
    macro_label: str
    physical_steps: int


@dataclass(frozen=True)
class FallbackTraceItem:
    edge_labels: tuple[str, ...]

    @property
    def physical_steps(self) -> int:
        return len(self.edge_labels)


TraceItem = MacroTraceItem | FallbackTraceItem


@dataclass(frozen=True)
class InformationClockTrace:
    seed: int
    seed_bits: int
    transition_steps: int
    items: tuple[TraceItem, ...]
    physical_reverse_steps: int

    @property
    def physical_steps(self) -> int:
        return self.seed_bits + self.transition_steps

    @property
    def macro_event_count(self) -> int:
        return sum(
            isinstance(item, MacroTraceItem)
            for item in self.items
        )

    @property
    def macro_physical_steps(self) -> int:
        return sum(
            item.physical_steps
            for item in self.items
            if isinstance(item, MacroTraceItem)
        )

    @property
    def fallback_physical_steps(self) -> int:
        return sum(
            item.physical_steps
            for item in self.items
            if isinstance(item, FallbackTraceItem)
        )

    @property
    def emitted_item_count(self) -> int:
        return len(self.items)


class InformationClockTraceCodec:
    def __init__(
        self,
        machine: SeededVerticalConnectionMachine,
    ) -> None:
        self.machine = machine
        self.connection = machine.connection
        self.physical_codec = self.connection.codec

        adjacency = {
            node: tuple(
                edge.target
                for edge in self.physical_codec.outgoing[node]
            )
            for node in self.physical_codec.nodes
        }
        self.structure: RecurrentStructure = (
            derive_recurrent_structure(adjacency)
        )

        pair_to_edge: dict[
            tuple[Node, Node],
            WeightedEdge,
        ] = {}
        ambiguous_pairs = set()

        for edge in self.physical_codec.edges:
            key = (edge.source, edge.target)
            if key in pair_to_edge:
                ambiguous_pairs.add(key)
            else:
                pair_to_edge[key] = edge

        self.macro_by_label = {
            edge.label: edge
            for edge in self.structure.macro_edges
        }
        self.macro_edge_labels: dict[
            str,
            tuple[str, ...],
        ] = {}
        self.macros_from: dict[
            Node,
            list[tuple[WeightedEdge, tuple[str, ...]]],
        ] = {
            node: []
            for node in self.structure.branch_nodes
        }

        for macro in self.structure.macro_edges:
            labels = []
            for source, target in zip(
                macro.path,
                macro.path[1:],
            ):
                key = (source, target)
                if key in ambiguous_pairs:
                    raise ValueError(
                        "macro path uses ambiguous parallel physical edges"
                    )
                physical = pair_to_edge.get(key)
                if physical is None:
                    raise ValueError(
                        "macro path edge missing from physical codec"
                    )
                labels.append(physical.label)

            label_tuple = tuple(labels)
            self.macro_edge_labels[
                macro.label
            ] = label_tuple
            self.macros_from[
                macro.source
            ].append((macro, label_tuple))

    def _seed_from_terminal_state(
        self,
        node: Node,
        rank: int,
    ) -> int:
        if rank != 0:
            raise AssertionError(
                "reverse trace did not reach singleton seed fiber"
            )
        try:
            return self.machine.start_node_to_seed[
                node
            ]
        except KeyError as exc:
            raise ValueError(
                "reverse trace did not reach a public seed node"
            ) from exc

    def _macro_match(
        self,
        edge_labels: tuple[str, ...],
        index: int,
    ):
        if index >= len(edge_labels):
            return None

        edge = self.physical_codec.edge_by_label[
            edge_labels[index]
        ]
        candidates = self.macros_from.get(
            edge.source,
            (),
        )

        matched = []
        for macro, labels in candidates:
            end = index + len(labels)
            if (
                end <= len(edge_labels)
                and edge_labels[index:end] == labels
            ):
                matched.append((macro, labels))

        if len(matched) > 1:
            raise AssertionError(
                "macro decomposition is not prefix-unique"
            )
        return matched[0] if matched else None

    def compress_edges(
        self,
        edge_labels,
    ) -> tuple[TraceItem, ...]:
        labels = tuple(edge_labels)
        items: list[TraceItem] = []
        fallback: list[str] = []
        index = 0

        def flush_fallback() -> None:
            if fallback:
                items.append(
                    FallbackTraceItem(
                        edge_labels=tuple(fallback)
                    )
                )
                fallback.clear()

        while index < len(labels):
            match = self._macro_match(
                labels,
                index,
            )
            if match is None:
                fallback.append(labels[index])
                index += 1
                continue

            flush_fallback()
            macro, macro_labels = match
            items.append(
                MacroTraceItem(
                    macro_label=macro.label,
                    physical_steps=macro.length,
                )
            )
            index += len(macro_labels)

        flush_fallback()
        return tuple(items)

    def decode_trace(
        self,
        final_state: int,
        steps: int,
    ) -> InformationClockTrace:
        early = self.machine._validate_decode_inputs(
            final_state,
            steps,
        )
        if early is not None:
            seed = self.machine._integer_from_bits(
                early
            )
            return InformationClockTrace(
                seed=seed,
                seed_bits=steps,
                transition_steps=0,
                items=(),
                physical_reverse_steps=0,
            )

        transition_steps = (
            steps - self.machine.seed_bits
        )
        cursor = VerticalConnectionBackwardCursor(
            self.connection,
            final_state,
            transition_steps,
        )

        reversed_labels = []
        while cursor.state.time > 0:
            edge = cursor.reverse()
            reversed_labels.append(edge.label)

        seed = self._seed_from_terminal_state(
            cursor.state.node,
            cursor.state.rank,
        )
        reversed_labels.reverse()
        labels = tuple(reversed_labels)
        items = self.compress_edges(labels)

        if (
            sum(item.physical_steps for item in items)
            != transition_steps
        ):
            raise AssertionError(
                "information-clock trace changed physical length"
            )

        return InformationClockTrace(
            seed=seed,
            seed_bits=self.machine.seed_bits,
            transition_steps=transition_steps,
            items=items,
            physical_reverse_steps=(
                cursor.metrics.reverse_steps
            ),
        )

    def expand_edge_labels(
        self,
        trace: InformationClockTrace,
    ) -> tuple[str, ...]:
        labels = []
        for item in trace.items:
            if isinstance(item, MacroTraceItem):
                labels.extend(
                    self.macro_edge_labels[
                        item.macro_label
                    ]
                )
            else:
                labels.extend(item.edge_labels)

        result = tuple(labels)
        if len(result) != trace.transition_steps:
            raise AssertionError(
                "expanded event trace has wrong physical length"
            )
        return result

    def expand_bits(
        self,
        trace: InformationClockTrace,
    ) -> list[int]:
        seed_values = self.machine._bits_from_integer(
            trace.seed,
            trace.seed_bits,
        )
        bits = list(seed_values)

        for label in self.expand_edge_labels(trace):
            edge = self.physical_codec.edge_by_label[
                label
            ]
            bits.append(
                int(self.machine.edge_symbol(edge))
            )

        if len(bits) != trace.physical_steps:
            raise AssertionError(
                "expanded event trace has wrong bit length"
            )
        return bits

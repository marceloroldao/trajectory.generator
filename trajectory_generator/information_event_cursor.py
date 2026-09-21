"""Hybrid exact backward cursor operating in information-clock events.

The cursor starts from the same full-universe final_state + physical step count
as the physical vertical decoder.

At each call to reverse_event():

1. try exact composed information-clock predecessor blocks ending at the current
   horizontal node;
2. if the current vertical rank lies inside one macro-block, jump directly to
   that macro-edge source fiber;
3. otherwise reverse exactly one physical edge.

The macro-block calculation includes all reachable predecessors in the public
universe, so recurrent-core merges and transient in-edges do not invalidate the
jump.

Macro candidates are evaluated directly as precompiled linear functionals of
the public count vector at the macro source time. The backward Floquet cursor
can look up that source vector from its compact recurrence window without
walking the candidate path.

A successful macro therefore performs one bounded count-vector lookback, one
integer dot product for the composed block offset, one rank interval test, and
one multi-step Floquet cursor move. No candidate path is replayed physically.
"""

from __future__ import annotations

from dataclasses import dataclass

from .composed_vertical_connection import (
    ComposedVerticalConnection,
)
from .exact_vertical_connection import (
    LocalFiberState,
)
from .information_clock_trace import (
    FallbackTraceItem,
    InformationClockTrace,
    InformationClockTraceCodec,
    MacroTraceItem,
)
from .vertical_connection_cursor import (
    VerticalConnectionBackwardCursor,
)


@dataclass(frozen=True)
class InformationEventCursorMetrics:
    logical_reverse_operations: int
    macro_jumps: int
    macro_physical_steps: int
    fallback_physical_steps: int
    equivalent_physical_steps: int
    count_cursor_restarts: int
    macro_probe_physical_steps: int
    macro_block_evaluations: int
    maximum_stored_floquet_rows: int
    phase_state_count: int

    @property
    def semantic_reduction_ratio(self) -> float:
        if self.logical_reverse_operations == 0:
            return 1.0
        return (
            self.equivalent_physical_steps
            / self.logical_reverse_operations
        )

    @property
    def maximum_stored_count_integers(self) -> int:
        return (
            self.maximum_stored_floquet_rows
            * self.phase_state_count
        )


class InformationEventBackwardCursor:
    def __init__(
        self,
        trace_codec: InformationClockTraceCodec,
        final_state: int,
        transition_steps: int,
    ) -> None:
        if transition_steps < 0:
            raise ValueError(
                "transition_steps must be non-negative"
            )

        self.trace_codec = trace_codec
        self.machine = trace_codec.machine
        self.connection = trace_codec.connection
        self.field = self.connection.machine.field
        initial = VerticalConnectionBackwardCursor(
            self.connection,
            final_state,
            transition_steps,
        )
        self.state = initial.state
        self.count_cursor = initial.count_cursor

        self._logical_operations = 0
        self._macro_jumps = 0
        self._macro_physical_steps = 0
        self._fallback_physical_steps = 0
        self._count_cursor_restarts = 0
        self._macro_probe_physical_steps = 0
        self._macro_block_evaluations = 0
        self._maximum_stored_rows = (
            self.count_cursor.stored_row_count
        )

        self.composed = ComposedVerticalConnection(
            self.connection
        )
        self.macro_candidates = {}
        for macro in trace_codec.structure.macro_edges:
            labels = trace_codec.macro_edge_labels[
                macro.label
            ]
            plan = self.composed.compile_path(
                labels
            )
            self.macro_candidates.setdefault(
                macro.target,
                [],
            ).append((
                macro.label,
                plan,
            ))

    @property
    def metrics(self) -> InformationEventCursorMetrics:
        return InformationEventCursorMetrics(
            logical_reverse_operations=(
                self._logical_operations
            ),
            macro_jumps=self._macro_jumps,
            macro_physical_steps=(
                self._macro_physical_steps
            ),
            fallback_physical_steps=(
                self._fallback_physical_steps
            ),
            equivalent_physical_steps=(
                self._macro_physical_steps
                + self._fallback_physical_steps
            ),
            count_cursor_restarts=(
                self._count_cursor_restarts
            ),
            macro_probe_physical_steps=(
                self._macro_probe_physical_steps
            ),
            macro_block_evaluations=(
                self._macro_block_evaluations
            ),
            maximum_stored_floquet_rows=(
                self._maximum_stored_rows
            ),
            phase_state_count=(
                self.field.phase_state_count
            ),
        )

    def _try_macro_jump(self):
        candidates = self.macro_candidates.get(
            self.state.node,
            (),
        )
        if not candidates:
            return None

        base_vectors_by_distance = {}

        for macro_label, plan in candidates:
            distance = plan.physical_steps
            if distance > self.state.time:
                continue
            if plan.target != self.state.node:
                continue

            base_lookup = base_vectors_by_distance.get(
                distance
            )
            if base_lookup is None:
                base_lookup = (
                    self.count_cursor.period_base_vector_at_back(
                        distance
                    )
                )
                base_vectors_by_distance[
                    distance
                ] = base_lookup

            base_vector, phase_offset = base_lookup
            start_time = (
                self.state.time - distance
            )
            if (
                phase_offset
                != plan.source_phase_offset
            ):
                continue

            block = (
                self.composed.embedding_from_period_base_vector(
                    plan,
                    start_time=start_time,
                    base_vector=base_vector,
                    target_size=self.state.fiber_size,
                )
            )
            self._macro_block_evaluations += 1

            if (
                block.source_size <= 0
                or not (
                    block.start
                    <= self.state.rank
                    < block.end
                )
            ):
                continue

            previous_rank = (
                self.state.rank - block.start
            )
            self.count_cursor.step_back_many(
                distance
            )
            self.state = LocalFiberState(
                time=self.state.time - distance,
                node=block.source,
                rank=previous_rank,
                fiber_size=block.source_size,
            )
            self._maximum_stored_rows = max(
                self._maximum_stored_rows,
                self.count_cursor.stored_row_count,
            )
            self._logical_operations += 1
            self._macro_jumps += 1
            self._macro_physical_steps += distance

            return MacroTraceItem(
                macro_label=macro_label,
                physical_steps=distance,
            )

        return None

    def _reverse_one_physical(self):
        current = self.state
        if current.time <= 0:
            raise ValueError("cannot reverse t=0")
        if self.count_cursor.time != current.time:
            raise AssertionError(
                "count cursor and event state time diverged"
            )

        incoming = self.connection.codec.incoming[
            current.node
        ]

        if len(incoming) == 1:
            chosen = incoming[0]
            self.count_cursor.step_back()
            previous = LocalFiberState(
                time=current.time - 1,
                node=chosen.source,
                rank=current.rank,
                fiber_size=current.fiber_size,
            )
        else:
            previous_vector = (
                self.count_cursor.previous_vector()
            )
            offset = 0
            chosen = None
            previous_rank = None
            previous_size = None

            for edge in incoming:
                block = previous_vector[
                    self.field.node_index[
                        edge.source
                    ]
                ]
                if block <= 0:
                    continue

                if current.rank < offset + block:
                    chosen = edge
                    previous_rank = (
                        current.rank - offset
                    )
                    previous_size = block
                    break
                offset += block

            if (
                chosen is None
                or previous_rank is None
                or previous_size is None
            ):
                raise ValueError(
                    "vertical rank belongs to no physical predecessor block"
                )

            self.count_cursor.step_back()
            previous = LocalFiberState(
                time=current.time - 1,
                node=chosen.source,
                rank=previous_rank,
                fiber_size=previous_size,
            )

        self.state = previous
        self._maximum_stored_rows = max(
            self._maximum_stored_rows,
            self.count_cursor.stored_row_count,
        )
        self._logical_operations += 1
        self._fallback_physical_steps += 1

        return FallbackTraceItem(
            edge_labels=(chosen.label,)
        )

    def reverse_event(self):
        if self.state.time <= 0:
            raise ValueError("cannot reverse t=0")

        macro = self._try_macro_jump()
        if macro is not None:
            return macro
        return self._reverse_one_physical()

    def decode_trace(
        self,
        *,
        seed_bits: int,
        start_node_to_seed,
    ) -> InformationClockTrace:
        reversed_items = []

        while self.state.time > 0:
            reversed_items.append(
                self.reverse_event()
            )

        if self.state.rank != 0:
            raise AssertionError(
                "event cursor did not reach singleton seed fiber"
            )
        try:
            seed = start_node_to_seed[
                self.state.node
            ]
        except KeyError as exc:
            raise ValueError(
                "event cursor did not reach a public seed node"
            ) from exc

        # Reverse order and coalesce adjacent single-edge fallbacks so the
        # public trace contract remains compact.
        reversed_items.reverse()
        items = []
        fallback = []

        def flush():
            if fallback:
                items.append(
                    FallbackTraceItem(
                        edge_labels=tuple(fallback)
                    )
                )
                fallback.clear()

        for item in reversed_items:
            if isinstance(item, MacroTraceItem):
                flush()
                items.append(item)
            else:
                fallback.extend(
                    item.edge_labels
                )
        flush()

        transition_steps = (
            self.metrics.equivalent_physical_steps
        )

        return InformationClockTrace(
            seed=seed,
            seed_bits=seed_bits,
            transition_steps=transition_steps,
            items=tuple(items),
            physical_reverse_steps=transition_steps,
        )

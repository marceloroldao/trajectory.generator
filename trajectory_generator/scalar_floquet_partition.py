"""Scalar Floquet oracle for address partition boundaries.

The full endpoint-count vector is not required to locate an enumerative address.
Reverse decoding only asks scalar questions such as:

- how many paths end before endpoint node v?
- how many predecessor paths belong to one incoming edge block?

Each question is an integer linear functional of the public count field. For a
phase-lifted universe, any such scalar sequence sampled once per period obeys
the same Floquet recurrence as the count vector.

This oracle evaluates those scalar functionals directly. It never calls
FloquetCountFieldRecurrence.vector_at() and never reconstructs the full
requested-time endpoint vector.

For physical time t=P*q+r:

1. project the requested full-node functional backward onto the base-phase
   Floquet slice across r public transitions;
2. generate only the first d scalar seed values on the P-step graph;
3. evaluate the q-th scalar value with the shared recurrence.

Seed sequences are kept in a bounded LRU cache. Without cache, resident working
memory is O(B+d), where B is the base-phase state count and d the Floquet
recurrence order, independent of physical horizon.
"""

from __future__ import annotations

from collections import OrderedDict
from typing import Hashable, Mapping, Sequence

from .count_field_recurrence import _nth_recurrence_weights
from .floquet_count_field import FloquetCountFieldRecurrence


Node = Hashable
Functional = tuple[tuple[int, int], ...]


def _canonical_functional(
    node_index: Mapping[Node, int],
    weights: Mapping[Node, int] | Sequence[tuple[Node, int]],
) -> Functional:
    items = weights.items() if isinstance(weights, Mapping) else weights
    combined: dict[int, int] = {}
    for node, weight in items:
        if not weight:
            continue
        index = node_index.get(node)
        if index is None:
            continue
        combined[index] = combined.get(index, 0) + int(weight)
    return tuple(
        (index, weight)
        for index, weight in sorted(combined.items())
        if weight
    )


class ScalarFloquetPartitionOracle:
    def __init__(
        self,
        field: FloquetCountFieldRecurrence,
        *,
        seed_cache_entries: int = 32,
    ) -> None:
        if seed_cache_entries < 0:
            raise ValueError("seed_cache_entries must be >= 0")

        self.field = field
        self.seed_cache_entries = seed_cache_entries
        self._seed_cache: OrderedDict[
            tuple[int, Functional],
            tuple[int, ...],
        ] = OrderedDict()

        # Precompute one-period adjacency on the base slice from the compact
        # period field. No physical-time count vectors are retained.
        self.base_outgoing = field.period_field.outgoing
        self.base_initial = field.period_field.initial_vector

        # For projecting a physical-time scalar functional onto base phase we
        # need public r-step paths from every base node. r < period.
        self.base_nodes = field.base_nodes

    @property
    def cached_functional_count(self) -> int:
        return len(self._seed_cache)

    def clear_cache(self) -> None:
        self._seed_cache.clear()

    def _project_to_base(
        self,
        functional: Functional,
        phase_offset: int,
    ) -> tuple[int, ...]:
        if not 0 <= phase_offset < self.field.period:
            raise ValueError("phase_offset outside period")

        full_weights = dict(functional)
        projected = []

        for base_node in self.base_nodes:
            frontier = {base_node: 1}
            for _ in range(phase_offset):
                nxt: dict[Node, int] = {}
                for source, multiplicity in frontier.items():
                    source_index = self.field.node_index[source]
                    for target_index in self.field.outgoing[source_index]:
                        target = self.field.nodes[target_index]
                        nxt[target] = (
                            nxt.get(target, 0) + multiplicity
                        )
                frontier = nxt

            value = 0
            for node, multiplicity in frontier.items():
                value += (
                    multiplicity
                    * full_weights.get(
                        self.field.node_index[node],
                        0,
                    )
                )
            projected.append(value)

        return tuple(projected)

    def _step_base(
        self,
        vector: Sequence[int],
    ) -> tuple[int, ...]:
        out = [0] * len(vector)
        for source, count in enumerate(vector):
            if not count:
                continue
            for target in self.base_outgoing[source]:
                out[target] += count
        return tuple(out)

    def _seed_values(
        self,
        phase_offset: int,
        functional: Functional,
    ) -> tuple[int, ...]:
        key = (phase_offset, functional)
        cached = self._seed_cache.get(key)
        if cached is not None:
            self._seed_cache.move_to_end(key)
            return cached

        projected = self._project_to_base(
            functional,
            phase_offset,
        )

        values = []
        base_vector = self.base_initial
        for i in range(self.field.order):
            values.append(
                sum(
                    weight * value
                    for weight, value in zip(
                        projected,
                        base_vector,
                    )
                )
            )
            if i + 1 < self.field.order:
                base_vector = self._step_base(base_vector)

        result = tuple(values)

        if self.seed_cache_entries:
            self._seed_cache[key] = result
            self._seed_cache.move_to_end(key)
            while len(self._seed_cache) > self.seed_cache_entries:
                self._seed_cache.popitem(last=False)

        return result

    def scalar_at(
        self,
        t: int,
        weights: Mapping[Node, int] | Sequence[tuple[Node, int]],
    ) -> int:
        if t < 0:
            raise ValueError("t must be >= 0")

        functional = _canonical_functional(
            self.field.node_index,
            weights,
        )
        if not functional:
            return 0

        period_index, phase_offset = divmod(
            t,
            self.field.period,
        )

        seeds = self._seed_values(
            phase_offset,
            functional,
        )

        if period_index < self.field.order:
            return seeds[period_index]

        recurrence_weights = _nth_recurrence_weights(
            period_index,
            self.field.coefficients,
        )
        return sum(
            coefficient * seed
            for coefficient, seed in zip(
                recurrence_weights,
                seeds,
            )
        )

    def node_count(self, node: Node, t: int) -> int:
        return self.scalar_at(t, ((node, 1),))

    def total_count(self, t: int) -> int:
        return self.scalar_at(
            t,
            tuple((node, 1) for node in self.field.nodes),
        )

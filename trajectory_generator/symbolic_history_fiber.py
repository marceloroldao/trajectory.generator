"""Symbol-induced structure on reversible history fibers.

The full fiber-gauge no-go applies when a fiber is treated as a bare finite set.
trajectory.generator histories carry more structure: each admissible transition
has a public input symbol, and the bootstrap state is itself a public symbol
word.

Given:
- a finite directed graph with symbol-labeled edges;
- a public totally ordered alphabet;
- a unique public bootstrap word for each initial node;

every admissible history has a public symbol word.

If symbol words are unique, they induce a canonical lexicographic order inside
each endpoint fiber.  This order is independent of arbitrary node identifiers
and edge enumeration as long as graph isomorphisms preserve public symbols.

The ordered fiber then has:
- a distinguished origin: lexicographically smallest history;
- a canonical rank 0..n-1;
- a derived cyclic coordinate Z_n by rank modulo n.

This is an *additional-structure* construction. It does not contradict the
unstructured-fiber no-go: the alphabet order and symbol labels are extra public
structure not contained in fiber cardinality alone.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Hashable, Mapping, Sequence


Node = Hashable
Symbol = Hashable
Word = tuple[Symbol, ...]


@dataclass(frozen=True)
class SymbolicEdge:
    symbol: Symbol
    source: Node
    target: Node


@dataclass(frozen=True)
class SymbolicHistory:
    start: Node
    endpoint: Node
    word: Word
    edges: tuple[SymbolicEdge, ...]


class SymbolicHistoryFibers:
    def __init__(
        self,
        adjacency: Mapping[
            Node,
            Sequence[tuple[Symbol, Node]],
        ],
        *,
        start_words: Mapping[Node, Sequence[Symbol]],
        alphabet_order: Sequence[Symbol],
    ) -> None:
        if not start_words:
            raise ValueError("start_words must be non-empty")

        self.alphabet_order = tuple(alphabet_order)
        if len(set(self.alphabet_order)) != len(
            self.alphabet_order
        ):
            raise ValueError("alphabet_order must be unique")
        self.symbol_rank = {
            symbol: i
            for i, symbol in enumerate(self.alphabet_order)
        }

        nodes = set(adjacency)
        for rows in adjacency.values():
            for symbol, target in rows:
                if symbol not in self.symbol_rank:
                    raise ValueError("edge uses unknown public symbol")
                nodes.add(target)

        for start, word in start_words.items():
            nodes.add(start)
            for symbol in word:
                if symbol not in self.symbol_rank:
                    raise ValueError("bootstrap uses unknown symbol")

        self.nodes = tuple(sorted(nodes, key=repr))
        self.start_words = {
            node: tuple(word)
            for node, word in start_words.items()
        }

        outgoing: dict[Node, list[SymbolicEdge]] = {
            node: [] for node in self.nodes
        }
        for source in self.nodes:
            for symbol, target in adjacency.get(
                source,
                (),
            ):
                outgoing[source].append(
                    SymbolicEdge(
                        symbol=symbol,
                        source=source,
                        target=target,
                    )
                )
        self.outgoing = {
            node: tuple(rows)
            for node, rows in outgoing.items()
        }

        initial: dict[Node, list[SymbolicHistory]] = {
            node: [] for node in self.nodes
        }
        for node, word in self.start_words.items():
            initial[node].append(
                SymbolicHistory(
                    start=node,
                    endpoint=node,
                    word=word,
                    edges=(),
                )
            )

        self._layers = [
            {
                node: tuple(rows)
                for node, rows in initial.items()
            }
        ]

    def _word_key(self, word: Word) -> tuple[int, ...]:
        return tuple(
            self.symbol_rank[symbol]
            for symbol in word
        )

    def ensure_horizon(self, time: int) -> None:
        if time < 0:
            raise ValueError("time must be >= 0")

        while len(self._layers) <= time:
            previous = self._layers[-1]
            nxt: dict[Node, list[SymbolicHistory]] = {
                node: [] for node in self.nodes
            }

            for source in self.nodes:
                for history in previous[source]:
                    for edge in self.outgoing[source]:
                        nxt[edge.target].append(
                            SymbolicHistory(
                                start=history.start,
                                endpoint=edge.target,
                                word=(
                                    history.word
                                    + (edge.symbol,)
                                ),
                                edges=(
                                    history.edges
                                    + (edge,)
                                ),
                            )
                        )

            self._layers.append(
                {
                    node: tuple(rows)
                    for node, rows in nxt.items()
                }
            )

    def histories(
        self,
        node: Node,
        time: int,
    ) -> tuple[SymbolicHistory, ...]:
        self.ensure_horizon(time)
        return self._layers[time].get(node, ())

    def ordered_histories(
        self,
        node: Node,
        time: int,
    ) -> tuple[SymbolicHistory, ...]:
        rows = self.histories(node, time)
        return tuple(
            sorted(
                rows,
                key=lambda row: self._word_key(
                    row.word
                ),
            )
        )

    def words_are_unique(
        self,
        *,
        time: int,
        within_each_fiber: bool = True,
    ) -> bool:
        self.ensure_horizon(time)

        if within_each_fiber:
            return all(
                len({
                    row.word
                    for row in self.histories(node, time)
                })
                == len(self.histories(node, time))
                for node in self.nodes
            )

        all_rows = [
            row
            for node in self.nodes
            for row in self.histories(node, time)
        ]
        return (
            len({row.word for row in all_rows})
            == len(all_rows)
        )

    def origin(
        self,
        node: Node,
        time: int,
    ) -> SymbolicHistory:
        rows = self.ordered_histories(node, time)
        if not rows:
            raise ValueError("fiber is empty")
        return rows[0]

    def rank(
        self,
        history: SymbolicHistory,
        time: int,
    ) -> int:
        rows = self.ordered_histories(
            history.endpoint,
            time,
        )
        for i, candidate in enumerate(rows):
            if candidate.word == history.word:
                return i
        raise ValueError("history not present in fiber")

    def history_by_rank(
        self,
        node: Node,
        time: int,
        rank: int,
    ) -> SymbolicHistory:
        rows = self.ordered_histories(node, time)
        if not 0 <= rank < len(rows):
            raise ValueError("rank outside fiber")
        return rows[rank]

    def cyclic_inverse_rank(
        self,
        node: Node,
        time: int,
        rank: int,
    ) -> int:
        size = len(self.ordered_histories(node, time))
        if size <= 0:
            raise ValueError("fiber is empty")
        if not 0 <= rank < size:
            raise ValueError("rank outside fiber")
        return (-rank) % size

    def cyclic_add_ranks(
        self,
        node: Node,
        time: int,
        left: int,
        right: int,
    ) -> int:
        size = len(self.ordered_histories(node, time))
        if size <= 0:
            raise ValueError("fiber is empty")
        if not 0 <= left < size or not 0 <= right < size:
            raise ValueError("rank outside fiber")
        return (left + right) % size

    def chart_signature(
        self,
        node: Node,
        time: int,
    ) -> tuple[Word, ...]:
        return tuple(
            row.word
            for row in self.ordered_histories(
                node,
                time,
            )
        )

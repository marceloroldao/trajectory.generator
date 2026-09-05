from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Iterable


@dataclass(frozen=True)
class MacroEdge:
    source: str
    target: str
    physical_length: int
    label: str


# Canonical macrograph for the recurrent-orbit candidate documented in
# experiments/information_clock_macrograph.py.
MACRO_EDGES: tuple[MacroEdge, ...] = (
    MacroEdge("A", "B", 1, "AB1"),
    MacroEdge("A", "A", 12, "AA12"),
    MacroEdge("B", "A", 2, "BA2"),
    MacroEdge("B", "A", 5, "BA5"),
)

_BY_SOURCE = {
    state: tuple(edge for edge in MACRO_EDGES if edge.source == state)
    for state in {edge.source for edge in MACRO_EDGES}
}


def _validate_length(total_length: int) -> None:
    if total_length < 0:
        raise ValueError("negative physical length")


@lru_cache(maxsize=None)
def count_paths(start_state: str, total_length: int, end_state: str | None = None) -> int:
    """Count admissible macro-event paths with exact physical length.

    If ``end_state`` is omitted, paths may terminate at either branch state.
    """
    _validate_length(total_length)
    if total_length == 0:
        return int(end_state is None or start_state == end_state)

    total = 0
    for edge in _BY_SOURCE.get(start_state, ()):
        if edge.physical_length <= total_length:
            total += count_paths(edge.target, total_length - edge.physical_length, end_state)
    return total


def rank_path(
    labels: Iterable[str],
    *,
    start_state: str,
    total_length: int,
    end_state: str | None = None,
) -> int:
    """Rank one admissible macro-event sequence lexicographically by edge label."""
    _validate_length(total_length)
    labels = tuple(labels)
    state = start_state
    remaining = total_length
    rank = 0

    for chosen_label in labels:
        options = sorted(_BY_SOURCE.get(state, ()), key=lambda edge: edge.label)
        chosen = None
        for edge in options:
            if edge.label == chosen_label:
                chosen = edge
                break
            if edge.physical_length <= remaining:
                rank += count_paths(edge.target, remaining - edge.physical_length, end_state)
        if chosen is None:
            raise ValueError(f"invalid edge label {chosen_label!r} from state {state!r}")
        if chosen.physical_length > remaining:
            raise ValueError("path exceeds requested physical length")
        state = chosen.target
        remaining -= chosen.physical_length

    if remaining != 0:
        raise ValueError("path does not consume requested physical length")
    if end_state is not None and state != end_state:
        raise ValueError("path terminates at the wrong branch state")
    return rank


def unrank_path(
    rank: int,
    *,
    start_state: str,
    total_length: int,
    end_state: str | None = None,
) -> tuple[str, ...]:
    """Recover the unique admissible macro-event sequence at ``rank``."""
    _validate_length(total_length)
    total = count_paths(start_state, total_length, end_state)
    if rank < 0 or rank >= total:
        raise ValueError("rank outside admissible range")

    state = start_state
    remaining = total_length
    out: list[str] = []

    while remaining:
        options = sorted(_BY_SOURCE.get(state, ()), key=lambda edge: edge.label)
        for edge in options:
            if edge.physical_length > remaining:
                continue
            bucket = count_paths(edge.target, remaining - edge.physical_length, end_state)
            if bucket == 0:
                continue
            if rank < bucket:
                out.append(edge.label)
                state = edge.target
                remaining -= edge.physical_length
                break
            rank -= bucket
        else:
            raise RuntimeError("no admissible continuation for valid rank")

    if end_state is not None and state != end_state:
        raise RuntimeError("decoded path ended at unexpected state")
    return tuple(out)


def regenerate_physical_lengths(labels: Iterable[str], *, start_state: str) -> tuple[int, ...]:
    """Expand a macro-event sequence to its physical-flight lengths.

    Full microscopic node regeneration is handled by the recurrent-orbit graph
    experiment; this function proves exact regeneration of the variable-length
    information clock implied by the public macrograph.
    """
    state = start_state
    lengths: list[int] = []
    for label in labels:
        edge = next((e for e in _BY_SOURCE.get(state, ()) if e.label == label), None)
        if edge is None:
            raise ValueError(f"invalid edge label {label!r} from state {state!r}")
        lengths.append(edge.physical_length)
        state = edge.target
    return tuple(lengths)

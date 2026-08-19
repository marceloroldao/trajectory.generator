"""Hierarchical / relational trajectory-address experiment.

This module explores a different question from `trajectory_address.py`.

For arbitrary data, a `width`-bit final state cannot encode more than `width` bits of
independent information. However, structured trajectories may have much lower entropy
than their raw step count suggests.

Here the trajectory is represented by relations between successive bits: the initial
bit plus the positions where the bit changes. For a public maximum number of changes
`max_changes`, every admissible trajectory can be ranked combinatorially into one
integer. That rank is then permuted by a public, reversible, step-dependent universe
map. The decoder receives only `(final_state, steps)` and the public configuration.

This is exact enumerative coding of a constrained trajectory family. It is not
compression of arbitrary data and does not violate the pigeonhole principle.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import comb
from typing import Iterable


@dataclass(frozen=True)
class HierarchicalTrajectoryConfig:
    width: int = 63
    max_changes: int = 5
    universe_mul: int = 0x2D
    universe_seed: int = 0x6D2B79F5

    def __post_init__(self) -> None:
        if not 1 <= self.width <= 64:
            raise ValueError("width must be between 1 and 64")
        if self.max_changes < 0:
            raise ValueError("max_changes must be non-negative")
        if self.universe_mul % 2 == 0:
            raise ValueError("universe_mul must be odd")

    @property
    def modulus(self) -> int:
        return 1 << self.width

    @property
    def mask(self) -> int:
        return self.modulus - 1


DEFAULT_HIERARCHICAL_CONFIG = HierarchicalTrajectoryConfig()


def admissible_count(steps: int, cfg: HierarchicalTrajectoryConfig = DEFAULT_HIERARCHICAL_CONFIG) -> int:
    """Number of binary trajectories of length `steps` with <= max_changes transitions."""
    if steps < 0:
        raise ValueError("steps must be non-negative")
    if steps == 0:
        return 1
    limit = min(cfg.max_changes, steps - 1)
    return 2 * sum(comb(steps - 1, k) for k in range(limit + 1))


def capacity_ok(steps: int, cfg: HierarchicalTrajectoryConfig = DEFAULT_HIERARCHICAL_CONFIG) -> bool:
    return admissible_count(steps, cfg) <= cfg.modulus


def _changes(bits: list[int]) -> list[int]:
    return [i for i in range(1, len(bits)) if bits[i] != bits[i - 1]]


def _rank_combination_lex(indices: list[int], n: int, k: int) -> int:
    """Rank a sorted k-combination from range(n) in lexicographic order."""
    rank = 0
    prev = -1
    for pos, value in enumerate(indices):
        for candidate in range(prev + 1, value):
            rank += comb(n - candidate - 1, k - pos - 1)
        prev = value
    return rank


def _unrank_combination_lex(rank: int, n: int, k: int) -> list[int]:
    if rank < 0 or rank >= comb(n, k):
        raise ValueError("combination rank out of range")
    out: list[int] = []
    next_min = 0
    for pos in range(k):
        for candidate in range(next_min, n):
            count = comb(n - candidate - 1, k - pos - 1)
            if rank < count:
                out.append(candidate)
                next_min = candidate + 1
                break
            rank -= count
    return out


def rank_trajectory(bits: Iterable[int], cfg: HierarchicalTrajectoryConfig = DEFAULT_HIERARCHICAL_CONFIG) -> tuple[int, int]:
    seq = [int(b) for b in bits]
    if any(b not in (0, 1) for b in seq):
        raise ValueError("bits must contain only 0 and 1")
    steps = len(seq)
    if steps == 0:
        return 0, 0
    changes = _changes(seq)
    k = len(changes)
    if k > cfg.max_changes:
        raise ValueError("trajectory exceeds configured max_changes")
    if not capacity_ok(steps, cfg):
        raise ValueError("admissible trajectory family exceeds final-state capacity")

    # Layout by number of changes, then initial bit, then combination rank.
    offset = 0
    for j in range(k):
        offset += 2 * comb(steps - 1, j)

    # Convert change positions 1..steps-1 to combination indices 0..steps-2.
    combo = [p - 1 for p in changes]
    within = _rank_combination_lex(combo, steps - 1, k)
    rank = offset + seq[0] * comb(steps - 1, k) + within
    return rank, steps


def unrank_trajectory(rank: int, steps: int, cfg: HierarchicalTrajectoryConfig = DEFAULT_HIERARCHICAL_CONFIG) -> list[int]:
    if steps < 0:
        raise ValueError("steps must be non-negative")
    if steps == 0:
        if rank != 0:
            raise ValueError("invalid rank for empty trajectory")
        return []
    total = admissible_count(steps, cfg)
    if rank < 0 or rank >= total:
        raise ValueError("rank outside admissible trajectory family")

    remaining = rank
    limit = min(cfg.max_changes, steps - 1)
    k = None
    bucket = 0
    for j in range(limit + 1):
        bucket = 2 * comb(steps - 1, j)
        if remaining < bucket:
            k = j
            break
        remaining -= bucket
    assert k is not None

    combos = comb(steps - 1, k)
    initial = 1 if remaining >= combos else 0
    within = remaining - initial * combos
    combo = _unrank_combination_lex(within, steps - 1, k)
    change_positions = {idx + 1 for idx in combo}

    bits = [initial]
    current = initial
    for i in range(1, steps):
        if i in change_positions:
            current ^= 1
        bits.append(current)
    return bits


def _time_word(steps: int, cfg: HierarchicalTrajectoryConfig) -> int:
    z = (steps + cfg.universe_seed) & cfg.mask
    z ^= (z << 13) & cfg.mask
    z ^= z >> 7
    z ^= (z << 17) & cfg.mask
    return z & cfg.mask


def _universe_forward(rank: int, steps: int, cfg: HierarchicalTrajectoryConfig) -> int:
    k = _time_word(steps, cfg)
    return (rank * cfg.universe_mul + k) & cfg.mask


def _universe_inverse(state: int, steps: int, cfg: HierarchicalTrajectoryConfig) -> int:
    k = _time_word(steps, cfg)
    inv = pow(cfg.universe_mul, -1, cfg.modulus)
    return ((state - k) * inv) & cfg.mask


def encode_hierarchical_trajectory(bits: Iterable[int], cfg: HierarchicalTrajectoryConfig = DEFAULT_HIERARCHICAL_CONFIG) -> tuple[int, int]:
    rank, steps = rank_trajectory(bits, cfg)
    return _universe_forward(rank, steps, cfg), steps


def decode_hierarchical_trajectory(final_state: int, steps: int, cfg: HierarchicalTrajectoryConfig = DEFAULT_HIERARCHICAL_CONFIG) -> list[int]:
    if not capacity_ok(steps, cfg):
        raise ValueError("admissible trajectory family exceeds final-state capacity")
    rank = _universe_inverse(final_state & cfg.mask, steps, cfg)
    if rank >= admissible_count(steps, cfg):
        raise ValueError("final state is not a valid address for this constrained trajectory family")
    return unrank_trajectory(rank, steps, cfg)

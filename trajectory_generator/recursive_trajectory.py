"""Recursive trajectory-relation experiment.

The trajectory is transformed repeatedly by an invertible local relation operator.
Level 0 is the original sequence. Level 1 describes local relations, level 2
relations among those relations, and so on.

A public maximum depth is searched and the admissible level with the fewest
non-root deviations is selected. The selected level is encoded inside the final
state, so decoding still receives only `(final_state, steps)` plus the public
configuration.

This is exact enumerative coding of a union of structured families. It is not
compression of arbitrary data and does not exceed the fixed-width state capacity.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import comb
from typing import Iterable


@dataclass(frozen=True)
class RecursiveTrajectoryConfig:
    width: int = 63
    max_deviations: int = 5
    max_level: int = 3
    universe_mul: int = 0x3D
    universe_seed: int = 0x27D4EB2D

    def __post_init__(self) -> None:
        if not 1 <= self.width <= 64:
            raise ValueError("width must be between 1 and 64")
        if self.max_deviations < 0:
            raise ValueError("max_deviations must be non-negative")
        if self.max_level < 0:
            raise ValueError("max_level must be non-negative")
        if self.universe_mul % 2 == 0:
            raise ValueError("universe_mul must be odd")

    @property
    def modulus(self) -> int:
        return 1 << self.width

    @property
    def mask(self) -> int:
        return self.modulus - 1


DEFAULT_RECURSIVE_CONFIG = RecursiveTrajectoryConfig()


def relation_transform(bits: Iterable[int]) -> list[int]:
    """Invertible local relation transform over GF(2)."""
    seq = [int(b) for b in bits]
    if any(b not in (0, 1) for b in seq):
        raise ValueError("bits must contain only 0 and 1")
    if not seq:
        return []
    out = [seq[0]]
    out.extend(seq[i] ^ seq[i - 1] for i in range(1, len(seq)))
    return out


def inverse_relation_transform(coeff: Iterable[int]) -> list[int]:
    c = [int(b) for b in coeff]
    if any(b not in (0, 1) for b in c):
        raise ValueError("coefficients must contain only 0 and 1")
    if not c:
        return []
    out = [c[0]]
    for i in range(1, len(c)):
        out.append(c[i] ^ out[i - 1])
    return out


def transform_level(bits: Iterable[int], level: int) -> list[int]:
    if level < 0:
        raise ValueError("level must be non-negative")
    out = [int(b) for b in bits]
    if any(b not in (0, 1) for b in out):
        raise ValueError("bits must contain only 0 and 1")
    for _ in range(level):
        out = relation_transform(out)
    return out


def inverse_level(coeff: Iterable[int], level: int) -> list[int]:
    if level < 0:
        raise ValueError("level must be non-negative")
    out = [int(b) for b in coeff]
    if any(b not in (0, 1) for b in out):
        raise ValueError("coefficients must contain only 0 and 1")
    for _ in range(level):
        out = inverse_relation_transform(out)
    return out


def deviation_count(bits: Iterable[int], level: int) -> int:
    coeff = transform_level(bits, level)
    return sum(coeff[1:]) if coeff else 0


def per_level_count(steps: int, cfg: RecursiveTrajectoryConfig = DEFAULT_RECURSIVE_CONFIG) -> int:
    if steps < 0:
        raise ValueError("steps must be non-negative")
    if steps == 0:
        return 1
    k = min(cfg.max_deviations, steps - 1)
    return 2 * sum(comb(steps - 1, j) for j in range(k + 1))


def address_envelope_count(steps: int, cfg: RecursiveTrajectoryConfig = DEFAULT_RECURSIVE_CONFIG) -> int:
    if steps == 0:
        return 1
    return (cfg.max_level + 1) * per_level_count(steps, cfg)


def capacity_ok(steps: int, cfg: RecursiveTrajectoryConfig = DEFAULT_RECURSIVE_CONFIG) -> bool:
    return address_envelope_count(steps, cfg) <= cfg.modulus


def _rank_combination_lex(indices: list[int], n: int, k: int) -> int:
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


def _rank_coeff(coeff: list[int], cfg: RecursiveTrajectoryConfig) -> int:
    if not coeff:
        return 0
    positions = [i - 1 for i in range(1, len(coeff)) if coeff[i] == 1]
    k = len(positions)
    if k > cfg.max_deviations:
        raise ValueError("trajectory exceeds configured max_deviations")
    n = len(coeff) - 1
    offset = sum(2 * comb(n, j) for j in range(k))
    within = _rank_combination_lex(positions, n, k)
    return offset + coeff[0] * comb(n, k) + within


def _unrank_coeff(rank: int, steps: int, cfg: RecursiveTrajectoryConfig) -> list[int]:
    if steps == 0:
        if rank != 0:
            raise ValueError("invalid empty rank")
        return []
    total = per_level_count(steps, cfg)
    if not 0 <= rank < total:
        raise ValueError("rank outside level family")
    remaining = rank
    n = steps - 1
    limit = min(cfg.max_deviations, n)
    chosen_k = None
    for k in range(limit + 1):
        bucket = 2 * comb(n, k)
        if remaining < bucket:
            chosen_k = k
            break
        remaining -= bucket
    assert chosen_k is not None
    combos = comb(n, chosen_k)
    root = 1 if remaining >= combos else 0
    within = remaining - root * combos
    positions = set(_unrank_combination_lex(within, n, chosen_k))
    coeff = [root]
    coeff.extend(1 if i in positions else 0 for i in range(n))
    return coeff


def choose_level(bits: Iterable[int], cfg: RecursiveTrajectoryConfig = DEFAULT_RECURSIVE_CONFIG) -> tuple[int, int]:
    seq = [int(b) for b in bits]
    scored = [(deviation_count(seq, level), level) for level in range(cfg.max_level + 1)]
    score, level = min(scored)
    if score > cfg.max_deviations:
        raise ValueError("trajectory is not admissible at any recursive level")
    return level, score


def _time_word(steps: int, cfg: RecursiveTrajectoryConfig) -> int:
    z = (steps + cfg.universe_seed) & cfg.mask
    z ^= (z << 13) & cfg.mask
    z ^= z >> 7
    z ^= (z << 17) & cfg.mask
    return z & cfg.mask


def _universe_forward(rank: int, steps: int, cfg: RecursiveTrajectoryConfig) -> int:
    return (rank * cfg.universe_mul + _time_word(steps, cfg)) & cfg.mask


def _universe_inverse(state: int, steps: int, cfg: RecursiveTrajectoryConfig) -> int:
    inv = pow(cfg.universe_mul, -1, cfg.modulus)
    return ((state - _time_word(steps, cfg)) * inv) & cfg.mask


def encode_recursive_trajectory(bits: Iterable[int], cfg: RecursiveTrajectoryConfig = DEFAULT_RECURSIVE_CONFIG) -> tuple[int, int]:
    seq = [int(b) for b in bits]
    if any(b not in (0, 1) for b in seq):
        raise ValueError("bits must contain only 0 and 1")
    steps = len(seq)
    if not capacity_ok(steps, cfg):
        raise ValueError("recursive address envelope exceeds final-state capacity")
    if steps == 0:
        return _universe_forward(0, 0, cfg), 0
    level, _ = choose_level(seq, cfg)
    local_rank = _rank_coeff(transform_level(seq, level), cfg)
    global_rank = level * per_level_count(steps, cfg) + local_rank
    return _universe_forward(global_rank, steps, cfg), steps


def decode_recursive_trajectory(final_state: int, steps: int, cfg: RecursiveTrajectoryConfig = DEFAULT_RECURSIVE_CONFIG) -> list[int]:
    if not capacity_ok(steps, cfg):
        raise ValueError("recursive address envelope exceeds final-state capacity")
    rank = _universe_inverse(final_state & cfg.mask, steps, cfg)
    if steps == 0:
        if rank != 0:
            raise ValueError("invalid final state")
        return []
    total = address_envelope_count(steps, cfg)
    if rank >= total:
        raise ValueError("final state is not a valid recursive trajectory address")
    bucket = per_level_count(steps, cfg)
    level, local_rank = divmod(rank, bucket)
    if level > cfg.max_level:
        raise ValueError("invalid recursive level")
    coeff = _unrank_coeff(local_rank, steps, cfg)
    return inverse_level(coeff, level)

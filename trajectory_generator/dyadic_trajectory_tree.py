"""Dyadic adaptive trajectory tree.

This is a stricter adaptive model than `adaptive_trajectory_tree.py`: the only
optional split is the public midpoint. Therefore the cut position carries no side
information. The final rank has two disjoint regions:

- unsplit: one recursive-relation block;
- split: left and right midpoint blocks, each with its own recursive level.

The decoder still receives only `(final_state, steps)` and the public config.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import comb
from typing import Iterable

from .recursive_trajectory import relation_transform, inverse_relation_transform


@dataclass(frozen=True)
class DyadicTrajectoryConfig:
    width: int = 63
    max_deviations: int = 5
    max_level: int = 3
    universe_mul: int = 0x49
    universe_seed: int = 0x85EBCA77

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


DEFAULT_DYADIC_CONFIG = DyadicTrajectoryConfig()


def transform_level(bits: Iterable[int], level: int) -> list[int]:
    out = [int(b) for b in bits]
    if any(b not in (0, 1) for b in out):
        raise ValueError("bits must contain only 0 and 1")
    for _ in range(level):
        out = relation_transform(out)
    return out


def inverse_level(coeff: Iterable[int], level: int) -> list[int]:
    out = [int(b) for b in coeff]
    if any(b not in (0, 1) for b in out):
        raise ValueError("coefficients must contain only 0 and 1")
    for _ in range(level):
        out = inverse_relation_transform(out)
    return out


def per_level_count(length: int, cfg: DyadicTrajectoryConfig = DEFAULT_DYADIC_CONFIG) -> int:
    if length <= 0:
        raise ValueError("length must be positive")
    k = min(cfg.max_deviations, length - 1)
    return 2 * sum(comb(length - 1, j) for j in range(k + 1))


def block_radix(length: int, cfg: DyadicTrajectoryConfig = DEFAULT_DYADIC_CONFIG) -> int:
    return (cfg.max_level + 1) * per_level_count(length, cfg)


def address_envelope_count(steps: int, cfg: DyadicTrajectoryConfig = DEFAULT_DYADIC_CONFIG) -> int:
    if steps < 0:
        raise ValueError("steps must be non-negative")
    if steps == 0:
        return 1
    unsplit = block_radix(steps, cfg)
    if steps < 2:
        return unsplit
    left = steps // 2
    right = steps - left
    return unsplit + block_radix(left, cfg) * block_radix(right, cfg)


def capacity_ok(steps: int, cfg: DyadicTrajectoryConfig = DEFAULT_DYADIC_CONFIG) -> bool:
    return address_envelope_count(steps, cfg) <= cfg.modulus


def _rank_combination(indices: list[int], n: int, k: int) -> int:
    rank = 0
    prev = -1
    for pos, value in enumerate(indices):
        for candidate in range(prev + 1, value):
            rank += comb(n - candidate - 1, k - pos - 1)
        prev = value
    return rank


def _unrank_combination(rank: int, n: int, k: int) -> list[int]:
    if rank < 0 or rank >= comb(n, k):
        raise ValueError("combination rank out of range")
    out: list[int] = []
    nxt = 0
    for pos in range(k):
        for candidate in range(nxt, n):
            count = comb(n - candidate - 1, k - pos - 1)
            if rank < count:
                out.append(candidate)
                nxt = candidate + 1
                break
            rank -= count
    return out


def _rank_coeff(coeff: list[int], cfg: DyadicTrajectoryConfig) -> int:
    positions = [i - 1 for i in range(1, len(coeff)) if coeff[i]]
    k = len(positions)
    if k > cfg.max_deviations:
        raise ValueError("block exceeds max_deviations")
    n = len(coeff) - 1
    offset = sum(2 * comb(n, j) for j in range(k))
    return offset + coeff[0] * comb(n, k) + _rank_combination(positions, n, k)


def _unrank_coeff(rank: int, length: int, cfg: DyadicTrajectoryConfig) -> list[int]:
    total = per_level_count(length, cfg)
    if not 0 <= rank < total:
        raise ValueError("rank outside block family")
    remaining = rank
    n = length - 1
    chosen = None
    for k in range(min(cfg.max_deviations, n) + 1):
        bucket = 2 * comb(n, k)
        if remaining < bucket:
            chosen = k
            break
        remaining -= bucket
    assert chosen is not None
    combos = comb(n, chosen)
    root = 1 if remaining >= combos else 0
    within = remaining - root * combos
    positions = set(_unrank_combination(within, n, chosen))
    return [root] + [1 if i in positions else 0 for i in range(n)]


def _encode_block(block: list[int], cfg: DyadicTrajectoryConfig) -> tuple[int, int]:
    per = per_level_count(len(block), cfg)
    best = None
    for level in range(cfg.max_level + 1):
        coeff = transform_level(block, level)
        dev = sum(coeff[1:]) if coeff else 0
        if dev > cfg.max_deviations:
            continue
        code = level * per + _rank_coeff(coeff, cfg)
        candidate = (dev, code)
        if best is None or candidate < best:
            best = candidate
    if best is None:
        raise ValueError("block is not admissible at any recursive level")
    return best[1], best[0]


def _decode_block(code: int, length: int, cfg: DyadicTrajectoryConfig) -> list[int]:
    per = per_level_count(length, cfg)
    level, local = divmod(code, per)
    if level > cfg.max_level:
        raise ValueError("invalid recursive level")
    return inverse_level(_unrank_coeff(local, length, cfg), level)


def _time_word(steps: int, cfg: DyadicTrajectoryConfig) -> int:
    z = (steps + cfg.universe_seed) & cfg.mask
    z ^= (z << 13) & cfg.mask
    z ^= z >> 7
    z ^= (z << 17) & cfg.mask
    return z & cfg.mask


def _universe_forward(rank: int, steps: int, cfg: DyadicTrajectoryConfig) -> int:
    return (rank * cfg.universe_mul + _time_word(steps, cfg)) & cfg.mask


def _universe_inverse(state: int, steps: int, cfg: DyadicTrajectoryConfig) -> int:
    inv = pow(cfg.universe_mul, -1, cfg.modulus)
    return ((state - _time_word(steps, cfg)) * inv) & cfg.mask


def encode_dyadic_trajectory(bits: Iterable[int], cfg: DyadicTrajectoryConfig = DEFAULT_DYADIC_CONFIG) -> tuple[int, int]:
    seq = [int(b) for b in bits]
    if any(b not in (0, 1) for b in seq):
        raise ValueError("bits must contain only 0 and 1")
    steps = len(seq)
    if steps == 0:
        return _universe_forward(0, 0, cfg), 0
    if not capacity_ok(steps, cfg):
        raise ValueError("dyadic address envelope exceeds final-state capacity")

    choices: list[tuple[int, int]] = []  # (total deviations, rank)
    try:
        code, dev = _encode_block(seq, cfg)
        choices.append((dev, code))
    except ValueError:
        pass

    if steps >= 2:
        mid = steps // 2
        try:
            left_code, left_dev = _encode_block(seq[:mid], cfg)
            right_code, right_dev = _encode_block(seq[mid:], cfg)
            split_rank = block_radix(steps, cfg) + left_code * block_radix(steps - mid, cfg) + right_code
            choices.append((left_dev + right_dev, split_rank))
        except ValueError:
            pass

    if not choices:
        raise ValueError("trajectory is not admissible as unsplit or midpoint-split")
    _, rank = min(choices)
    return _universe_forward(rank, steps, cfg), steps


def decode_dyadic_trajectory(final_state: int, steps: int, cfg: DyadicTrajectoryConfig = DEFAULT_DYADIC_CONFIG) -> list[int]:
    if steps < 0:
        raise ValueError("steps must be non-negative")
    if steps == 0:
        rank = _universe_inverse(final_state & cfg.mask, 0, cfg)
        if rank != 0:
            raise ValueError("invalid empty address")
        return []
    if not capacity_ok(steps, cfg):
        raise ValueError("dyadic address envelope exceeds final-state capacity")
    rank = _universe_inverse(final_state & cfg.mask, steps, cfg)
    if rank >= address_envelope_count(steps, cfg):
        raise ValueError("final state is not a valid dyadic trajectory address")
    unsplit = block_radix(steps, cfg)
    if rank < unsplit:
        return _decode_block(rank, steps, cfg)
    rank -= unsplit
    mid = steps // 2
    right_radix = block_radix(steps - mid, cfg)
    left_code, right_code = divmod(rank, right_radix)
    return _decode_block(left_code, mid, cfg) + _decode_block(right_code, steps - mid, cfg)

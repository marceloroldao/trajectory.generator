"""Adaptive block trajectory tree.

This experiment lets different contiguous blocks choose different recursive relation
levels. Crucially, the block partition and level choices are encoded inside the final
state through exact combinatorial ranking; the decoder still receives only
`(final_state, steps)` plus the public configuration.

The representation envelope counts *representations*, not distinct trajectories, so
its capacity check is conservative and never hides side information.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from math import comb
from typing import Iterable

from .recursive_trajectory import relation_transform, inverse_relation_transform


@dataclass(frozen=True)
class AdaptiveTrajectoryConfig:
    width: int = 63
    max_deviations: int = 5
    max_level: int = 3
    max_blocks: int = 4
    universe_mul: int = 0x45
    universe_seed: int = 0x165667B1

    def __post_init__(self) -> None:
        if not 1 <= self.width <= 64:
            raise ValueError("width must be between 1 and 64")
        if self.max_deviations < 0:
            raise ValueError("max_deviations must be non-negative")
        if self.max_level < 0:
            raise ValueError("max_level must be non-negative")
        if self.max_blocks < 1:
            raise ValueError("max_blocks must be >= 1")
        if self.universe_mul % 2 == 0:
            raise ValueError("universe_mul must be odd")

    @property
    def modulus(self) -> int:
        return 1 << self.width

    @property
    def mask(self) -> int:
        return self.modulus - 1


DEFAULT_ADAPTIVE_CONFIG = AdaptiveTrajectoryConfig()


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


def _per_level_count(length: int, cfg: AdaptiveTrajectoryConfig) -> int:
    if length <= 0:
        raise ValueError("block length must be positive")
    k = min(cfg.max_deviations, length - 1)
    return 2 * sum(comb(length - 1, j) for j in range(k + 1))


def _block_radix(length: int, cfg: AdaptiveTrajectoryConfig) -> int:
    return (cfg.max_level + 1) * _per_level_count(length, cfg)


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


def _rank_coeff(coeff: list[int], cfg: AdaptiveTrajectoryConfig) -> int:
    positions = [i - 1 for i in range(1, len(coeff)) if coeff[i] == 1]
    k = len(positions)
    if k > cfg.max_deviations:
        raise ValueError("block exceeds max_deviations")
    n = len(coeff) - 1
    offset = sum(2 * comb(n, j) for j in range(k))
    within = _rank_combination_lex(positions, n, k)
    return offset + coeff[0] * comb(n, k) + within


def _unrank_coeff(rank: int, length: int, cfg: AdaptiveTrajectoryConfig) -> list[int]:
    total = _per_level_count(length, cfg)
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
    positions = set(_unrank_combination_lex(within, n, chosen))
    return [root] + [1 if i in positions else 0 for i in range(n)]


def _block_code(block: list[int], cfg: AdaptiveTrajectoryConfig) -> tuple[int, int, int]:
    best = None
    per = _per_level_count(len(block), cfg)
    for level in range(cfg.max_level + 1):
        coeff = transform_level(block, level)
        deviations = sum(coeff[1:]) if coeff else 0
        if deviations > cfg.max_deviations:
            continue
        local = _rank_coeff(coeff, cfg)
        code = level * per + local
        item = (deviations, code, level)
        if best is None or item < best:
            best = item
    if best is None:
        raise ValueError("block not admissible at any recursive level")
    deviations, code, level = best
    return code, level, deviations


@lru_cache(maxsize=None)
def _representation_count_cached(total: int, blocks: int, width: int, max_dev: int, max_level: int, max_blocks: int) -> int:
    cfg = AdaptiveTrajectoryConfig(width, max_dev, max_level, max_blocks)
    if blocks == 0:
        return 1 if total == 0 else 0
    if total < blocks or blocks < 0:
        return 0
    count = 0
    max_first = total - (blocks - 1)
    for first_len in range(1, max_first + 1):
        count += _block_radix(first_len, cfg) * _representation_count_cached(
            total - first_len, blocks - 1, width, max_dev, max_level, max_blocks
        )
    return count


def representation_count(total: int, blocks: int, cfg: AdaptiveTrajectoryConfig = DEFAULT_ADAPTIVE_CONFIG) -> int:
    return _representation_count_cached(total, blocks, cfg.width, cfg.max_deviations, cfg.max_level, cfg.max_blocks)


def address_envelope_count(steps: int, cfg: AdaptiveTrajectoryConfig = DEFAULT_ADAPTIVE_CONFIG) -> int:
    if steps < 0:
        raise ValueError("steps must be non-negative")
    if steps == 0:
        return 1
    return sum(representation_count(steps, b, cfg) for b in range(1, min(cfg.max_blocks, steps) + 1))


def capacity_ok(steps: int, cfg: AdaptiveTrajectoryConfig = DEFAULT_ADAPTIVE_CONFIG) -> bool:
    return address_envelope_count(steps, cfg) <= cfg.modulus


def _segment(seq: list[int], cfg: AdaptiveTrajectoryConfig) -> list[tuple[list[int], int]]:
    """Dynamic program: fewest blocks, then fewest deviations, then lexicographic cuts."""
    n = len(seq)
    dp: list[tuple[int, int, list[tuple[int, int, int]]] | None] = [None] * (n + 1)
    dp[0] = (0, 0, [])
    for end in range(1, n + 1):
        best = None
        for start in range(end):
            prev = dp[start]
            if prev is None or prev[0] >= cfg.max_blocks:
                continue
            block = seq[start:end]
            try:
                code, level, dev = _block_code(block, cfg)
            except ValueError:
                continue
            candidate = (prev[0] + 1, prev[1] + dev, prev[2] + [(end - start, code, level)])
            key = (candidate[0], candidate[1], tuple(x[0] for x in candidate[2]), tuple(x[1] for x in candidate[2]))
            if best is None or key < best[0]:
                best = (key, candidate)
        if best is not None:
            dp[end] = best[1]
    if dp[n] is None:
        raise ValueError("trajectory is not admissible within max_blocks")
    return [(seq[sum(x[0] for x in dp[n][2][:i]):sum(x[0] for x in dp[n][2][:i+1])], item[1]) for i, item in enumerate(dp[n][2])]


def _rank_representation(lengths: list[int], codes: list[int], cfg: AdaptiveTrajectoryConfig) -> int:
    total = sum(lengths)
    blocks = len(lengths)
    rank = sum(representation_count(total, b, cfg) for b in range(1, blocks))
    rem = total
    for i, (length, code) in enumerate(zip(lengths, codes)):
        left_blocks = blocks - i - 1
        for smaller in range(1, length):
            if rem - smaller < left_blocks:
                break
            rank += _block_radix(smaller, cfg) * representation_count(rem - smaller, left_blocks, cfg)
        suffix_count = representation_count(rem - length, left_blocks, cfg)
        rank += code * suffix_count
        rem -= length
    return rank


def _unrank_representation(rank: int, steps: int, cfg: AdaptiveTrajectoryConfig) -> tuple[list[int], list[int]]:
    if not 0 <= rank < address_envelope_count(steps, cfg):
        raise ValueError("rank outside adaptive envelope")
    blocks = None
    for b in range(1, min(cfg.max_blocks, steps) + 1):
        count = representation_count(steps, b, cfg)
        if rank < count:
            blocks = b
            break
        rank -= count
    assert blocks is not None
    lengths: list[int] = []
    codes: list[int] = []
    rem = steps
    for i in range(blocks):
        left_blocks = blocks - i - 1
        for length in range(1, rem - left_blocks + 1):
            suffix_count = representation_count(rem - length, left_blocks, cfg)
            bucket = _block_radix(length, cfg) * suffix_count
            if rank < bucket:
                code, rank = divmod(rank, suffix_count)
                lengths.append(length)
                codes.append(code)
                rem -= length
                break
            rank -= bucket
    return lengths, codes


def _time_word(steps: int, cfg: AdaptiveTrajectoryConfig) -> int:
    z = (steps + cfg.universe_seed) & cfg.mask
    z ^= (z << 13) & cfg.mask
    z ^= z >> 7
    z ^= (z << 17) & cfg.mask
    return z & cfg.mask


def _universe_forward(rank: int, steps: int, cfg: AdaptiveTrajectoryConfig) -> int:
    return (rank * cfg.universe_mul + _time_word(steps, cfg)) & cfg.mask


def _universe_inverse(state: int, steps: int, cfg: AdaptiveTrajectoryConfig) -> int:
    inv = pow(cfg.universe_mul, -1, cfg.modulus)
    return ((state - _time_word(steps, cfg)) * inv) & cfg.mask


def encode_adaptive_trajectory(bits: Iterable[int], cfg: AdaptiveTrajectoryConfig = DEFAULT_ADAPTIVE_CONFIG) -> tuple[int, int]:
    seq = [int(b) for b in bits]
    if any(b not in (0, 1) for b in seq):
        raise ValueError("bits must contain only 0 and 1")
    steps = len(seq)
    if steps == 0:
        return _universe_forward(0, 0, cfg), 0
    if not capacity_ok(steps, cfg):
        raise ValueError("adaptive representation envelope exceeds final-state capacity")
    blocks = _segment(seq, cfg)
    lengths = [len(block) for block, _ in blocks]
    codes = [code for _, code in blocks]
    rank = _rank_representation(lengths, codes, cfg)
    return _universe_forward(rank, steps, cfg), steps


def decode_adaptive_trajectory(final_state: int, steps: int, cfg: AdaptiveTrajectoryConfig = DEFAULT_ADAPTIVE_CONFIG) -> list[int]:
    if steps < 0:
        raise ValueError("steps must be non-negative")
    if steps == 0:
        rank = _universe_inverse(final_state & cfg.mask, 0, cfg)
        if rank != 0:
            raise ValueError("invalid empty adaptive address")
        return []
    if not capacity_ok(steps, cfg):
        raise ValueError("adaptive representation envelope exceeds final-state capacity")
    rank = _universe_inverse(final_state & cfg.mask, steps, cfg)
    if rank >= address_envelope_count(steps, cfg):
        raise ValueError("final state is not a valid adaptive trajectory address")
    lengths, codes = _unrank_representation(rank, steps, cfg)
    out: list[int] = []
    for length, code in zip(lengths, codes):
        per = _per_level_count(length, cfg)
        level, local_rank = divmod(code, per)
        if level > cfg.max_level:
            raise ValueError("invalid block level")
        coeff = _unrank_coeff(local_rank, length, cfg)
        out.extend(inverse_level(coeff, level))
    return out

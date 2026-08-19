"""Self-resolving canonical trajectory tree.

A block is treated as a leaf whenever it is representable by one of the public
recursive-relation levels within `max_deviations`. Only when no leaf description
exists is the block split at the public midpoint and the same rule applied
recursively.

The decoder still receives only `(final_state, steps)` plus the public config.
Leaf addresses and split addresses occupy disjoint numeric ranges, so the tree
shape is inferred from the address itself rather than supplied as side metadata.

Important: the envelope count is conservative because split ranges include some
codes whose reconstructed sequence would also have been leaf-admissible. Those
codes are never emitted by the canonical encoder, but they still consume address
space. This makes capacity estimates safe rather than optimistic.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from math import comb
from typing import Iterable

from .recursive_trajectory import relation_transform, inverse_relation_transform


@dataclass(frozen=True)
class SelfResolvingTreeConfig:
    width: int = 63
    max_deviations: int = 5
    max_level: int = 3
    universe_mul: int = 0x55
    universe_seed: int = 0xC2B2AE3D

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


DEFAULT_SELF_RESOLVING_CONFIG = SelfResolvingTreeConfig()


def _transform_level(bits: list[int], level: int) -> list[int]:
    out = list(bits)
    for _ in range(level):
        out = relation_transform(out)
    return out


def _inverse_level(coeff: list[int], level: int) -> list[int]:
    out = list(coeff)
    for _ in range(level):
        out = inverse_relation_transform(out)
    return out


def _per_level_count(length: int, cfg: SelfResolvingTreeConfig) -> int:
    if length <= 0:
        raise ValueError("length must be positive")
    k = min(cfg.max_deviations, length - 1)
    return 2 * sum(comb(length - 1, j) for j in range(k + 1))


def leaf_radix(length: int, cfg: SelfResolvingTreeConfig = DEFAULT_SELF_RESOLVING_CONFIG) -> int:
    return (cfg.max_level + 1) * _per_level_count(length, cfg)


def address_envelope_count(steps: int, cfg: SelfResolvingTreeConfig = DEFAULT_SELF_RESOLVING_CONFIG) -> int:
    if steps < 0:
        raise ValueError("steps must be non-negative")
    if steps == 0:
        return 1

    @lru_cache(maxsize=None)
    def count(n: int) -> int:
        leaves = leaf_radix(n, cfg)
        if n < 2:
            return leaves
        left = n // 2
        right = n - left
        return leaves + count(left) * count(right)

    return count(steps)


def capacity_ok(steps: int, cfg: SelfResolvingTreeConfig = DEFAULT_SELF_RESOLVING_CONFIG) -> bool:
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


def _rank_coeff(coeff: list[int], cfg: SelfResolvingTreeConfig) -> int:
    positions = [i - 1 for i in range(1, len(coeff)) if coeff[i]]
    k = len(positions)
    if k > cfg.max_deviations:
        raise ValueError("leaf exceeds max_deviations")
    n = len(coeff) - 1
    offset = sum(2 * comb(n, j) for j in range(k))
    return offset + coeff[0] * comb(n, k) + _rank_combination(positions, n, k)


def _unrank_coeff(rank: int, length: int, cfg: SelfResolvingTreeConfig) -> list[int]:
    total = _per_level_count(length, cfg)
    if not 0 <= rank < total:
        raise ValueError("rank outside leaf family")
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


def _try_leaf(block: list[int], cfg: SelfResolvingTreeConfig) -> tuple[int, int] | None:
    per = _per_level_count(len(block), cfg)
    best = None
    for level in range(cfg.max_level + 1):
        coeff = _transform_level(block, level)
        dev = sum(coeff[1:]) if coeff else 0
        if dev > cfg.max_deviations:
            continue
        code = level * per + _rank_coeff(coeff, cfg)
        cand = (dev, code)
        if best is None or cand < best:
            best = cand
    return best


def _encode_node(block: list[int], cfg: SelfResolvingTreeConfig) -> int:
    leaf = _try_leaf(block, cfg)
    if leaf is not None:
        return leaf[1]
    if len(block) < 2:
        raise ValueError("non-admissible atomic block")
    mid = len(block) // 2
    left_code = _encode_node(block[:mid], cfg)
    right_code = _encode_node(block[mid:], cfg)
    right_radix = address_envelope_count(len(block) - mid, cfg)
    return leaf_radix(len(block), cfg) + left_code * right_radix + right_code


def _decode_node(code: int, length: int, cfg: SelfResolvingTreeConfig) -> list[int]:
    leaves = leaf_radix(length, cfg)
    if code < leaves:
        per = _per_level_count(length, cfg)
        level, local = divmod(code, per)
        if level > cfg.max_level:
            raise ValueError("invalid leaf level")
        return _inverse_level(_unrank_coeff(local, length, cfg), level)

    if length < 2:
        raise ValueError("split code for atomic block")
    code -= leaves
    mid = length // 2
    right_len = length - mid
    right_radix = address_envelope_count(right_len, cfg)
    left_code, right_code = divmod(code, right_radix)
    left_max = address_envelope_count(mid, cfg)
    if left_code >= left_max:
        raise ValueError("invalid split address")
    return _decode_node(left_code, mid, cfg) + _decode_node(right_code, right_len, cfg)


def _time_word(steps: int, cfg: SelfResolvingTreeConfig) -> int:
    z = (steps + cfg.universe_seed) & cfg.mask
    z ^= (z << 13) & cfg.mask
    z ^= z >> 7
    z ^= (z << 17) & cfg.mask
    return z & cfg.mask


def _universe_forward(rank: int, steps: int, cfg: SelfResolvingTreeConfig) -> int:
    return (rank * cfg.universe_mul + _time_word(steps, cfg)) & cfg.mask


def _universe_inverse(state: int, steps: int, cfg: SelfResolvingTreeConfig) -> int:
    inv = pow(cfg.universe_mul, -1, cfg.modulus)
    return ((state - _time_word(steps, cfg)) * inv) & cfg.mask


def encode_self_resolving_tree(bits: Iterable[int], cfg: SelfResolvingTreeConfig = DEFAULT_SELF_RESOLVING_CONFIG) -> tuple[int, int]:
    seq = [int(b) for b in bits]
    if any(b not in (0, 1) for b in seq):
        raise ValueError("bits must contain only 0 and 1")
    steps = len(seq)
    if steps == 0:
        return _universe_forward(0, 0, cfg), 0
    if not capacity_ok(steps, cfg):
        raise ValueError("self-resolving tree envelope exceeds final-state capacity")
    rank = _encode_node(seq, cfg)
    return _universe_forward(rank, steps, cfg), steps


def decode_self_resolving_tree(final_state: int, steps: int, cfg: SelfResolvingTreeConfig = DEFAULT_SELF_RESOLVING_CONFIG) -> list[int]:
    if steps < 0:
        raise ValueError("steps must be non-negative")
    if steps == 0:
        rank = _universe_inverse(final_state & cfg.mask, 0, cfg)
        if rank != 0:
            raise ValueError("invalid empty address")
        return []
    if not capacity_ok(steps, cfg):
        raise ValueError("self-resolving tree envelope exceeds final-state capacity")
    rank = _universe_inverse(final_state & cfg.mask, steps, cfg)
    if rank >= address_envelope_count(steps, cfg):
        raise ValueError("invalid self-resolving tree address")
    return _decode_node(rank, steps, cfg)

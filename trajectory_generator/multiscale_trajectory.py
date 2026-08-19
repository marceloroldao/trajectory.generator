"""Multi-scale trajectory tree experiment.

This module extends the relational trajectory idea with two public coordinate bases:

- local: each bit is related to the immediately previous bit;
- fenwick: each bit is related to a hierarchical ancestor defined by its least
  significant set bit.

A trajectory is encoded in the basis requiring the fewest non-root deviations,
subject to a public maximum. The selected basis is encoded inside the final state;
no side metadata beyond `(final_state, steps)` is required.

This is exact enumerative coding of structured trajectory families. It is not
compression of arbitrary data and does not exceed the information capacity of the
fixed-width final state.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import comb
from typing import Iterable


@dataclass(frozen=True)
class MultiScaleTrajectoryConfig:
    width: int = 63
    max_deviations: int = 5
    modes: tuple[str, ...] = ("local", "fenwick")
    universe_mul: int = 0x35
    universe_seed: int = 0x1B873593

    def __post_init__(self) -> None:
        if not 1 <= self.width <= 64:
            raise ValueError("width must be between 1 and 64")
        if self.max_deviations < 0:
            raise ValueError("max_deviations must be non-negative")
        if not self.modes:
            raise ValueError("at least one mode is required")
        if any(m not in {"local", "fenwick"} for m in self.modes):
            raise ValueError("unsupported mode")
        if len(set(self.modes)) != len(self.modes):
            raise ValueError("modes must be unique")
        if self.universe_mul % 2 == 0:
            raise ValueError("universe_mul must be odd")

    @property
    def modulus(self) -> int:
        return 1 << self.width

    @property
    def mask(self) -> int:
        return self.modulus - 1


DEFAULT_MULTISCALE_CONFIG = MultiScaleTrajectoryConfig()


def _parent(i: int, mode: str) -> int:
    if i <= 0:
        raise ValueError("root has no parent")
    if mode == "local":
        return i - 1
    if mode == "fenwick":
        return i - (i & -i)
    raise ValueError("unsupported mode")


def transform(bits: Iterable[int], mode: str) -> list[int]:
    seq = [int(b) for b in bits]
    if any(b not in (0, 1) for b in seq):
        raise ValueError("bits must contain only 0 and 1")
    if not seq:
        return []
    coeff = [seq[0]]
    for i in range(1, len(seq)):
        coeff.append(seq[i] ^ seq[_parent(i, mode)])
    return coeff


def inverse_transform(coeff: Iterable[int], mode: str) -> list[int]:
    c = [int(b) for b in coeff]
    if any(b not in (0, 1) for b in c):
        raise ValueError("coefficients must contain only 0 and 1")
    if not c:
        return []
    bits = [c[0]]
    for i in range(1, len(c)):
        bits.append(c[i] ^ bits[_parent(i, mode)])
    return bits


def deviation_count(bits: Iterable[int], mode: str) -> int:
    coeff = transform(bits, mode)
    return sum(coeff[1:]) if coeff else 0


def per_mode_count(steps: int, cfg: MultiScaleTrajectoryConfig = DEFAULT_MULTISCALE_CONFIG) -> int:
    if steps < 0:
        raise ValueError("steps must be non-negative")
    if steps == 0:
        return 1
    k = min(cfg.max_deviations, steps - 1)
    return 2 * sum(comb(steps - 1, j) for j in range(k + 1))


def address_envelope_count(steps: int, cfg: MultiScaleTrajectoryConfig = DEFAULT_MULTISCALE_CONFIG) -> int:
    if steps == 0:
        return 1
    return len(cfg.modes) * per_mode_count(steps, cfg)


def capacity_ok(steps: int, cfg: MultiScaleTrajectoryConfig = DEFAULT_MULTISCALE_CONFIG) -> bool:
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


def _rank_coeff(coeff: list[int], cfg: MultiScaleTrajectoryConfig) -> int:
    if not coeff:
        return 0
    positions = [i - 1 for i in range(1, len(coeff)) if coeff[i] == 1]
    k = len(positions)
    if k > cfg.max_deviations:
        raise ValueError("trajectory exceeds configured max_deviations")
    n = len(coeff) - 1
    offset = 0
    for j in range(k):
        offset += 2 * comb(n, j)
    within = _rank_combination_lex(positions, n, k)
    return offset + coeff[0] * comb(n, k) + within


def _unrank_coeff(rank: int, steps: int, cfg: MultiScaleTrajectoryConfig) -> list[int]:
    if steps == 0:
        if rank != 0:
            raise ValueError("invalid empty rank")
        return []
    total = per_mode_count(steps, cfg)
    if rank < 0 or rank >= total:
        raise ValueError("rank outside mode family")
    remaining = rank
    n = steps - 1
    k_limit = min(cfg.max_deviations, n)
    k = None
    for j in range(k_limit + 1):
        bucket = 2 * comb(n, j)
        if remaining < bucket:
            k = j
            break
        remaining -= bucket
    assert k is not None
    combos = comb(n, k)
    root = 1 if remaining >= combos else 0
    within = remaining - root * combos
    positions = set(_unrank_combination_lex(within, n, k))
    coeff = [root]
    coeff.extend(1 if i in positions else 0 for i in range(n))
    return coeff


def _time_word(steps: int, cfg: MultiScaleTrajectoryConfig) -> int:
    z = (steps + cfg.universe_seed) & cfg.mask
    z ^= (z << 13) & cfg.mask
    z ^= z >> 7
    z ^= (z << 17) & cfg.mask
    return z & cfg.mask


def _universe_forward(rank: int, steps: int, cfg: MultiScaleTrajectoryConfig) -> int:
    return (rank * cfg.universe_mul + _time_word(steps, cfg)) & cfg.mask


def _universe_inverse(state: int, steps: int, cfg: MultiScaleTrajectoryConfig) -> int:
    inv = pow(cfg.universe_mul, -1, cfg.modulus)
    return ((state - _time_word(steps, cfg)) * inv) & cfg.mask


def choose_mode(bits: Iterable[int], cfg: MultiScaleTrajectoryConfig = DEFAULT_MULTISCALE_CONFIG) -> tuple[str, int]:
    seq = [int(b) for b in bits]
    scored = [(deviation_count(seq, mode), idx, mode) for idx, mode in enumerate(cfg.modes)]
    score, _, mode = min(scored)
    if score > cfg.max_deviations:
        raise ValueError("trajectory is not admissible in any configured scale")
    return mode, score


def encode_multiscale_trajectory(bits: Iterable[int], cfg: MultiScaleTrajectoryConfig = DEFAULT_MULTISCALE_CONFIG) -> tuple[int, int]:
    seq = [int(b) for b in bits]
    if any(b not in (0, 1) for b in seq):
        raise ValueError("bits must contain only 0 and 1")
    steps = len(seq)
    if not capacity_ok(steps, cfg):
        raise ValueError("multiscale address envelope exceeds final-state capacity")
    if steps == 0:
        return _universe_forward(0, 0, cfg), 0
    mode, _ = choose_mode(seq, cfg)
    mode_index = cfg.modes.index(mode)
    local_rank = _rank_coeff(transform(seq, mode), cfg)
    global_rank = mode_index * per_mode_count(steps, cfg) + local_rank
    return _universe_forward(global_rank, steps, cfg), steps


def decode_multiscale_trajectory(final_state: int, steps: int, cfg: MultiScaleTrajectoryConfig = DEFAULT_MULTISCALE_CONFIG) -> list[int]:
    if not capacity_ok(steps, cfg):
        raise ValueError("multiscale address envelope exceeds final-state capacity")
    rank = _universe_inverse(final_state & cfg.mask, steps, cfg)
    if steps == 0:
        if rank != 0:
            raise ValueError("invalid final state")
        return []
    total = address_envelope_count(steps, cfg)
    if rank >= total:
        raise ValueError("final state is not a valid multiscale trajectory address")
    bucket = per_mode_count(steps, cfg)
    mode_index, local_rank = divmod(rank, bucket)
    if mode_index >= len(cfg.modes):
        raise ValueError("invalid scale mode")
    coeff = _unrank_coeff(local_rank, steps, cfg)
    return inverse_transform(coeff, cfg.modes[mode_index])

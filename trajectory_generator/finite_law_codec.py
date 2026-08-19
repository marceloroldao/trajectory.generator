"""Generic exact codec for finite local trajectory-admissibility laws.

A rule with memory `m` assigns each `m`-bit history state one of three actions:
- 0: force next bit to 0
- 1: force next bit to 1
- 2: next bit is free in {0,1}

The codec ranks admissible trajectories lexicographically using dynamic counts of
valid suffix continuations. The final state is a reversible public permutation of
that rank. Decoding receives only `(final_state, steps)` plus the public rule/config.

This is exact enumerative coding of a constrained family, not compression of
arbitrary data.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Iterable


FORCE_0 = 0
FORCE_1 = 1
FREE = 2


@dataclass(frozen=True)
class FiniteLawConfig:
    rule: tuple[int, ...]
    memory: int
    width: int = 63
    universe_mul: int = 0x5B
    universe_seed: int = 0x165667B1

    def __post_init__(self) -> None:
        if self.memory < 1:
            raise ValueError("memory must be >= 1")
        if len(self.rule) != (1 << self.memory):
            raise ValueError("rule length must equal 2^memory")
        if any(a not in (FORCE_0, FORCE_1, FREE) for a in self.rule):
            raise ValueError("rule actions must be 0, 1, or 2")
        if not 1 <= self.width <= 64:
            raise ValueError("width must be between 1 and 64")
        if self.universe_mul % 2 == 0:
            raise ValueError("universe_mul must be odd")

    @property
    def modulus(self) -> int:
        return 1 << self.width

    @property
    def mask(self) -> int:
        return self.modulus - 1


# Representative memory-3 laws found by exhaustive scan. Actions are ordered by
# history states 000,001,...,111. These constants are descriptive labels only;
# none of the target algebraic constants are used by the codec.
MEMORY3_PLASTIC_RULE = (0, 0, 1, 0, 0, 2, 1, 0)
MEMORY3_PHI_RULE = (0, 0, 1, 2, 0, 2, 1, 2)
MEMORY3_TRIBONACCI_RULE = (0, 2, 2, 2, 1, 2, 2, 2)


def _allowed(action: int) -> tuple[int, ...]:
    if action == FORCE_0:
        return (0,)
    if action == FORCE_1:
        return (1,)
    return (0, 1)


def _next_state(state: int, bit: int, memory: int) -> int:
    return ((state << 1) & ((1 << memory) - 1)) | bit


def admissible_count(steps: int, cfg: FiniteLawConfig) -> int:
    if steps < 0:
        raise ValueError("steps must be non-negative")
    if steps <= cfg.memory:
        return 1 << steps

    @lru_cache(maxsize=None)
    def suffix_count(state: int, remaining: int) -> int:
        if remaining == 0:
            return 1
        return sum(
            suffix_count(_next_state(state, bit, cfg.memory), remaining - 1)
            for bit in _allowed(cfg.rule[state])
        )

    remaining = steps - cfg.memory
    return sum(suffix_count(state, remaining) for state in range(1 << cfg.memory))


def capacity_ok(steps: int, cfg: FiniteLawConfig) -> bool:
    return admissible_count(steps, cfg) <= cfg.modulus


def validate(bits: Iterable[int], cfg: FiniteLawConfig) -> bool:
    seq = [int(b) for b in bits]
    if any(b not in (0, 1) for b in seq):
        return False
    if len(seq) <= cfg.memory:
        return True
    state = 0
    for b in seq[: cfg.memory]:
        state = (state << 1) | b
    for bit in seq[cfg.memory :]:
        if bit not in _allowed(cfg.rule[state]):
            return False
        state = _next_state(state, bit, cfg.memory)
    return True


def rank_trajectory(bits: Iterable[int], cfg: FiniteLawConfig) -> tuple[int, int]:
    seq = [int(b) for b in bits]
    if any(b not in (0, 1) for b in seq):
        raise ValueError("bits must contain only 0 and 1")
    steps = len(seq)
    if not validate(seq, cfg):
        raise ValueError("trajectory violates local law")
    if not capacity_ok(steps, cfg):
        raise ValueError("admissible family exceeds final-state capacity")
    if steps == 0:
        return 0, 0
    if steps <= cfg.memory:
        rank = 0
        for b in seq:
            rank = (rank << 1) | b
        return rank, steps

    @lru_cache(maxsize=None)
    def suffix_count(state: int, remaining: int) -> int:
        if remaining == 0:
            return 1
        return sum(
            suffix_count(_next_state(state, bit, cfg.memory), remaining - 1)
            for bit in _allowed(cfg.rule[state])
        )

    prefix = 0
    for b in seq[: cfg.memory]:
        prefix = (prefix << 1) | b

    remaining = steps - cfg.memory
    rank = 0
    for smaller_prefix in range(prefix):
        rank += suffix_count(smaller_prefix, remaining)

    state = prefix
    for index, bit in enumerate(seq[cfg.memory :]):
        rem_after = remaining - index - 1
        allowed = _allowed(cfg.rule[state])
        if bit == 1 and 0 in allowed:
            rank += suffix_count(_next_state(state, 0, cfg.memory), rem_after)
        state = _next_state(state, bit, cfg.memory)

    return rank, steps


def unrank_trajectory(rank: int, steps: int, cfg: FiniteLawConfig) -> list[int]:
    if steps < 0:
        raise ValueError("steps must be non-negative")
    total = admissible_count(steps, cfg)
    if not 0 <= rank < total:
        raise ValueError("rank outside admissible family")
    if steps == 0:
        return []
    if steps <= cfg.memory:
        return [((rank >> (steps - 1 - i)) & 1) for i in range(steps)]

    @lru_cache(maxsize=None)
    def suffix_count(state: int, remaining: int) -> int:
        if remaining == 0:
            return 1
        return sum(
            suffix_count(_next_state(state, bit, cfg.memory), remaining - 1)
            for bit in _allowed(cfg.rule[state])
        )

    remaining = steps - cfg.memory
    prefix = None
    for state in range(1 << cfg.memory):
        count = suffix_count(state, remaining)
        if rank < count:
            prefix = state
            break
        rank -= count
    assert prefix is not None

    bits = [((prefix >> (cfg.memory - 1 - i)) & 1) for i in range(cfg.memory)]
    state = prefix
    for rem in range(remaining, 0, -1):
        options = _allowed(cfg.rule[state])
        chosen = None
        for bit in options:
            count = suffix_count(_next_state(state, bit, cfg.memory), rem - 1)
            if rank < count:
                chosen = bit
                break
            rank -= count
        assert chosen is not None
        bits.append(chosen)
        state = _next_state(state, chosen, cfg.memory)
    return bits


def _time_word(steps: int, cfg: FiniteLawConfig) -> int:
    z = (steps + cfg.universe_seed) & cfg.mask
    z ^= (z << 13) & cfg.mask
    z ^= z >> 7
    z ^= (z << 17) & cfg.mask
    return z & cfg.mask


def _forward(rank: int, steps: int, cfg: FiniteLawConfig) -> int:
    return (rank * cfg.universe_mul + _time_word(steps, cfg)) & cfg.mask


def _inverse(state: int, steps: int, cfg: FiniteLawConfig) -> int:
    inv = pow(cfg.universe_mul, -1, cfg.modulus)
    return ((state - _time_word(steps, cfg)) * inv) & cfg.mask


def encode_finite_law(bits: Iterable[int], cfg: FiniteLawConfig) -> tuple[int, int]:
    rank, steps = rank_trajectory(bits, cfg)
    return _forward(rank, steps, cfg), steps


def decode_finite_law(final_state: int, steps: int, cfg: FiniteLawConfig) -> list[int]:
    if not capacity_ok(steps, cfg):
        raise ValueError("admissible family exceeds final-state capacity")
    rank = _inverse(final_state & cfg.mask, steps, cfg)
    total = admissible_count(steps, cfg)
    if rank >= total:
        raise ValueError("final state is not a valid address for this law and step count")
    return unrank_trajectory(rank, steps, cfg)

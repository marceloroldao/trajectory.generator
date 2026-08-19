"""Exact codec for state-and-phase dynamic admissibility laws.

The active local rule is selected deterministically from both the current history
state and the public time phase.  No external rule schedule is stored.

For memory m, a dynamic law contains a public bank of ordinary finite local laws.
At step t >= m, the active law index is

    selector(history, t) = (popcount(history) + (t % period)) % len(rule_bank)

The selected law then decides whether the next bit is forced to 0, forced to 1,
or free.  Encoder and decoder therefore derive the same active law from the
trajectory state and time alone.

Ranking/unranking uses dynamic programming over (history, time).  Decoding still
receives only (final_state, steps) plus the public configuration.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Iterable

from .finite_law_codec import FORCE_0, FORCE_1, FREE


@dataclass(frozen=True)
class DynamicLawConfig:
    rule_bank: tuple[tuple[int, ...], ...]
    memory: int = 3
    period: int = 3
    width: int = 63
    universe_mul: int = 0x6D
    universe_seed: int = 0x27D4EB2F

    def __post_init__(self) -> None:
        if self.memory < 1:
            raise ValueError("memory must be >= 1")
        if self.period < 1:
            raise ValueError("period must be >= 1")
        if not self.rule_bank:
            raise ValueError("rule_bank cannot be empty")
        expected = 1 << self.memory
        for rule in self.rule_bank:
            if len(rule) != expected:
                raise ValueError("every rule length must equal 2^memory")
            if any(a not in (FORCE_0, FORCE_1, FREE) for a in rule):
                raise ValueError("rule actions must be FORCE_0, FORCE_1, or FREE")
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


MEMORY3_PLASTIC_RULE = (0, 0, 1, 0, 0, 2, 1, 0)
MEMORY3_PHI_RULE = (0, 0, 1, 2, 0, 2, 1, 2)
MEMORY3_TRIBONACCI_RULE = (0, 2, 2, 2, 1, 2, 2, 2)

DEFAULT_DYNAMIC_CONFIG = DynamicLawConfig(
    rule_bank=(MEMORY3_PLASTIC_RULE, MEMORY3_PHI_RULE),
    memory=3,
    period=3,
)


def _allowed(action: int) -> tuple[int, ...]:
    if action == FORCE_0:
        return (0,)
    if action == FORCE_1:
        return (1,)
    return (0, 1)


def _next_state(state: int, bit: int, memory: int) -> int:
    return ((state << 1) & ((1 << memory) - 1)) | bit


def active_rule_index(state: int, t: int, cfg: DynamicLawConfig = DEFAULT_DYNAMIC_CONFIG) -> int:
    """Return the public state-and-time dependent rule index."""
    return (state.bit_count() + (t % cfg.period)) % len(cfg.rule_bank)


def active_action(state: int, t: int, cfg: DynamicLawConfig = DEFAULT_DYNAMIC_CONFIG) -> int:
    rule = cfg.rule_bank[active_rule_index(state, t, cfg)]
    return rule[state]


def admissible_count(steps: int, cfg: DynamicLawConfig = DEFAULT_DYNAMIC_CONFIG) -> int:
    if steps < 0:
        raise ValueError("steps must be non-negative")
    if steps <= cfg.memory:
        return 1 << steps

    @lru_cache(maxsize=None)
    def suffix_count(state: int, t: int, remaining: int) -> int:
        if remaining == 0:
            return 1
        return sum(
            suffix_count(_next_state(state, bit, cfg.memory), t + 1, remaining - 1)
            for bit in _allowed(active_action(state, t, cfg))
        )

    remaining = steps - cfg.memory
    return sum(suffix_count(state, cfg.memory, remaining) for state in range(1 << cfg.memory))


def capacity_ok(steps: int, cfg: DynamicLawConfig = DEFAULT_DYNAMIC_CONFIG) -> bool:
    return admissible_count(steps, cfg) <= cfg.modulus


def validate(bits: Iterable[int], cfg: DynamicLawConfig = DEFAULT_DYNAMIC_CONFIG) -> bool:
    seq = [int(b) for b in bits]
    if any(b not in (0, 1) for b in seq):
        return False
    if len(seq) <= cfg.memory:
        return True
    state = 0
    for bit in seq[: cfg.memory]:
        state = (state << 1) | bit
    for t, bit in enumerate(seq[cfg.memory :], start=cfg.memory):
        if bit not in _allowed(active_action(state, t, cfg)):
            return False
        state = _next_state(state, bit, cfg.memory)
    return True


def rank_trajectory(bits: Iterable[int], cfg: DynamicLawConfig = DEFAULT_DYNAMIC_CONFIG) -> tuple[int, int]:
    seq = [int(b) for b in bits]
    if any(b not in (0, 1) for b in seq):
        raise ValueError("bits must contain only 0 and 1")
    steps = len(seq)
    if not validate(seq, cfg):
        raise ValueError("trajectory violates dynamic law")
    if not capacity_ok(steps, cfg):
        raise ValueError("admissible family exceeds final-state capacity")
    if steps == 0:
        return 0, 0
    if steps <= cfg.memory:
        rank = 0
        for bit in seq:
            rank = (rank << 1) | bit
        return rank, steps

    @lru_cache(maxsize=None)
    def suffix_count(state: int, t: int, remaining: int) -> int:
        if remaining == 0:
            return 1
        return sum(
            suffix_count(_next_state(state, bit, cfg.memory), t + 1, remaining - 1)
            for bit in _allowed(active_action(state, t, cfg))
        )

    prefix = 0
    for bit in seq[: cfg.memory]:
        prefix = (prefix << 1) | bit
    remaining = steps - cfg.memory
    rank = 0
    for smaller_prefix in range(prefix):
        rank += suffix_count(smaller_prefix, cfg.memory, remaining)

    state = prefix
    for offset, bit in enumerate(seq[cfg.memory :]):
        t = cfg.memory + offset
        rem_after = remaining - offset - 1
        allowed = _allowed(active_action(state, t, cfg))
        if bit == 1 and 0 in allowed:
            rank += suffix_count(_next_state(state, 0, cfg.memory), t + 1, rem_after)
        state = _next_state(state, bit, cfg.memory)
    return rank, steps


def unrank_trajectory(rank: int, steps: int, cfg: DynamicLawConfig = DEFAULT_DYNAMIC_CONFIG) -> list[int]:
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
    def suffix_count(state: int, t: int, remaining: int) -> int:
        if remaining == 0:
            return 1
        return sum(
            suffix_count(_next_state(state, bit, cfg.memory), t + 1, remaining - 1)
            for bit in _allowed(active_action(state, t, cfg))
        )

    remaining = steps - cfg.memory
    prefix = None
    for state in range(1 << cfg.memory):
        count = suffix_count(state, cfg.memory, remaining)
        if rank < count:
            prefix = state
            break
        rank -= count
    assert prefix is not None

    bits = [((prefix >> (cfg.memory - 1 - i)) & 1) for i in range(cfg.memory)]
    state = prefix
    for offset in range(remaining):
        t = cfg.memory + offset
        rem_after = remaining - offset - 1
        chosen = None
        for bit in _allowed(active_action(state, t, cfg)):
            count = suffix_count(_next_state(state, bit, cfg.memory), t + 1, rem_after)
            if rank < count:
                chosen = bit
                break
            rank -= count
        assert chosen is not None
        bits.append(chosen)
        state = _next_state(state, chosen, cfg.memory)
    return bits


def _time_word(steps: int, cfg: DynamicLawConfig) -> int:
    z = (steps + cfg.universe_seed) & cfg.mask
    z ^= (z << 13) & cfg.mask
    z ^= z >> 7
    z ^= (z << 17) & cfg.mask
    return z & cfg.mask


def _forward(rank: int, steps: int, cfg: DynamicLawConfig) -> int:
    return (rank * cfg.universe_mul + _time_word(steps, cfg)) & cfg.mask


def _inverse(state: int, steps: int, cfg: DynamicLawConfig) -> int:
    inv = pow(cfg.universe_mul, -1, cfg.modulus)
    return ((state - _time_word(steps, cfg)) * inv) & cfg.mask


def encode_dynamic_law(bits: Iterable[int], cfg: DynamicLawConfig = DEFAULT_DYNAMIC_CONFIG) -> tuple[int, int]:
    rank, steps = rank_trajectory(bits, cfg)
    return _forward(rank, steps, cfg), steps


def decode_dynamic_law(final_state: int, steps: int, cfg: DynamicLawConfig = DEFAULT_DYNAMIC_CONFIG) -> list[int]:
    if not capacity_ok(steps, cfg):
        raise ValueError("admissible family exceeds final-state capacity")
    rank = _inverse(final_state & cfg.mask, steps, cfg)
    total = admissible_count(steps, cfg)
    if rank >= total:
        raise ValueError("final state is not valid for this dynamic law and step count")
    return unrank_trajectory(rank, steps, cfg)

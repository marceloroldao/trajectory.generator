"""Trajectory universe with an explicit causal coherence memory.

The decoder still receives only ``(final_state, steps)`` plus this public
configuration.  The coherence variable is *not* stored as side metadata: it is
recomputed while ranking/unranking because it evolves deterministically from
the recovered path.

State for the admissibility grammar is therefore

    (3-bit history, coherence_bucket, public phase)

rather than just (history, phase).

This module is exact enumerative coding of a constrained family.  It is not a
compression scheme for arbitrary binary data.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Iterable

from .policy_universe import (
    ALL_RULES,
    BALANCED_POLICY_WEIGHTS,
    RIGID_LONG_POLICY_WEIGHTS,
    _allowed,
    _feature_vector,
    _next_state,
)

MEMORY = 3
STATE_COUNT = 1 << MEMORY

# A small public policy bank.  Nothing here targets phi or another named
# constant.  The search experiment may replace these profiles later.
POLICY_BANK: tuple[tuple[int, ...], ...] = (
    BALANCED_POLICY_WEIGHTS,
    RIGID_LONG_POLICY_WEIGHTS,
    (2, 3, 1, 3, 1, 2, 0, 3, 0),
    (0, 2, 3, 1, 2, 2, 1, 5, 0),
    (0, 0, 3, 4, 0, 2, 2, 3, 0),
)


@dataclass(frozen=True)
class CoherenceMemoryConfig:
    width: int = 63
    coherence_levels: int = 4
    # Maps coherence bucket -> policy-bank index.
    policy_map: tuple[int, ...] = (1, 0, 0, 3)
    update_mode: str = "occupancy"  # occupancy | signed_bit | rolling
    universe_mul: int = 0x5B
    universe_seed: int = 0x243F6A88

    def __post_init__(self) -> None:
        if not 1 <= self.width <= 64:
            raise ValueError("width must be between 1 and 64")
        if self.coherence_levels < 2:
            raise ValueError("coherence_levels must be >= 2")
        if len(self.policy_map) != self.coherence_levels:
            raise ValueError("policy_map length must equal coherence_levels")
        if any(not 0 <= p < len(POLICY_BANK) for p in self.policy_map):
            raise ValueError("policy_map contains invalid policy index")
        if self.update_mode not in ("occupancy", "signed_bit", "rolling"):
            raise ValueError("unknown update_mode")
        if self.universe_mul % 2 == 0:
            raise ValueError("universe_mul must be odd")

    @property
    def modulus(self) -> int:
        return 1 << self.width

    @property
    def mask(self) -> int:
        return self.modulus - 1


DEFAULT_COHERENCE_MEMORY_CONFIG = CoherenceMemoryConfig()


def initial_coherence(prefix_state: int, cfg: CoherenceMemoryConfig) -> int:
    # Public deterministic initialization from the first 3 bits.
    return min(cfg.coherence_levels - 1, prefix_state.bit_count())


def update_coherence(c: int, state: int, bit: int, cfg: CoherenceMemoryConfig) -> int:
    nxt = _next_state(state, bit)
    top = cfg.coherence_levels - 1
    if cfg.update_mode == "occupancy":
        balanced = nxt.bit_count() in (1, 2)
        return min(top, c + 1) if balanced else max(0, c - 1)
    if cfg.update_mode == "signed_bit":
        return (c + (1 if bit else -1)) % cfg.coherence_levels
    # rolling: history-sensitive finite accumulator
    return ((c << 1) ^ nxt ^ bit) % cfg.coherence_levels


@lru_cache(maxsize=None)
def _selected_rule_index_cached(state: int, phase: int, policy_index: int) -> int:
    weights = POLICY_BANK[policy_index]
    best_index = 0
    best_score = None
    for index, rule in enumerate(ALL_RULES):
        features = _feature_vector(rule, index, state, phase)
        score = sum(a * b for a, b in zip(features, weights))
        if best_score is None or score > best_score:
            best_score = score
            best_index = index
    return best_index


def selected_rule_index(state: int, t: int, coherence: int, cfg: CoherenceMemoryConfig = DEFAULT_COHERENCE_MEMORY_CONFIG) -> int:
    policy_index = cfg.policy_map[coherence]
    return _selected_rule_index_cached(state, t % 3, policy_index)


def active_action(state: int, t: int, coherence: int, cfg: CoherenceMemoryConfig = DEFAULT_COHERENCE_MEMORY_CONFIG) -> int:
    return ALL_RULES[selected_rule_index(state, t, coherence, cfg)][state]


def _prefix_state(bits: list[int]) -> int:
    state = 0
    for bit in bits:
        state = (state << 1) | bit
    return state


def _suffix_counter(cfg: CoherenceMemoryConfig):
    @lru_cache(maxsize=None)
    def suffix(state: int, coherence: int, t: int, remaining: int) -> int:
        if remaining == 0:
            return 1
        total = 0
        for bit in _allowed(active_action(state, t, coherence, cfg)):
            total += suffix(
                _next_state(state, bit),
                update_coherence(coherence, state, bit, cfg),
                t + 1,
                remaining - 1,
            )
        return total
    return suffix


def admissible_count(steps: int, cfg: CoherenceMemoryConfig = DEFAULT_COHERENCE_MEMORY_CONFIG) -> int:
    if steps < 0:
        raise ValueError("steps must be non-negative")
    if steps <= MEMORY:
        return 1 << steps
    suffix = _suffix_counter(cfg)
    rem = steps - MEMORY
    total = 0
    for state in range(STATE_COUNT):
        total += suffix(state, initial_coherence(state, cfg), MEMORY, rem)
    return total


def capacity_ok(steps: int, cfg: CoherenceMemoryConfig = DEFAULT_COHERENCE_MEMORY_CONFIG) -> bool:
    return admissible_count(steps, cfg) <= cfg.modulus


def validate(bits: Iterable[int], cfg: CoherenceMemoryConfig = DEFAULT_COHERENCE_MEMORY_CONFIG) -> bool:
    seq = [int(b) for b in bits]
    if any(b not in (0, 1) for b in seq):
        return False
    if len(seq) <= MEMORY:
        return True
    state = _prefix_state(seq[:MEMORY])
    c = initial_coherence(state, cfg)
    for t, bit in enumerate(seq[MEMORY:], start=MEMORY):
        if bit not in _allowed(active_action(state, t, c, cfg)):
            return False
        c = update_coherence(c, state, bit, cfg)
        state = _next_state(state, bit)
    return True


def rank_trajectory(bits: Iterable[int], cfg: CoherenceMemoryConfig = DEFAULT_COHERENCE_MEMORY_CONFIG) -> tuple[int, int]:
    seq = [int(b) for b in bits]
    if not validate(seq, cfg):
        raise ValueError("trajectory violates coherence-memory universe")
    steps = len(seq)
    if not capacity_ok(steps, cfg):
        raise ValueError("admissible family exceeds final-state capacity")
    if steps <= MEMORY:
        return _prefix_state(seq), steps

    suffix = _suffix_counter(cfg)
    rem = steps - MEMORY
    prefix = _prefix_state(seq[:MEMORY])
    rank = 0
    for state0 in range(prefix):
        rank += suffix(state0, initial_coherence(state0, cfg), MEMORY, rem)

    state = prefix
    c = initial_coherence(state, cfg)
    for t, bit in enumerate(seq[MEMORY:], start=MEMORY):
        rem_after = steps - t - 1
        options = _allowed(active_action(state, t, c, cfg))
        if bit == 1 and 0 in options:
            nstate = _next_state(state, 0)
            nc = update_coherence(c, state, 0, cfg)
            rank += suffix(nstate, nc, t + 1, rem_after)
        c = update_coherence(c, state, bit, cfg)
        state = _next_state(state, bit)
    return rank, steps


def unrank_trajectory(rank: int, steps: int, cfg: CoherenceMemoryConfig = DEFAULT_COHERENCE_MEMORY_CONFIG) -> list[int]:
    total = admissible_count(steps, cfg)
    if not 0 <= rank < total:
        raise ValueError("rank outside admissible family")
    if steps <= MEMORY:
        return [((rank >> (steps - 1 - i)) & 1) for i in range(steps)] if steps else []

    suffix = _suffix_counter(cfg)
    rem = steps - MEMORY
    prefix = None
    for state0 in range(STATE_COUNT):
        count = suffix(state0, initial_coherence(state0, cfg), MEMORY, rem)
        if rank < count:
            prefix = state0
            break
        rank -= count
    assert prefix is not None

    bits = [((prefix >> (MEMORY - 1 - i)) & 1) for i in range(MEMORY)]
    state = prefix
    c = initial_coherence(state, cfg)
    for t in range(MEMORY, steps):
        rem_after = steps - t - 1
        for bit in _allowed(active_action(state, t, c, cfg)):
            nstate = _next_state(state, bit)
            nc = update_coherence(c, state, bit, cfg)
            count = suffix(nstate, nc, t + 1, rem_after)
            if rank < count:
                bits.append(bit)
                state, c = nstate, nc
                break
            rank -= count
    return bits


def _time_word(steps: int, cfg: CoherenceMemoryConfig) -> int:
    z = (steps + cfg.universe_seed) & cfg.mask
    z ^= (z << 13) & cfg.mask
    z ^= z >> 7
    z ^= (z << 17) & cfg.mask
    return z & cfg.mask


def _forward(rank: int, steps: int, cfg: CoherenceMemoryConfig) -> int:
    return (rank * cfg.universe_mul + _time_word(steps, cfg)) & cfg.mask


def _inverse(state: int, steps: int, cfg: CoherenceMemoryConfig) -> int:
    inv = pow(cfg.universe_mul, -1, cfg.modulus)
    return ((state - _time_word(steps, cfg)) * inv) & cfg.mask


def encode_coherence_memory(bits: Iterable[int], cfg: CoherenceMemoryConfig = DEFAULT_COHERENCE_MEMORY_CONFIG) -> tuple[int, int]:
    rank, steps = rank_trajectory(bits, cfg)
    return _forward(rank, steps, cfg), steps


def decode_coherence_memory(final_state: int, steps: int, cfg: CoherenceMemoryConfig = DEFAULT_COHERENCE_MEMORY_CONFIG) -> list[int]:
    if not capacity_ok(steps, cfg):
        raise ValueError("admissible family exceeds final-state capacity")
    rank = _inverse(final_state & cfg.mask, steps, cfg)
    total = admissible_count(steps, cfg)
    if rank >= total:
        raise ValueError("invalid address for coherence-memory universe")
    return unrank_trajectory(rank, steps, cfg)

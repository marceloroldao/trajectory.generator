"""Endogenous coherence-based dynamic law selector.

The active local law is chosen deterministically from the current history state
and public time phase. No law index sequence is stored externally.

This experiment intentionally does not target phi, the plastic constant, or any
other numerical constant. The selector uses only local state occupancy proxy
(popcount), phase, and a preference for either free or forced transitions.

The resulting admissible family can be ranked/unranked exactly because the
selector is a public deterministic function of the decoded prefix and time.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Iterable

from .finite_law_codec import (
    FORCE_0,
    FORCE_1,
    FREE,
    MEMORY3_PHI_RULE,
    MEMORY3_PLASTIC_RULE,
    MEMORY3_TRIBONACCI_RULE,
)


@dataclass(frozen=True)
class CoherenceUniverseConfig:
    width: int = 63
    memory: int = 3
    period: int = 3
    universe_mul: int = 0x5D
    universe_seed: int = 0x27D4EB2D
    laws: tuple[tuple[int, ...], ...] = (
        MEMORY3_PLASTIC_RULE,
        MEMORY3_PHI_RULE,
        MEMORY3_TRIBONACCI_RULE,
    )

    def __post_init__(self) -> None:
        if self.memory != 3:
            raise ValueError("current experiment is defined for memory=3")
        if self.period < 1:
            raise ValueError("period must be >= 1")
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


DEFAULT_COHERENCE_UNIVERSE_CONFIG = CoherenceUniverseConfig()


def _allowed(action: int) -> tuple[int, ...]:
    if action == FORCE_0:
        return (0,)
    if action == FORCE_1:
        return (1,)
    return (0, 1)


def _next_state(state: int, bit: int, memory: int) -> int:
    return ((state << 1) & ((1 << memory) - 1)) | bit


def select_law(state: int, t: int, cfg: CoherenceUniverseConfig = DEFAULT_COHERENCE_UNIVERSE_CONFIG) -> int:
    """Choose the active law from state/phase coherence only.

    Design rule:
    - a balanced 3-bit history (popcount 1 or 2) is allowed extra freedom only
      during phase 1 of the public period;
    - otherwise the selector prefers a forced transition;
    - among forced candidates, prefer the one whose next history is closer to a
      balanced occupancy of 1.5 ones;
    - a tiny deterministic state/phase tie-break avoids hidden preferences.
    """

    pop = state.bit_count()
    phase = t % cfg.period
    desired_free = pop in (1, 2) and phase == 1

    best_index = 0
    best_score = None
    for j, law in enumerate(cfg.laws):
        action = law[state]
        is_free = action == FREE
        score = 0.0 if is_free == desired_free else 2.0

        if not is_free:
            nxt = _next_state(state, action, cfg.memory)
            score += 0.3 * abs(nxt.bit_count() - 1.5)

        score += 0.01 * ((j + phase + (state & 1)) % len(cfg.laws))

        if best_score is None or score < best_score:
            best_score = score
            best_index = j

    return best_index


def admissible_count(steps: int, cfg: CoherenceUniverseConfig = DEFAULT_COHERENCE_UNIVERSE_CONFIG) -> int:
    if steps < 0:
        raise ValueError("steps must be non-negative")
    if steps <= cfg.memory:
        return 1 << steps

    counts = [1] * (1 << cfg.memory)
    for t in range(cfg.memory, steps):
        nxt_counts = [0] * (1 << cfg.memory)
        for state, count in enumerate(counts):
            if count == 0:
                continue
            law_index = select_law(state, t, cfg)
            action = cfg.laws[law_index][state]
            for bit in _allowed(action):
                nxt_counts[_next_state(state, bit, cfg.memory)] += count
        counts = nxt_counts
    return sum(counts)


def capacity_ok(steps: int, cfg: CoherenceUniverseConfig = DEFAULT_COHERENCE_UNIVERSE_CONFIG) -> bool:
    return admissible_count(steps, cfg) <= cfg.modulus


def validate(bits: Iterable[int], cfg: CoherenceUniverseConfig = DEFAULT_COHERENCE_UNIVERSE_CONFIG) -> bool:
    seq = [int(b) for b in bits]
    if any(b not in (0, 1) for b in seq):
        return False
    if len(seq) <= cfg.memory:
        return True

    state = 0
    for b in seq[: cfg.memory]:
        state = (state << 1) | b

    for t, bit in enumerate(seq[cfg.memory :], start=cfg.memory):
        law_index = select_law(state, t, cfg)
        action = cfg.laws[law_index][state]
        if bit not in _allowed(action):
            return False
        state = _next_state(state, bit, cfg.memory)
    return True


def _suffix_counter(cfg: CoherenceUniverseConfig):
    @lru_cache(maxsize=None)
    def count(state: int, t: int, remaining: int) -> int:
        if remaining == 0:
            return 1
        law_index = select_law(state, t, cfg)
        action = cfg.laws[law_index][state]
        return sum(
            count(_next_state(state, bit, cfg.memory), t + 1, remaining - 1)
            for bit in _allowed(action)
        )
    return count


def rank_trajectory(bits: Iterable[int], cfg: CoherenceUniverseConfig = DEFAULT_COHERENCE_UNIVERSE_CONFIG) -> tuple[int, int]:
    seq = [int(b) for b in bits]
    if any(b not in (0, 1) for b in seq):
        raise ValueError("bits must contain only 0 and 1")
    steps = len(seq)
    if not validate(seq, cfg):
        raise ValueError("trajectory violates coherence-universe law")
    if not capacity_ok(steps, cfg):
        raise ValueError("admissible family exceeds final-state capacity")
    if steps == 0:
        return 0, 0
    if steps <= cfg.memory:
        rank = 0
        for b in seq:
            rank = (rank << 1) | b
        return rank, steps

    suffix_count = _suffix_counter(cfg)
    remaining = steps - cfg.memory
    prefix = 0
    for b in seq[: cfg.memory]:
        prefix = (prefix << 1) | b

    rank = 0
    for smaller_prefix in range(prefix):
        rank += suffix_count(smaller_prefix, cfg.memory, remaining)

    state = prefix
    for t, bit in enumerate(seq[cfg.memory :], start=cfg.memory):
        rem_after = steps - t - 1
        law_index = select_law(state, t, cfg)
        action = cfg.laws[law_index][state]
        options = _allowed(action)
        if bit == 1 and 0 in options:
            rank += suffix_count(_next_state(state, 0, cfg.memory), t + 1, rem_after)
        state = _next_state(state, bit, cfg.memory)

    return rank, steps


def unrank_trajectory(rank: int, steps: int, cfg: CoherenceUniverseConfig = DEFAULT_COHERENCE_UNIVERSE_CONFIG) -> list[int]:
    total = admissible_count(steps, cfg)
    if not 0 <= rank < total:
        raise ValueError("rank outside admissible family")
    if steps == 0:
        return []
    if steps <= cfg.memory:
        return [((rank >> (steps - 1 - i)) & 1) for i in range(steps)]

    suffix_count = _suffix_counter(cfg)
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
    for t in range(cfg.memory, steps):
        law_index = select_law(state, t, cfg)
        action = cfg.laws[law_index][state]
        chosen = None
        for bit in _allowed(action):
            count = suffix_count(_next_state(state, bit, cfg.memory), t + 1, steps - t - 1)
            if rank < count:
                chosen = bit
                break
            rank -= count
        assert chosen is not None
        bits.append(chosen)
        state = _next_state(state, chosen, cfg.memory)
    return bits


def _time_word(steps: int, cfg: CoherenceUniverseConfig) -> int:
    z = (steps + cfg.universe_seed) & cfg.mask
    z ^= (z << 13) & cfg.mask
    z ^= z >> 7
    z ^= (z << 17) & cfg.mask
    return z & cfg.mask


def _forward(rank: int, steps: int, cfg: CoherenceUniverseConfig) -> int:
    return (rank * cfg.universe_mul + _time_word(steps, cfg)) & cfg.mask


def _inverse(state: int, steps: int, cfg: CoherenceUniverseConfig) -> int:
    inv = pow(cfg.universe_mul, -1, cfg.modulus)
    return ((state - _time_word(steps, cfg)) * inv) & cfg.mask


def encode_coherence_universe(bits: Iterable[int], cfg: CoherenceUniverseConfig = DEFAULT_COHERENCE_UNIVERSE_CONFIG) -> tuple[int, int]:
    rank, steps = rank_trajectory(bits, cfg)
    return _forward(rank, steps, cfg), steps


def decode_coherence_universe(final_state: int, steps: int, cfg: CoherenceUniverseConfig = DEFAULT_COHERENCE_UNIVERSE_CONFIG) -> list[int]:
    if not capacity_ok(steps, cfg):
        raise ValueError("admissible family exceeds final-state capacity")
    rank = _inverse(final_state & cfg.mask, steps, cfg)
    total = admissible_count(steps, cfg)
    if rank >= total:
        raise ValueError("invalid final state for this coherence universe")
    return unrank_trajectory(rank, steps, cfg)

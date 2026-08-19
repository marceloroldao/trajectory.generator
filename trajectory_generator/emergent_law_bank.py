"""Endogenous law-bank universe over all memory-3 local rules.

The candidate bank contains every memory-3 rule with actions:
0 = force next bit 0
1 = force next bit 1
2 = leave next bit free

There are 3^8 = 6,561 laws.  No spectral constant is used by the selector.
For each (history, public phase), the selector scores every law by local
coherence plus global combinatorial properties of the grammar:

- balance between free and forced actions: free_count * (8 - free_count)
- symmetry between force-0 and force-1 actions
- number of forced transitions that move into balanced-popcount states
- coverage of reachable 3-bit next states

The selected law index is therefore a deterministic consequence of the current
history and public phase.  The active-law sequence is not stored as metadata.

The exact codec ranks admissible trajectories using dynamic suffix counts, so
decoding still receives only (final_state, steps) plus this public definition.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from itertools import product
from typing import Iterable

FORCE_0 = 0
FORCE_1 = 1
FREE = 2

MEMORY = 3
STATE_COUNT = 1 << MEMORY
ALL_RULES: tuple[tuple[int, ...], ...] = tuple(product((FORCE_0, FORCE_1, FREE), repeat=STATE_COUNT))


def _allowed(action: int) -> tuple[int, ...]:
    return (0, 1) if action == FREE else (action,)


def _next_state(state: int, bit: int) -> int:
    return ((state << 1) & 0b111) | bit


def _rule_features(rule: tuple[int, ...]) -> tuple[int, int, int, int]:
    free = rule.count(FREE)
    force0 = rule.count(FORCE_0)
    force1 = rule.count(FORCE_1)
    freedom_balance = free * (STATE_COUNT - free)
    force_symmetry = -abs(force0 - force1)

    balanced_forced = 0
    covered: set[int] = set()
    for state, action in enumerate(rule):
        for bit in _allowed(action):
            covered.add(_next_state(state, bit))
        if action != FREE:
            if _next_state(state, action).bit_count() in (1, 2):
                balanced_forced += 1
    return freedom_balance, force_symmetry, balanced_forced, len(covered)


RULE_FEATURES: tuple[tuple[int, int, int, int], ...] = tuple(_rule_features(rule) for rule in ALL_RULES)


def _local_score(rule: tuple[int, ...], state: int, phase: int) -> tuple[int, int]:
    action = rule[state]
    options = _allowed(action)
    balanced_next = sum(1 for bit in options if _next_state(state, bit).bit_count() in (1, 2))
    pop = state.bit_count()

    # Extreme histories prefer a definite restoring move.  Balanced histories
    # permit extra freedom only on public phase 1.
    if pop in (0, 3):
        return (1 if action != FREE else 0, balanced_next)
    if phase == 1:
        return (1 if action == FREE else 0, balanced_next)
    return (balanced_next, 1 if action != FREE else 0)


@lru_cache(maxsize=None)
def selected_rule_index(state: int, phase: int) -> int:
    if not 0 <= state < STATE_COUNT:
        raise ValueError("state must be a 3-bit history")
    phase %= 3
    best_score = None
    best_index = None
    for index, rule in enumerate(ALL_RULES):
        local = _local_score(rule, state, phase)
        freedom_balance, force_symmetry, balanced_forced, coverage = RULE_FEATURES[index]
        score = (
            local[0],
            local[1],
            freedom_balance,
            force_symmetry,
            balanced_forced,
            coverage,
            -index,  # deterministic canonical tie-break
        )
        if best_score is None or score > best_score:
            best_score = score
            best_index = index
    assert best_index is not None
    return best_index


def active_action(state: int, t: int) -> int:
    return ALL_RULES[selected_rule_index(state, t % 3)][state]


@dataclass(frozen=True)
class EmergentLawBankConfig:
    width: int = 63
    universe_mul: int = 0x5B
    universe_seed: int = 0x27D4EB2D

    def __post_init__(self) -> None:
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


DEFAULT_EMERGENT_LAW_BANK_CONFIG = EmergentLawBankConfig()


def _prefix_state(bits: list[int]) -> int:
    state = 0
    for bit in bits:
        state = (state << 1) | bit
    return state


@lru_cache(maxsize=None)
def _suffix_count(state: int, t: int, remaining: int) -> int:
    if remaining == 0:
        return 1
    return sum(
        _suffix_count(_next_state(state, bit), t + 1, remaining - 1)
        for bit in _allowed(active_action(state, t))
    )


def admissible_count(steps: int) -> int:
    if steps < 0:
        raise ValueError("steps must be non-negative")
    if steps <= MEMORY:
        return 1 << steps
    remaining = steps - MEMORY
    return sum(_suffix_count(state, MEMORY, remaining) for state in range(STATE_COUNT))


def capacity_ok(steps: int, cfg: EmergentLawBankConfig = DEFAULT_EMERGENT_LAW_BANK_CONFIG) -> bool:
    return admissible_count(steps) <= cfg.modulus


def validate(bits: Iterable[int]) -> bool:
    seq = [int(b) for b in bits]
    if any(bit not in (0, 1) for bit in seq):
        return False
    if len(seq) <= MEMORY:
        return True
    state = _prefix_state(seq[:MEMORY])
    for t, bit in enumerate(seq[MEMORY:], start=MEMORY):
        if bit not in _allowed(active_action(state, t)):
            return False
        state = _next_state(state, bit)
    return True


def rank_trajectory(bits: Iterable[int], cfg: EmergentLawBankConfig = DEFAULT_EMERGENT_LAW_BANK_CONFIG) -> tuple[int, int]:
    seq = [int(b) for b in bits]
    if any(bit not in (0, 1) for bit in seq):
        raise ValueError("bits must contain only 0 and 1")
    steps = len(seq)
    if not validate(seq):
        raise ValueError("trajectory violates emergent law-bank universe")
    if not capacity_ok(steps, cfg):
        raise ValueError("admissible family exceeds final-state capacity")
    if steps <= MEMORY:
        return _prefix_state(seq), steps

    remaining = steps - MEMORY
    prefix = _prefix_state(seq[:MEMORY])
    rank = sum(_suffix_count(state, MEMORY, remaining) for state in range(prefix))

    state = prefix
    for t, bit in enumerate(seq[MEMORY:], start=MEMORY):
        rem_after = steps - t - 1
        options = _allowed(active_action(state, t))
        if bit == 1 and 0 in options:
            rank += _suffix_count(_next_state(state, 0), t + 1, rem_after)
        state = _next_state(state, bit)
    return rank, steps


def unrank_trajectory(rank: int, steps: int, cfg: EmergentLawBankConfig = DEFAULT_EMERGENT_LAW_BANK_CONFIG) -> list[int]:
    total = admissible_count(steps)
    if not 0 <= rank < total:
        raise ValueError("rank outside admissible family")
    if steps <= MEMORY:
        return [((rank >> (steps - 1 - i)) & 1) for i in range(steps)] if steps else []

    remaining = steps - MEMORY
    prefix = None
    for state in range(STATE_COUNT):
        count = _suffix_count(state, MEMORY, remaining)
        if rank < count:
            prefix = state
            break
        rank -= count
    assert prefix is not None

    bits = [((prefix >> (MEMORY - 1 - i)) & 1) for i in range(MEMORY)]
    state = prefix
    for t in range(MEMORY, steps):
        options = _allowed(active_action(state, t))
        chosen = None
        rem_after = steps - t - 1
        for bit in options:
            count = _suffix_count(_next_state(state, bit), t + 1, rem_after)
            if rank < count:
                chosen = bit
                break
            rank -= count
        assert chosen is not None
        bits.append(chosen)
        state = _next_state(state, chosen)
    return bits


def _time_word(steps: int, cfg: EmergentLawBankConfig) -> int:
    z = (steps + cfg.universe_seed) & cfg.mask
    z ^= (z << 13) & cfg.mask
    z ^= z >> 7
    z ^= (z << 17) & cfg.mask
    return z & cfg.mask


def _forward(rank: int, steps: int, cfg: EmergentLawBankConfig) -> int:
    return (rank * cfg.universe_mul + _time_word(steps, cfg)) & cfg.mask


def _inverse(state: int, steps: int, cfg: EmergentLawBankConfig) -> int:
    inv = pow(cfg.universe_mul, -1, cfg.modulus)
    return ((state - _time_word(steps, cfg)) * inv) & cfg.mask


def encode_emergent_law_bank(bits: Iterable[int], cfg: EmergentLawBankConfig = DEFAULT_EMERGENT_LAW_BANK_CONFIG) -> tuple[int, int]:
    rank, steps = rank_trajectory(bits, cfg)
    return _forward(rank, steps, cfg), steps


def decode_emergent_law_bank(final_state: int, steps: int, cfg: EmergentLawBankConfig = DEFAULT_EMERGENT_LAW_BANK_CONFIG) -> list[int]:
    if not capacity_ok(steps, cfg):
        raise ValueError("admissible family exceeds final-state capacity")
    rank = _inverse(final_state & cfg.mask, steps, cfg)
    total = admissible_count(steps)
    if rank >= total:
        raise ValueError("invalid address for emergent law-bank universe")
    return unrank_trajectory(rank, steps, cfg)

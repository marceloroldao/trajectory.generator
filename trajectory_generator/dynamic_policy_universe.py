"""Second-order dynamic policy universe over all memory-3 laws.

The active selector weights are not fixed globally. A public deterministic
context map chooses one of three weight profiles from the current 3-bit history
and phase:

- extreme histories (popcount 0 or 3)
- balanced histories during public phase 1
- other balanced histories

The chosen weight profile then scores all 3^8 = 6,561 local laws. The active
policy sequence and active law sequence are therefore regenerated from
(history, time); neither is stored as side metadata.

This is exact enumerative coding of a constrained family, not compression of
arbitrary binary data.
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

# Feature order:
# extreme_restore, phase_free, balanced_next, forced, free,
# freedom_balance, force_symmetry, balanced_forced, coverage
#
# These three profiles were found by a seeded exploratory search constrained to
# moderate information rate. They are not optimized for phi or another named
# constant.
EXTREME_WEIGHTS = (2, 3, 1, 3, 1, 2, 0, 3, 0)
PHASE1_WEIGHTS = (0, 2, 3, 1, 2, 2, 1, 5, 0)
BALANCED_WEIGHTS = (0, 0, 3, 4, 0, 2, 2, 3, 0)


def _allowed(action: int) -> tuple[int, ...]:
    return (0, 1) if action == FREE else (action,)


def _next_state(state: int, bit: int) -> int:
    return ((state << 1) & 0b111) | bit


def _global_features(rule: tuple[int, ...]) -> tuple[int, int, int, int]:
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
        if action != FREE and _next_state(state, action).bit_count() in (1, 2):
            balanced_forced += 1
    return freedom_balance, force_symmetry, balanced_forced, len(covered)


RULE_GLOBAL_FEATURES = tuple(_global_features(rule) for rule in ALL_RULES)


def _feature_vector(rule: tuple[int, ...], index: int, state: int, phase: int) -> tuple[int, ...]:
    action = rule[state]
    options = _allowed(action)
    pop = state.bit_count()
    balanced_next = sum(1 for bit in options if _next_state(state, bit).bit_count() in (1, 2))
    extreme_restore = int(
        pop in (0, 3)
        and action != FREE
        and _next_state(state, action).bit_count() in (1, 2)
    )
    phase_free = int(pop in (1, 2) and phase == 1 and action == FREE)
    return (
        extreme_restore,
        phase_free,
        balanced_next,
        int(action != FREE),
        int(action == FREE),
        *RULE_GLOBAL_FEATURES[index],
    )


def active_weights(state: int, phase: int) -> tuple[int, ...]:
    """Return the public selector policy active in this context."""
    phase %= 3
    if state.bit_count() in (0, 3):
        return EXTREME_WEIGHTS
    if phase == 1:
        return PHASE1_WEIGHTS
    return BALANCED_WEIGHTS


@lru_cache(maxsize=None)
def selected_rule_index(state: int, phase: int) -> int:
    if not 0 <= state < STATE_COUNT:
        raise ValueError("state must be a 3-bit history")
    phase %= 3
    weights = active_weights(state, phase)
    best_index = 0
    best_score = None
    for index, rule in enumerate(ALL_RULES):
        features = _feature_vector(rule, index, state, phase)
        score = sum(a * b for a, b in zip(features, weights))
        if best_score is None or score > best_score:
            best_score = score
            best_index = index
    return best_index


def active_action(state: int, t: int) -> int:
    return ALL_RULES[selected_rule_index(state, t % 3)][state]


@dataclass(frozen=True)
class DynamicPolicyUniverseConfig:
    width: int = 63
    universe_mul: int = 0x5B
    universe_seed: int = 0x510E527F

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


DEFAULT_DYNAMIC_POLICY_UNIVERSE_CONFIG = DynamicPolicyUniverseConfig()


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


def capacity_ok(steps: int, cfg: DynamicPolicyUniverseConfig = DEFAULT_DYNAMIC_POLICY_UNIVERSE_CONFIG) -> bool:
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


def rank_trajectory(bits: Iterable[int], cfg: DynamicPolicyUniverseConfig = DEFAULT_DYNAMIC_POLICY_UNIVERSE_CONFIG) -> tuple[int, int]:
    seq = [int(b) for b in bits]
    if not validate(seq):
        raise ValueError("trajectory violates dynamic-policy universe")
    steps = len(seq)
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


def unrank_trajectory(rank: int, steps: int, cfg: DynamicPolicyUniverseConfig = DEFAULT_DYNAMIC_POLICY_UNIVERSE_CONFIG) -> list[int]:
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
        rem_after = steps - t - 1
        for bit in _allowed(active_action(state, t)):
            count = _suffix_count(_next_state(state, bit), t + 1, rem_after)
            if rank < count:
                bits.append(bit)
                state = _next_state(state, bit)
                break
            rank -= count
    return bits


def _time_word(steps: int, cfg: DynamicPolicyUniverseConfig) -> int:
    z = (steps + cfg.universe_seed) & cfg.mask
    z ^= (z << 13) & cfg.mask
    z ^= z >> 7
    z ^= (z << 17) & cfg.mask
    return z & cfg.mask


def _forward(rank: int, steps: int, cfg: DynamicPolicyUniverseConfig) -> int:
    return (rank * cfg.universe_mul + _time_word(steps, cfg)) & cfg.mask


def _inverse(state: int, steps: int, cfg: DynamicPolicyUniverseConfig) -> int:
    inv = pow(cfg.universe_mul, -1, cfg.modulus)
    return ((state - _time_word(steps, cfg)) * inv) & cfg.mask


def encode_dynamic_policy_universe(bits: Iterable[int], cfg: DynamicPolicyUniverseConfig = DEFAULT_DYNAMIC_POLICY_UNIVERSE_CONFIG) -> tuple[int, int]:
    rank, steps = rank_trajectory(bits, cfg)
    return _forward(rank, steps, cfg), steps


def decode_dynamic_policy_universe(final_state: int, steps: int, cfg: DynamicPolicyUniverseConfig = DEFAULT_DYNAMIC_POLICY_UNIVERSE_CONFIG) -> list[int]:
    if not capacity_ok(steps, cfg):
        raise ValueError("admissible family exceeds final-state capacity")
    rank = _inverse(final_state & cfg.mask, steps, cfg)
    total = admissible_count(steps)
    if rank >= total:
        raise ValueError("invalid address for dynamic-policy universe")
    return unrank_trajectory(rank, steps, cfg)

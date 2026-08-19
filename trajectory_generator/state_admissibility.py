"""State-dependent admissibility law with Fibonacci growth.

Rule:
- for the first two bits, both values are free;
- from t >= 2, if the two previous bits are equal, the next bit is forced to
  the opposite value;
- if the two previous bits differ, the next bit is free.

No golden-ratio constant is present. The number of admissible binary trajectories
of length n (n >= 1) is 2*F_(n+1), so successive count ratios converge to phi.
This is a combinatorial consequence of this particular public rule, not evidence
that phi is universally privileged.

Ranking/unranking is exact via dynamic programming over the 2-bit automaton, so
decoding still requires only (final_state, steps) plus the public rule.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Iterable


@dataclass(frozen=True)
class StateAdmissibilityConfig:
    width: int = 63
    universe_mul: int = 0x63
    universe_seed: int = 0x7F4A7C15

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


DEFAULT_STATE_ADMISSIBILITY_CONFIG = StateAdmissibilityConfig()


def allowed_next(prefix: list[int]) -> tuple[int, ...]:
    if len(prefix) < 2:
        return (0, 1)
    a, b = prefix[-2], prefix[-1]
    if a == b:
        return (b ^ 1,)
    return (0, 1)


def validate_trajectory(bits: Iterable[int]) -> bool:
    seq = [int(b) for b in bits]
    if any(b not in (0, 1) for b in seq):
        return False
    prefix: list[int] = []
    for bit in seq:
        if bit not in allowed_next(prefix):
            return False
        prefix.append(bit)
    return True


@lru_cache(maxsize=None)
def _count_suffix(remaining: int, a: int, b: int) -> int:
    if remaining == 0:
        return 1
    total = 0
    choices = (b ^ 1,) if a == b else (0, 1)
    for bit in choices:
        total += _count_suffix(remaining - 1, b, bit)
    return total


def admissible_count(steps: int) -> int:
    if steps < 0:
        raise ValueError("steps must be non-negative")
    if steps == 0:
        return 1
    if steps == 1:
        return 2
    return sum(_count_suffix(steps - 2, a, b) for a in (0, 1) for b in (0, 1))


def capacity_ok(steps: int, cfg: StateAdmissibilityConfig = DEFAULT_STATE_ADMISSIBILITY_CONFIG) -> bool:
    return admissible_count(steps) <= cfg.modulus


def rank_trajectory(bits: Iterable[int], cfg: StateAdmissibilityConfig = DEFAULT_STATE_ADMISSIBILITY_CONFIG) -> tuple[int, int]:
    seq = [int(b) for b in bits]
    if not validate_trajectory(seq):
        raise ValueError("trajectory violates state-dependent admissibility law")
    steps = len(seq)
    if not capacity_ok(steps, cfg):
        raise ValueError("admissible family exceeds final-state capacity")
    if steps == 0:
        return 0, 0

    rank = 0
    prefix: list[int] = []
    for t, bit in enumerate(seq):
        choices = allowed_next(prefix)
        for candidate in choices:
            if candidate >= bit:
                break
            if t == 0:
                # Candidate first bit: sum both possible second-bit branches.
                if steps == 1:
                    rank += 1
                else:
                    rank += sum(_count_suffix(steps - 2, candidate, b) for b in (0, 1))
            elif t == 1:
                rank += _count_suffix(steps - 2, prefix[-1], candidate)
            else:
                rank += _count_suffix(steps - t - 1, prefix[-1], candidate)
        prefix.append(bit)
    return rank, steps


def unrank_trajectory(rank: int, steps: int, cfg: StateAdmissibilityConfig = DEFAULT_STATE_ADMISSIBILITY_CONFIG) -> list[int]:
    if steps < 0:
        raise ValueError("steps must be non-negative")
    total = admissible_count(steps)
    if not capacity_ok(steps, cfg):
        raise ValueError("admissible family exceeds final-state capacity")
    if not 0 <= rank < total:
        raise ValueError("rank outside admissible family")
    if steps == 0:
        return []

    out: list[int] = []
    for t in range(steps):
        choices = allowed_next(out)
        chosen = None
        for candidate in choices:
            if t == 0:
                count = 1 if steps == 1 else sum(_count_suffix(steps - 2, candidate, b) for b in (0, 1))
            elif t == 1:
                count = _count_suffix(steps - 2, out[-1], candidate)
            else:
                count = _count_suffix(steps - t - 1, out[-1], candidate)
            if rank < count:
                chosen = candidate
                break
            rank -= count
        if chosen is None:
            raise RuntimeError("unrank failed")
        out.append(chosen)
    return out


def _time_word(steps: int, cfg: StateAdmissibilityConfig) -> int:
    z = (steps + cfg.universe_seed) & cfg.mask
    z ^= (z << 13) & cfg.mask
    z ^= z >> 7
    z ^= (z << 17) & cfg.mask
    return z & cfg.mask


def _permute(rank: int, steps: int, cfg: StateAdmissibilityConfig) -> int:
    return (rank * cfg.universe_mul + _time_word(steps, cfg)) & cfg.mask


def _unpermute(state: int, steps: int, cfg: StateAdmissibilityConfig) -> int:
    inv = pow(cfg.universe_mul, -1, cfg.modulus)
    return ((state - _time_word(steps, cfg)) * inv) & cfg.mask


def encode_state_admissible(bits: Iterable[int], cfg: StateAdmissibilityConfig = DEFAULT_STATE_ADMISSIBILITY_CONFIG) -> tuple[int, int]:
    rank, steps = rank_trajectory(bits, cfg)
    return _permute(rank, steps, cfg), steps


def decode_state_admissible(final_state: int, steps: int, cfg: StateAdmissibilityConfig = DEFAULT_STATE_ADMISSIBILITY_CONFIG) -> list[int]:
    if not capacity_ok(steps, cfg):
        raise ValueError("admissible family exceeds final-state capacity")
    rank = _unpermute(final_state & cfg.mask, steps, cfg)
    if rank >= admissible_count(steps):
        raise ValueError("final state is not a valid address for this admissible family")
    return unrank_trajectory(rank, steps, cfg)

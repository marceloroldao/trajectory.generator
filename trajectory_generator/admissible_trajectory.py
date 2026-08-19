"""Trajectory families constrained by public admissibility laws.

The default law revives the original 'universe every 3 cycles' idea in a strict
information-theoretic form: every third bit is not free. It is forced by the two
previous bits plus a public time phase. The remaining positions are free.

Therefore a length-n trajectory has only 2^F(n) admissible members, where F(n)
is the number of free positions. The final state stores the exact rank of the free
choices through a reversible public permutation. Decoding receives only
(final_state, steps) and reconstructs the forced positions from the law.

This is exact coding of a constrained family, not compression of arbitrary data.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class PeriodicAdmissibilityConfig:
    width: int = 63
    period: int = 3
    universe_mul: int = 0x5B
    universe_seed: int = 0x9E3779B9

    def __post_init__(self) -> None:
        if not 1 <= self.width <= 64:
            raise ValueError("width must be between 1 and 64")
        if self.period < 3:
            raise ValueError("period must be >= 3")
        if self.universe_mul % 2 == 0:
            raise ValueError("universe_mul must be odd")

    @property
    def modulus(self) -> int:
        return 1 << self.width

    @property
    def mask(self) -> int:
        return self.modulus - 1


DEFAULT_ADMISSIBILITY_CONFIG = PeriodicAdmissibilityConfig()


def is_forced_position(t: int, cfg: PeriodicAdmissibilityConfig = DEFAULT_ADMISSIBILITY_CONFIG) -> bool:
    return t >= 2 and (t % cfg.period) == (cfg.period - 1)


def free_positions(steps: int, cfg: PeriodicAdmissibilityConfig = DEFAULT_ADMISSIBILITY_CONFIG) -> list[int]:
    if steps < 0:
        raise ValueError("steps must be non-negative")
    return [t for t in range(steps) if not is_forced_position(t, cfg)]


def free_count(steps: int, cfg: PeriodicAdmissibilityConfig = DEFAULT_ADMISSIBILITY_CONFIG) -> int:
    return len(free_positions(steps, cfg))


def admissible_count(steps: int, cfg: PeriodicAdmissibilityConfig = DEFAULT_ADMISSIBILITY_CONFIG) -> int:
    return 1 << free_count(steps, cfg)


def capacity_ok(steps: int, cfg: PeriodicAdmissibilityConfig = DEFAULT_ADMISSIBILITY_CONFIG) -> bool:
    return free_count(steps, cfg) <= cfg.width


def forced_bit(prefix: list[int], t: int, cfg: PeriodicAdmissibilityConfig = DEFAULT_ADMISSIBILITY_CONFIG) -> int:
    if not is_forced_position(t, cfg):
        raise ValueError("position is not forced")
    # The universe participates through a public phase that changes every period.
    phase = (t // cfg.period) & 1
    return prefix[t - 1] ^ prefix[t - 2] ^ phase


def validate_trajectory(bits: Iterable[int], cfg: PeriodicAdmissibilityConfig = DEFAULT_ADMISSIBILITY_CONFIG) -> bool:
    seq = [int(b) for b in bits]
    if any(b not in (0, 1) for b in seq):
        return False
    for t in range(len(seq)):
        if is_forced_position(t, cfg) and seq[t] != forced_bit(seq, t, cfg):
            return False
    return True


def _time_word(steps: int, cfg: PeriodicAdmissibilityConfig) -> int:
    z = (steps + cfg.universe_seed) & cfg.mask
    z ^= (z << 13) & cfg.mask
    z ^= z >> 7
    z ^= (z << 17) & cfg.mask
    return z & cfg.mask


def _permute(rank: int, steps: int, cfg: PeriodicAdmissibilityConfig) -> int:
    return (rank * cfg.universe_mul + _time_word(steps, cfg)) & cfg.mask


def _unpermute(state: int, steps: int, cfg: PeriodicAdmissibilityConfig) -> int:
    inv = pow(cfg.universe_mul, -1, cfg.modulus)
    return ((state - _time_word(steps, cfg)) * inv) & cfg.mask


def rank_admissible(bits: Iterable[int], cfg: PeriodicAdmissibilityConfig = DEFAULT_ADMISSIBILITY_CONFIG) -> tuple[int, int]:
    seq = [int(b) for b in bits]
    if any(b not in (0, 1) for b in seq):
        raise ValueError("bits must contain only 0 and 1")
    if not validate_trajectory(seq, cfg):
        raise ValueError("trajectory violates the public admissibility law")
    steps = len(seq)
    if not capacity_ok(steps, cfg):
        raise ValueError("admissible family exceeds final-state capacity")
    rank = 0
    for t in free_positions(steps, cfg):
        rank = (rank << 1) | seq[t]
    return rank, steps


def unrank_admissible(rank: int, steps: int, cfg: PeriodicAdmissibilityConfig = DEFAULT_ADMISSIBILITY_CONFIG) -> list[int]:
    if steps < 0:
        raise ValueError("steps must be non-negative")
    if not capacity_ok(steps, cfg):
        raise ValueError("admissible family exceeds final-state capacity")
    f = free_count(steps, cfg)
    if not 0 <= rank < (1 << f):
        raise ValueError("rank outside admissible family")

    free_bits = [(rank >> (f - 1 - i)) & 1 for i in range(f)]
    free_i = 0
    out: list[int] = []
    for t in range(steps):
        if is_forced_position(t, cfg):
            out.append(forced_bit(out, t, cfg))
        else:
            out.append(free_bits[free_i])
            free_i += 1
    return out


def encode_admissible_trajectory(bits: Iterable[int], cfg: PeriodicAdmissibilityConfig = DEFAULT_ADMISSIBILITY_CONFIG) -> tuple[int, int]:
    rank, steps = rank_admissible(bits, cfg)
    return _permute(rank, steps, cfg), steps


def decode_admissible_trajectory(final_state: int, steps: int, cfg: PeriodicAdmissibilityConfig = DEFAULT_ADMISSIBILITY_CONFIG) -> list[int]:
    if not capacity_ok(steps, cfg):
        raise ValueError("admissible family exceeds final-state capacity")
    rank = _unpermute(final_state & cfg.mask, steps, cfg)
    if rank >= admissible_count(steps, cfg):
        raise ValueError("final state is not a valid address for this admissible family")
    return unrank_admissible(rank, steps, cfg)

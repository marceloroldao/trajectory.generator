"""Linear-time reversible trajectory-address experiment.

This module constructs a second machine with a stricter design objective than the
original mixed-state core: recover an arbitrary bit trajectory of length <= state
width from only `(final_state, steps)` in O(steps), without a trajectory log or
search table.

It does this by maintaining a public schedule of occupied deviation coordinates.
The deterministic universe transform permutes all coordinates and XORs a public
time word. At each step, the data bit is injected into a coordinate that is known
to be free of prior data deviation. The decoder recomputes the same public
schedule and universe baseline, reads the injected coordinate, removes it, and
applies the exact inverse universe transform.

This is not compression and the final state is not a cryptographic hash. It is a
reversible trajectory address with a hard capacity of `width` arbitrary bits.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class TrajectoryAddressConfig:
    width: int = 63
    initial_state: int = 0
    universe_seed: int = 0x6D2B79F5

    def __post_init__(self) -> None:
        if not 1 <= self.width <= 64:
            raise ValueError("width must be between 1 and 64")

    @property
    def mask(self) -> int:
        return (1 << self.width) - 1


DEFAULT_ADDRESS_CONFIG = TrajectoryAddressConfig()


def _rotl(x: int, r: int, width: int) -> int:
    mask = (1 << width) - 1
    r %= width
    x &= mask
    if r == 0:
        return x
    return ((x << r) | (x >> (width - r))) & mask


def _rotr(x: int, r: int, width: int) -> int:
    mask = (1 << width) - 1
    r %= width
    x &= mask
    if r == 0:
        return x
    return ((x >> r) | (x << (width - r))) & mask


def _time_word(t: int, cfg: TrajectoryAddressConfig) -> int:
    z = (t + cfg.universe_seed) & cfg.mask
    z ^= (z << 13) & cfg.mask
    z ^= z >> 7
    z ^= (z << 17) & cfg.mask
    return z & cfg.mask


def _rotation(t: int, cfg: TrajectoryAddressConfig) -> int:
    return (7 * t + 3) % cfg.width


def _universe_forward(x: int, t: int, cfg: TrajectoryAddressConfig) -> int:
    return (_rotl(x, _rotation(t, cfg), cfg.width) ^ _time_word(t, cfg)) & cfg.mask


def _universe_inverse(y: int, t: int, cfg: TrajectoryAddressConfig) -> int:
    return _rotr((y ^ _time_word(t, cfg)) & cfg.mask, _rotation(t, cfg), cfg.width)


def _schedule(steps: int, cfg: TrajectoryAddressConfig):
    """Return `(rotation, injection_coordinate, baseline_after_universe)` per step."""
    if steps < 0:
        raise ValueError("steps must be non-negative")
    if steps > cfg.width:
        raise ValueError("arbitrary reversible capacity exceeded: steps > state width")

    occupied: set[int] = set()
    baseline = cfg.initial_state & cfg.mask
    out: list[tuple[int, int, int]] = []

    for t in range(steps):
        r = _rotation(t, cfg)
        occupied_after_rotation = {(p + r) % cfg.width for p in occupied}

        coordinate = next(
            (q for q in range(cfg.width) if q not in occupied_after_rotation),
            None,
        )
        if coordinate is None:
            raise RuntimeError("no free trajectory coordinate")

        baseline = _universe_forward(baseline, t, cfg)
        out.append((r, coordinate, baseline))
        occupied = occupied_after_rotation | {coordinate}

    return out


def encode_trajectory_address(
    bits: Iterable[int],
    cfg: TrajectoryAddressConfig = DEFAULT_ADDRESS_CONFIG,
) -> tuple[int, int]:
    seq = [int(b) for b in bits]
    if any(b not in (0, 1) for b in seq):
        raise ValueError("bits must contain only 0 and 1")
    schedule = _schedule(len(seq), cfg)

    x = cfg.initial_state & cfg.mask
    for t, bit in enumerate(seq):
        _, coordinate, _ = schedule[t]
        x = _universe_forward(x, t, cfg)
        if bit == 1:
            x ^= 1 << coordinate
    return x & cfg.mask, len(seq)


def decode_trajectory_address(
    final_state: int,
    steps: int,
    cfg: TrajectoryAddressConfig = DEFAULT_ADDRESS_CONFIG,
) -> list[int]:
    """Recover the unique trajectory in O(steps) from `(final_state, steps)` only."""
    schedule = _schedule(steps, cfg)
    x = final_state & cfg.mask
    bits = [0] * steps

    for t in range(steps - 1, -1, -1):
        _, coordinate, baseline_after_universe = schedule[t]

        # This coordinate contains no prior data deviation by construction. Therefore
        # actual_bit_at_coordinate XOR public_baseline_bit is exactly the input bit.
        bit = ((x >> coordinate) & 1) ^ ((baseline_after_universe >> coordinate) & 1)
        bits[t] = bit

        if bit == 1:
            x ^= 1 << coordinate
        x = _universe_inverse(x, t, cfg)

    if x != (cfg.initial_state & cfg.mask):
        raise ValueError("invalid final state for the supplied step count/configuration")
    return bits

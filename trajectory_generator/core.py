"""Reversible, time-dependent trajectory dynamics.

The design goal is not cryptographic security. It is to create a compact laboratory
for studying whether ordered state transitions can remain distinguishable from only
(final_state, number_of_steps).

No golden-ratio constant is used by the dynamics.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List


@dataclass(frozen=True)
class MachineConfig:
    width: int = 63
    initial_state: int = 0
    universe_period: int = 3

    # All multipliers are odd, therefore invertible modulo 2**width.
    universe_mul: int = 0x2D
    data1_mul: int = 0x35

    # Arbitrary non-special constants. They are deliberately not derived from phi.
    universe_seed: int = 0x6D2B79F5
    data_seed: int = 0x1B873593

    def __post_init__(self) -> None:
        if not 4 <= self.width <= 64:
            raise ValueError("width must be between 4 and 64")
        if self.universe_period <= 0:
            raise ValueError("universe_period must be positive")
        if self.universe_mul % 2 == 0 or self.data1_mul % 2 == 0:
            raise ValueError("modular multipliers must be odd")

    @property
    def modulus(self) -> int:
        return 1 << self.width

    @property
    def mask(self) -> int:
        return self.modulus - 1


DEFAULT_CONFIG = MachineConfig()


def rotl(x: int, r: int, width: int) -> int:
    mask = (1 << width) - 1
    r %= width
    x &= mask
    if r == 0:
        return x
    return ((x << r) | (x >> (width - r))) & mask


def rotr(x: int, r: int, width: int) -> int:
    mask = (1 << width) - 1
    r %= width
    x &= mask
    if r == 0:
        return x
    return ((x >> r) | (x << (width - r))) & mask


def _time_word(t: int, seed: int, cfg: MachineConfig) -> int:
    """Deterministic time word without using a hash or stored trajectory data."""
    mask = cfg.mask
    z = (t + seed) & mask
    z ^= (z << 13) & mask
    z ^= z >> 7
    z ^= (z << 17) & mask
    return z & mask


def universe_forward(x: int, t: int, cfg: MachineConfig = DEFAULT_CONFIG) -> int:
    """Deterministic universe evolution. Applied independently of the input bit."""
    if t % cfg.universe_period != 0:
        return x & cfg.mask

    k = _time_word(t, cfg.universe_seed, cfg)
    r = (3 * t + 5) % cfg.width

    # Affine modular map followed by rotation and XOR.
    # The inverse exists because universe_mul is odd.
    y = (x * cfg.universe_mul + k) & cfg.mask
    y = rotl(y, r, cfg.width)
    y ^= rotr(k, (t + 1) % cfg.width, cfg.width)
    return y & cfg.mask


def universe_inverse(y: int, t: int, cfg: MachineConfig = DEFAULT_CONFIG) -> int:
    if t % cfg.universe_period != 0:
        return y & cfg.mask

    k = _time_word(t, cfg.universe_seed, cfg)
    r = (3 * t + 5) % cfg.width
    inv_mul = pow(cfg.universe_mul, -1, cfg.modulus)

    x = y ^ rotr(k, (t + 1) % cfg.width, cfg.width)
    x = rotr(x, r, cfg.width)
    x = ((x - k) * inv_mul) & cfg.mask
    return x


def data_forward(x: int, bit: int, t: int, cfg: MachineConfig = DEFAULT_CONFIG) -> int:
    """Data transition.

    bit=0 intentionally leaves the post-universe state unchanged.
    bit=1 applies a reversible non-commutative perturbation.
    """
    if bit not in (0, 1):
        raise ValueError("bit must be 0 or 1")
    if bit == 0:
        return x & cfg.mask

    k = _time_word(t, cfg.data_seed, cfg)
    r = (5 * t + 1) % cfg.width
    y = (x * cfg.data1_mul + k) & cfg.mask
    y ^= rotl(k, (2 * t + 3) % cfg.width, cfg.width)
    y = rotl(y, r, cfg.width)
    return y & cfg.mask


def data_inverse(y: int, bit: int, t: int, cfg: MachineConfig = DEFAULT_CONFIG) -> int:
    if bit not in (0, 1):
        raise ValueError("bit must be 0 or 1")
    if bit == 0:
        return y & cfg.mask

    k = _time_word(t, cfg.data_seed, cfg)
    r = (5 * t + 1) % cfg.width
    inv_mul = pow(cfg.data1_mul, -1, cfg.modulus)

    x = rotr(y, r, cfg.width)
    x ^= rotl(k, (2 * t + 3) % cfg.width, cfg.width)
    x = ((x - k) * inv_mul) & cfg.mask
    return x


def step_forward(x: int, bit: int, t: int, cfg: MachineConfig = DEFAULT_CONFIG) -> int:
    """One complete step: universe first, then data."""
    x = universe_forward(x, t, cfg)
    return data_forward(x, bit, t, cfg)


def step_inverse(y: int, bit: int, t: int, cfg: MachineConfig = DEFAULT_CONFIG) -> int:
    """Exact inverse when the bit is known."""
    y = data_inverse(y, bit, t, cfg)
    return universe_inverse(y, t, cfg)


def encode_bits(
    bits: Iterable[int], cfg: MachineConfig = DEFAULT_CONFIG, *, return_trajectory: bool = False
):
    """Encode an ordered bit trajectory into one final state.

    The returned step count is the number of data bits. The trajectory is returned
    only for diagnostics when explicitly requested and is never required by decoders.
    """
    x = cfg.initial_state & cfg.mask
    trajectory: List[int] = [x]
    count = 0
    for t, bit in enumerate(bits):
        x = step_forward(x, int(bit), t, cfg)
        count += 1
        if return_trajectory:
            trajectory.append(x)
    if return_trajectory:
        return x, count, trajectory
    return x, count


def int_to_bits(value: int, n_bits: int) -> list[int]:
    if value < 0 or value >= (1 << n_bits):
        raise ValueError("value does not fit n_bits")
    return [(value >> shift) & 1 for shift in range(n_bits - 1, -1, -1)]


def bits_to_int(bits: Iterable[int]) -> int:
    value = 0
    for bit in bits:
        if bit not in (0, 1):
            raise ValueError("bits must contain only 0 and 1")
        value = (value << 1) | int(bit)
    return value


def bytes_to_bits(data: bytes) -> list[int]:
    out: list[int] = []
    for byte in data:
        out.extend((byte >> shift) & 1 for shift in range(7, -1, -1))
    return out


def bits_to_bytes(bits: Iterable[int]) -> bytes:
    seq = list(bits)
    if len(seq) % 8:
        raise ValueError("bit length must be a multiple of 8")
    out = bytearray()
    for i in range(0, len(seq), 8):
        out.append(bits_to_int(seq[i : i + 8]))
    return bytes(out)

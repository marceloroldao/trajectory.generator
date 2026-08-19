"""Decoders that use only final state + number of steps.

The exact decoder is intentionally exhaustive. Its purpose is scientific: determine
whether the mapping is injective before optimizing the search procedure.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .core import DEFAULT_CONFIG, MachineConfig, encode_bits, int_to_bits


@dataclass(frozen=True)
class DecodeResult:
    final_state: int
    steps: int
    matches: tuple[tuple[int, ...], ...]
    searched: int

    @property
    def unique(self) -> bool:
        return len(self.matches) == 1

    @property
    def ambiguous(self) -> bool:
        return len(self.matches) > 1

    @property
    def found(self) -> bool:
        return bool(self.matches)

    @property
    def bits(self) -> Optional[list[int]]:
        if not self.unique:
            return None
        return list(self.matches[0])


def decode_exhaustive(
    final_state: int,
    steps: int,
    cfg: MachineConfig = DEFAULT_CONFIG,
    *,
    max_matches: int = 2,
) -> DecodeResult:
    """Recover candidate trajectories from only `(final_state, steps)`.

    `max_matches=2` is enough to distinguish unique from ambiguous while stopping
    early after proving a collision. Set it higher to inspect collision multiplicity.

    Complexity is O(2**steps * steps), so this is a correctness oracle for small
    experiments, not a production decoder.
    """
    if steps < 0:
        raise ValueError("steps must be non-negative")
    if max_matches < 1:
        raise ValueError("max_matches must be >= 1")

    target = final_state & cfg.mask
    matches: list[tuple[int, ...]] = []
    searched = 0

    for value in range(1 << steps):
        bits = int_to_bits(value, steps)
        state, count = encode_bits(bits, cfg)
        searched += 1
        if count == steps and state == target:
            matches.append(tuple(bits))
            if len(matches) >= max_matches:
                break

    return DecodeResult(target, steps, tuple(matches), searched)


def recover_unique(final_state: int, steps: int, cfg: MachineConfig = DEFAULT_CONFIG) -> list[int]:
    """Return the trajectory only if `(final_state, steps)` identifies it uniquely."""
    result = decode_exhaustive(final_state, steps, cfg, max_matches=2)
    if not result.found:
        raise LookupError("no trajectory maps to the supplied final state and step count")
    if result.ambiguous:
        raise ValueError("ambiguous: multiple trajectories produce the same final state")
    assert result.bits is not None
    return result.bits

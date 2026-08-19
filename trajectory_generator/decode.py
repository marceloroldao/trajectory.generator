"""Decoders using only final state + number of steps.

Two exact strategies are provided:

- exhaustive: O(2**n) correctness oracle;
- meet-in-the-middle (MITM): O(2**ceil(n/2)) time and O(2**floor(n/2))
  memory, while preserving the same strict input contract.

Neither decoder receives a trajectory log, checksum, plaintext hint, or side table.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .core import (
    DEFAULT_CONFIG,
    MachineConfig,
    encode_bits,
    int_to_bits,
    step_forward,
    step_inverse,
)


@dataclass(frozen=True)
class DecodeResult:
    final_state: int
    steps: int
    matches: tuple[tuple[int, ...], ...]
    searched: int
    method: str = "unknown"

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


def _validate(steps: int, max_matches: int) -> None:
    if steps < 0:
        raise ValueError("steps must be non-negative")
    if max_matches < 1:
        raise ValueError("max_matches must be >= 1")


def decode_exhaustive(
    final_state: int,
    steps: int,
    cfg: MachineConfig = DEFAULT_CONFIG,
    *,
    max_matches: int = 2,
) -> DecodeResult:
    """Recover candidate trajectories by enumerating all 2**steps bit strings."""
    _validate(steps, max_matches)

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

    return DecodeResult(target, steps, tuple(matches), searched, "exhaustive")


def decode_mitm(
    final_state: int,
    steps: int,
    cfg: MachineConfig = DEFAULT_CONFIG,
    *,
    max_matches: int = 2,
) -> DecodeResult:
    """Exact meet-in-the-middle recovery from `(final_state, steps)` only.

    Split the trajectory at `mid = floor(steps/2)`.

    Forward side:
        enumerate every prefix from the public initial state and record the state at
        time `mid`.

    Backward side:
        enumerate every suffix and apply the exact public inverse transitions from
        the supplied final state back to time `mid`.

    A trajectory is a solution exactly when both sides meet at the same intermediate
    state. No intermediate state is supplied to the decoder; it is discovered by the
    search itself.

    Time:   O(2**ceil(n/2) * n)
    Memory: O(2**floor(n/2))
    """
    _validate(steps, max_matches)
    target = final_state & cfg.mask

    if steps == 0:
        matches = (tuple(),) if target == (cfg.initial_state & cfg.mask) else tuple()
        return DecodeResult(target, 0, matches, 1, "mitm")

    mid = steps // 2
    suffix_len = steps - mid

    # Multiple prefixes may meet at one state in a non-injective prefix frontier.
    forward: dict[int, list[tuple[int, ...]]] = {}
    searched = 0

    for value in range(1 << mid):
        prefix = int_to_bits(value, mid)
        x = cfg.initial_state & cfg.mask
        for t, bit in enumerate(prefix):
            x = step_forward(x, bit, t, cfg)
        forward.setdefault(x, []).append(tuple(prefix))
        searched += 1

    matches: list[tuple[int, ...]] = []

    for value in range(1 << suffix_len):
        suffix = int_to_bits(value, suffix_len)
        x = target

        # Reverse the suffix at its actual absolute times.
        for local in range(suffix_len - 1, -1, -1):
            t = mid + local
            x = step_inverse(x, suffix[local], t, cfg)

        searched += 1
        prefixes = forward.get(x)
        if not prefixes:
            continue

        for prefix in prefixes:
            candidate = prefix + tuple(suffix)

            # Defensive end-to-end verification keeps the decoder auditable even if
            # a future core implementation changes.
            verify_state, verify_steps = encode_bits(candidate, cfg)
            if verify_steps == steps and verify_state == target:
                matches.append(candidate)
                if len(matches) >= max_matches:
                    return DecodeResult(target, steps, tuple(matches), searched, "mitm")

    return DecodeResult(target, steps, tuple(matches), searched, "mitm")


def recover_unique(
    final_state: int,
    steps: int,
    cfg: MachineConfig = DEFAULT_CONFIG,
) -> list[int]:
    """Return the unique trajectory using the MITM decoder.

    Raises rather than guessing when no trajectory exists or multiple trajectories
    produce the same `(final_state, steps)` pair.
    """
    result = decode_mitm(final_state, steps, cfg, max_matches=2)
    if not result.found:
        raise LookupError("no trajectory maps to the supplied final state and step count")
    if result.ambiguous:
        raise ValueError("ambiguous: multiple trajectories produce the same final state")
    assert result.bits is not None
    return result.bits

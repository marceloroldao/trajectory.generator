"""Decoders using only final state + number of steps.

Exact strategies:

- exhaustive: O(2**n) correctness oracle;
- meet-in-the-middle (MITM): O(2**ceil(n/2)) time and O(2**floor(n/2)) memory;
- partitioned MITM: exact recovery with a tunable memory/time tradeoff.

No decoder receives a trajectory log, checksum, plaintext hint, or side table.
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


def _forward_prefix_state(prefix: list[int], cfg: MachineConfig) -> int:
    x = cfg.initial_state & cfg.mask
    for t, bit in enumerate(prefix):
        x = step_forward(x, bit, t, cfg)
    return x


def _backward_suffix_state(
    target: int,
    suffix: list[int],
    mid: int,
    cfg: MachineConfig,
) -> int:
    x = target & cfg.mask
    for local in range(len(suffix) - 1, -1, -1):
        t = mid + local
        x = step_inverse(x, suffix[local], t, cfg)
    return x


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
    """Exact meet-in-the-middle recovery from `(final_state, steps)` only."""
    _validate(steps, max_matches)
    target = final_state & cfg.mask

    if steps == 0:
        matches = (tuple(),) if target == (cfg.initial_state & cfg.mask) else tuple()
        return DecodeResult(target, 0, matches, 1, "mitm")

    mid = steps // 2
    suffix_len = steps - mid

    forward: dict[int, list[tuple[int, ...]]] = {}
    searched = 0

    for value in range(1 << mid):
        prefix = int_to_bits(value, mid)
        x = _forward_prefix_state(prefix, cfg)
        forward.setdefault(x, []).append(tuple(prefix))
        searched += 1

    matches: list[tuple[int, ...]] = []

    for value in range(1 << suffix_len):
        suffix = int_to_bits(value, suffix_len)
        x = _backward_suffix_state(target, suffix, mid, cfg)
        searched += 1
        prefixes = forward.get(x)
        if not prefixes:
            continue

        for prefix in prefixes:
            candidate = prefix + tuple(suffix)
            verify_state, verify_steps = encode_bits(candidate, cfg)
            if verify_steps == steps and verify_state == target:
                matches.append(candidate)
                if len(matches) >= max_matches:
                    return DecodeResult(target, steps, tuple(matches), searched, "mitm")

    return DecodeResult(target, steps, tuple(matches), searched, "mitm")


def decode_mitm_partitioned(
    final_state: int,
    steps: int,
    cfg: MachineConfig = DEFAULT_CONFIG,
    *,
    partition_bits: int = 8,
    max_matches: int = 2,
) -> DecodeResult:
    """Exact MITM with bounded memory by midpoint-state partitioning.

    The midpoint state is partitioned by its low `partition_bits`. For each bucket,
    only matching forward prefixes are retained in memory; backward suffixes are then
    searched for that same bucket. This introduces no side information: the bucket is
    derived from the candidate midpoint state generated during decoding.

    Peak forward-memory is reduced by roughly 2**partition_bits for well-mixed states,
    while time increases by approximately that factor because suffixes are revisited
    per bucket. The method remains exact and auditable.
    """
    _validate(steps, max_matches)
    if partition_bits < 0:
        raise ValueError("partition_bits must be non-negative")
    if partition_bits > cfg.width:
        raise ValueError("partition_bits cannot exceed state width")

    target = final_state & cfg.mask
    if steps == 0:
        matches = (tuple(),) if target == (cfg.initial_state & cfg.mask) else tuple()
        return DecodeResult(target, 0, matches, 1, "mitm-partitioned")

    if partition_bits == 0:
        result = decode_mitm(target, steps, cfg, max_matches=max_matches)
        return DecodeResult(result.final_state, result.steps, result.matches, result.searched, "mitm-partitioned")

    mid = steps // 2
    suffix_len = steps - mid
    bucket_mask = (1 << partition_bits) - 1
    bucket_count = 1 << partition_bits
    matches: list[tuple[int, ...]] = []
    searched = 0

    for bucket in range(bucket_count):
        forward: dict[int, list[tuple[int, ...]]] = {}

        for value in range(1 << mid):
            prefix = int_to_bits(value, mid)
            x = _forward_prefix_state(prefix, cfg)
            searched += 1
            if (x & bucket_mask) == bucket:
                forward.setdefault(x, []).append(tuple(prefix))

        if not forward:
            continue

        for value in range(1 << suffix_len):
            suffix = int_to_bits(value, suffix_len)
            x = _backward_suffix_state(target, suffix, mid, cfg)
            searched += 1
            if (x & bucket_mask) != bucket:
                continue

            prefixes = forward.get(x)
            if not prefixes:
                continue

            for prefix in prefixes:
                candidate = prefix + tuple(suffix)
                verify_state, verify_steps = encode_bits(candidate, cfg)
                if verify_steps == steps and verify_state == target:
                    matches.append(candidate)
                    if len(matches) >= max_matches:
                        return DecodeResult(
                            target,
                            steps,
                            tuple(matches),
                            searched,
                            "mitm-partitioned",
                        )

    return DecodeResult(target, steps, tuple(matches), searched, "mitm-partitioned")


def recover_unique(
    final_state: int,
    steps: int,
    cfg: MachineConfig = DEFAULT_CONFIG,
) -> list[int]:
    """Return the unique trajectory using the exact MITM decoder."""
    result = decode_mitm(final_state, steps, cfg, max_matches=2)
    if not result.found:
        raise LookupError("no trajectory maps to the supplied final state and step count")
    if result.ambiguous:
        raise ValueError("ambiguous: multiple trajectories produce the same final state")
    assert result.bits is not None
    return result.bits

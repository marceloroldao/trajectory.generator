"""Streaming colex trajectory address.

This module is an operational refinement of hierarchical_trajectory.py.

The admissible family is unchanged: binary trajectories with at most K changes.
The difference is mechanical. Instead of ranking/unranking the complete set of
change positions in one batch, this codec maintains a public combinatorial
address after every physical step.

For a sparse event set S subset {1..n} with |S|=r, use colex rank

    C(S) = sum(C(s_i - 1, i), i=1..r)

and place exact-r subsets inside public count buckets. Colex has a useful online
property: appending the new largest position n+1 adds exactly C(n, r+1).

In reverse, for a state with r events among n positions, the newest position n
is present iff the within-bucket colex rank is >= C(n-1, r).

Thus each reverse step decides the newest branch using only the current address,
the public step count, and K. No trajectory table or full combination unrank is
required.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import comb
from typing import Iterable


@dataclass(frozen=True)
class StreamingColexConfig:
    width: int = 63
    max_changes: int = 5

    def __post_init__(self) -> None:
        if self.width < 1:
            raise ValueError("width must be >= 1")
        if self.max_changes < 0:
            raise ValueError("max_changes must be >= 0")

    @property
    def modulus(self) -> int:
        return 1 << self.width


DEFAULT_STREAMING_COLEX_CONFIG = StreamingColexConfig()


def _sparse_count(n: int, k: int) -> int:
    if n < 0:
        raise ValueError("n must be >= 0")
    if k < 0:
        return 0
    return sum(comb(n, j) for j in range(min(k, n) + 1))


def admissible_count(
    steps: int,
    cfg: StreamingColexConfig = DEFAULT_STREAMING_COLEX_CONFIG,
) -> int:
    """Number of length-steps binary trajectories with <=K changes."""
    if steps < 0:
        raise ValueError("steps must be >= 0")
    if steps == 0:
        return 1
    return 2 * _sparse_count(steps - 1, cfg.max_changes)


def capacity_ok(
    steps: int,
    cfg: StreamingColexConfig = DEFAULT_STREAMING_COLEX_CONFIG,
) -> bool:
    return admissible_count(steps, cfg) <= cfg.modulus


def _bucket_offset(n: int, k: int, r: int) -> int:
    if not 0 <= r <= min(k, n):
        raise ValueError("event count outside sparse family")
    return sum(comb(n, j) for j in range(r))


def _pack_sparse(colex: int, n: int, k: int, r: int) -> int:
    bucket = comb(n, r)
    if not 0 <= colex < bucket:
        raise ValueError("colex rank outside exact-count bucket")
    return _bucket_offset(n, k, r) + colex


def _unpack_sparse(address: int, n: int, k: int) -> tuple[int, int]:
    total = _sparse_count(n, k)
    if not 0 <= address < total:
        raise ValueError("sparse address outside admissible family")
    remaining = address
    for r in range(min(k, n) + 1):
        bucket = comb(n, r)
        if remaining < bucket:
            return r, remaining
        remaining -= bucket
    raise AssertionError("unreachable sparse bucket")


def _sparse_forward(address: int, n: int, k: int, event: int) -> int:
    r, colex = _unpack_sparse(address, n, k)
    if event not in (0, 1):
        raise ValueError("event must be 0 or 1")

    if event:
        if r >= k:
            raise ValueError("change budget exhausted")
        r_new = r + 1
        colex_new = colex + comb(n, r_new)
    else:
        r_new = r
        colex_new = colex

    return _pack_sparse(colex_new, n + 1, k, r_new)


def _sparse_reverse(address: int, n: int, k: int) -> tuple[int, int]:
    if n < 1:
        raise ValueError("n must be >= 1")
    r, colex = _unpack_sparse(address, n, k)

    # Exact-r combinations not containing newest position n occupy
    # [0, C(n-1,r)); those containing n occupy the remaining suffix.
    threshold = comb(n - 1, r) if r <= n - 1 else 0
    if r > 0 and colex >= threshold:
        event = 1
        r_prev = r - 1
        colex_prev = colex - threshold
    else:
        event = 0
        r_prev = r
        colex_prev = colex

    return _pack_sparse(colex_prev, n - 1, k, r_prev), event


def _unpack_full(
    state: int,
    steps: int,
    cfg: StreamingColexConfig,
) -> tuple[int, int]:
    if steps == 0:
        if state != 0:
            raise ValueError("empty trajectory has only state 0")
        return 0, 0

    block = _sparse_count(steps - 1, cfg.max_changes)
    total = 2 * block
    if not 0 <= state < total:
        raise ValueError("state outside admissible family")
    initial = 1 if state >= block else 0
    sparse = state - initial * block
    return initial, sparse


def _pack_full(
    initial: int,
    sparse: int,
    steps: int,
    cfg: StreamingColexConfig,
) -> int:
    if steps == 0:
        if initial != 0 or sparse != 0:
            raise ValueError("empty trajectory has only state 0")
        return 0
    if initial not in (0, 1):
        raise ValueError("initial bit must be 0 or 1")

    block = _sparse_count(steps - 1, cfg.max_changes)
    if not 0 <= sparse < block:
        raise ValueError("sparse component outside admissible family")
    state = initial * block + sparse
    if state >= cfg.modulus:
        raise ValueError("state exceeds configured width")
    return state


def current_bit(
    state: int,
    steps: int,
    cfg: StreamingColexConfig = DEFAULT_STREAMING_COLEX_CONFIG,
) -> int:
    if steps <= 0:
        raise ValueError("current bit is undefined for empty trajectory")
    initial, sparse = _unpack_full(state, steps, cfg)
    r, _ = _unpack_sparse(sparse, steps - 1, cfg.max_changes)
    return initial ^ (r & 1)


def forward_step(
    state: int,
    steps: int,
    bit: int,
    cfg: StreamingColexConfig = DEFAULT_STREAMING_COLEX_CONFIG,
) -> tuple[int, int]:
    """Append one bit and return (new_state, new_steps)."""
    if bit not in (0, 1):
        raise ValueError("bit must be 0 or 1")
    if steps < 0:
        raise ValueError("steps must be >= 0")
    if not capacity_ok(steps + 1, cfg):
        raise ValueError("next prefix exceeds configured state capacity")

    if steps == 0:
        if state != 0:
            raise ValueError("empty trajectory has only state 0")
        return bit, 1

    initial, sparse = _unpack_full(state, steps, cfg)
    r, _ = _unpack_sparse(sparse, steps - 1, cfg.max_changes)
    previous_bit = initial ^ (r & 1)
    change = previous_bit ^ bit

    sparse_new = _sparse_forward(
        sparse,
        steps - 1,
        cfg.max_changes,
        change,
    )
    return _pack_full(initial, sparse_new, steps + 1, cfg), steps + 1


def reverse_step(
    state: int,
    steps: int,
    cfg: StreamingColexConfig = DEFAULT_STREAMING_COLEX_CONFIG,
) -> tuple[int, int, int, int]:
    """Remove the newest bit.

    Returns:
        (predecessor_state, predecessor_steps, recovered_bit, change_event)
    """
    if steps <= 0:
        raise ValueError("cannot reverse an empty trajectory")
    if not capacity_ok(steps, cfg):
        raise ValueError("trajectory family exceeds configured state capacity")

    if steps == 1:
        if state not in (0, 1):
            raise ValueError("invalid one-bit state")
        return 0, 0, state, 0

    initial, sparse = _unpack_full(state, steps, cfg)
    r, _ = _unpack_sparse(sparse, steps - 1, cfg.max_changes)
    recovered_bit = initial ^ (r & 1)

    sparse_prev, change = _sparse_reverse(
        sparse,
        steps - 1,
        cfg.max_changes,
    )
    predecessor = _pack_full(initial, sparse_prev, steps - 1, cfg)
    return predecessor, steps - 1, recovered_bit, change


def encode(
    bits: Iterable[int],
    cfg: StreamingColexConfig = DEFAULT_STREAMING_COLEX_CONFIG,
) -> tuple[int, int]:
    state = 0
    steps = 0
    for bit in bits:
        state, steps = forward_step(state, steps, int(bit), cfg)
    return state, steps


def decode(
    final_state: int,
    steps: int,
    cfg: StreamingColexConfig = DEFAULT_STREAMING_COLEX_CONFIG,
) -> list[int]:
    if steps < 0:
        raise ValueError("steps must be >= 0")
    if steps == 0:
        if final_state != 0:
            raise ValueError("empty trajectory has only state 0")
        return []

    current = final_state
    n = steps
    out = [0] * steps
    for i in range(steps - 1, -1, -1):
        current, n, bit, _ = reverse_step(current, n, cfg)
        out[i] = bit

    if current != 0 or n != 0:
        raise AssertionError("reverse did not return to origin")
    return out

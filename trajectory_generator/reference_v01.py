"""Frozen trajectory.generator v0.1 reference core.

Public API:
    count(T)
    rank(path)
    unrank(address, T)
    append(address, T, z)
    access(address, T, k)

A path contains a 3-bit initial prefix followed by T transition labels.
This module is intentionally self-contained and does not import experiments.
It implements the frozen 4-bit private-state law, exact interval-conditioned
matrix counts, and the jointly ranked dyadic forest address.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Iterable, Sequence

LIMIT63 = 1 << 63


def _initial_topology(state: int) -> int:
    oldest = (state >> 2) & 1
    middle = (state >> 1) & 1
    newest = state & 1
    r1 = oldest ^ middle
    r2 = middle ^ newest
    return (oldest << 2) | (r1 << 1) | r2


def initial_private(state: int) -> tuple[int, int, int, int]:
    q = _initial_topology(state)
    return ((state >> 2) & 1, (q >> 0) & 1, (q >> 1) & 1, (q >> 2) & 1)


def allowed(p: tuple[int, int, int, int], z: int, phase: int) -> bool:
    r0, r1, r2, r3 = p
    if z not in (0, 1):
        return False
    if phase == 0:
        v = (1 ^ r0 ^ r3 ^ z ^ (r0&r2) ^ (r0&z) ^ (r2&r3) ^
             (r2&z) ^ (r3&z) ^ (r0&r2&z) ^ (r1&r2&z) ^
             (r1&r3&z) ^ (r0&r1&r3&z) ^ (r1&r2&r3&z) ^
             (r0&r1&r2&r3&z))
    elif phase == 1:
        v = (r1 ^ r3 ^ (r1&r3) ^ (r3&z) ^ (r1&r2&z) ^
             (r1&r3&z) ^ (r1&r2&r3&z))
    elif phase == 2:
        v = (r2 ^ (r0&r1) ^ (r1&r3) ^ (r1&z) ^ (r2&z) ^
             (r0&r1&r2) ^ (r0&r1&r3) ^ (r0&r2&r3) ^
             (r1&r2&r3) ^ (r1&r2&r3&z))
    else:
        raise ValueError("phase must be 0, 1, or 2")
    return bool(v & 1)


def step(p: tuple[int, int, int, int], z: int, phase: int) -> tuple[int, int, int, int]:
    if z not in (0, 1):
        raise ValueError("z must be 0 or 1")
    r0, r1, r2, r3 = p
    n0 = r0 ^ r2
    n2 = r1
    n3 = r2
    if phase == 0:
        n1 = 1 ^ r0 ^ r3 ^ z ^ (r1&r2)
    elif phase == 1:
        n1 = r1 ^ r3 ^ z ^ (r0&r1) ^ (r1&r2) ^ (r0&r1&r2)
    elif phase == 2:
        n1 = r0 ^ r3 ^ z
    else:
        raise ValueError("phase must be 0, 1, or 2")
    return (n0&1, n1&1, n2&1, n3&1)


STATES = tuple((a,b,c,d) for a in (0,1) for b in (0,1) for c in (0,1) for d in (0,1))
STATE_INDEX = {p:i for i,p in enumerate(STATES)}
INIT = tuple(sorted(initial_private(s) for s in range(8)))
INITIAL_TO_PREFIX = {initial_private(s): s for s in range(8)}
NSTATE = len(STATES)


def _eye():
    return tuple(tuple(int(i == j) for j in range(NSTATE)) for i in range(NSTATE))


def _mm(a, b):
    return tuple(
        tuple(sum(a[i][k] * b[k][j] for k in range(NSTATE)) for j in range(NSTATE))
        for i in range(NSTATE)
    )


def _phase_matrix(ph: int):
    out = [[0] * NSTATE for _ in range(NSTATE)]
    for p in STATES:
        for z in (0, 1):
            if allowed(p, z, ph):
                out[STATE_INDEX[p]][STATE_INDEX[step(p, z, ph)]] += 1
    return tuple(tuple(row) for row in out)


_PHASE = tuple(_phase_matrix(ph) for ph in range(3))
_CYCLE = tuple(_mm(_mm(_PHASE[ph], _PHASE[(ph+1)%3]), _PHASE[(ph+2)%3]) for ph in range(3))


def _mpow(base, n: int):
    out = _eye()
    while n:
        if n & 1:
            out = _mm(out, base)
        base = _mm(base, base)
        n >>= 1
    return out


@lru_cache(maxsize=None)
def _interval_matrix(t0: int, t1: int):
    if t0 < 0 or t1 < t0:
        raise ValueError("require 0 <= t0 <= t1")
    length = t1 - t0
    q, r = divmod(length, 3)
    ph = t0 % 3
    out = _mpow(_CYCLE[ph], q)
    for j in range(r):
        out = _mm(out, _PHASE[(ph+j)%3])
    return out


def paths_count(t0: int, t1: int, starts: Sequence[tuple], ends: Sequence[tuple]) -> int:
    m = _interval_matrix(t0, t1)
    return sum(m[STATE_INDEX[s]][STATE_INDEX[e]] for s in starts for e in ends)


def count(T: int) -> int:
    if T < 0:
        raise ValueError("T must be >= 0")
    return paths_count(0, T, INIT, STATES)


def _block_lengths(T: int):
    return tuple(1 << i for i in range(T.bit_length()-1, -1, -1) if (T >> i) & 1)


def _block_intervals(T: int):
    out = []
    t = 0
    for L in _block_lengths(T):
        out.append((t, t+L))
        t += L
    assert t == T
    return tuple(out)


def _enumerate_edges(t0: int, starts: Sequence[tuple], ends: Sequence[tuple]):
    E = set(ends)
    ph = t0 % 3
    out = []
    for s in sorted(starts):
        for z in (0, 1):
            if allowed(s, z, ph):
                q = step(s, z, ph)
                if q in E:
                    out.append((s, z, q))
    return out


def _block_info(t0: int, t1: int, starts: Sequence[tuple], ends: Sequence[tuple]):
    mid = (t0 + t1) // 2
    out = []
    off = 0
    for p in STATES:
        lc = paths_count(t0, mid, starts, (p,))
        if not lc:
            continue
        rc = paths_count(mid, t1, (p,), ends)
        if not rc:
            continue
        size = lc * rc
        out.append((off, off+size, p, lc, rc))
        off += size
    assert off == paths_count(t0, t1, starts, ends)
    return mid, out


@dataclass(frozen=True)
class _Block:
    t0: int
    t1: int
    start: tuple[int,int,int,int]
    end: tuple[int,int,int,int]
    rank: int

    @property
    def length(self) -> int:
        return self.t1 - self.t0


def _rank_segment(states, zs, t0, t1, starts, ends):
    L = t1 - t0
    if L == 0:
        return 0
    if L == 1:
        target = (states[t0], zs[t0], states[t1])
        return _enumerate_edges(t0, starts, ends).index(target)
    mid, blocks = _block_info(t0, t1, starts, ends)
    pm = states[mid]
    for lo, hi, p, lc, rc in blocks:
        if p == pm:
            lr = _rank_segment(states, zs, t0, mid, starts, (p,))
            rr = _rank_segment(states, zs, mid, t1, (p,), ends)
            return lo + lr * rc + rr
    raise AssertionError("midpoint state not rankable")


def _merge_blocks(left: _Block, right: _Block) -> _Block:
    if not (left.t1 == right.t0 and left.end == right.start and left.length == right.length):
        raise ValueError("blocks are not merge-compatible")
    mid = left.end
    _, blocks = _block_info(left.t0, right.t1, (left.start,), (right.end,))
    for lo, hi, p, lc, rc in blocks:
        if p == mid:
            return _Block(left.t0, right.t1, left.start, right.end, lo + left.rank * rc + right.rank)
    raise AssertionError("merge midpoint not found")


def _decode_block_bit(block: _Block, k: int):
    if not block.t0 <= k < block.t1:
        raise IndexError(k)
    t0, t1 = block.t0, block.t1
    starts, ends = (block.start,), (block.end,)
    r = block.rank
    while t1 - t0 > 1:
        mid, blocks = _block_info(t0, t1, starts, ends)
        for lo, hi, p, lc, rc in blocks:
            if lo <= r < hi:
                rem = r - lo
                lr, rr = divmod(rem, rc)
                if k < mid:
                    t1, ends, r = mid, (p,), lr
                else:
                    t0, starts, r = mid, (p,), rr
                break
        else:
            raise AssertionError("block rank outside decomposition")
    return _enumerate_edges(t0, starts, ends)[r][1]


def _build_forest(path: Sequence[int]):
    if len(path) < 3:
        raise ValueError("path must contain the 3-bit initial prefix")
    if any(int(b) not in (0,1) for b in path):
        raise ValueError("path must contain only bits")
    s = (int(path[0]) << 2) | (int(path[1]) << 1) | int(path[2])
    p = initial_private(s)
    states = [p]
    zs = [int(z) for z in path[3:]]
    for t, z in enumerate(zs):
        if not allowed(p, z, t % 3):
            raise ValueError(f"inadmissible transition at t={t}")
        p = step(p, z, t % 3)
        states.append(p)
    forest = []
    for t, z in enumerate(zs):
        edge_rank = _enumerate_edges(t, (states[t],), (states[t+1],)).index((states[t], z, states[t+1]))
        forest.append(_Block(t, t+1, states[t], states[t+1], edge_rank))
        while len(forest) >= 2 and forest[-1].length == forest[-2].length:
            right = forest.pop(); left = forest.pop()
            forest.append(_merge_blocks(left, right))
    return s, forest


@lru_cache(maxsize=None)
def _suffix_count(T: int, j: int, p: tuple) -> int:
    ints = _block_intervals(T)
    if j == len(ints):
        return 1
    t0, t1 = ints[j]
    return sum(paths_count(t0, t1, (p,), (q,)) * _suffix_count(T, j+1, q) for q in STATES)


def _rank_forest(prefix: int, forest: Sequence[_Block], T: int) -> int:
    ints = _block_intervals(T)
    if len(forest) != len(ints):
        raise ValueError("forest shape does not match T")
    p0 = initial_private(prefix)
    rank_value = 0
    for p in INIT:
        c = _suffix_count(T, 0, p)
        if p == p0:
            break
        rank_value += c
    else:
        raise ValueError("invalid initial prefix")
    p = p0
    for j, b in enumerate(forest):
        t0, t1 = ints[j]
        if (b.t0, b.t1, b.start) != (t0, t1, p):
            raise ValueError("non-canonical forest")
        for q in STATES:
            local_n = paths_count(t0, t1, (p,), (q,))
            if not local_n:
                continue
            tail = _suffix_count(T, j+1, q)
            if q == b.end:
                if not 0 <= b.rank < local_n:
                    raise ValueError("local rank outside block")
                rank_value += b.rank * tail
                p = q
                break
            rank_value += local_n * tail
        else:
            raise AssertionError("endpoint not rankable")
    return rank_value


def _unrank_forest(address: int, T: int):
    total = count(T)
    if not 0 <= address < total:
        raise ValueError("address outside time slice")
    if T == 0:
        p = INIT[address]
        return INITIAL_TO_PREFIX[p], []
    r = address
    p0 = None
    for p in INIT:
        c = _suffix_count(T, 0, p)
        if r < c:
            p0 = p
            break
        r -= c
    assert p0 is not None
    prefix = INITIAL_TO_PREFIX[p0]
    p = p0
    forest = []
    for j, (t0, t1) in enumerate(_block_intervals(T)):
        for q in STATES:
            local_n = paths_count(t0, t1, (p,), (q,))
            if not local_n:
                continue
            tail = _suffix_count(T, j+1, q)
            size = local_n * tail
            if r < size:
                local_rank, r = divmod(r, tail)
                forest.append(_Block(t0, t1, p, q, local_rank))
                p = q
                break
            r -= size
        else:
            raise AssertionError("unrank block failed")
    assert r == 0
    return prefix, forest


def rank(path: Iterable[int]) -> int:
    seq = tuple(int(x) for x in path)
    prefix, forest = _build_forest(seq)
    return _rank_forest(prefix, forest, len(seq)-3)


def unrank(address: int, T: int) -> list[int]:
    prefix, forest = _unrank_forest(int(address), int(T))
    out = [(prefix >> 2) & 1, (prefix >> 1) & 1, prefix & 1]
    for k in range(T):
        for b in forest:
            if b.t0 <= k < b.t1:
                out.append(_decode_block_bit(b, k))
                break
        else:
            raise AssertionError("missing block for position")
    return out


def access(address: int, T: int, k: int) -> int:
    if not 0 <= k < T:
        raise IndexError(k)
    _, forest = _unrank_forest(int(address), int(T))
    for b in forest:
        if b.t0 <= k < b.t1:
            return _decode_block_bit(b, k)
    raise AssertionError("missing block")


def append(address: int, T: int, z: int) -> int:
    prefix, forest = _unrank_forest(int(address), int(T))
    p = initial_private(prefix) if T == 0 else forest[-1].end
    ph = T % 3
    if not allowed(p, int(z), ph):
        raise ValueError("inadmissible transition")
    q = step(p, int(z), ph)
    leaf = _Block(T, T+1, p, q, 0)
    work = list(forest) + [leaf]
    while len(work) >= 2 and work[-1].length == work[-2].length:
        right = work.pop(); left = work.pop()
        work.append(_merge_blocks(left, right))
    return _rank_forest(prefix, work, T+1)


def address_bits(T: int) -> int:
    n = count(T)
    return 0 if n <= 1 else (n-1).bit_length()


__all__ = ["count", "rank", "unrank", "append", "access", "address_bits", "paths_count"]

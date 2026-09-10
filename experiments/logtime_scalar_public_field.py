"""Evaluate the scalar public field directly from time in O(log n).

The growth scalar obeys
    g[n+3] = 2 g[n+2] - g[n+1] + g[n]
with (g0,g1,g2)=(1,0,0).

For S_n=[g_n,g_{n+1},g_{n+2}]^T,
    S_{n+1} = K S_n
with companion matrix
        [0  1  0]
    K = [0  0  1]
        [1 -1  2].

Binary exponentiation gives S_n=K^n S_0 in O(log n), so the public count
field at arbitrary physical time t can be reconstructed from t alone without
walking from zero or retaining modal history.
"""
from __future__ import annotations

from functools import lru_cache
import random

from scalar_public_field import (
    g as g_linear,
    scalar_counts_at,
    STATES,
    M,
    TRANS0,
    PLUS0,
    PLUSN,
    MINUS0,
    MINUSN,
    GBASE,
    INITIAL_TO_PREFIX,
    state_offsets,
    opts,
)
from standalone_four_bit_codec import initial_private, allowed, step

K = (
    (0, 1, 0),
    (0, 0, 1),
    (1, -1, 2),
)
I3 = (
    (1, 0, 0),
    (0, 1, 0),
    (0, 0, 1),
)
S0 = (1, 0, 0)


def mm3(a, b):
    return tuple(
        tuple(sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3))
        for i in range(3)
    )


def mv3(a, v):
    return tuple(sum(a[i][j] * v[j] for j in range(3)) for i in range(3))


def mpow3(base, n: int):
    if n < 0:
        raise ValueError("n must be >= 0")
    out = I3
    while n:
        if n & 1:
            out = mm3(out, base)
        base = mm3(base, base)
        n >>= 1
    return out


@lru_cache(maxsize=None)
def scalar_triplet_fast(n: int):
    if n < 0:
        raise ValueError("n must be >= 0")
    return mv3(mpow3(K, n), S0)


@lru_cache(maxsize=None)
def g_fast(n: int) -> int:
    return scalar_triplet_fast(n)[0]


def fast_growth_amplitudes(n: int):
    gn, gn1, gn2 = scalar_triplet_fast(n)
    return gn, gn2 - 2 * gn1, gn1


def vadd(*vs):
    return [sum(v[i] for v in vs) for i in range(len(vs[0]))]


def vscale(c, v):
    return [c * x for x in v]


@lru_cache(maxsize=None)
def fast_counts_at(t: int):
    if t < 0:
        raise ValueError("t must be >= 0")
    n, r = divmod(t, 3)
    a, b, c = fast_growth_amplitudes(n)
    growth = vadd(vscale(a, GBASE[0]), vscale(b, GBASE[1]), vscale(c, GBASE[2]))
    plus = vadd(PLUS0, vscale(n, PLUSN))
    minus = vscale((-1) ** n, vadd(MINUS0, vscale(-n, MINUSN)))
    trans = TRANS0 if n == 0 else [0] * 16
    v = vadd(trans, plus, minus, growth)
    assert all(x.denominator == 1 and x >= 0 for x in v)
    v = [int(x) for x in v]
    for ph in range(r):
        v = [sum(M[ph][i][j] * v[j] for j in range(16)) for i in range(16)]
        assert all(x.denominator == 1 for x in v)
        v = [int(x) for x in v]
    return {STATES[i]: v[i] for i in range(16) if v[i]}


def unpack_global(a, t):
    c = fast_counts_at(t)
    offs, total = state_offsets(c)
    if not 0 <= a < total:
        raise ValueError
    for p in sorted(c):
        if a < offs[p] + c[p]:
            return p, a - offs[p]
    raise AssertionError


def pack_global(p, r, t):
    c = fast_counts_at(t)
    offs, _ = state_offsets(c)
    if p not in c or not 0 <= r < c[p]:
        raise ValueError
    return offs[p] + r


def incoming_blocks(q, tprev):
    c = fast_counts_at(tprev)
    phase = tprev % 3
    off = 0
    out = []
    for p in sorted(c):
        for z in opts(p, phase):
            if step(p, z, phase) == q:
                out.append((off, off + c[p], p, z, c[p]))
                off += c[p]
    return out


def forward_address(a, z, t):
    p, r = unpack_global(a, t)
    ph = t % 3
    if not allowed(p, z, ph):
        raise ValueError
    q = step(p, z, ph)
    for lo, hi, pp, zz, _ in incoming_blocks(q, t):
        if pp == p and zz == z:
            return pack_global(q, lo + r, t + 1)
    raise AssertionError


def decode_address(a, T):
    p, r = unpack_global(a, T)
    zs = []
    for tp in range(T - 1, -1, -1):
        hit = None
        for lo, hi, pp, z, _ in incoming_blocks(p, tp):
            if lo <= r < hi:
                hit = (pp, z, r - lo)
                break
        if hit is None:
            raise AssertionError
        p, z, r = hit
        zs.append(z)
    assert p in INITIAL_TO_PREFIX and r == 0
    s = INITIAL_TO_PREFIX[p]
    return [(s >> 2) & 1, (s >> 1) & 1, s & 1] + list(reversed(zs))


def encode_path(path):
    s = (path[0] << 2) | (path[1] << 1) | path[2]
    p = initial_private(s)
    a = pack_global(p, 0, 0)
    for t, z in enumerate(path[3:]):
        a = forward_address(a, int(z), t)
    return a, len(path) - 3


def main():
    # Exact equivalence against the O(n) recurrence across a broad range.
    for n in range(1000):
        assert g_fast(n) == g_linear(n), n
    print('fast_scalar_identity_0_999 ok')

    # Large direct lookup: no iteration from zero in the implementation.
    n = 10000
    a, b, c = scalar_triplet_fast(n)
    assert c == 2 * b - a + scalar_triplet_fast(n - 1)[2]
    print('direct_triplet_n10000_bitlengths', tuple(abs(x).bit_length() for x in (a, b, c)))
    print('complexity O(log n) matrix squarings')

    # Exact count-field equality at all times used by the codec frontier.
    for t in range(221):
        assert fast_counts_at(t) == scalar_counts_at(t), t
    print('fast_count_field_equivalence_0_220 ok')

    rng = random.Random(20260910)
    for T in range(10):
        total = sum(fast_counts_at(T).values())
        for addr in range(total):
            path = decode_address(addr, T)
            aa, tt = encode_path(path)
            assert aa == addr and tt == T
        print('exhaustive_fast_roundtrip', T, total, 'ok')

    for T in (16, 64, 128, 200, 218):
        total = sum(fast_counts_at(T).values())
        for _ in range(200):
            addr = rng.randrange(total)
            path = decode_address(addr, T)
            aa, tt = encode_path(path)
            assert aa == addr and tt == T
        print('random_fast_roundtrip', T, 200, 'ok')

    n218 = sum(fast_counts_at(218).values())
    n219 = sum(fast_counts_at(219).values())
    print('count218', n218)
    print('count219', n219)
    assert n218 == 9131204053820206208
    assert n219 == 10214739716735776832
    print('public_lookup_contract: counts(t) from time alone in O(log t)')


if __name__ == '__main__':
    main()

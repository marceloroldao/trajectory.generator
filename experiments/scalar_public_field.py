"""Collapse the 3 live growth amplitudes to one scalar recurrence.

For the growth-sector update
    (a,b,c) -> (c, a-c, b+2c)
let g_n := a_n. Then
    c_n = g_{n+1}
    b_n = g_{n+2} - 2 g_{n+1}
and every coordinate satisfies
    g_{n+3} = 2 g_{n+2} - g_{n+1} + g_n,
with g_0=1, g_1=0, g_2=0.

Because n=floor(t/3) is public, the three amplitudes need not be stored as
independent state: they can be reconstructed exactly from time and this fixed
recurrence. This experiment replaces growth_amplitudes() with the scalar law
and demands exact count-field and codec equivalence through the 63-bit
frontier.
"""
from __future__ import annotations

from functools import lru_cache
import random

from modal_horizon_free_address import (
    STATES, M, TRANS0, PLUS0, PLUSN, MINUS0, MINUSN, GBASE,
    INITIAL_TO_PREFIX, state_offsets, opts, vadd, vscale,
)
from standalone_four_bit_codec import initial_private, allowed, step
from horizon_free_endpoint_rank import counts_at as dp_counts_at


@lru_cache(maxsize=None)
def g(n: int) -> int:
    if n < 0:
        raise ValueError("n must be >= 0")
    if n == 0:
        return 1
    if n in (1, 2):
        return 0
    a, b, c = 1, 0, 0
    for _ in range(n - 2):
        a, b, c = b, c, 2*c - b + a
    return c


def scalar_growth_amplitudes(n: int):
    gn = g(n)
    gn1 = g(n + 1)
    gn2 = g(n + 2)
    # From a_{n+1}=c_n and a_{n+2}=b_n+2c_n.
    return gn, gn2 - 2*gn1, gn1


def phase0_vector_scalar(n: int):
    a, b, c = scalar_growth_amplitudes(n)
    growth = vadd(vscale(a, GBASE[0]), vscale(b, GBASE[1]), vscale(c, GBASE[2]))
    plus = vadd(PLUS0, vscale(n, PLUSN))
    minus = vscale((-1)**n, vadd(MINUS0, vscale(-n, MINUSN)))
    trans = TRANS0 if n == 0 else [0]*16
    out = vadd(trans, plus, minus, growth)
    assert all(x.denominator == 1 and x >= 0 for x in out)
    return [int(x) for x in out]


@lru_cache(maxsize=None)
def scalar_counts_at(t: int):
    if t < 0:
        raise ValueError
    n, r = divmod(t, 3)
    v = phase0_vector_scalar(n)
    for ph in range(r):
        v = [sum(M[ph][i][j]*v[j] for j in range(16)) for i in range(16)]
        assert all(x.denominator == 1 for x in v)
        v = [int(x) for x in v]
    return {STATES[i]: v[i] for i in range(16) if v[i]}


def unpack_global(a, t):
    c = scalar_counts_at(t)
    offs, total = state_offsets(c)
    if not 0 <= a < total:
        raise ValueError
    for p in sorted(c):
        if a < offs[p] + c[p]:
            return p, a - offs[p]
    raise AssertionError


def pack_global(p, r, t):
    c = scalar_counts_at(t)
    offs, _ = state_offsets(c)
    if p not in c or not 0 <= r < c[p]:
        raise ValueError
    return offs[p] + r


def incoming_blocks(q, tprev):
    c = scalar_counts_at(tprev)
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
    # Scalar identity versus original three-amplitude recurrence.
    from modal_horizon_free_address import growth_amplitudes
    for n in range(0, 100):
        assert scalar_growth_amplitudes(n) == tuple(int(x) for x in growth_amplitudes(n)), n
    print('scalar_amplitude_identity_0_99 ok')
    print('scalar_recurrence g[n+3]=2g[n+2]-g[n+1]+g[n]')
    print('g_0_12', [g(i) for i in range(13)])

    # Exact count-field equality for every physical time through 220.
    for t in range(221):
        assert scalar_counts_at(t) == dp_counts_at(t), t
    print('scalar_count_field_equivalence_0_220 ok')

    # End-to-end codec validation.
    rng = random.Random(20260910)
    for T in range(10):
        total = sum(scalar_counts_at(T).values())
        for a in range(total):
            path = decode_address(a, T)
            aa, tt = encode_path(path)
            assert aa == a and tt == T
        print('exhaustive_scalar_roundtrip', T, total, 'ok')

    for T in (16, 64, 128, 200, 218):
        total = sum(scalar_counts_at(T).values())
        for _ in range(200):
            a = rng.randrange(total)
            path = decode_address(a, T)
            aa, tt = encode_path(path)
            assert aa == a and tt == T
        print('random_scalar_roundtrip', T, 200, 'ok')

    n218 = sum(scalar_counts_at(218).values())
    n219 = sum(scalar_counts_at(219).values())
    print('count218', n218)
    print('count219', n219)
    assert n218 == 9131204053820206208
    assert n219 == 10214739716735776832
    print('public_dynamic_state_required: time only; scalar modes are deterministic functions of t')


if __name__ == '__main__':
    main()

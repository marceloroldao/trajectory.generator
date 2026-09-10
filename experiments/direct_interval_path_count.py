"""Direct interval-conditioned path counts from fixed laws only.

This isolates the quantity used by hierarchical/joint-dyadic ranking:
    paths_count(t0,t1,start,end)

No trajectory history and no DP over [0,t0) are required.  Because the
transition law is 3-periodic, an interval is represented by a fixed 16x16
matrix product.  Full 3-step cycles are exponentiated by squaring, giving
O(log (t1-t0)) matrix multiplications (plus big-integer arithmetic).

The experiment cross-checks direct interval counts against an independent
step-by-step DP for many phases, lengths and endpoint pairs, then verifies the
218/219 frontier.
"""
from __future__ import annotations
from functools import lru_cache
import random

from standalone_four_bit_codec import initial_private, allowed, step

STATES=tuple((a,b,c,d) for a in (0,1) for b in (0,1) for c in (0,1) for d in (0,1))
IDX={p:i for i,p in enumerate(STATES)}
N=16
INIT=tuple(sorted(initial_private(s) for s in range(8)))
ALL=STATES


def eye():
    return tuple(tuple(int(i==j) for j in range(N)) for i in range(N))


def mm(a,b):
    return tuple(tuple(sum(a[i][k]*b[k][j] for k in range(N)) for j in range(N)) for i in range(N))


def phase_matrix(ph):
    out=[[0]*N for _ in range(N)]
    for p in STATES:
        for z in (0,1):
            if allowed(p,z,ph):
                out[IDX[p]][IDX[step(p,z,ph)]] += 1
    return tuple(tuple(r) for r in out)

A=tuple(phase_matrix(ph) for ph in range(3))


def cycle_matrix(start_phase):
    # Row-vector convention: v' = v A0 A1 A2.
    return mm(mm(A[start_phase],A[(start_phase+1)%3]),A[(start_phase+2)%3])

C=tuple(cycle_matrix(ph) for ph in range(3))


def mpow(base,n):
    out=eye()
    while n:
        if n&1: out=mm(out,base)
        base=mm(base,base); n//=2
    return out


@lru_cache(maxsize=None)
def interval_matrix(t0:int,t1:int):
    if t1<t0: raise ValueError
    length=t1-t0
    q,r=divmod(length,3)
    ph=t0%3
    out=mpow(C[ph],q)
    for j in range(r):
        out=mm(out,A[(ph+j)%3])
    return out


def direct_paths_count(t0,t1,starts,ends):
    M=interval_matrix(t0,t1)
    return sum(M[IDX[s]][IDX[e]] for s in starts for e in ends)


def dp_paths_count(t0,t1,starts,ends):
    v={p:0 for p in STATES}
    for p in starts:v[p]+=1
    for t in range(t0,t1):
        nv={p:0 for p in STATES}
        for p,c in v.items():
            if not c:continue
            for z in (0,1):
                if allowed(p,z,t%3):nv[step(p,z,t%3)]+=c
        v=nv
    return sum(v[e] for e in ends)


def main():
    rng=random.Random(20260910)
    # Exhaust endpoint pairs over representative lengths/phases.
    for t0 in range(6):
        for L in list(range(0,25)) + [32,64,127,128,200,218]:
            t1=t0+L
            for s in STATES:
                for e in STATES:
                    a=direct_paths_count(t0,t1,(s,),(e,))
                    b=dp_paths_count(t0,t1,(s,),(e,))
                    assert a==b,(t0,t1,s,e,a,b)
    print('direct_interval_endpoint_equivalence ok')

    # Random endpoint subsets.
    for _ in range(500):
        t0=rng.randrange(0,50); L=rng.randrange(0,219); t1=t0+L
        starts=tuple(p for p in STATES if rng.randrange(2)) or (rng.choice(STATES),)
        ends=tuple(p for p in STATES if rng.randrange(2)) or (rng.choice(STATES),)
        assert direct_paths_count(t0,t1,starts,ends)==dp_paths_count(t0,t1,starts,ends)
    print('direct_interval_subset_equivalence 500 ok')

    n218=direct_paths_count(0,218,INIT,ALL)
    n219=direct_paths_count(0,219,INIT,ALL)
    assert n218==9131204053820206208
    assert n219==10214739716735776832
    print('count218',n218,'bits',n218.bit_length())
    print('count219',n219,'bits',n219.bit_length())
    print('interval_count_inputs_only: t0,t1,start/end sets,fixed transition law')
    print('matrix_multiplication_complexity: O(log interval_length), excluding bigint cost')

if __name__=='__main__':main()

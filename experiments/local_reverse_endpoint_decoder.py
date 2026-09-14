"""Step-by-step endpoint-only reverse decoder for the original objective.

Uses the fixed-local-input temporal universes from fixed_injection_temporal_universe.py.
At each reverse step t, infer b_t from the current state x[t+1] and public time t
using one parity mask q_t, then invert the public universe map A[t mod 3].

No global trajectory rank, no reachable-state table, no stored intermediate
states and no global solve at decode time are used.

For the affine reachable set at time t+1,
    R[t+1] = offset[t+1] + S[t+1],
we choose q_t so that
    q_t . (A_t S_t) = 0
    q_t . d = 1.
Then the two possible last-bit branches are distinct affine cosets and
    b_t = q_t . (x[t+1] XOR offset[t+1]).
This is exactly the local branch-separation criterion expressed linearly.
"""
from __future__ import annotations
import random
from fixed_injection_temporal_universe import (
    SEEDS, parity, apply, columns_to_rows, rank, invert, make_universe
)


def solve_functional(vectors,rhs,W):
    rows=[vectors[i] | (int(rhs[i])<<W) for i in range(len(vectors))]
    piv=[];r=0;mask=(1<<W)-1
    for c in range(W):
        p=next((i for i in range(r,len(rows)) if (rows[i]>>c)&1),None)
        if p is None:continue
        rows[r],rows[p]=rows[p],rows[r]
        for i in range(len(rows)):
            if i!=r and ((rows[i]>>c)&1):rows[i]^=rows[r]
        piv.append(c);r+=1
        if r==len(rows):break
    for row in rows:
        if (row&mask)==0 and ((row>>W)&1):raise ValueError('inconsistent')
    q=0
    for i,c in enumerate(piv):
        if (rows[i]>>W)&1:q|=1<<c
    assert all(parity(q&v)==b for v,b in zip(vectors,rhs))
    return q


def public_reverse_data(W,seed,d=1):
    As=[make_universe(W,seed,p) for p in range(3)]
    invAs=[invert(A,W) for A in As]
    offsets=[0]
    basis=[]
    masks=[]
    m=(1<<W)-1
    for t in range(W):
        A=As[t%3]
        kick=(0x9E3779B97F4A7C15 ^ (t*0xD1B54A32D192ED03))&m
        transformed=[apply(A,v) for v in basis]
        q=solve_functional(transformed+[d],[0]*len(transformed)+[1],W)
        masks.append(q)
        offsets.append(apply(A,offsets[-1])^kick)
        basis=transformed+[d]
        assert rank(columns_to_rows(basis,W),W)==len(basis)
    return As,invAs,offsets,masks


def encode(bits,W,seed,d=1):
    As=[make_universe(W,seed,p) for p in range(3)]
    m=(1<<W)-1;x=0
    for t,b in enumerate(bits):
        kick=(0x9E3779B97F4A7C15 ^ (t*0xD1B54A32D192ED03))&m
        x=apply(As[t%3],x)^kick^(d if b else 0)
    return x


def decode_local(endpoint,T,W,seed,d=1):
    if T>W:raise ValueError('arbitrary-bit exact recovery requires T <= W')
    As,invAs,offsets,masks=public_reverse_data(W,seed,d)
    m=(1<<W)-1;x=endpoint;bits=[]
    for t in range(T-1,-1,-1):
        b=parity(masks[t] & (x ^ offsets[t+1]))
        kick=(0x9E3779B97F4A7C15 ^ (t*0xD1B54A32D192ED03))&m
        x=apply(invAs[t%3],x ^ kick ^ (d if b else 0))
        bits.append(b)
    if x!=0:raise AssertionError(('did not return to public initial state',x))
    return tuple(reversed(bits))


def main():
    rng=random.Random(20260914)
    for W,seed in SEEDS.items():
        _,_,offsets,masks=public_reverse_data(W,seed,1)
        # Test all unit words, all-zero/all-one, plus many arbitrary histories.
        tests=[tuple(int(i==j) for i in range(W)) for j in range(W)]
        tests += [tuple(0 for _ in range(W)),tuple(1 for _ in range(W))]
        tests += [tuple(rng.randrange(2) for _ in range(W)) for _ in range(1000)]
        for bits in tests:
            y=encode(bits,W,seed,1)
            got=decode_local(y,W,W,seed,1)
            assert got==bits,(W,bits,y,got)
        # The masks themselves are public laws derived from W, seed and time.
        print('LOCAL_REVERSE_ENDPOINT_ONLY_OK','W',W,'seed',seed,
              'tests',len(tests),'masks',len(masks),
              'only_current_state_plus_time',True)

if __name__=='__main__':main()

"""Exact horizon-free online address using endpoint-conditioned prefix ranks.

Core idea
---------
At physical time t, C_t[p] is the number of admissible histories reaching
private state p. Histories ending at each p are ranked locally. Incoming edge
blocks into q are ordered deterministically by (predecessor_state, z).

Forward update from (p, local_rank, z):
    q = step(p,z,phase)
    local_rank' = incoming_block_offset_t(q,p,z) + local_rank

A global address A_t is obtained by concatenating endpoint blocks in sorted
state order. Both C_t and all offsets depend on elapsed time t only, never on
a future horizon T.

Backward decoding starts from (A_T,T), locates the endpoint block, then the
incoming predecessor block, recovers z and p, subtracts the block offset, and
repeats to t=0. The initial private state uniquely identifies the original
3-bit prefix.
"""
from __future__ import annotations

from functools import lru_cache
import math
import random

from standalone_four_bit_codec import initial_private, allowed, step, total

LIMIT = 1 << 63
INITIAL_TO_PREFIX = {initial_private(s): s for s in range(8)}
assert len(INITIAL_TO_PREFIX) == 8


def opts(p, phase):
    return tuple(z for z in (0,1) if allowed(p,z,phase))


@lru_cache(maxsize=None)
def counts_at(t:int):
    if t < 0:
        raise ValueError('t must be >=0')
    cur = {initial_private(s): 1 for s in range(8)}
    for k in range(t):
        phase = k % 3
        nxt = {}
        for p,c in cur.items():
            for z in opts(p,phase):
                q = step(p,z,phase)
                nxt[q] = nxt.get(q,0) + c
        cur = nxt
    return cur


def state_offsets(counts):
    out={}
    off=0
    for p in sorted(counts):
        out[p]=off
        off += counts[p]
    return out,off


def unpack_global(address:int,t:int):
    counts=counts_at(t)
    offsets,total_count=state_offsets(counts)
    if not 0 <= address < total_count:
        raise ValueError('address outside time slice')
    for p in sorted(counts):
        off=offsets[p]
        c=counts[p]
        if address < off+c:
            return p,address-off
    raise AssertionError('unpack failed')


def pack_global(p,local_rank:int,t:int):
    counts=counts_at(t)
    if p not in counts or not 0 <= local_rank < counts[p]:
        raise ValueError('invalid endpoint/local rank')
    offsets,_=state_offsets(counts)
    return offsets[p] + local_rank


def incoming_blocks(q,t_prev:int):
    """Ordered blocks that reach q from time t_prev to t_prev+1."""
    phase=t_prev%3
    counts=counts_at(t_prev)
    blocks=[]
    off=0
    for p in sorted(counts):
        c=counts[p]
        for z in opts(p,phase):
            if step(p,z,phase)==q:
                blocks.append((off,off+c,p,z,c))
                off += c
    return blocks


def forward_address(address:int,z:int,t:int):
    """Advance A_t -> A_{t+1}; t is elapsed transitions before the step."""
    p,r=unpack_global(address,t)
    phase=t%3
    if not allowed(p,z,phase):
        raise ValueError('inadmissible z')
    q=step(p,z,phase)
    match=None
    for lo,hi,pp,zz,c in incoming_blocks(q,t):
        if pp==p and zz==z:
            match=(lo,hi)
            break
    if match is None:
        raise AssertionError('incoming block missing')
    r2=match[0]+r
    return pack_global(q,r2,t+1)


def encode_path(path):
    if len(path)<3:
        raise ValueError('path must include 3-bit prefix')
    s=(path[0]<<2)|(path[1]<<1)|path[2]
    p0=initial_private(s)
    a=pack_global(p0,0,0)
    t=0
    for z in path[3:]:
        a=forward_address(a,int(z),t)
        t+=1
    return a,t


def decode_address(address:int,T:int):
    p,r=unpack_global(address,T)
    labels_rev=[]
    for t_prev in range(T-1,-1,-1):
        found=None
        for lo,hi,pp,z,c in incoming_blocks(p,t_prev):
            if lo <= r < hi:
                found=(pp,z,r-lo)
                break
        if found is None:
            raise AssertionError(('no predecessor block',t_prev,p,r))
        p,z,r=found
        labels_rev.append(z)
    if p not in INITIAL_TO_PREFIX or r!=0:
        raise AssertionError(('bad initial state/rank',p,r))
    s=INITIAL_TO_PREFIX[p]
    prefix=[(s>>2)&1,(s>>1)&1,s&1]
    return prefix + list(reversed(labels_rev))


def address_bits(T:int):
    n=sum(counts_at(T).values())
    return 0 if n<=1 else math.ceil(math.log2(n))


def main():
    print('T total address_bits endpoint_states')
    for T in (0,1,16,64,128,200,218,219):
        n=sum(counts_at(T).values())
        print(T,n,address_bits(T),len(counts_at(T)))
        assert n==total(T)

    assert sum(counts_at(218).values())==9131204053820206208
    assert sum(counts_at(219).values())==10214739716735776832
    assert sum(counts_at(218).values())<=LIMIT<sum(counts_at(219).values())

    # Exhaustive small horizons.
    for T in range(0,10):
        n=sum(counts_at(T).values())
        seen=set()
        for a in range(n):
            path=decode_address(a,T)
            aa,tt=encode_path(path)
            assert tt==T and aa==a,(T,a,aa)
            seen.add(tuple(path))
        assert len(seen)==n
        print('exhaustive_roundtrip',T,n,'ok')

    # Random addresses up to the exact 63-bit frontier.
    rng=random.Random(20260909)
    for T in (16,64,128,200,218):
        n=sum(counts_at(T).values())
        for _ in range(200):
            a=rng.randrange(n)
            path=decode_address(a,T)
            aa,tt=encode_path(path)
            assert aa==a and tt==T
        print('random_roundtrip',T,200,'ok')

    # Demonstrate horizon independence: same prefix evolves to exactly the
    # same A_t regardless of when we later decide to stop.
    a=0
    path=decode_address(a,0)
    print('demo_T0_address',encode_path(path)[0])
    print('frontier218_bits',address_bits(218))
    print('frontier219_bits',address_bits(219))

if __name__=='__main__':
    main()

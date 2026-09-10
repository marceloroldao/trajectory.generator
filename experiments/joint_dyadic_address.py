"""Jointly ranked dyadic address: one integer, online-updatable, random-access friendly.

The dyadic forest experiment proved that keeping each block rank plus a raw
4-bit endpoint can require 80 bits at T=218.  That overhead is artificial:
endpoint choices and local ranks are correlated.  This experiment enumerates
all admissible dyadic-forest descriptions *jointly*.

For T, the block lengths are the powers of two in the binary decomposition of
T, ordered from largest to smallest.  A description is:
  initial private state p0,
  for each block j: endpoint p_{j+1} and rank r_j among paths from p_j to
  p_{j+1} over that block interval.

Suffix dynamic programming counts how many complete descriptions continue from
any boundary state.  Lexicographic ranking over (next endpoint, local rank)
therefore gives a bijection [0,N(T)) without storing endpoints separately.

Random access: unrank only the O(log T) block chain, select the block containing
k, then descend its hierarchical rank in O(log block_length).

Online update: from the current joint address at T, unrank its O(log T) forest,
append one length-1 transition, perform binary carries/merges, and rerank the
new forest.  No full trajectory reconstruction is used.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import math, random

from hierarchical_random_access_address import STATES, INIT, ALL, paths_count
from dyadic_online_forest import Block, build_forest, merge_blocks, decode_block_bit
from standalone_four_bit_codec import initial_private, allowed, step

STATE_INDEX={p:i for i,p in enumerate(STATES)}
INITIAL_TO_PREFIX={initial_private(s):s for s in range(8)}


def block_lengths(T:int):
    return tuple(1<<i for i in range(T.bit_length()-1,-1,-1) if (T>>i)&1)


def block_intervals(T:int):
    out=[];t=0
    for L in block_lengths(T):out.append((t,t+L));t+=L
    assert t==T
    return tuple(out)


@lru_cache(maxsize=None)
def suffix_count(T:int,j:int,p:tuple)->int:
    """Number of dyadic forest suffixes from boundary p at block index j."""
    ints=block_intervals(T)
    if j==len(ints):return 1
    t0,t1=ints[j]
    return sum(paths_count(t0,t1,(p,),(q,))*suffix_count(T,j+1,q) for q in STATES)


def total_count(T:int)->int:
    if T==0:return len(INIT)
    return sum(suffix_count(T,0,p) for p in INIT)


def rank_forest(prefix:int,forest:list[Block],T:int)->int:
    ints=block_intervals(T)
    assert len(forest)==len(ints)
    p0=initial_private(prefix)
    assert p0 in INIT
    rank=0
    # initial-state blocks
    for p in INIT:
        c=suffix_count(T,0,p)
        if p==p0:break
        rank+=c
    else:raise AssertionError

    p=p0
    for j,b in enumerate(forest):
        t0,t1=ints[j]
        assert (b.t0,b.t1,b.start)==(t0,t1,p)
        target=b.end
        # Choices are ordered by endpoint q, then local path rank within p->q.
        for q in STATES:
            local_n=paths_count(t0,t1,(p,),(q,))
            if not local_n:continue
            tail=suffix_count(T,j+1,q)
            if q==target:
                assert 0<=b.rank<local_n
                rank += b.rank*tail
                p=q
                break
            rank += local_n*tail
        else:raise AssertionError(('endpoint not rankable',j,target))
    return rank


def unrank_forest(rank:int,T:int):
    total=total_count(T)
    if not 0<=rank<total:raise ValueError('rank outside time slice')
    if T==0:
        p=INIT[rank];s=INITIAL_TO_PREFIX[p]
        return s,[]
    # initial state
    p0=None
    for p in INIT:
        c=suffix_count(T,0,p)
        if rank<c:p0=p;break
        rank-=c
    assert p0 is not None
    prefix=INITIAL_TO_PREFIX[p0]
    p=p0;forest=[]
    for j,(t0,t1) in enumerate(block_intervals(T)):
        found=False
        for q in STATES:
            local_n=paths_count(t0,t1,(p,),(q,))
            if not local_n:continue
            tail=suffix_count(T,j+1,q)
            size=local_n*tail
            if rank<size:
                local_rank,rank=divmod(rank,tail)
                forest.append(Block(t0,t1,p,q,local_rank));p=q;found=True;break
            rank-=size
        if not found:raise AssertionError(('unrank block failed',j))
    assert rank==0
    return prefix,forest


def path_to_joint(prefix_bits,zs):
    s=(prefix_bits[0]<<2)|(prefix_bits[1]<<1)|prefix_bits[2]
    _,_,forest=build_forest(prefix_bits,zs)
    return rank_forest(s,forest,len(zs))


def joint_bit_at(rank:int,T:int,k:int):
    if not 0<=k<T:raise IndexError
    _,forest=unrank_forest(rank,T)
    for b in forest:
        if b.t0<=k<b.t1:return decode_block_bit(b,k)
    raise AssertionError


def append_joint(rank:int,T:int,z:int):
    """A_T,z -> A_{T+1}, rebuilding only O(log T) dyadic blocks."""
    s,forest=unrank_forest(rank,T)
    if T==0:
        p=initial_private(s)
    else:
        p=forest[-1].end
    ph=T%3
    if not allowed(p,z,ph):raise ValueError('inadmissible transition')
    q=step(p,z,ph)
    # Fixed endpoints over one step imply a unique edge in this automaton.
    leaf=Block(T,T+1,p,q,0)
    forest=list(forest)+[leaf]
    while len(forest)>=2 and forest[-1].length==forest[-2].length:
        r=forest.pop();l=forest.pop();forest.append(merge_blocks(l,r))
    return rank_forest(s,forest,T+1)


def decode_prefix_and_labels(rank:int,T:int):
    """Reference decode through dyadic blocks, for validation only."""
    s,forest=unrank_forest(rank,T)
    pref=[(s>>2)&1,(s>>1)&1,s&1]
    zs=[joint_bit_at(rank,T,k)[0] for k in range(T)]
    return pref,zs


def main():
    # Counts must be exactly the original language.
    expected218=9131204053820206208
    expected219=10214739716735776832
    for T in range(0,219):
        # paths_count over INIT -> ALL is the independent language count.
        assert total_count(T)==paths_count(0,T,INIT,ALL),T
    assert total_count(218)==expected218 and total_count(219)==expected219
    print('joint_counts_0_219 ok')
    print('count218',total_count(218),'bits',total_count(218).bit_length())
    print('count219',total_count(219),'bits',total_count(219).bit_length())

    # Exhaustive bijection + online update for small horizons.
    for T in range(0,9):
        n=total_count(T)
        seen=set()
        for r in range(n):
            s,forest=unrank_forest(r,T)
            rr=rank_forest(s,forest,T)
            assert rr==r
            seen.add((s,tuple((b.end,b.rank) for b in forest)))
            if T<8:
                p=initial_private(s) if T==0 else forest[-1].end
                for z in (0,1):
                    if allowed(p,z,T%3):
                        r2=append_joint(r,T,z)
                        s2,f2=unrank_forest(r2,T+1)
                        assert s2==s and f2[-1].end==step(p,z,T%3)
        assert len(seen)==n
        print('exhaustive_joint',T,n,'ok')

    rng=random.Random(20260910)
    for T in (16,64,128,200,218):
        n=total_count(T);maxdepth=0
        for _ in range(200):
            r=rng.randrange(n)
            s,f=unrank_forest(r,T)
            assert rank_forest(s,f,T)==r
            for _ in range(12):
                k=rng.randrange(T);z,d=joint_bit_at(r,T,k);maxdepth=max(maxdepth,d)
                # cross-check by reference block lookup
                for b in f:
                    if b.t0<=k<b.t1:
                        assert decode_block_bit(b,k)[0]==z;break
        print('random_joint',T,'samples',200,'max_bit_depth',maxdepth,'blocks',len(block_lengths(T)))

    # Online construction from random paths; compare final joint rank by direct forest rank.
    for T in (16,64,128,218):
        for _ in range(100):
            s=rng.randrange(8);p=initial_private(s);pref=[(s>>2)&1,(s>>1)&1,s&1]
            r=rank_forest(s,[],0)
            zs=[]
            for t in range(T):
                opts=[z for z in (0,1) if allowed(p,z,t%3)];z=rng.choice(opts);zs.append(z)
                r=append_joint(r,t,z);p=step(p,z,t%3)
            rd=path_to_joint(pref,zs)
            assert r==rd
        print('online_joint',T,100,'ok')

    print('T218_serialized_bits_exact',math.ceil(math.log2(total_count(218))))
    print('fits_63_exact',total_count(218)<=(1<<63))
    print('random_access_blocks',block_lengths(218))
    print('interpretation: endpoints and local ranks are jointly enumerated; no separate endpoint overhead')

if __name__=='__main__':main()

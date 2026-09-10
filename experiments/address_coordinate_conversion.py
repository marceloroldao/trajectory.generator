"""Analyze direct conversion between endpoint/colex and hierarchical ranks.

Goals:
1. Quantify midpoint-state fragmentation inside endpoint/colex rank blocks.
2. Provide an exact streaming conversion baseline that does not materialize the
   whole path, while measuring its unavoidable one-step predecessor work.
3. Test whether a state-only logarithmic block conversion is plausible.

The two ranks enumerate the same admissible finite-state language but use very
 different orders.  Endpoint rank is causal/online; hierarchical rank is
 midpoint-recursive/random-access friendly.
"""
from __future__ import annotations

from collections import defaultdict
from functools import lru_cache
import random

from horizon_free_endpoint_rank import (
    counts_at, state_offsets, unpack_global, incoming_blocks, INITIAL_TO_PREFIX,
)
from hierarchical_random_access_address import (
    paths_count, INIT, ALL, rank_path, unrank_path,
)
from standalone_four_bit_codec import step


def endpoint_predecessor(address:int,t:int):
    """One exact inverse endpoint-rank step: A_t -> (A_{t-1}, z_{t-1})."""
    if t<=0: raise ValueError
    p,r=unpack_global(address,t)
    for lo,hi,pp,z,_ in incoming_blocks(p,t-1):
        if lo <= r < hi:
            rprev=r-lo
            cprev=counts_at(t-1)
            offs,_=state_offsets(cprev)
            return offs[pp]+rprev,z,pp
    raise AssertionError


def endpoint_mid_state(address:int,T:int,m:int):
    """Resolve the state at time m by exact endpoint reversal; count steps."""
    if not 0<=m<=T:raise ValueError
    a=address;steps=0
    if T==0:
        p,_=unpack_global(a,0);return p,0
    p,_=unpack_global(a,T)
    for t in range(T,m,-1):
        a,z,p=endpoint_predecessor(a,t);steps+=1
    return p,steps


def intervals(vals):
    """Contiguous index intervals for equal values in a sequence."""
    by=defaultdict(list)
    if not vals:return by
    start=0;cur=vals[0]
    for i in range(1,len(vals)+1):
        if i==len(vals) or vals[i]!=cur:
            by[cur].append((start,i));
            if i<len(vals):start=i;cur=vals[i]
    return by


def fragmentation(T:int):
    """Exact fragmentation of midpoint states in global endpoint rank order."""
    m=T//2
    total=sum(counts_at(T).values())
    vals=[]
    for a in range(total):
        p,_=endpoint_mid_state(a,T,m)
        vals.append(p)
    by=intervals(vals)
    nintervals=sum(len(v) for v in by.values())
    max_per=max((len(v) for v in by.values()),default=0)
    return total,m,len(by),nintervals,max_per


def endpoint_to_hierarchical_streaming(address:int,T:int):
    """Exact baseline conversion using reverse streaming, no path object decode.

    We collect transition labels because rank_path currently consumes them; the
    predecessor walk itself is online/streaming and can be wired into a future
    hierarchical accumulator.  Cost counter makes the O(T) nature explicit.
    """
    if T<0:raise ValueError
    if T==0:
        p,r=unpack_global(address,0);assert r==0
        s=INITIAL_TO_PREFIX[p]
        pref=[(s>>2)&1,(s>>1)&1,s&1]
        return rank_path(pref,[]),0
    a=address;rev=[];steps=0
    for t in range(T,0,-1):
        a,z,p=endpoint_predecessor(a,t);rev.append(z);steps+=1
    p0,r0=unpack_global(a,0);assert r0==0
    s=INITIAL_TO_PREFIX[p0];pref=[(s>>2)&1,(s>>1)&1,s&1]
    R=rank_path(pref,list(reversed(rev)))
    return R,steps


def hierarchical_to_endpoint_streaming(rank:int,T:int):
    """Reference inverse conversion, currently via hierarchical unrank + online endpoint encode."""
    from horizon_free_endpoint_rank import encode_path
    pref,zs=unrank_path(rank,T)
    a,t=encode_path(pref+list(zs));assert t==T
    return a,T


def main():
    # Exact permutation/bijection small horizons.
    for T in range(0,9):
        total=sum(counts_at(T).values())
        seen=set()
        for a in range(total):
            r,steps=endpoint_to_hierarchical_streaming(a,T)
            aa,_=hierarchical_to_endpoint_streaming(r,T)
            assert aa==a
            seen.add(r)
            assert steps==T
        assert seen==set(range(total))
        print('conversion_bijection',T,total,'ok')

    # Fragmentation is expensive to enumerate, so keep exact scan to horizons
    # where the language remains small.
    print('T total mid states intervals max_intervals_per_state')
    first_extra=None
    for T in range(1,19):
        total,m,states,nint,mx=fragmentation(T)
        print(T,total,m,states,nint,mx)
        if first_extra is None and nint>states:first_extra=(T,total,m,states,nint,mx)
    print('first_fragmentation',first_extra)

    # Sample full-frontier conversion correctness/cost.
    rng=random.Random(20260910)
    T=218;total=sum(counts_at(T).values())
    for _ in range(50):
        a=rng.randrange(total)
        r,steps=endpoint_to_hierarchical_streaming(a,T)
        aa,_=hierarchical_to_endpoint_streaming(r,T)
        assert aa==a and steps==T
    print('frontier_conversion_samples',50,'ok')
    print('endpoint_to_hierarchical_predecessor_steps',T)
    print('state_only_OlogT_direct_conversion_candidate', 'no' if first_extra else 'undetermined')
    print('interpretation: coordinate conversion is a nontrivial rank permutation; current exact baseline is O(T)')

if __name__=='__main__':main()

"""Hierarchical reversible trajectory address with random symbol access.

The existing endpoint/colex rank is excellent for online accumulation but its
multi-step predecessor blocks are not contiguous by midpoint state.  This
experiment changes only the *enumeration/order* of the same admissible paths.

For a segment [l,r], split at m=floor((l+r)/2).  Paths are grouped by the
private state P_m.  Inside each midpoint block, the Cartesian product

    paths(left boundary set -> P_m) x paths(P_m -> right boundary set)

is ranked as left_rank * right_count + right_rank.

This gives a bijection [0,N(T)) <-> admissible trajectories and lets z_k be
recovered by descending only the half containing k.  The recursion has
O(log T) levels.  Segment path counts come from the fixed 3-periodic transition
matrices; with cold binary matrix powers the arithmetic work is O(log^2 T),
and with cached public interval matrices repeated queries have O(log T) tree
work.
"""
from __future__ import annotations

from functools import lru_cache
import random

from standalone_four_bit_codec import initial_private, allowed, step
from logtime_scalar_public_field import fast_counts_at

STATES=tuple((a,b,c,d) for a in (0,1) for b in (0,1) for c in (0,1) for d in (0,1))
IDX={p:i for i,p in enumerate(STATES)}
N=len(STATES)
INIT=tuple(sorted(initial_private(s) for s in range(8)))
ALL=STATES


def eye():
    return tuple(tuple(1 if i==j else 0 for j in range(N)) for i in range(N))

def mm(a,b):
    return tuple(tuple(sum(a[i][k]*b[k][j] for k in range(N)) for j in range(N)) for i in range(N))

def phase_matrix(ph):
    a=[[0]*N for _ in range(N)]
    for p in STATES:
        i=IDX[p]
        for z in (0,1):
            if allowed(p,z,ph):
                q=step(p,z,ph);a[i][IDX[q]]+=1
    return tuple(tuple(r) for r in a)
A=tuple(phase_matrix(ph) for ph in range(3))

@lru_cache(maxsize=None)
def mpow(a_key,n):
    ph=a_key
    base=mm(A[ph],mm(A[(ph+1)%3],A[(ph+2)%3]))
    out=eye()
    while n:
        if n&1:out=mm(out,base)
        base=mm(base,base);n//=2
    return out

@lru_cache(maxsize=None)
def segment_matrix(phase,length):
    if length<0:raise ValueError
    q,r=divmod(length,3)
    out=mpow(phase,q)
    ph=(phase+3*q)%3
    for j in range(r):out=mm(out,A[(ph+j)%3])
    return out


def paths_count(t0,t1,starts,ends):
    if t1<t0:raise ValueError
    M=segment_matrix(t0%3,t1-t0)
    return sum(M[IDX[s]][IDX[e]] for s in starts for e in ends)


def enumerate_edges(t0,starts,ends):
    out=[];ph=t0%3;E=set(ends)
    for s in sorted(starts):
        for z in (0,1):
            if allowed(s,z,ph):
                q=step(s,z,ph)
                if q in E:out.append((s,z,q))
    return out


def block_info(t0,t1,starts,ends):
    mid=(t0+t1)//2
    out=[];off=0
    for p in STATES:
        lc=paths_count(t0,mid,starts,(p,))
        if not lc:continue
        rc=paths_count(mid,t1,(p,),ends)
        if not rc:continue
        size=lc*rc
        out.append((off,off+size,p,lc,rc));off+=size
    assert off==paths_count(t0,t1,starts,ends)
    return mid,out


def rank_segment(states,zs,t0,t1,starts,ends):
    L=t1-t0
    if L==0:return 0
    if L==1:
        target=(states[t0],zs[t0],states[t1])
        return enumerate_edges(t0,starts,ends).index(target)
    mid,blocks=block_info(t0,t1,starts,ends)
    pm=states[mid]
    for lo,hi,p,lc,rc in blocks:
        if p==pm:
            lr=rank_segment(states,zs,t0,mid,starts,(p,))
            rr=rank_segment(states,zs,mid,t1,(p,),ends)
            return lo+lr*rc+rr
    raise AssertionError


def rank_path(prefix,zs):
    s=(prefix[0]<<2)|(prefix[1]<<1)|prefix[2]
    p=initial_private(s)
    if not zs:
        return INIT.index(p)
    states=[p]
    for t,z in enumerate(zs):
        assert allowed(p,z,t%3);p=step(p,z,t%3);states.append(p)
    return rank_segment(states,list(zs),0,len(zs),INIT,ALL)


def unrank_segment(rank,t0,t1,starts,ends,states_out,zs_out):
    L=t1-t0
    if L==0:return
    if L==1:
        edges=enumerate_edges(t0,starts,ends)
        s,z,q=edges[rank]
        states_out[t0]=s;states_out[t1]=q;zs_out[t0]=z;return
    mid,blocks=block_info(t0,t1,starts,ends)
    for lo,hi,p,lc,rc in blocks:
        if lo<=rank<hi:
            rem=rank-lo;lr,rr=divmod(rem,rc)
            states_out[mid]=p
            unrank_segment(lr,t0,mid,starts,(p,),states_out,zs_out)
            unrank_segment(rr,mid,t1,(p,),ends,states_out,zs_out)
            return
    raise ValueError('rank out of range')


def unrank_path(rank,T):
    total=paths_count(0,T,INIT,ALL)
    if not 0<=rank<total:raise ValueError
    states=[None]*(T+1);zs=[None]*T
    if T==0:
        p=INIT[rank];s=next(s for s in range(8) if initial_private(s)==p)
        return [(s>>2)&1,(s>>1)&1,s&1],[]
    unrank_segment(rank,0,T,INIT,ALL,states,zs)
    s=next(s for s in range(8) if initial_private(s)==states[0])
    return [(s>>2)&1,(s>>1)&1,s&1],zs


def bit_at(rank,T,k):
    """Return transition label z_k without reconstructing the other labels."""
    if not 0<=k<T:raise IndexError
    starts,ends=INIT,ALL;t0,t1=0,T;r=rank;levels=0
    while t1-t0>1:
        mid,blocks=block_info(t0,t1,starts,ends);levels+=1
        hit=None
        for lo,hi,p,lc,rc in blocks:
            if lo<=r<hi:
                rem=r-lo;lr,rr=divmod(rem,rc);hit=(p,lr,rr);break
        if hit is None:raise ValueError
        p,lr,rr=hit
        if k<mid:
            t1=mid;ends=(p,);r=lr
        else:
            t0=mid;starts=(p,);r=rr
    edge=enumerate_edges(t0,starts,ends)[r]
    return edge[1],levels+1


def main():
    for T in range(0,219):
        assert paths_count(0,T,INIT,ALL)==sum(fast_counts_at(T).values()),T
    print('hierarchical_language_counts_0_218 ok')

    for T in range(0,9):
        total=paths_count(0,T,INIT,ALL)
        for r in range(total):
            pref,zs=unrank_path(r,T)
            assert rank_path(pref,zs)==r
            for k,z in enumerate(zs):assert bit_at(r,T,k)[0]==z
        print('exhaustive_hierarchical',T,total,'ok')

    rng=random.Random(20260910)
    for T in (16,64,128,200,218):
        total=paths_count(0,T,INIT,ALL);max_levels=0
        for _ in range(200):
            r=rng.randrange(total);pref,zs=unrank_path(r,T)
            assert rank_path(pref,zs)==r
            for _ in range(8):
                k=rng.randrange(T);z,levels=bit_at(r,T,k);assert z==zs[k]
                max_levels=max(max_levels,levels)
        print('random_access',T,'samples',1600,'max_levels',max_levels,'ok')

    n218=paths_count(0,218,INIT,ALL);n219=paths_count(0,219,INIT,ALL)
    print('count218',n218);print('count219',n219)
    assert n218==9131204053820206208 and n219==10214739716735776832
    print('rank_bits_at_218',n218.bit_length())
    print('random_access_tree_depth_bound',(218).bit_length())

if __name__=='__main__':main()

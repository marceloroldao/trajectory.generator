"""Test whether the horizon-free endpoint rank supports logarithmic random access.

The current address orders histories recursively by final state and immediate
predecessor blocks.  Direct O(log T) access to a symbol z_k would be possible
with binary lifting if, after composing L reverse steps, histories sharing the
same state at time T-L occupied a single contiguous interval inside the final
state's local rank.

This experiment checks that exact interval-contiguity property for all final
states and block lengths up to a configurable horizon.  It does not assume the
property; a counterexample is a structural result showing that the present
colexicographic endpoint rank cannot be jumped by state-only binary lifting.
"""
from __future__ import annotations

from collections import defaultdict

from logtime_scalar_public_field import fast_counts_at
from standalone_four_bit_codec import allowed, step

STATES = tuple((a,b,c,d) for a in (0,1) for b in (0,1) for c in (0,1) for d in (0,1))


def opts(p, phase):
    return tuple(z for z in (0,1) if allowed(p,z,phase))


def one_step_blocks(q, tprev):
    counts = fast_counts_at(tprev)
    off = 0
    out = []
    for p in sorted(counts):
        for z in opts(p, tprev % 3):
            if step(p,z,tprev % 3) == q:
                out.append((off, off + counts[p], p, z))
                off += counts[p]
    return out


def reverse_expand(q, T, depth):
    """Return ordered leaf intervals after `depth` reverse steps.

    Each leaf is (lo, hi, state_at_T_minus_depth, reverse_word).
    Intervals are expressed in the local rank within q at time T.
    """
    leaves=[(0, fast_counts_at(T).get(q,0), q, ())]
    # only meaningful for a fixed final q: local rank range is count[T][q]
    for d in range(depth):
        tp=T-1-d
        nxt=[]
        for lo,hi,cur,word in leaves:
            # cur's local rank at tp+1 spans [0,count(cur)); map its immediate
            # predecessor blocks into the parent interval by translation.
            blocks=one_step_blocks(cur,tp)
            assert (hi-lo)==fast_counts_at(tp+1).get(cur,0)
            for blo,bhi,p,z in blocks:
                nxt.append((lo+blo,lo+bhi,p,(z,)+word))
        leaves=nxt
    return leaves


def contiguous_by_state(leaves):
    by=defaultdict(list)
    for lo,hi,p,w in leaves:
        by[p].append((lo,hi,w))
    bad={}
    for p,ints in by.items():
        ints=sorted(ints)
        merged=[]
        for lo,hi,w in ints:
            if merged and merged[-1][1]==lo:
                merged[-1]=(merged[-1][0],hi)
            else:
                merged.append((lo,hi))
        if len(merged)>1:
            bad[p]=merged
    return bad


def main():
    first=None
    checked=0
    # Horizons chosen to cover all three phases and increasing block lengths.
    for T in range(1,25):
        counts=fast_counts_at(T)
        for q in sorted(counts):
            maxd=min(T,10)
            for depth in range(2,maxd+1):
                leaves=reverse_expand(q,T,depth)
                bad=contiguous_by_state(leaves)
                checked+=1
                if bad and first is None:
                    p=next(iter(bad))
                    first=(T,q,depth,p,bad[p],len(leaves))
    print('cases_checked',checked)
    print('first_noncontiguous',first)
    if first is None:
        print('state_only_block_lifting_candidate yes')
    else:
        print('state_only_block_lifting_candidate no')
        print('interpretation: same midpoint state occupies multiple disjoint rank intervals')

if __name__=='__main__':
    main()

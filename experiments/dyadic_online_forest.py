"""Dyadic online forest as a candidate unified causal/random-access coordinate.

Each new transition starts as a length-1 block. Adjacent equal-length blocks are
merged by binary carry. A block stores its fixed start/end private states and a
hierarchical rank among paths connecting those endpoints over that interval.

This is not yet the final single-integer address. The experiment asks a more
basic question: can an online O(log T)-block summary retain exact path identity
and support O(log T)-depth symbol access with modest information overhead?
"""
from __future__ import annotations
from dataclasses import dataclass
import math, random

from hierarchical_random_access_address import (
    STATES, paths_count, block_info, enumerate_edges, rank_segment, unrank_segment,
)
from standalone_four_bit_codec import initial_private, allowed, step

@dataclass
class Block:
    t0:int; t1:int; start:tuple; end:tuple; rank:int
    @property
    def length(self):return self.t1-self.t0


def rank_fixed(states,zs,t0,t1,start,end):
    return rank_segment(states,zs,t0,t1,(start,),(end,))


def merge_blocks(left:Block,right:Block)->Block:
    assert left.t1==right.t0 and left.end==right.start and left.length==right.length
    t0,t1=left.t0,right.t1;mid=left.t1;p=left.end
    # Same midpoint ordering as hierarchical rank, now with fixed outer endpoints.
    _,blocks=block_info(t0,t1,(left.start,),(right.end,))
    for lo,hi,pm,lc,rc in blocks:
        if pm==p:
            assert left.rank<lc and right.rank<rc
            return Block(t0,t1,left.start,right.end,lo+left.rank*rc+right.rank)
    raise AssertionError


def build_forest(prefix,zs):
    s=(prefix[0]<<2)|(prefix[1]<<1)|prefix[2];p=initial_private(s)
    states=[p]
    for t,z in enumerate(zs):
        assert allowed(p,z,t%3);p=step(p,z,t%3);states.append(p)
    forest=[]
    for t,z in enumerate(zs):
        e=enumerate_edges(t,(states[t],),(states[t+1],))
        r=e.index((states[t],z,states[t+1]))
        forest.append(Block(t,t+1,states[t],states[t+1],r))
        while len(forest)>=2 and forest[-1].length==forest[-2].length:
            b=forest.pop();a=forest.pop();forest.append(merge_blocks(a,b))
    return s,states,forest


def decode_block_bit(block:Block,k:int):
    assert block.t0<=k<block.t1
    t0,t1=block.t0,block.t1;starts=(block.start,);ends=(block.end,);r=block.rank;levels=0
    while t1-t0>1:
        mid,blocks=block_info(t0,t1,starts,ends);levels+=1
        for lo,hi,p,lc,rc in blocks:
            if lo<=r<hi:
                rem=r-lo;lr,rr=divmod(rem,rc)
                if k<mid:t1=mid;ends=(p,);r=lr
                else:t0=mid;starts=(p,);r=rr
                break
        else:raise AssertionError
    return enumerate_edges(t0,starts,ends)[r][1],levels+1


def forest_bit(forest,k):
    for b in forest:
        if b.t0<=k<b.t1:return decode_block_bit(b,k)
    raise IndexError


def block_capacity_bits(b:Block):
    n=paths_count(b.t0,b.t1,(b.start,),(b.end,))
    return 0 if n<=1 else math.ceil(math.log2(n))


def summary_bits(forest):
    # Practical tuple representation: each block rank plus its endpoint. Start of
    # first block comes from 3-bit prefix; subsequent starts equal previous ends.
    rank_bits=sum(block_capacity_bits(b) for b in forest)
    endpoint_bits=4*len(forest)
    return rank_bits,endpoint_bits,3+rank_bits+endpoint_bits


def main():
    rng=random.Random(20260910)
    for T in range(1,17):
        # generate one admissible path
        s=rng.randrange(8);p=initial_private(s);zs=[]
        for t in range(T):
            os=[z for z in (0,1) if allowed(p,z,t%3)];z=rng.choice(os);zs.append(z);p=step(p,z,t%3)
        pref=[(s>>2)&1,(s>>1)&1,s&1];_,_,f=build_forest(pref,zs)
        assert [b.length for b in f]==sorted([1<<i for i in range(T.bit_length()) if T>>i&1],reverse=True)
        for k,z in enumerate(zs):assert forest_bit(f,k)[0]==z
        print('small',T,'blocks',[b.length for b in f],'bits',summary_bits(f))

    T=218; samples=200; totals=[];maxdepth=0;shapes=set()
    for _ in range(samples):
        s=rng.randrange(8);p=initial_private(s);zs=[]
        for t in range(T):
            os=[z for z in (0,1) if allowed(p,z,t%3)];z=rng.choice(os);zs.append(z);p=step(p,z,t%3)
        pref=[(s>>2)&1,(s>>1)&1,s&1];_,_,f=build_forest(pref,zs)
        shapes.add(tuple(b.length for b in f));totals.append(summary_bits(f))
        for _ in range(16):
            k=rng.randrange(T);z,d=forest_bit(f,k);assert z==zs[k];maxdepth=max(maxdepth,d)
    print('T218_shapes',shapes)
    print('T218_samples',samples)
    print('T218_rank_bits_min_max_avg',min(x[0] for x in totals),max(x[0] for x in totals),sum(x[0] for x in totals)/samples)
    print('T218_total_bits_min_max_avg',min(x[2] for x in totals),max(x[2] for x in totals),sum(x[2] for x in totals)/samples)
    print('T218_max_random_access_depth',maxdepth)
    print('single_rank_target_bits',63)
    print('interpretation: dyadic forest is online and random-access friendly; endpoint metadata is current overhead target')

if __name__=='__main__':main()

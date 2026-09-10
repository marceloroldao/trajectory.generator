"""Dyadic online forest as a candidate unified causal/random-access coordinate.

Each new transition starts as a length-1 block. Adjacent equal-length blocks are
merged by binary carry. A block stores its fixed start/end private states and a
hierarchical rank among paths connecting those endpoints over that interval.

This experiment validates exact online merging, random symbol access, sampled
bit cost, and an exact dynamic-programming bound on the serialized bit cost at
T=218 over all reachable block-boundary state chains.
"""
from __future__ import annotations
from dataclasses import dataclass
import math, random

from hierarchical_random_access_address import (
    STATES, paths_count, block_info, enumerate_edges, rank_segment,
)
from standalone_four_bit_codec import initial_private, allowed, step

@dataclass
class Block:
    t0:int; t1:int; start:tuple; end:tuple; rank:int
    @property
    def length(self):return self.t1-self.t0


def merge_blocks(left:Block,right:Block)->Block:
    assert left.t1==right.t0 and left.end==right.start and left.length==right.length
    t0,t1=left.t0,right.t1;p=left.end
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


def cap_bits(n:int):
    return 0 if n<=1 else (n-1).bit_length()


def block_capacity_bits(b:Block):
    return cap_bits(paths_count(b.t0,b.t1,(b.start,),(b.end,)))


def summary_bits(forest):
    rank_bits=sum(block_capacity_bits(b) for b in forest)
    endpoint_bits=4*len(forest)
    return rank_bits,endpoint_bits,3+rank_bits+endpoint_bits


def dyadic_shape(T:int):
    out=[];pos=0
    for i in range(T.bit_length()-1,-1,-1):
        L=1<<i
        if T&L:
            out.append((pos,pos+L));pos+=L
    assert pos==T
    return out


def exact_serialized_bit_bounds(T:int):
    """Exact min/max fixed-field cost over every reachable boundary-state chain.

    Serialization model:
      3 bits initial prefix;
      for each canonical dyadic block: 4-bit end state, then a fixed-width local
      rank of ceil(log2 paths(start,end,interval)).

    Given T, block intervals are public. Given the previous end state, the next
    rank width is determined once its explicit 4-bit end state is read, so the
    representation is uniquely parseable despite variable widths.
    """
    shape=dyadic_shape(T)
    # Distinguish the 8 prefixes even if future experiments ever map them to the
    # same state; currently initial_private is injective.
    cur={initial_private(s):(3,3) for s in range(8)}
    for t0,t1 in shape:
        nxt={}
        for start,(mn,mx) in cur.items():
            for end in STATES:
                n=paths_count(t0,t1,(start,),(end,))
                if not n:continue
                cost=4+cap_bits(n)
                if end not in nxt:nxt[end]=(mn+cost,mx+cost)
                else:nxt[end]=(min(nxt[end][0],mn+cost),max(nxt[end][1],mx+cost))
        cur=nxt
    return min(v[0] for v in cur.values()),max(v[1] for v in cur.values()),shape,len(cur)


def main():
    rng=random.Random(20260910)
    for T in range(1,17):
        s=rng.randrange(8);p=initial_private(s);zs=[]
        for t in range(T):
            os=[z for z in (0,1) if allowed(p,z,t%3)];z=rng.choice(os);zs.append(z);p=step(p,z,t%3)
        pref=[(s>>2)&1,(s>>1)&1,s&1];_,_,f=build_forest(pref,zs)
        assert [b.length for b in f]==[b-a for a,b in dyadic_shape(T)]
        for k,z in enumerate(zs):assert forest_bit(f,k)[0]==z
        print('small',T,'blocks',[b.length for b in f],'bits',summary_bits(f))

    T=218;samples=200;totals=[];maxdepth=0;shapes=set()
    for _ in range(samples):
        s=rng.randrange(8);p=initial_private(s);zs=[]
        for t in range(T):
            os=[z for z in (0,1) if allowed(p,z,t%3)];z=rng.choice(os);zs.append(z);p=step(p,z,t%3)
        pref=[(s>>2)&1,(s>>1)&1,s&1];_,_,f=build_forest(pref,zs)
        shapes.add(tuple(b.length for b in f));totals.append(summary_bits(f))
        for _ in range(16):
            k=rng.randrange(T);z,d=forest_bit(f,k);assert z==zs[k];maxdepth=max(maxdepth,d)

    exact_min,exact_max,shape,nend=exact_serialized_bit_bounds(T)
    print('T218_shapes',shapes)
    print('T218_samples',samples)
    print('T218_rank_bits_min_max_avg_sample',min(x[0] for x in totals),max(x[0] for x in totals),sum(x[0] for x in totals)/samples)
    print('T218_total_bits_min_max_avg_sample',min(x[2] for x in totals),max(x[2] for x in totals),sum(x[2] for x in totals)/samples)
    print('T218_exact_serialized_min_max',exact_min,exact_max)
    print('T218_exact_shape',[(b-a) for a,b in shape])
    print('T218_reachable_final_boundary_states',nend)
    print('T218_max_random_access_depth',maxdepth)
    print('single_rank_target_bits',63)
    print('fits_63_all_boundary_chains',exact_max<=63)
    print('interpretation: exact max decides whether this practical online/random-access serialization preserves the 63-bit target')

if __name__=='__main__':main()

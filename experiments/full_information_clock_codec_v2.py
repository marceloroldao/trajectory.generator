"""Corrected full information-clock codec.

Covers the complete phase-lifted causal graph for topological candidate
params=(0,2,4,4), including transient entry and a final partial deterministic
flight.  The decoder receives only (final_state, physical_steps).

The implementation deliberately condenses deterministic stretches and sums only
at actual branch nodes.  It is exact enumerative coding of the constrained path
language, not arbitrary-data compression.
"""
from __future__ import annotations
from functools import lru_cache

from recurrent_orbit_core import graph
from topological_transition_state import initial_topology

PARAMS=(0,2,4,4)
WIDTH=63
MODULUS=1<<WIDTH
MASK=MODULUS-1
MUL=0x5B
SEED=0x3C6EF372

EDGES=graph(PARAMS)
BRANCH=frozenset(n for n,v in EDGES.items() if len(v)>1)
INITIAL=tuple((s,initial_topology(s),0) for s in range(8))


def deterministic_run(node):
    """Return path to first branch, or a branchless deterministic cycle."""
    if node in BRANCH:
        return (node,),node,None
    path=[node]; seen={node:0}; cur=node
    while True:
        nxts=EDGES[cur]
        if len(nxts)!=1:
            return tuple(path),None,None
        nxt=nxts[0]
        path.append(nxt)
        # A branch return must be recognized before generic cycle detection.
        if nxt in BRANCH:
            return tuple(path),nxt,None
        if nxt in seen:
            return tuple(path),None,seen[nxt]
        seen[nxt]=len(path)-1
        cur=nxt


@lru_cache(maxsize=None)
def macro_choices(branch):
    if branch not in BRANCH:
        raise ValueError("macro_choices requires branch node")
    out=[]
    for first in EDGES[branch]:
        path=[branch,first]
        if first in BRANCH:
            out.append((first,1,tuple(path),None))
            continue
        seen={branch:0,first:1}; cur=first
        while True:
            nxts=EDGES[cur]
            if len(nxts)!=1:
                out.append((None,len(path)-1,tuple(path),None)); break
            nxt=nxts[0]; path.append(nxt)
            # Critical ordering: a return to the source branch is a branch
            # event, not a branchless deterministic cycle.
            if nxt in BRANCH:
                out.append((nxt,len(path)-1,tuple(path),None)); break
            if nxt in seen:
                out.append((None,len(path)-1,tuple(path),seen[nxt])); break
            seen[nxt]=len(path)-1; cur=nxt
    return tuple(out)


@lru_cache(maxsize=None)
def suffix_count(node,remaining):
    if remaining<0:return 0
    if remaining==0:return 1
    if node not in BRANCH:
        path,target,cycle=deterministic_run(node)
        d=len(path)-1
        if target is not None:
            return 1 if remaining<=d else suffix_count(target,remaining-d)
        if cycle is not None:return 1
        return int(remaining<=d)
    total=0
    for target,length,path,cycle in macro_choices(node):
        if remaining<=length:
            total+=1
        elif target is not None:
            total+=suffix_count(target,remaining-length)
        elif cycle is not None:
            total+=1
    return total


def admissible_count(steps):
    if steps<0:raise ValueError("steps must be non-negative")
    return sum(suffix_count(n,steps) for n in INITIAL)


def stepwise_reference_count(steps):
    dist={n:1 for n in INITIAL}
    for _ in range(steps):
        nxt={}
        for n,c in dist.items():
            for m in EDGES[n]:nxt[m]=nxt.get(m,0)+c
        dist=nxt
    return sum(dist.values())


def _unique_continue(causal,remaining):
    while remaining:
        nxts=EDGES[causal[-1]]
        if len(nxts)!=1:raise RuntimeError("unique continuation reached branch")
        causal.append(nxts[0]);remaining-=1


def _unrank_from(start,rank,remaining):
    causal=[start];cur=start
    while remaining:
        if cur not in BRANCH:
            run,target,cycle=deterministic_run(cur);d=len(run)-1
            if remaining<=d:
                causal.extend(run[1:remaining+1]);break
            causal.extend(run[1:]);remaining-=d
            if target is not None:
                cur=target;continue
            if cycle is not None:
                _unique_continue(causal,remaining);remaining=0;break
            raise ValueError("path extends beyond deterministic terminal")
        selected=None
        for choice in macro_choices(cur):
            target,length,path,cycle=choice
            if remaining<=length:count=1
            elif target is not None:count=suffix_count(target,remaining-length)
            elif cycle is not None:count=1
            else:count=0
            if rank<count:
                selected=choice;break
            rank-=count
        if selected is None:raise ValueError("rank outside suffix family")
        target,length,path,cycle=selected
        if remaining<=length:
            causal.extend(path[1:remaining+1]);remaining=0;break
        causal.extend(path[1:]);remaining-=length
        if target is not None:
            cur=target;continue
        if cycle is not None:
            _unique_continue(causal,remaining);remaining=0;break
        raise ValueError("terminal macro cannot complete requested length")
    return tuple(causal)


def unrank_path(rank,steps):
    total=admissible_count(steps)
    if not 0<=rank<total:raise ValueError("rank outside family")
    for start in INITIAL:
        c=suffix_count(start,steps)
        if rank<c:return _unrank_from(start,rank,steps)
        rank-=c
    raise RuntimeError("initial state resolution failed")


def rank_path(path):
    path=tuple(path)
    if not path or path[0] not in INITIAL:raise ValueError("invalid initial state")
    for a,b in zip(path,path[1:]):
        if b not in EDGES[a]:raise ValueError("invalid edge")
    steps=len(path)-1
    i0=INITIAL.index(path[0])
    rank=sum(suffix_count(n,steps) for n in INITIAL[:i0])
    pos=0;remaining=steps;cur=path[0]
    while remaining:
        if cur not in BRANCH:
            expected=EDGES[cur]
            if len(expected)!=1 or path[pos+1]!=expected[0]:raise ValueError("bad deterministic edge")
            pos+=1;remaining-=1;cur=path[pos];continue
        actual=path[pos+1];found=False
        for target,length,macro,cycle in macro_choices(cur):
            if macro[1]==actual:
                take=min(remaining,length)
                if path[pos:pos+take+1]!=macro[:take+1]:raise ValueError("bad macro flight")
                pos+=take;remaining-=take;cur=path[pos];found=True;break
            if remaining<=length:rank+=1
            elif target is not None:rank+=suffix_count(target,remaining-length)
            elif cycle is not None:rank+=1
        if not found:raise ValueError("unknown branch choice")
    return rank


def bits_from_path(path):
    s=path[0][0]
    return [(s>>2)&1,(s>>1)&1,s&1]+[n[0]&1 for n in path[1:]]


def time_word(steps):
    z=(steps+SEED)&MASK
    z^=(z<<13)&MASK;z^=z>>7;z^=(z<<17)&MASK
    return z&MASK


def forward(rank,steps):return (rank*MUL+time_word(steps))&MASK

def inverse(state,steps):return ((state-time_word(steps))*pow(MUL,-1,MODULUS))&MASK

def capacity_ok(steps):return admissible_count(steps)<=MODULUS


def encode_path(path):
    path=tuple(path);steps=len(path)-1
    if not capacity_ok(steps):raise ValueError("family exceeds 63-bit capacity")
    return forward(rank_path(path),steps),steps


def decode_path(final_state,steps):
    if not capacity_ok(steps):raise ValueError("family exceeds 63-bit capacity")
    rank=inverse(final_state&MASK,steps);total=admissible_count(steps)
    if rank>=total:raise ValueError("invalid address")
    path=unrank_path(rank,steps)
    return path,bits_from_path(path)


def self_test(max_steps=48,per_length=256):
    for n in range(max_steps+1):
        a=admissible_count(n);b=stepwise_reference_count(n)
        assert a==b,(n,a,b)
        for rank in range(min(a,per_length)):
            p=unrank_path(rank,n)
            assert len(p)==n+1
            assert rank_path(p)==rank
            d,bits=decode_path(forward(rank,n),n)
            assert d==p and len(bits)==n+3
    return True


def main():
    print("branch_nodes",len(BRANCH))
    print("self_test",self_test())
    for n in range(215,226):
        c=admissible_count(n)
        print(n,c,c<=MODULUS)

if __name__=="__main__":main()

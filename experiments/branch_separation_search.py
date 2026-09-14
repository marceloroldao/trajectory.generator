"""Search fixed local endpoint laws for exact arbitrary-bit history recovery.

State is one W-bit endpoint x. Input bit selects one of two *fixed* local maps
    x' = F_b(x)
with no external rank or trajectory memory.

We search affine permutations modulo 2**W:
    F_b(x) = a_b*x + c_b (mod 2**W), a_b odd.

Starting from x=0, a candidate passes depth T iff every one of the 2**T input
words has a distinct endpoint. Perfect capacity means passing through T=W.

This is not claimed to beat information theory. It asks a narrower structural
question: can natural fixed local dynamics make the endpoint itself a complete
coordinate of an arbitrary history up to the endpoint's full W-bit capacity?
"""
from __future__ import annotations
from itertools import product


def endpoint(word,W,a0,c0,a1,c1):
    m=(1<<W)-1; x=0
    for b in word:
        if b==0: x=(a0*x+c0)&m
        else: x=(a1*x+c1)&m
    return x


def depth_stats(W,a0,c0,a1,c1,maxT=None):
    if maxT is None:maxT=W
    reachable={0}
    out=[]
    m=(1<<W)-1
    for T in range(1,maxT+1):
        r0={(a0*x+c0)&m for x in reachable}
        r1={(a1*x+c1)&m for x in reachable}
        overlap=len(r0&r1)
        nxt=r0|r1
        injective=(len(nxt)==2*len(reachable) and overlap==0)
        out.append((T,len(nxt),overlap,injective))
        reachable=nxt
        if not injective:break
    return out


def search(W,limit=None):
    M=1<<W
    odds=range(1,M,2)
    tested=0; best=(-1,None,None)
    # Normalize c0=0: a global translation/conjugacy freedom makes this a
    # useful search gauge. c1 must differ from c0 at depth 1.
    c0=0
    for a0 in odds:
      for a1 in odds:
        for c1 in range(1,M):
            tested+=1
            st=depth_stats(W,a0,c0,a1,c1,W)
            d=sum(1 for row in st if row[3])
            if d>best[0]:best=(d,(a0,c0,a1,c1),st)
            if d==W:
                return tested,best
            if limit and tested>=limit:return tested,best
    return tested,best


def verify_words(W,params):
    seen={}
    for word in product((0,1),repeat=W):
        x=endpoint(word,W,*params)
        if x in seen:return False,(seen[x],word,x)
        seen[x]=word
    return len(seen)==(1<<W),None


def main():
    for W in range(2,9):
        tested,best=search(W)
        d,params,stats=best
        print('W',W,'tested',tested,'best_depth',d,'params',params,'stats',stats)
        if d==W:
            ok,collision=verify_words(W,params)
            assert ok,collision
            print('PERFECT_CAPACITY',W,params)
        else:
            print('NO_PERFECT_FOUND_IN_AFFINE_FAMILY',W)

if __name__=='__main__':main()

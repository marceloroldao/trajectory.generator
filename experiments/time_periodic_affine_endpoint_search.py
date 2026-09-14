"""Search t mod 3 affine endpoint-only laws for exact arbitrary-history recovery.

Original objective only:
    arbitrary input bits -> local dynamics -> keep only (X_final,T)
No external rank, no path table, no restricted language.

For phase p=t mod 3 and input b in {0,1}:
    x' = a[p,b] * x + c[p,b]  (mod 2**W)
with odd a so each branch is individually a permutation.

A candidate passes depth T iff all 2**T words have distinct endpoints.
Full-capacity success means passing through T=W.
"""
from __future__ import annotations
import random


def depth_stats(W, params):
    mask=(1<<W)-1
    reachable={0}
    rows=[]
    for t in range(W):
        ph=t%3
        a0,c0,a1,c1=params[ph]
        r0={(a0*x+c0)&mask for x in reachable}
        r1={(a1*x+c1)&mask for x in reachable}
        overlap=len(r0&r1)
        nxt=r0|r1
        injective=(len(nxt)==2*len(reachable) and overlap==0)
        rows.append((t+1,len(nxt),overlap,injective))
        reachable=nxt
        if not injective:
            break
    return rows


def depth(W,params):
    return sum(1 for row in depth_stats(W,params) if row[3])


def search(W, trials=500_000, seed=None):
    rng=random.Random((20260914+W) if seed is None else seed)
    M=1<<W
    odds=tuple(range(1,M,2))
    best=(-1,None,None)
    for i in range(trials):
        p=[(rng.choice(odds),rng.randrange(M),rng.choice(odds),rng.randrange(M)) for _ in range(3)]
        st=depth_stats(W,p)
        d=sum(1 for r in st if r[3])
        if d>best[0]:
            best=(d,p,st)
        if d==W:
            return i+1,best
    return trials,best


def main():
    # Canonical successes already independently found for W<=5.
    known={
        3:[(1,3,1,1),(1,5,3,1),(3,2,3,7)],
        4:[(15,8,1,9),(13,6,9,0),(1,13,1,1)],
        5:[(1,1,21,17),(9,24,19,25),(5,14,15,7)],
    }
    for W,p in known.items():
        st=depth_stats(W,p)
        print('KNOWN',W,'depth',depth(W,p),'params',p,'stats',st)
        assert depth(W,p)==W

    # Harder widths: deterministic random search. Not a proof of impossibility if no hit.
    for W in (6,7):
        tested,best=search(W)
        d,p,st=best
        print('SEARCH',W,'tested',tested,'best_depth',d,'params',p,'stats',st)
        assert d<=W
        if d==W:
            print('FULL_CAPACITY_FOUND',W,p)
        else:
            print('NO_FULL_CAPACITY_FOUND_IN_SAMPLE',W)

if __name__=='__main__':
    main()

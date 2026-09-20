"""Matrix gate for multilayer trajectory universes.

Measures three distinct limits:
1. information-theoretic Kmax for (W,T);
2. exact collision-free K<=2 behavior of orbit-derived endpoint directions;
3. sampled K=3/4 behavior where exhaustive enumeration is too expensive.

A pass never means arbitrary T-bit recovery. It only means sparse innovation
histories in the tested class remain distinguishable by the natural endpoint.
"""
from __future__ import annotations
from itertools import combinations
from math import comb,log2
import random
from multilayer_orbit_innovation_universe import propagated_columns

def theoretical_kmax(W,T):
    total=0;best=-1
    for k in range(T+1):
        n=total+comb(T,k)
        if n>(1<<W):break
        total=n;best=k
    return best,log2(total) if total else 0.0

def exact_up_to_k2(cols):
    seen={0:()}
    for i,c in enumerate(cols):
        if c in seen:return False,(seen[c],(i,))
        seen[c]=(i,)
    for i,j in combinations(range(len(cols)),2):
        y=cols[i]^cols[j]
        if y in seen:return False,(seen[y],(i,j))
        seen[y]=(i,j)
    return True,None

def sampled_k(cols,k,n,seed):
    rng=random.Random(seed); seen={}
    T=len(cols)
    for _ in range(n):
        p=tuple(sorted(rng.sample(range(T),k)))
        y=0
        for i in p:y^=cols[i]
        q=seen.get(y)
        if q is not None and q!=p:return False,(q,p)
        seen[y]=p
    return True,None

def main():
    cases=[
        (63,256),(63,1024),
        (128,1024),(128,4096),
        (256,1024),(256,4096),
        (512,4096),(512,16384),
    ]
    for W,T in cases:
        Kbound,bits=theoretical_kmax(W,T)
        cols=propagated_columns(T,W)
        ok2,c2=exact_up_to_k2(cols)
        # Samples are evidence only, never proof of K>=3 uniqueness.
        n=100_000
        ok3,c3=sampled_k(cols,3,n,20260920+W+T+3)
        ok4,c4=sampled_k(cols,4,n,20260920+W+T+4)
        print("MATRIX_GATE",
              "W",W,"T",T,
              "theory_Kmax",Kbound,"theory_used_bits",round(bits,3),
              "K2_exact",ok2,"K2_collision",c2,
              "K3_sample",ok3,"K3_collision",c3,
              "K4_sample",ok4,"K4_collision",c4)

if __name__=="__main__":main()

"""Search a natural 63-bit endpoint dynamics for long sparse innovations.

No combinatorial rank is used by the candidate dynamics. Every innovation applies
the SAME local perturbation d=1. Public time evolution spreads it:

    x[t+1] = A[t mod P] x[t] XOR c[t] XOR d*e[t]

For a fixed innovation budget K, we ask whether distinct innovation sets produce
distinct natural endpoints. This is exact for K<=2 via algebraic collision tests:
single innovations require distinct signatures s_t; pairs require all XORs
s_i XOR s_j distinct and disjoint from lower-weight signatures.

This tests whether time itself gives a unique geometric signature to sparse
innovations without explicitly ranking their positions.
"""
from __future__ import annotations
import random

W=63
MASK=(1<<W)-1

def parity(x): return x.bit_count()&1
def apply(A,x): return sum((parity(row&x)<<i) for i,row in enumerate(A))
def rank(rows):
    rows=list(rows); r=0
    for c in range(W):
        p=next((i for i in range(r,len(rows)) if (rows[i]>>c)&1),None)
        if p is None: continue
        rows[r],rows[p]=rows[p],rows[r]
        for i in range(len(rows)):
            if i!=r and ((rows[i]>>c)&1): rows[i]^=rows[r]
        r+=1
    return r

def universe(seed,phase):
    rng=random.Random(seed*131+phase)
    rows=[1<<i for i in range(W)]
    rot=1+rng.randrange(W-1)
    rows=rows[-rot:]+rows[:-rot]
    for _ in range(4*W):
        i=rng.randrange(W); j=rng.randrange(W-1)
        if j>=i:j+=1
        rows[i]^=rows[j]
    assert rank(rows)==W
    return tuple(rows)

def signatures(T,seed,P=3,d=1):
    As=[universe(seed,p) for p in range(P)]
    # signature of innovation at t in final state; compute backwards.
    sig=[0]*T
    x=d
    for t in range(T-1,-1,-1):
        sig[t]=x
        x=apply(As[t%P],x)
    return sig

def weight1_ok(sig):
    return len(set(sig))==len(sig) and 0 not in sig

def weight2_ok(sig):
    seen={0}
    seen.update(sig)
    n=len(sig)
    for i in range(n):
        a=sig[i]
        for j in range(i+1,n):
            x=a^sig[j]
            if x in seen:return False,(i,j,x)
            seen.add(x)
    return True,None

def search(T,limit=200):
    best=None
    for seed in range(1,limit+1):
        s=signatures(T,seed)
        one=weight1_ok(s)
        two,collision=weight2_ok(s) if one else (False,None)
        score=(int(one),int(two))
        if best is None or score>best[0]:best=(score,seed,collision)
        if two:return seed,s
    return None,best

def main():
    for T in (256,512,1024,4096):
        found,info=search(T,64)
        if found:
            print("NATURAL_SPARSE_ENDPOINT","T",T,"seed",found,
                  "K1",True,"K2",True,"rank_used",False,
                  "fixed_injection",True)
        else:
            print("NO_K2_CANDIDATE","T",T,"best",info)
if __name__=="__main__":main()

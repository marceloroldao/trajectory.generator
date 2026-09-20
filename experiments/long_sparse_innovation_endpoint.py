"""Long-trajectory endpoint-only test with sparse innovations.

The public universe predicts the payload. Only deviations (innovations) are free.
We encode the innovation SET directly into one W-bit endpoint using combinatorial
ranking. This is an intentionally strict accounting experiment, not yet the
desired natural dynamical solution: it tells us exactly when a long trajectory
can fit because its free-information cardinality is <= 2**W.

For fixed T and at most K innovations, the number of possible residual histories is
    N(T,K) = sum_{k=0..K} C(T,k).
Exact recovery from a W-bit endpoint is possible iff N(T,K) <= 2**W.
"""
from __future__ import annotations
from math import comb, log2
import random

W=63

def universe_predict(hist,t):
    if t < 4:
        return ((t*3+1)>>1)&1
    return hist[t-1]^hist[t-4]^int(t%7==0)

def synthesize(T, positions):
    pos=set(positions); out=[]
    for t in range(T):
        p=universe_predict(out,t)
        out.append(p ^ int(t in pos))
    return tuple(out)

def innovations(bits):
    hist=[]; pos=[]
    for t,b in enumerate(bits):
        p=universe_predict(hist,t)
        if b^p: pos.append(t)
        hist.append(b)
    return tuple(pos)

def space(T,K):
    return sum(comb(T,k) for k in range(K+1))

def rank_subset_fixed(pos,T,k):
    # lexicographic combinatorial rank among k-subsets
    r=0; prev=-1
    for i,x in enumerate(pos):
        for y in range(prev+1,x):
            r += comb(T-1-y,k-1-i)
        prev=x
    return r

def unrank_subset_fixed(r,T,k):
    out=[]; start=0
    for i in range(k):
        for x in range(start,T):
            n=comb(T-1-x,k-1-i)
            if r<n:
                out.append(x); start=x+1; break
            r-=n
        else: raise ValueError("rank")
    return tuple(out)

def encode_positions(pos,T,K):
    k=len(pos)
    if k>K: raise ValueError("too many innovations")
    offset=sum(comb(T,j) for j in range(k))
    a=offset+rank_subset_fixed(tuple(pos),T,k)
    if a >= 1<<W: raise ValueError("endpoint capacity exceeded")
    return a

def decode_positions(a,T,K):
    off=0
    for k in range(K+1):
        n=comb(T,k)
        if a<off+n:
            return unrank_subset_fixed(a-off,T,k)
        off+=n
    raise ValueError("invalid endpoint")

def max_k(T,W=W):
    total=0
    k=-1
    while k+1<=T and total+comb(T,k+1)<=1<<W:
        k+=1; total+=comb(T,k)
    return k,total

def main():
    rng=random.Random(20260920)
    for T in (64,128,256,512,1024,4096):
        K,N=max_k(T)
        print("CAPACITY","T",T,"Kmax",K,"log2_space",log2(N) if N else 0)
        testK=min(K,8)
        for _ in range(100):
            k=rng.randrange(testK+1)
            pos=tuple(sorted(rng.sample(range(T),k)))
            bits=synthesize(T,pos)
            assert innovations(bits)==pos
            a=encode_positions(pos,T,K)
            gotpos=decode_positions(a,T,K)
            assert gotpos==pos
            recovered=synthesize(T,gotpos)
            assert recovered==bits
        print("LONG_ENDPOINT_ONLY_ACCOUNTING_OK","T",T,"tested_K",testK,
              "endpoint_bits",W)
    print("CAUTION: endpoint currently equals a combinatorial innovation rank; this is a capacity/accounting control, not the target natural trajectory dynamics.")

if __name__=="__main__": main()

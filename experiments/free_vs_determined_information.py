"""Measure free information versus universe-determined trajectory structure.

Goal: keep the original endpoint-only contract honest.  The temporal universe
may generate many state changes, but only independent input choices count as
free information.  This experiment constructs payloads from a deterministic
predictor plus sparse residual innovations:

    b_t = predictor(history,t) XOR e_t

The residual e_t is the genuinely free part.  We compare:
  * raw payload bits T
  * residual entropy / number of nonzero innovations
  * exact description cost under a simple sparse residual code
  * endpoint-only capacity W

No claim of generic compression is made.  If the residual description exceeds
W, a W-bit endpoint cannot identify all such payloads exactly.
"""
from __future__ import annotations
from math import comb, ceil, log2
import random

def predictor(bits,t):
    # Public deterministic relation: periodic + short causal recurrence.
    if t < 3:
        return (t == 1)
    return bits[t-1] ^ bits[t-3] ^ ((t % 5) == 0)

def generate(T, flips, seed):
    rng=random.Random(seed)
    positions=sorted(rng.sample(range(T),flips))
    pos=set(positions); bits=[]
    for t in range(T):
        p=int(bool(predictor(bits,t)))
        bits.append(p ^ int(t in pos))
    return tuple(bits),tuple(positions)

def residual(payload):
    e=[]
    hist=[]
    for t,b in enumerate(payload):
        p=int(bool(predictor(hist,t)))
        e.append(b^p);hist.append(b)
    return tuple(e)

def sparse_cost(T,k):
    # Enumerative position code + k residual values (values are all 1 here).
    if k==0:return 0
    return ceil(log2(comb(T,k)))

def main():
    W=63
    for T in (63,128,256,512,1024):
        for k in (0,1,2,4,8):
            if k>T:continue
            bits,pos=generate(T,k,20260920+T+k)
            e=residual(bits)
            assert tuple(i for i,x in enumerate(e) if x)==pos
            cost=sparse_cost(T,k)
            print("FREE_VS_DETERMINED",
                  "T",T,"innovations",k,"sparse_bits",cost,
                  "fits_W63",cost<=W,
                  "determined_steps",T-k)
    print("INTERPRETATION: trajectory length is not information content; only independent innovations require capacity.")

if __name__=="__main__":main()

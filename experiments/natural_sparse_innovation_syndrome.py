"""Natural 63-bit endpoint dynamics for long trajectories with sparse innovations.

No combinatorial rank is maintained.  At each time t the public universe exposes
one deterministic 63-bit direction h(t).  If the observed bit differs from the
universe prediction, the endpoint state is updated locally:

    X[t+1] = R_t(X[t]) XOR h(t) * e_t

where R_t is a public reversible rotation/shear and e_t is the innovation bit.

At the end only (X_T,T) remains.  Recovery searches sparse innovation sets whose
public propagated directions XOR to the normalized endpoint.  This is syndrome
decoding over GF(2): natural online dynamics, but decoding complexity grows with
the innovation budget.  It is NOT arbitrary-data compression.
"""
from __future__ import annotations
from itertools import combinations
import random

W=63; MASK=(1<<W)-1

def rotl(x,r):
    r%=W
    return ((x<<r)|(x>>(W-r)))&MASK if r else x&MASK

def universe_direction(t):
    # Public deterministic direction, generated from time only.
    x=(t+1)*0x9E3779B97F4A7C15 & MASK
    x ^= x>>30; x=(x*0xBF58476D1CE4E5B9)&MASK
    x ^= x>>27; x=(x*0x94D049BB133111EB)&MASK
    x ^= x>>31
    return x or 1

def step_state(x,t,e):
    # Reversible public motion plus local innovation kick.
    r=(t%17)+1
    x=rotl(x,r)
    x ^= rotl(x,7)  # public shear; experiment only uses forward propagation
    x &= MASK
    if e: x ^= universe_direction(t)
    return x

def encode_innovations(T,pos):
    S=set(pos);x=0
    for t in range(T): x=step_state(x,t,int(t in S))
    return x

def propagated_columns(T):
    # Contribution of each possible innovation to X_T.
    cols=[]
    for src in range(T):
        x=universe_direction(src)
        for t in range(src+1,T):
            r=(t%17)+1
            x=rotl(x,r)^rotl(rotl(x,r),7)
            x&=MASK
        cols.append(x)
    return cols

def decode_k0_k1_k2(endpoint,T):
    cols=propagated_columns(T)
    if endpoint==0:return ()
    one={v:i for i,v in enumerate(cols)}
    if endpoint in one:return (one[endpoint],)
    for i,a in enumerate(cols):
        j=one.get(endpoint^a)
        if j is not None and j>i:return (i,j)
    raise ValueError("not decodable with <=2 innovations")

def main():
    rng=random.Random(20260920)
    for T in (128,256,512,1024):
        # Exact exhaustive validation for all 0/1/2-innovation histories.
        seen={0:()}
        collision=None
        cols=propagated_columns(T)
        for i,c in enumerate(cols):
            if c in seen: collision=(seen[c],(i,));break
            seen[c]=(i,)
        if collision is None:
            for i,j in combinations(range(T),2):
                y=cols[i]^cols[j]
                if y in seen:
                    collision=(seen[y],(i,j));break
                seen[y]=(i,j)
        print("NATURAL_SYNDROME","T",T,"histories_checked",len(seen),
              "collision",collision)
        if collision is None:
            for _ in range(100):
                k=rng.randrange(3)
                pos=tuple(sorted(rng.sample(range(T),k)))
                y=encode_innovations(T,pos)
                got=decode_k0_k1_k2(y,T)
                assert got==pos,(T,pos,y,got)
            print("NATURAL_ENDPOINT_RECOVERY_OK","T",T,"K",2,"endpoint_bits",W)

if __name__=="__main__":main()

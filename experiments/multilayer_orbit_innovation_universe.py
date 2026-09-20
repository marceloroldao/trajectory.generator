"""Multilayer orbit universe for sparse innovations.

The innovation direction is no longer hashed directly from time. A public
multilayer state U=(H,V,Z) evolves autonomously. Its current relation generates
where an innovation perturbs the memory state X.

All endpoint bits count toward the information budget. U is public and
input-independent, so it need not be retained as payload-dependent state.

Widths 63, 256 and 512 are tested. The experiment checks uniqueness of all
histories with <=2 innovations for long T, and samples <=3 where exhaustive
enumeration is too expensive.
"""
from __future__ import annotations
from itertools import combinations
import random

def mask(W): return (1<<W)-1
def rotl(x,r,W):
    m=mask(W);r%=W
    return ((x<<r)|(x>>(W-r)))&m if r else x&m

def seed_layers(W):
    m=mask(W)
    return (0x9E3779B97F4A7C15&m,0xD1B54A32D192ED03&m,0x94D049BB133111EB&m)

def orbit_step(U,t,W):
    h,v,z=U;m=mask(W)
    # horizontal, vertical, relation layer; autonomous and reversible-ish mixing
    nh=rotl(h^v,(t%23)+1,W)
    nv=rotl(v^z,(t%29)+3,W)
    nz=rotl(z^h,(t%31)+5,W)
    # public phase-3 universe kick, input-independent
    if t%3==0:
        nh ^= rotl(z,7,W)
        nv ^= rotl(h,11,W)
        nz ^= rotl(v,13,W)
    return nh&m,nv&m,nz&m

def relation_direction(U,t,W):
    h,v,z=U;m=mask(W)
    d=(h ^ rotl(v,17,W) ^ rotl(z,37,W) ^
       rotl(h&v,5,W) ^ rotl(v&z,9,W) ^ (1<<(t%W)))&m
    return d or 1

def memory_step(x,d,t,W,e):
    # Public linear-ish motion; innovation enters along orbit-derived relation d.
    y=rotl(x,(t%19)+1,W)
    y ^= rotl(y,7,W)
    y &= mask(W)
    return y ^ (d if e else 0)

def propagated_columns(T,W):
    U=seed_layers(W); dirs=[]
    for t in range(T):
        d=relation_direction(U,t,W);dirs.append(d)
        U=orbit_step(U,t,W)
    cols=[]
    for src in range(T):
        x=dirs[src]
        for t in range(src+1,T):
            x=memory_step(x,0,t,W,0)
        cols.append(x)
    return cols

def exact_unique_k2(cols):
    seen={0:()}
    for i,c in enumerate(cols):
        if c in seen:return False,(seen[c],(i,))
        seen[c]=(i,)
    for i,j in combinations(range(len(cols)),2):
        y=cols[i]^cols[j]
        if y in seen:return False,(seen[y],(i,j))
        seen[y]=(i,j)
    return True,None

def sampled_unique_k3(cols,samples,seed):
    rng=random.Random(seed); seen={}
    T=len(cols)
    for _ in range(samples):
        p=tuple(sorted(rng.sample(range(T),3)))
        y=cols[p[0]]^cols[p[1]]^cols[p[2]]
        q=seen.get(y)
        if q is not None and q!=p:return False,(q,p)
        seen[y]=p
    return True,None

def main():
    cases=[(63,256),(63,1024),(256,1024),(256,4096),(512,4096),(512,16384)]
    for W,T in cases:
        cols=propagated_columns(T,W)
        ok2,col2=exact_unique_k2(cols)
        ok3,col3=sampled_unique_k3(cols,200000,20260920+W+T)
        print("MULTILAYER_ORBIT","W",W,"T",T,
              "K2_exact_unique",ok2,"K2_collision",col2,
              "K3_sample_unique",ok3,"K3_collision",col3)

if __name__=="__main__":main()

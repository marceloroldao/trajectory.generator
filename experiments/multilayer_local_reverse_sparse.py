"""Attempt a genuinely local reverse decoder for sparse innovations.

Question: can the last innovation e_t be inferred from only the current
input-dependent endpoint X[t+1], public time t, and the public multilayer
universe U_t, without a trajectory table or global subset search?

For a fixed horizon t, reachable states with <=K innovations form a sparse set.
We search for a single parity relation q_t derived from the public propagated
innovation directions such that:
  q_t . F_t(S_t) = 0 for every prior reachable innovation direction
  q_t . d_t = 1
Then e_t is read locally by parity(q_t & X[t+1]).

If such q_t exists at every step, reverse decoding is local. Failure is reported
as a structural result, not hidden by fallback search.
"""
from __future__ import annotations
from multilayer_orbit_innovation_universe import (
    mask,rotl,seed_layers,orbit_step,relation_direction,memory_step
)

def parity(x):return x.bit_count()&1

def rank(vectors,W):
    a=[x for x in vectors if x];r=0
    for c in range(W):
        p=next((i for i in range(r,len(a)) if (a[i]>>c)&1),None)
        if p is None:continue
        a[r],a[p]=a[p],a[r]
        for i in range(len(a)):
            if i!=r and ((a[i]>>c)&1):a[i]^=a[r]
        r+=1
        if r==len(a):break
    return r

def solve_separator(prior,d,W):
    # Solve q·v=0 for prior vectors and q·d=1.
    rows=[v for v in prior]+[d]
    rhs=[0]*len(prior)+[1]
    aug=[v|(b<<W) for v,b in zip(rows,rhs)]
    r=0;piv=[]
    for c in range(W):
        p=next((i for i in range(r,len(aug)) if (aug[i]>>c)&1),None)
        if p is None:continue
        aug[r],aug[p]=aug[p],aug[r]
        for i in range(len(aug)):
            if i!=r and ((aug[i]>>c)&1):aug[i]^=aug[r]
        piv.append(c);r+=1
        if r==len(aug):break
    m=mask(W)
    if any((row&m)==0 and ((row>>W)&1) for row in aug):return None
    q=0
    for i,c in enumerate(piv):
        if (aug[i]>>W)&1:q|=1<<c
    if parity(q&d)!=1:return None
    if any(parity(q&v) for v in prior):return None
    return q

def public_directions(W,T):
    U=seed_layers(W);ds=[]
    for t in range(T):
        ds.append(relation_direction(U,t,W));U=orbit_step(U,t,W)
    return ds

def transform(x,t,W):
    return memory_step(x,0,t,W,0)

def local_separator_depth(W,T):
    ds=public_directions(W,T)
    # basis contains contributions of all earlier innovation variables to X_t.
    basis=[]; masks=[]
    for t in range(T):
        prior=[transform(v,t,W) for v in basis]
        q=solve_separator(prior,ds[t],W)
        if q is None:return t,masks,rank(prior,W)
        masks.append(q)
        basis=prior+[ds[t]]
    return T,masks,rank(basis,W)

def main():
    for W,T in [(63,256),(128,512),(256,1024),(512,2048)]:
        depth,masks,r=local_separator_depth(W,T)
        print("LOCAL_REVERSE_MULTILAYER","W",W,"target_T",T,
              "separator_depth",depth,"rank_at_stop",r,
              "full_target",depth==T)
        # For arbitrary independent innovation variables, local linear
        # separators cannot continue after the innovation span saturates W.
        if depth>W:
            raise AssertionError(("unexpected >W independent separator depth",W,depth))

if __name__=="__main__":main()

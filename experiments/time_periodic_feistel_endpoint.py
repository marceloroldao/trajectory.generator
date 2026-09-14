"""Time-periodic two-layer Feistel candidates for the original endpoint-only objective.

State X=(H,V), each layer w bits; total endpoint width W=2w.
At phase p=t mod 3 and input bit b:
    H' = V
    V' = H XOR rot(V,r[p,b]) XOR k[p,b]
Each branch is a permutation. No rank/history/side information is retained.

We test exact endpoint injectivity for arbitrary bit strings through T=W and
explicit backwards recovery from (X_final,T) only. Reverse recovery chooses the
unique bit whose inverse predecessor lies in the reachable set at time t. Those
reachable sets are used here only as a proof/test oracle; a candidate is not yet
accepted as a compact decoder law until the bit can be inferred locally without
such a table.
"""
from __future__ import annotations
from itertools import product


def rotl(x,r,w):
    m=(1<<w)-1; r%=w
    return ((x<<r)|(x>>(w-r)))&m if r else x&m


def forward(state,b,t,w,params):
    h,v=state; r,k=params[t%3][b]
    return v,(h ^ rotl(v,r,w) ^ k)&((1<<w)-1)


def inverse(state,b,t,w,params):
    hp,vp=state
    # hp = old v
    oldv=hp
    r,k=params[t%3][b]
    oldh=(vp ^ rotl(oldv,r,w) ^ k)&((1<<w)-1)
    return oldh,oldv


def endpoint(bits,w,params):
    s=(0,0)
    for t,b in enumerate(bits): s=forward(s,b,t,w,params)
    return s


def reachable_layers(T,w,params):
    levels=[{(0,0)}]
    for t in range(T):
        nxt=set()
        for s in levels[-1]:
            nxt.add(forward(s,0,t,w,params)); nxt.add(forward(s,1,t,w,params))
        levels.append(nxt)
    return levels


def reverse_with_reachable(x,T,w,params,levels):
    bits=[]
    for t in range(T-1,-1,-1):
        candidates=[]
        for b in (0,1):
            p=inverse(x,b,t,w,params)
            if p in levels[t]: candidates.append((b,p))
        if len(candidates)!=1:
            raise AssertionError((t,x,candidates))
        b,x=candidates[0]; bits.append(b)
    return tuple(reversed(bits))


def verify(w,params):
    W=2*w
    levels=reachable_layers(W,w,params)
    for t,L in enumerate(levels):
        assert len(L)==1<<t,(w,t,len(L),1<<t)
    for bits in product((0,1),repeat=W):
        x=endpoint(bits,w,params)
        got=reverse_with_reachable(x,W,w,params,levels)
        assert got==bits,(w,bits,x,got)
    return levels


def main():
    # Deterministically discovered candidates.
    cases={
        2:[[(0,2),(1,0)],[(1,2),(0,0)],[(1,1),(1,2)]],
        3:[[(2,2),(2,3)],[(0,1),(0,3)],[(2,6),(2,7)]],
        4:[[(3,1),(3,2)],[(1,15),(1,14)],[(0,12),(0,11)]],
    }
    for w,p in cases.items():
        levels=verify(w,p)
        W=2*w
        print('FULL_CAPACITY','layer_bits',w,'endpoint_bits',W,
              'depth',W,'final_distinct',len(levels[-1]),'params',p)

if __name__=='__main__':main()

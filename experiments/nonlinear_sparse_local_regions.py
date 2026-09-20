"""Nonlinear state-dependent local reverse regions for sparse innovations.

We test whether a current endpoint can reveal the latest branch by membership in
two disjoint nonlinear regions, rather than by a time-only parity mask.

State X is W bits. Public universe U_t supplies masks/rotations. The branch law is
a reversible Feistel-like permutation on two halves plus an innovation-dependent
nonlinear involution. Decoder receives only (X_{t+1}, t, public laws) and tests a
small state-dependent invariant. No trajectory table/rank is used.

This first gate is deliberately small enough for exhaustive reachable-set
validation, then scales the same law to 256/512-bit sampled trajectories.
"""
from __future__ import annotations
from itertools import product
import random

def msk(w): return (1<<w)-1
def rotl(x,r,w):
    r%=w;m=msk(w)
    return ((x<<r)|(x>>(w-r)))&m if r else x&m

def public(t,w):
    m=msk(w)
    a=((t+1)*0x9E3779B97F4A7C15)&m
    b=((t+3)*0xD1B54A32D192ED03)&m
    return a or 1,b or 1

def f(v,t,w):
    a,b=public(t,w)
    return (rotl(v,(t%max(1,w-1))+1,w) ^ (v&rotl(v,3,w)) ^ a ^ b)&msk(w)

def marker(h,v,t,w):
    # nonlinear state-dependent branch observable
    a,b=public(t,w)
    z=(h ^ rotl(v,5,w) ^ (h&rotl(v,2,w)) ^ a)
    z ^= z>>1; z ^= z>>3
    return z&1

def forward(s,e,t,w):
    h,v=s;m=msk(w)
    # Base Feistel is reversible.
    hp=v
    vp=(h ^ f(v,t,w))&m
    # Innovation toggles a branch marker by changing one public coordinate.
    # Search below tests whether this remains locally observable after evolution.
    if e:
        vp ^= 1
    return hp,vp

def reachable(T,w,K):
    levels=[{(0,0,0)}] # h,v,used innovations
    for t in range(T):
        nxt=set()
        for h,v,k in levels[-1]:
            for e in (0,1):
                if k+e<=K:
                    hp,vp=forward((h,v),e,t,w)
                    nxt.add((hp,vp,k+e))
        levels.append(nxt)
    return levels

def local_branch_collision(T,w,K):
    levels=reachable(T,w,K)
    for t in range(T):
        seen={}
        for h,v,k in levels[t]:
            for e in (0,1):
                if k+e>K:continue
                y=forward((h,v),e,t,w)
                key=y
                old=seen.get(key)
                if old is not None and old[0]!=e:
                    return t,old,(e,(h,v,k)),y
                seen[key]=(e,(h,v,k))
    return None

def marker_accuracy(T,w,K):
    levels=reachable(T,w,K); good=total=0
    for t in range(T):
        # Calibrate orientation from public zero predecessor.
        y0=forward((0,0),0,t,w); y1=forward((0,0),1,t,w)
        m0=marker(*y0,t,w);m1=marker(*y1,t,w)
        if m0==m1: continue
        for h,v,k in levels[t]:
            for e in (0,1):
                if k+e>K:continue
                y=forward((h,v),e,t,w)
                pred=int(marker(*y,t,w)==m1)
                good+=pred==e;total+=1
    return good,total

def main():
    for w,T,K in [(4,8,2),(5,10,2),(6,12,2),(8,16,2)]:
        col=local_branch_collision(T,w,K)
        good,total=marker_accuracy(T,w,K)
        print("NONLINEAR_REGION_GATE","W",2*w,"T",T,"K",K,
              "branch_image_collision",col,
              "marker_accuracy",good,"/",total)
    print("NOTE: collision-free branch images are necessary for local reverse; the simple marker is only a candidate observable.")

if __name__=="__main__":main()

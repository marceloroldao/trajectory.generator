"""Analyze whether joint dyadic address admits direct piecewise update A_{t+1}=Psi(A_t,t,z).

For each time t and admissible z, enumerate the exact mapping from joint rank A_t
to joint rank A_{t+1}. Compress consecutive source ranks whose target obeys
A' = A + delta into affine slope-1 intervals. Also test more general constant
integer slope over runs.

This is an analysis of the rank permutation, not a new codec.
"""
from __future__ import annotations
from collections import defaultdict
from joint_dyadic_address import total_count, unrank_forest, append_joint
from standalone_four_bit_codec import initial_private, allowed


def endpoint_of(rank,t):
    s,f=unrank_forest(rank,t)
    return initial_private(s) if t==0 else f[-1].end


def mapping(t,z):
    out=[]
    for a in range(total_count(t)):
        p=endpoint_of(a,t)
        if allowed(p,z,t%3):
            out.append((a,append_joint(a,t,z)))
    return out


def slope1_runs(pairs):
    if not pairs:return []
    runs=[];s=pairs[0][0];pa,py=pairs[0];d=py-pa
    for a,y in pairs[1:]:
        if a==pa+1 and y==py+1 and y-a==d:
            pa,py=a,y;continue
        runs.append((s,pa,d));s=a;pa,py=a,y;d=y-a
    runs.append((s,pa,d));return runs


def affine_runs(pairs):
    if not pairs:return []
    if len(pairs)==1:return [(pairs[0][0],pairs[0][0],0,pairs[0][1])]
    runs=[];sidx=0
    while sidx<len(pairs):
        if sidx==len(pairs)-1:
            a,y=pairs[sidx];runs.append((a,a,0,y));break
        a0,y0=pairs[sidx];a1,y1=pairs[sidx+1]
        if a1!=a0+1:
            runs.append((a0,a0,0,y0));sidx+=1;continue
        m=y1-y0;b=y0-m*a0;e=sidx+1
        while e+1<len(pairs):
            a,y=pairs[e+1]
            if a!=pairs[e][0]+1 or y!=m*a+b:break
            e+=1
        runs.append((a0,pairs[e][0],m,b));sidx=e+1
    return runs


def main():
    print('t z domain slope1_runs general_affine_runs max_slope1_len max_affine_len')
    first_nontrivial=None
    for t in range(0,19):
        for z in (0,1):
            ps=mapping(t,z);r1=slope1_runs(ps);ra=affine_runs(ps)
            ml1=max((b-a+1 for a,b,_ in r1),default=0)
            mla=max((b-a+1 for a,b,_,_ in ra),default=0)
            print(t,z,len(ps),len(r1),len(ra),ml1,mla)
            if first_nontrivial is None and len(r1)>1:first_nontrivial=(t,z,len(ps),len(r1))
    print('first_nontrivial',first_nontrivial)

    # Moderate horizons: enumerate mappings while counts are still manageable.
    for t in (20,24,28,32,36,40):
        row=[]
        for z in (0,1):
            ps=mapping(t,z);r1=slope1_runs(ps);ra=affine_runs(ps)
            row.append((z,len(ps),len(r1),len(ra),max((b-a+1 for a,b,_ in r1),default=0)))
        print('moderate',t,row)

    print('interpretation: few slope-1 intervals => direct offset law plausible; rapid fragmentation => need dyadic carry state or richer public index')

if __name__=='__main__':main()

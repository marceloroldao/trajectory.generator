"""Search compact nonlinear observables for local branch inference.

Given sparse reachable predecessor states, derive candidate Boolean observables
from current (H,V,U_t) using XOR/AND/rotations. Score whether one observable
separates innovation/no-innovation images at every tested time. This is a search
for a LAW, not a trajectory lookup table: one formula must generalize across
all reachable states and times.
"""
from __future__ import annotations
from nonlinear_sparse_local_regions import reachable,forward,rotl,public

def features(h,v,t,w):
    a,b=public(t,w)
    xs=[
        h,v,h^v,h&v,
        rotl(h,1,w),rotl(v,1,w),
        h&rotl(v,1,w),v&rotl(h,1,w),
        h&rotl(v,2,w),v&rotl(h,2,w),
        h^rotl(v,3,w),v^rotl(h,3,w),
        h^a,v^b,(h&a)^(v&b),
    ]
    # Collapse each relation to several public parity-like local bits.
    out=[]
    for x in xs:
        out += [x&1,(x.bit_count()&1),((x^(x>>1))&1),((x^(x>>3))&1)]
    return tuple(out)

def score(w,T,K):
    levels=reachable(T,w,K)
    nfeat=len(features(0,0,0,w))
    good=[0]*nfeat; total=0
    # orientation is allowed to depend on public phase t mod 3 only.
    orient=[[None]*nfeat for _ in range(3)]
    records=[]
    for t in range(T):
        for h,v,k in levels[t]:
            for e in (0,1):
                if k+e>K:continue
                y=forward((h,v),e,t,w)
                fs=features(*y,t,w)
                records.append((t,e,fs));total+=1
    for j in range(nfeat):
        ok=True;count=0
        for phase in range(3):
            vals=[(e,fs[j]) for t,e,fs in records if t%3==phase]
            if not vals:continue
            # try identity or inversion
            c0=sum(v==e for e,v in vals);c1=sum((1-v)==e for e,v in vals)
            orient[phase][j]=0 if c0>=c1 else 1
            count+=max(c0,c1)
        good[j]=count
    best=max(range(nfeat),key=lambda j:good[j])
    return best,good[best],total,orient[0][best],orient[1][best],orient[2][best]

def main():
    for w,T,K in [(4,8,2),(5,10,2),(6,12,2),(8,16,2)]:
        print("NONLINEAR_OBSERVABLE_SEARCH","W",2*w,"T",T,"K",K,
              "best",score(w,T,K))

if __name__=="__main__":main()

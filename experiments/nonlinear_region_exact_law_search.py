"""Exact search for a compact nonlinear local reverse law.

Search Boolean relations Q(H',V',U_t) that distinguish branch e for EVERY
reachable state under a K-sparse promise. A candidate must be one public formula
(shared across trajectories); only a 3-phase orientation bit may vary.

The search builds a richer algebra of primitive state relations and all XORs of
one/two/three primitive Boolean observables. Exhaustive small-universe testing
makes a 100% result a proof for the tested (W,T,K), not a sample.
"""
from __future__ import annotations
from itertools import combinations
from nonlinear_sparse_local_regions import reachable,forward,rotl,public

def primitives(h,v,t,w):
    a,b=public(t,w)
    words=[
        h,v,h^v,h&v,h|v,
        rotl(h,1,w),rotl(v,1,w),rotl(h,2,w),rotl(v,2,w),
        h&rotl(v,1,w),v&rotl(h,1,w),
        h&rotl(v,2,w),v&rotl(h,2,w),
        h^rotl(v,3,w),v^rotl(h,3,w),
        h^a,v^b,(h&a)^(v&b),(h^a)&(v^b),
    ]
    out=[]
    for x in words:
        out.extend((x&1,x.bit_count()&1,(x^(x>>1))&1,(x^(x>>3))&1))
    return tuple(out)

def records(w,T,K):
    levels=reachable(T,w,K); out=[]
    for t in range(T):
        for h,v,k in levels[t]:
            for e in (0,1):
                if k+e>K: continue
                hp,vp=forward((h,v),e,t,w)
                out.append((t%3,e,primitives(hp,vp,t,w)))
    return out

def exact_formula(w,T,K,max_terms=3):
    rec=records(w,T,K); n=len(rec[0][2])
    # Formula is XOR of selected primitive bits. For each phase it may be
    # complemented, but within that phase it must equal e on every record.
    for size in range(1,max_terms+1):
        for idx in combinations(range(n),size):
            phase_values=[set(),set(),set()]
            for p,e,f in rec:
                q=0
                for j in idx:q^=f[j]
                phase_values[p].add(q^e)
                if len(phase_values[p])>1: break
            if all(len(s)<=1 for s in phase_values):
                orient=tuple(next(iter(s)) if s else 0 for s in phase_values)
                return idx,orient,len(rec)
    return None,None,len(rec)

def main():
    cases=[(4,8,2),(5,10,2),(6,12,2),(7,14,2),(8,16,2)]
    for w,T,K in cases:
        idx,orient,n=exact_formula(w,T,K,3)
        print("EXACT_NONLINEAR_LAW","W",2*w,"T",T,"K",K,
              "formula",idx,"phase_xor",orient,"records",n,
              "PASS",idx is not None)

if __name__=="__main__":main()

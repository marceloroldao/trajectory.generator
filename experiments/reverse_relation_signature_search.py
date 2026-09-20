"""Search compact relation signatures for exact sparse reverse.

Instead of rebuilding the full reachable manifold, search a bounded signature
S(X,U_t,K_remaining) whose value separates predecessor branches on exhaustive
small universes. A signature is a tuple of public nonlinear observables. The
same selected observables must work at every t; phase may only alter orientation.

This is an intermediate bridge between an exponential manifold decoder and a
constant/local reverse law.
"""
from itertools import combinations
from nonlinear_sparse_local_regions import rotl,public
from partition_preserving_universe_search import step

def levels(w,T,K,p):
    out=[{(0,0,0)}]
    for t in range(T):
        nxt=set()
        for h,v,k in out[-1]:
            for e in (0,1):
                if k+e<=K:
                    y=step((h,v),e,t,w,p)
                    nxt.add((y[0],y[1],k+e))
        out.append(nxt)
    return out

def obs(h,v,t,w):
    a,b=public(t,w)
    words=(h,v,h^v,h&v,h|v,h^rotl(v,1,w),v^rotl(h,1,w),
           h&rotl(v,1,w),v&rotl(h,1,w),h^a,v^b,(h&a)^(v&b))
    z=[]
    for x in words:z.extend((x&1,x.bit_count()&1,(x^(x>>1))&1))
    return tuple(z)

def dataset(w,T,K,p):
    L=levels(w,T,K,p); rec=[]
    for t in range(T):
        for h,v,k in L[t]:
            for e in (0,1):
                if k+e>K:continue
                hp,vp=step((h,v),e,t,w,p)
                rec.append((t,e,obs(hp,vp,t,w)))
    return rec

def signature_separates(rec,idx):
    # For each t, identical signature may never represent both branches.
    seen={}
    for t,e,f in rec:
        sig=tuple(f[j] for j in idx)
        key=(t,sig)
        old=seen.get(key)
        if old is not None and old!=e:return False
        seen[key]=e
    return True

def search(w,T,K,p,max_bits=5):
    rec=dataset(w,T,K,p);n=len(rec[0][2])
    for size in range(1,max_bits+1):
        for idx in combinations(range(n),size):
            if signature_separates(rec,idx):
                return idx,len(rec)
    return None,len(rec)

def main():
    laws=[(1,2,3,1,5),(2,1,5,3,7),(3,2,9,1,11)]
    for p in laws:
        for w,T,K in ((3,6,2),(4,8,2),(5,10,2),(6,12,2)):
            sig,n=search(w,T,K,p)
            print("REVERSE_SIGNATURE","law",p,"W",2*w,"T",T,"K",K,
                  "signature",sig,"bits",None if sig is None else len(sig),
                  "records",n,"PASS",sig is not None)

if __name__=="__main__":main()

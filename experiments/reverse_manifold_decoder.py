"""Reference reverse decoder using only the mathematical sparse manifold.

This is NOT the desired final decoder because it reconstructs reachable sets
during decoding. Its role is a proof/control: when branch images are disjoint,
endpoint + T + public law + K is sufficient to reverse exactly.

No trajectory table is stored in the endpoint. The decoder recomputes the
allowed manifold from public laws, which can be exponentially expensive.
"""
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

def encode(bits,w,p):
    s=(0,0)
    for t,e in enumerate(bits):s=step(s,e,t,w,p)
    return s

def decode(endpoint,T,w,K,p):
    L=levels(w,T,K,p)
    cur=endpoint;used_max=K;bits=[]
    for t in range(T-1,-1,-1):
        candidates=[]
        for h,v,k in L[t]:
            for e in (0,1):
                if k+e<=K and step((h,v),e,t,w,p)==cur:
                    candidates.append(((h,v),e,k))
        # Endpoint-only exact reverse requires one branch/predecessor.
        if len(candidates)!=1:
            raise ValueError(("ambiguous reverse",t,cur,len(candidates)))
        prev,e,k=candidates[0]
        bits.append(e);cur=prev
    bits.reverse()
    return bits

def main():
    # Reference cases only; laws are controls until cross-width gate validates.
    laws=[(1,2,3,1,5),(2,1,5,3,7),(3,2,9,1,11)]
    for p in laws:
        for w,T,K in ((3,6,2),(4,8,2),(5,10,2)):
            checked=0;ok=True
            # enumerate all bit words with <=K innovations
            for word in range(1<<T):
                bits=[(word>>i)&1 for i in range(T)]
                if sum(bits)>K:continue
                checked+=1
                ep=encode(bits,w,p)
                try:got=decode(ep,T,w,K,p)
                except ValueError:
                    ok=False;break
                if got!=bits:
                    ok=False;break
            print("MANIFOLD_REVERSE","law",p,"W",2*w,"T",T,"K",K,
                  "checked",checked,"PASS",ok)

if __name__=="__main__":main()

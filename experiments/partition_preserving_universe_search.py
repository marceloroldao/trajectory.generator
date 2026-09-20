"""Search small nonlinear universes that preserve local branch partitions.

A candidate is accepted only when I0(t) and I1(t) are disjoint at every tested
time for every K-sparse reachable predecessor. Search parameters are PUBLIC law
parameters, not trajectory-specific data.

The experiment searches Feistel-style laws and innovation kicks derived from
the current public phase. Passing small exhaustive gates is only a candidate;
the same parameterized law must later scale without retuning per payload.
"""
from itertools import product

def mask(w):return (1<<w)-1
def rotl(x,r,w):
    r%=w;m=mask(w)
    return ((x<<r)|(x>>(w-r)))&m if r else x&m

def F(v,t,w,r1,r2,c):
    return (rotl(v,r1,w) ^ (v&rotl(v,r2,w)) ^ ((t+1)*c))&mask(w)

def step(s,e,t,w,p):
    r1,r2,c,krot,kmul=p
    h,v=s
    hp=v
    vp=(h^F(v,t,w,r1,r2,c))&mask(w)
    if e:
        # State/public-phase dependent nonlinear branch kick.
        kick=(rotl(h^v,krot,w)^((t+1)*kmul))&mask(w)
        vp^=kick or 1
    return hp,vp

def gate(w,T,K,p):
    level={(0,0,0)}
    for t in range(T):
        images=[set(),set()];nxt=set()
        for h,v,k in level:
            for e in (0,1):
                if k+e>K:continue
                y=step((h,v),e,t,w,p)
                images[e].add(y);nxt.add((y[0],y[1],k+e))
        if images[0]&images[1]:
            return False,t,len(level)
        level=nxt
    return True,T,len(level)

def search(w,T,K,limit=20):
    found=[]
    constants=[1,3,5,7,9,11,13,15]
    for r1,r2,c,krot,kmul in product(range(1,min(w,5)),range(1,min(w,5)),constants,range(1,min(w,5)),constants):
        p=(r1,r2,c&mask(w),krot,kmul&mask(w))
        ok,depth,n=gate(w,T,K,p)
        if ok:
            found.append((p,depth,n))
            if len(found)>=limit:break
    return found

def main():
    for w,T,K in ((3,6,2),(4,8,2),(5,10,2),(6,12,2),(6,12,3)):
        ans=search(w,T,K)
        print("PARTITION_SEARCH","W",2*w,"T",T,"K",K,
              "found",len(ans),"examples",ans[:3])

if __name__=="__main__":main()

"""Exhaustive endpoint-injectivity tests for the original trajectory.generator objective.

No external rank, history, side channel or restricted admissible language is used.
The decoder is simply a lookup used by the *test harness* to decide whether the
endpoint map is injective; it is not part of the candidate machine.

We test small widths exhaustively so failure/success is exact.
"""
from __future__ import annotations
from dataclasses import dataclass
from itertools import product


def rotl(x:int,r:int,w:int)->int:
    m=(1<<w)-1; r%=w
    return ((x<<r)|(x>>(w-r)))&m if r else x&m

@dataclass(frozen=True)
class Result:
    name:str; layer_bits:int; total_bits:int; T:int; distinct:int; total_inputs:int; max_mult:int
    @property
    def injective(self): return self.distinct==self.total_inputs

# ---- Candidate A: two-layer reversible shift-register-like coupling ----
def step_a(state,bit,t,w):
    h,v=state; m=(1<<w)-1
    # public universe phase acts every third cycle, independent of input
    if t%3==0:
        h=rotl(h,1,w)^v
        v=rotl(v,2,w)^((t*3+1)&m)
    # local data coupling; no extra retained data outside (h,v)
    nh=(rotl(h,1,w)^v^bit)&m
    nv=(rotl(v,1,w)^h^(bit<<(t%w)))&m
    return nh,nv

# ---- Candidate B: Feistel-like two-layer permutation selected by bit ----
def step_b(state,bit,t,w):
    h,v=state; m=(1<<w)-1
    k=((t+1)*0x5B)&m
    f=(rotl(v,(t%w)+1,w)^k)&m
    if bit==0:
        return v,(h^f)&m
    # alternate reversible branch
    g=(rotl(v,(2*t+1)%w,w)^((k<<1)&m)^1)&m
    return v,(h^g)&m

# ---- Candidate C: layered orbit with public universe kick and signed direction ----
def step_c(state,bit,t,w):
    h,v=state; m=(1<<w)-1
    if t%3==0:
        # deterministic universe motion
        h=(h + (2*t+1))&m
        v=rotl(v^h,1,w)
    direction=1 if bit else -1
    h=(h + direction*(v|1))&m
    v=rotl(v^h^(bit*((t+1)&m)),1,w)
    return h,v

CANDIDATES=(('coupled',step_a),('feistel_branch',step_b),('orbit_signed',step_c))


def endpoint(step_fn,bits,w):
    s=(0,0)
    for t,b in enumerate(bits): s=step_fn(s,b,t,w)
    return s


def exhaustive(name,step_fn,w,T):
    buckets={}
    for bits in product((0,1),repeat=T):
        x=endpoint(step_fn,bits,w)
        buckets[x]=buckets.get(x,0)+1
    return Result(name,w,2*w,T,len(buckets),1<<T,max(buckets.values()))


def main():
    for w in (2,3,4,5,6):
        W=2*w
        print(f'--- layer_bits={w} total_endpoint_bits={W} ---')
        for name,fn in CANDIDATES:
            first_fail=None
            for T in range(1,min(W+3,14)):
                r=exhaustive(name,fn,w,T)
                print(name,'T',T,'distinct',r.distinct,'/',r.total_inputs,'max_mult',r.max_mult,'injective',r.injective)
                if not r.injective and first_fail is None:first_fail=T
            print(name,'first_fail',first_fail)
        # theorem sanity: T=W+1 must be impossible for any map into 2^W endpoints.
        T=W+1
        if T<=13:
            for name,fn in CANDIDATES:
                r=exhaustive(name,fn,w,T)
                assert not r.injective
        print()

if __name__=='__main__': main()

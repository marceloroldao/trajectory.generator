"""Use exact invariant modes to drive the horizon-free trajectory address.

The 3-step public count field V_n=C_{3n} has characteristic polynomial

  x (x-1)^2 (x+1)^2 (x^3-2x^2+x-1).

Because the four factors are pairwise coprime, we construct exact rational CRT
projectors and decompose the fixed initial count vector into four invariant
parts.  The neutral and alternating Jordan sectors are explicit functions of
n, the transient dies after one Floquet period, and only the cubic growth
sector needs a live 3-scalar state (a,b,c).

We then replace counts_at(t) in the horizon-free endpoint-rank codec with this
modal field and demand exact encode/decode equivalence through T=218.
"""
from __future__ import annotations

from fractions import Fraction
from functools import lru_cache
import random

from count_vector_recurrence import mat_phase, mm, mv, vec0
from standalone_four_bit_codec import initial_private, allowed, step
from horizon_free_endpoint_rank import counts_at as dp_counts_at

STATES = tuple((a,b,c,d) for a in (0,1) for b in (0,1) for c in (0,1) for d in (0,1))
IDX={p:i for i,p in enumerate(STATES)}
INITIAL_TO_PREFIX={initial_private(s):s for s in range(8)}

# low -> high coefficients
F0=[Fraction(0),Fraction(1)]                         # x
FP=[Fraction(1),Fraction(-2),Fraction(1)]           # (x-1)^2
FM=[Fraction(1),Fraction(2),Fraction(1)]            # (x+1)^2
FG=[Fraction(-1),Fraction(1),Fraction(-2),Fraction(1)] # x^3-2x^2+x-1
FACTORS=(('transient',F0),('plus',FP),('minus',FM),('growth',FG))


def trim(p):
    p=list(p)
    while len(p)>1 and p[-1]==0:p.pop()
    return p

def padd(a,b):
    n=max(len(a),len(b)); out=[Fraction(0)]*n
    for i in range(n):out[i]=(a[i] if i<len(a) else 0)+(b[i] if i<len(b) else 0)
    return trim(out)

def psub(a,b):return padd(a,[-x for x in b])
def pmul(a,b):
    out=[Fraction(0)]*(len(a)+len(b)-1)
    for i,x in enumerate(a):
        for j,y in enumerate(b):out[i+j]+=x*y
    return trim(out)
def pdivmod(a,b):
    a=trim(a);b=trim(b)
    if b==[0]:raise ZeroDivisionError
    q=[Fraction(0)]*max(1,len(a)-len(b)+1); r=a[:]
    while not (len(r)==1 and r[0]==0) and len(r)>=len(b):
        k=len(r)-len(b); c=r[-1]/b[-1]; q[k]+=c
        sub=[Fraction(0)]*k+[c*x for x in b]
        r=psub(r,sub)
    return trim(q),trim(r)
def pmod(a,m):return pdivmod(a,m)[1]
def pegcd(a,b):
    r0,r1=trim(a),trim(b); s0,s1=[Fraction(1)],[Fraction(0)]; t0,t1=[Fraction(0)],[Fraction(1)]
    while r1 != [Fraction(0)]:
        q,r=pdivmod(r0,r1)
        r0,r1=r1,r
        s0,s1=s1,psub(s0,pmul(q,s1))
        t0,t1=t1,psub(t0,pmul(q,t1))
    lead=r0[-1]
    return [x/lead for x in r0],[x/lead for x in s0],[x/lead for x in t0]


def matrix_frac(A):return [[Fraction(x) for x in row] for row in A]
def mvq(A,v):return [sum(A[i][j]*v[j] for j in range(len(v))) for i in range(len(A))]
def vadd(*vs):return [sum(v[i] for v in vs) for i in range(len(vs[0]))]
def vsub(a,b):return [x-y for x,y in zip(a,b)]
def vscale(c,v):return [c*x for x in v]

def apply_poly(F,p,v):
    out=[Fraction(0)]*len(v); cur=[Fraction(x) for x in v]
    for c in p:
        out=vadd(out,vscale(c,cur))
        cur=mvq(F,cur)
    return out


def projectors(char):
    out={}
    for name,f in FACTORS:
        q,rem=pdivmod(char,f); assert rem==[0]
        g,s,_=pegcd(q,f); assert g==[Fraction(1)]
        e=pmod(pmul(q,s),char)
        assert pmod(e,f)==[Fraction(1)]
        for oname,of in FACTORS:
            if oname!=name: assert pmod(e,of)==[Fraction(0)]
        out[name]=e
    return out


def setup_modes():
    M=[matrix_frac(mat_phase(p)) for p in range(3)]
    F=matrix_frac(mm(mat_phase(2),mm(mat_phase(1),mat_phase(0))))
    char=[Fraction(1)]
    for _,f in FACTORS:char=pmul(char,f)
    proj=projectors(char)
    v0=[Fraction(x) for x in vec0()]
    parts={name:apply_poly(F,e,v0) for name,e in proj.items()}
    assert vadd(*parts.values())==v0

    plus0=parts['plus']; plusN=vsub(mvq(F,plus0),plus0)
    assert mvq(F,plusN)==plusN
    minus0=parts['minus']; minusN=vadd(mvq(F,minus0),minus0)
    assert mvq(F,minusN)==vscale(-1,minusN)
    trans0=parts['transient']; assert mvq(F,trans0)==[0]*16

    g0=parts['growth']; g1=mvq(F,g0); g2=mvq(F,g1)
    assert mvq(F,g2)==vadd(g0,vscale(-1,g1),vscale(2,g2))
    return M,F,trans0,plus0,plusN,minus0,minusN,(g0,g1,g2)

M,F,TRANS0,PLUS0,PLUSN,MINUS0,MINUSN,GBASE=setup_modes()


@lru_cache(maxsize=None)
def growth_amplitudes(n:int):
    a,b,c=Fraction(1),Fraction(0),Fraction(0)
    for _ in range(n):
        a,b,c=c,a-c,b+2*c
    return a,b,c


@lru_cache(maxsize=None)
def phase0_vector(n:int):
    a,b,c=growth_amplitudes(n)
    growth=vadd(vscale(a,GBASE[0]),vscale(b,GBASE[1]),vscale(c,GBASE[2]))
    plus=vadd(PLUS0,vscale(n,PLUSN))
    minus=vscale(Fraction((-1)**n),vsub(MINUS0,vscale(n,MINUSN)))
    trans=TRANS0 if n==0 else [Fraction(0)]*16
    out=vadd(trans,plus,minus,growth)
    assert all(x.denominator==1 and x>=0 for x in out)
    return tuple(int(x) for x in out)


@lru_cache(maxsize=None)
def modal_counts_at(t:int):
    if t<0:raise ValueError
    n,r=divmod(t,3)
    v=list(phase0_vector(n))
    for ph in range(r):v=[int(x) for x in mv(M[ph],v)]
    return tuple((STATES[i],v[i]) for i in range(16) if v[i])


def counts_dict(t:int):
    return dict(modal_counts_at(t))


def state_offsets(counts):
    off=0; d={}
    for p in sorted(counts):d[p]=off;off+=counts[p]
    return d,off

def opts(p,phase):return tuple(z for z in (0,1) if allowed(p,z,phase))

def unpack_global(a,t):
    c=counts_dict(t); offs,total=state_offsets(c)
    if not 0<=a<total:raise ValueError
    for p in sorted(c):
        if a<offs[p]+c[p]:return p,a-offs[p]
    raise AssertionError

def pack_global(p,r,t):
    c=counts_dict(t);offs,_=state_offsets(c)
    if p not in c or not 0<=r<c[p]:raise ValueError
    return offs[p]+r

def incoming_blocks(q,tprev):
    c=counts_dict(tprev);phase=tprev%3;off=0;out=[]
    for p in sorted(c):
        for z in opts(p,phase):
            if step(p,z,phase)==q:
                out.append((off,off+c[p],p,z,c[p]));off+=c[p]
    return out

def forward_address(a,z,t):
    p,r=unpack_global(a,t);ph=t%3
    if not allowed(p,z,ph):raise ValueError
    q=step(p,z,ph)
    for lo,hi,pp,zz,_ in incoming_blocks(q,t):
        if pp==p and zz==z:return pack_global(q,lo+r,t+1)
    raise AssertionError

def decode_address(a,T):
    p,r=unpack_global(a,T);zs=[]
    for tp in range(T-1,-1,-1):
        hit=None
        for lo,hi,pp,z,_ in incoming_blocks(p,tp):
            if lo<=r<hi:hit=(pp,z,r-lo);break
        if hit is None:raise AssertionError
        p,z,r=hit;zs.append(z)
    assert p in INITIAL_TO_PREFIX and r==0
    s=INITIAL_TO_PREFIX[p]
    return [(s>>2)&1,(s>>1)&1,s&1]+list(reversed(zs))
def encode_path(path):
    s=(path[0]<<2)|(path[1]<<1)|path[2];p=initial_private(s);a=pack_global(p,0,0)
    for t,z in enumerate(path[3:]):a=forward_address(a,int(z),t)
    return a,len(path)-3


def main():
    for t in range(221):
        assert counts_dict(t)==dp_counts_at(t),t
    print('modal_count_field_equivalence_0_220 ok')
    print('public_live_amplitudes 3')
    for n in (0,1,2,10,50,72):print('growth_amp',n,growth_amplitudes(n))

    rng=random.Random(20260910)
    for T in range(10):
        total=sum(counts_dict(T).values())
        for a in range(total):
            p=decode_address(a,T);aa,tt=encode_path(p);assert aa==a and tt==T
        print('exhaustive_modal_roundtrip',T,total,'ok')
    for T in (16,64,128,200,218):
        total=sum(counts_dict(T).values())
        for _ in range(200):
            a=rng.randrange(total);p=decode_address(a,T);aa,tt=encode_path(p);assert aa==a and tt==T
        print('random_modal_roundtrip',T,200,'ok')
    n218=sum(counts_dict(218).values());n219=sum(counts_dict(219).values())
    print('count218',n218);print('count219',n219)
    assert n218==9131204053820206208 and n219==10214739716735776832

if __name__=='__main__':main()

"""Positive control for the original endpoint-only objective.

This intentionally reaches the information-theoretic limit, not beyond it.
It proves the test harness can recognize exact recovery from `(X_final,T)` only.

State: W bits, viewed as two logical layers but counted together.
Law: a public invertible universe permutation followed by injection of one new
bit into a fresh causal direction.  The implementation uses a controllable
linear recurrence (cyclic shift + input) and an invertible public scrambling
coordinate transform.

Because the construction is conjugate to a shift register, it is a *control*,
not the desired final discovery.  It is explicitly labelled so we do not
confuse 'works' with 'novel trajectory physics'.
"""
from __future__ import annotations
from itertools import product


def rotl(x:int,r:int,W:int)->int:
    m=(1<<W)-1;r%=W
    return ((x<<r)|(x>>(W-r)))&m if r else x&m

def rotr(x:int,r:int,W:int)->int:
    m=(1<<W)-1;r%=W
    return ((x>>r)|(x<<(W-r)))&m if r else x&m

# Invertible xorshift coordinate transform and inverse.
def scramble(x:int,W:int)->int:
    m=(1<<W)-1
    # triangular XOR maps over GF(2), hence invertible
    x ^= (x<<1)&m
    x ^= x>>2
    return x&m

def _undo_rshift_xor(y:int,s:int,W:int)->int:
    x=0
    # recover from MSB to LSB
    for i in range(W-1,-1,-1):
        bit=(y>>i)&1
        if i+s<W: bit ^= (x>>(i+s))&1
        x |= bit<<i
    return x

def _undo_lshift_xor(y:int,s:int,W:int)->int:
    x=0
    for i in range(W):
        bit=(y>>i)&1
        if i-s>=0: bit ^= (x>>(i-s))&1
        x |= bit<<i
    return x

def unscramble(y:int,W:int)->int:
    x=_undo_rshift_xor(y,2,W)
    x=_undo_lshift_xor(x,1,W)
    return x&((1<<W)-1)


def step(x:int,b:int,t:int,W:int)->int:
    # Work in hidden canonical coordinate u; endpoint exposed to caller remains x.
    u=unscramble(x,W)
    u=rotl(u,1,W)^b
    # deterministic public universe phase; conjugated coordinate changes are
    # already represented by scramble/unscramble, no side state is retained.
    return scramble(u,W)


def encode(bits,W):
    x=scramble(0,W)
    for t,b in enumerate(bits):
        if t>=W: raise ValueError('arbitrary exact control only defined through T<=W')
        x=step(x,int(b),t,W)
    return x


def decode(x,T,W):
    if not 0<=T<=W: raise ValueError
    u=unscramble(x,W)
    # After T cyclic shifts from zero, chronological bits occupy low T bits in
    # reverse insertion order under this convention.
    out=[]
    for _ in range(T):
        b=u&1
        out.append(b)
        u=rotr(u^b,1,W)
    return list(reversed(out))


def exhaustive(W):
    for T in range(W+1):
        seen={}
        for bits in product((0,1),repeat=T):
            x=encode(bits,W)
            if x in seen:
                return False,('collision',W,T,seen[x],bits,x)
            seen[x]=bits
            rec=decode(x,T,W)
            if tuple(rec)!=bits:
                return False,('decode',W,T,bits,rec,x)
        assert len(seen)==1<<T
    return True,None


def main():
    for W in range(2,13):
        ok,err=exhaustive(W)
        print('W',W,'perfect_through_T_equals_W',ok,err)
        assert ok
    print('interpretation: endpoint-only exact arbitrary recovery is achievable up to W bits in a W-bit endpoint')
    print('non_claim: this control is conjugate to explicit bit accumulation and does not compress arbitrary information')

if __name__=='__main__':main()

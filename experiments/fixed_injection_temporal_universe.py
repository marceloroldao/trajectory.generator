"""Original-objective experiment: fixed local input injection, temporal universe only.

Unlike endpoint_controllability_general.py, the data bit does NOT get a
purpose-designed direction d_t.  Every bit enters through the same single state
coordinate d=1.  Only the public time-periodic universe maps A[t mod 3] spread
that local perturbation through the W-bit endpoint.

    x[t+1] = A[t mod 3] x[t] XOR d*b[t] XOR c[t]

The endpoint after T=W is

    x[W] = cbar XOR M b

and exact endpoint-only recovery is possible iff the controllability matrix M
has rank W.  This is still not compression: W arbitrary input bits are retained
in W endpoint bits.  It is a stricter test of the user's trajectory hypothesis
because the input channel itself is fixed/local and separation is produced by
the evolving universe.
"""
from __future__ import annotations
import random


def parity(x:int)->int:return x.bit_count()&1

def apply(A,x):return sum((parity(row&x)<<i) for i,row in enumerate(A))

def columns_to_rows(cols,W):
    rows=[0]*W
    for j,col in enumerate(cols):
        for i in range(W):
            if (col>>i)&1:rows[i]|=1<<j
    return tuple(rows)

def rank(rows,W):
    rows=list(rows);r=0
    for c in range(W):
        p=next((i for i in range(r,len(rows)) if (rows[i]>>c)&1),None)
        if p is None:continue
        rows[r],rows[p]=rows[p],rows[r]
        for i in range(len(rows)):
            if i!=r and ((rows[i]>>c)&1):rows[i]^=rows[r]
        r+=1
        if r==len(rows):break
    return r

def invert(A,W):
    rows=[A[i]|(1<<(W+i)) for i in range(W)]
    for c in range(W):
        p=next((i for i in range(c,W) if (rows[i]>>c)&1),None)
        if p is None:raise ValueError('singular')
        rows[c],rows[p]=rows[p],rows[c]
        for i in range(W):
            if i!=c and ((rows[i]>>c)&1):rows[i]^=rows[c]
    m=(1<<W)-1
    return tuple((row>>W)&m for row in rows)


def make_universe(W,seed,phase):
    """Sparse reversible linear map built only from public row shears/permutation."""
    rng=random.Random((seed<<3)+phase)
    rows=[1<<i for i in range(W)]
    r=1+rng.randrange(max(1,W-1))
    rows=rows[-r:]+rows[:-r]  # coordinate permutation
    for _ in range(2*W):
        i=rng.randrange(W);j=rng.randrange(W-1)
        if j>=i:j+=1
        rows[i]^=rows[j]      # elementary reversible shear
    A=tuple(rows)
    assert rank(A,W)==W
    return A


def propagated_columns(W,As,d=1):
    cols=[]
    for src in range(W):
        x=d
        for t in range(src+1,W):x=apply(As[t%3],x)
        cols.append(x)
    return cols

def affine_const(W,As):
    m=(1<<W)-1;x=0
    for t in range(W):
        c=((0x9E3779B97F4A7C15 ^ (t*0xD1B54A32D192ED03))&m)
        x=apply(As[t%3],x)^c
    return x

def encode(bits,W,As,d=1):
    m=(1<<W)-1;x=0
    for t,b in enumerate(bits):
        c=((0x9E3779B97F4A7C15 ^ (t*0xD1B54A32D192ED03))&m)
        x=apply(As[t%3],x)^c^(d if b else 0)
    return x

def decoder_matrix(W,As,d=1):
    M=columns_to_rows(propagated_columns(W,As,d),W)
    return M,invert(M,W)

def decode(y,W,As,d=1):
    M,Minv=decoder_matrix(W,As,d)
    z=y^affine_const(W,As)
    bvec=apply(Minv,z)
    return tuple((bvec>>i)&1 for i in range(W))

# Deterministic first seeds found by exhaustive seed scan 1..999.
SEEDS={16:2,32:4,63:2}


def main():
    rng=random.Random(20260914)
    for W,seed in SEEDS.items():
        As=[make_universe(W,seed,p) for p in range(3)]
        M,Minv=decoder_matrix(W,As,1)
        assert rank(M,W)==W
        tests=[]
        tests.extend(tuple(int(i==j) for i in range(W)) for j in range(W))
        tests += [tuple(rng.randrange(2) for _ in range(W)) for _ in range(500)]
        tests += [tuple(0 for _ in range(W)),tuple(1 for _ in range(W))]
        for bits in tests:
            y=encode(bits,W,As,1)
            got=decode(y,W,As,1)
            assert got==bits,(W,bits,y,got)
        print('FIXED_LOCAL_INJECTION_FULL_CAPACITY',
              'W',W,'seed',seed,'rank',rank(M,W),'tests',len(tests),
              'input_direction',1,'endpoint_only',True)

if __name__=='__main__':main()

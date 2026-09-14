"""General endpoint-only history recovery via controllability over GF(2).

Original objective contract:
    arbitrary W input bits -> natural W-bit endpoint -> exact recovery from endpoint+T
No external rank, trajectory table, restricted language, or side information.

For an affine time-varying binary system
    x[t+1] = A_t x[t] xor d_t*b[t] xor c_t,
the endpoint at T=W is
    x[W] = offset xor sum_j v_j b[j]
where v_j = A_{W-1}...A_{j+1} d_j.
Exact recovery of every W-bit input is equivalent to the W transported input
vectors v_j having rank W over GF(2).

This file constructs and validates a systematic full-rank family. The base
operator is an invertible companion/LFSR map C with one cyclic injection vector.
A public time-dependent change of coordinates U_t then gives
    A_t = U_{t+1} C U_t^{-1},  d_t = U_{t+1} d,
which preserves full controllability while making the natural state evolution
explicitly time-dependent. U_t carries no history and is reconstructed from t.

This does not compress arbitrary data: T=W is the information-theoretic limit.
"""
from __future__ import annotations
from dataclasses import dataclass
import random


def parity(x:int)->int:
    return x.bit_count() & 1


def mat_vec(rows, x, W):
    y=0
    for i,row in enumerate(rows):
        y |= parity(row & x) << i
    return y


def identity(W):
    return tuple(1<<i for i in range(W))


def mat_mul(A,B,W):
    out=[]
    for ar in A:
        r=0; m=ar
        while m:
            lsb=m & -m; k=lsb.bit_length()-1
            r ^= B[k]; m ^= lsb
        out.append(r)
    return tuple(out)


def inv_matrix(A,W):
    left=list(A); right=[1<<i for i in range(W)]
    for col in range(W):
        pivot=next((r for r in range(col,W) if (left[r]>>col)&1),None)
        if pivot is None: raise ValueError('singular')
        left[col],left[pivot]=left[pivot],left[col]
        right[col],right[pivot]=right[pivot],right[col]
        for r in range(W):
            if r!=col and ((left[r]>>col)&1):
                left[r]^=left[col]; right[r]^=right[col]
    assert tuple(left)==identity(W)
    return tuple(right)


def companion_rows(W):
    if W==1:return (1,)
    rows=[1<<(i+1) for i in range(W-1)]
    rows.append((1<<0)|(1<<1))
    return tuple(rows)


def rank_vectors(cols,W):
    basis=[0]*W; rank=0
    for v in cols:
        x=v
        while x:
            p=x.bit_length()-1
            if basis[p]: x ^= basis[p]
            else:
                basis[p]=x; rank+=1; break
    return rank


def find_cyclic_injection(C,W):
    for bit in range(W):
        d=1<<bit; cols=[]; x=d
        for _ in range(W):
            cols.append(x); x=mat_vec(C,x,W)
        if rank_vectors(cols,W)==W:return d
    raise AssertionError('no cyclic basis vector found')


def public_U(t,W):
    I=list(identity(W)); ph=t%3
    if W==1:return tuple(I)
    if ph==0:
        for i in range(1,W): I[i]^=1<<(i-1)
    elif ph==1:
        for i in range(W-1): I[i]^=1<<(i+1)
    else:
        I=[1<<((i+1)%W) for i in range(W)]
    return tuple(I)


def law_at(t,W,C,d):
    Ut=public_U(t,W); Un=public_U(t+1,W)
    Uti=inv_matrix(Ut,W)
    A=mat_mul(mat_mul(Un,C,W),Uti,W)
    dv=mat_vec(Un,d,W)
    c=mat_vec(Un, ((t+1)*0x9E3779B1) & ((1<<W)-1), W)
    return A,dv,c


def decoder_rows(cols,W):
    rows=[]
    for outbit in range(W):
        row=0
        for j,col in enumerate(cols): row |= ((col>>outbit)&1)<<j
        rows.append(row)
    return inv_matrix(tuple(rows),W)


@dataclass(frozen=True)
class Model:
    W:int
    laws:tuple
    offset:int
    cols:tuple
    decoder:tuple
    injection:int


def build_model(W:int)->Model:
    C=companion_rows(W); d=find_cyclic_injection(C,W)
    laws=tuple(law_at(t,W,C,d) for t in range(W))

    def enc(bits):
        x=0
        for b,(A,dv,c) in zip(bits,laws):
            x=mat_vec(A,x,W) ^ (dv if b else 0) ^ c
        return x

    offset=enc([0]*W)
    cols=[]
    for j in range(W):
        bits=[0]*W; bits[j]=1
        cols.append(enc(bits)^offset)
    assert rank_vectors(cols,W)==W
    decoder=decoder_rows(cols,W)
    return Model(W,laws,offset,tuple(cols),decoder,d)


def encode_model(bits,model:Model):
    if len(bits)!=model.W: raise ValueError('T must equal W for full-capacity model')
    x=0
    for b,(A,dv,c) in zip(bits,model.laws):
        x=mat_vec(A,x,model.W) ^ (dv if b else 0) ^ c
    return x


def decode_model(x,model:Model):
    bvec=mat_vec(model.decoder,x^model.offset,model.W)
    return [(bvec>>j)&1 for j in range(model.W)]


def validate_width(W, exhaustive=False, samples=1000):
    model=build_model(W)
    rng=random.Random(20260914+W)
    if exhaustive:
        for n in range(1<<W):
            bits=[(n>>j)&1 for j in range(W)]
            x=encode_model(bits,model); got=decode_model(x,model)
            assert got==bits,(W,n,x,got,bits)
        tested=1<<W
    else:
        for _ in range(samples):
            bits=[rng.randrange(2) for _ in range(W)]
            x=encode_model(bits,model); got=decode_model(x,model)
            assert got==bits,(W,x)
        tested=samples
    return {'W':W,'rank':rank_vectors(model.cols,W),'d':model.injection,'offset':model.offset,'samples':tested}


def main():
    for W in range(2,13):
        r=validate_width(W,exhaustive=(W<=10),samples=500)
        print('small',r)
    for W in (16,32,63):
        r=validate_width(W,exhaustive=False,samples=2000)
        print('target',r)
    print('PASS: endpoint-only arbitrary-history recovery at full capacity T=W for all tested widths')
    print('NOTE: construction is linear-affine and information-preserving, not compression')

if __name__=='__main__':main()

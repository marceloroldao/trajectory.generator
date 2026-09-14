"""General endpoint-only history recovery as a GF(2) controllability problem.

For a W-bit state x and arbitrary input bits b_t, consider

    x[t+1] = A_t x[t] XOR d_t*b_t XOR c_t

with all A_t invertible and public.  Starting from public x0, the final endpoint is

    x[T] = cbar XOR M_T b

where column t of M_T is the input direction d_t propagated through all later
state transitions.  Exact recovery from (x[T],T) alone is possible iff M_T has
full column rank T.  At full capacity T=W, M_W must be invertible.

This file does NOT claim compression.  It formalizes the exact structural
criterion behind the successful small periodic Feistel candidates and tests
systematic constructions at W=16,32,63.
"""
from __future__ import annotations
import random


def parity(x:int)->int:return x.bit_count()&1


def rotl(x:int,r:int,W:int)->int:
    r%=W; m=(1<<W)-1
    return ((x<<r)|(x>>(W-r)))&m if r else x&m

# Matrix representation: tuple of W row bitmasks. Bit j in row i is A[i,j].
def mat_identity(W):return tuple(1<<i for i in range(W))

def mat_apply(A,x):
    return sum((parity(row & x)<<i) for i,row in enumerate(A))

def mat_compose(A,B,W):
    # A o B
    cols=[]
    for j in range(W):cols.append(mat_apply(A,mat_apply(B,1<<j)))
    rows=[0]*W
    for j,col in enumerate(cols):
        for i in range(W):
            if (col>>i)&1:rows[i]|=1<<j
    return tuple(rows)

def mat_rank_rows(rows,W):
    rows=list(rows); rank=0
    for col in range(W):
        pivot=next((r for r in range(rank,len(rows)) if (rows[r]>>col)&1),None)
        if pivot is None:continue
        rows[rank],rows[pivot]=rows[pivot],rows[rank]
        for r in range(len(rows)):
            if r!=rank and ((rows[r]>>col)&1):rows[r]^=rows[rank]
        rank+=1
        if rank==len(rows):break
    return rank

def columns_to_rows(cols,W):
    rows=[0]*W
    for j,col in enumerate(cols):
        for i in range(W):
            if (col>>i)&1:rows[i]|=1<<j
    return tuple(rows)

def invert_square(A,W):
    rows=[A[i] | (1<<(W+i)) for i in range(W)]
    for col in range(W):
        pivot=next((r for r in range(col,W) if (rows[r]>>col)&1),None)
        if pivot is None:raise ValueError('singular')
        rows[col],rows[pivot]=rows[pivot],rows[col]
        for r in range(W):
            if r!=col and ((rows[r]>>col)&1):rows[r]^=rows[col]
    return tuple((rows[i]>>W)&((1<<W)-1) for i in range(W))


def make_mixing_A(W:int, phase:int):
    """Public invertible nontrivial linear mixing map.

    Composition of elementary reversible XOR-shear operations and rotation.
    This is deliberately not a one-bit shift register.  It remains a finite
    W-bit state, so information-theoretic capacity is still exactly W bits.
    """
    def f(x):
        m=(1<<W)-1
        # cyclic rotation is invertible
        x=rotl(x,1+(phase%(max(1,W-1))),W)
        # triangular XOR shears are invertible when applied in this order
        x ^= (x<<1)&m
        # undo ambiguity risk by use of explicit elementary bit shears below is
        # handled by constructing A and checking rank; reject if not invertible.
        return x&m
    cols=[f(1<<j) for j in range(W)]
    A=columns_to_rows(cols,W)
    if mat_rank_rows(A,W)!=W:
        # deterministic fallback: rotation + one elementary shear x_i ^= x_j.
        rows=list(columns_to_rows([rotl(1<<j,phase+1,W) for j in range(W)],W))
        rows[(phase+3)%W] ^= rows[(phase+7)%W]
        A=tuple(rows)
        assert mat_rank_rows(A,W)==W
    return A


def propagated_columns(W:int,T:int,As,ds):
    # Directly propagate each input impulse through the actual time-varying law.
    cols=[]
    for src in range(T):
        x=ds[src]
        for t in range(src+1,T):x=mat_apply(As[t],x)
        cols.append(x)
    return cols


def affine_const(W,T,As,cs):
    x=0
    for t in range(T):x=mat_apply(As[t],x)^cs[t]
    return x


def encode(bits,W,As,ds,cs):
    x=0
    for t,b in enumerate(bits):x=mat_apply(As[t],x)^cs[t]^(ds[t] if b else 0)
    return x


def decode(y,W,T,As,ds,cs):
    cols=propagated_columns(W,T,As,ds)
    if T!=W:raise ValueError('full-capacity decoder here expects T=W')
    M=columns_to_rows(cols,W)
    inv=invert_square(M,W)
    z=y^affine_const(W,T,As,cs)
    bvec=mat_apply(inv,z)
    return tuple((bvec>>i)&1 for i in range(W))


def choose_directions(W,As):
    """Greedily choose one local input direction d_t so propagated columns stay independent.

    This uses only the public law design stage, not message data or endpoint history.
    It proves existence constructively for the chosen A_t family when all W columns
    can be selected. Directions are then fixed public constants of the machine.
    """
    ds=[0]*W; chosen=[]
    # choose backwards: when t is fixed, later propagation P_t is invertible,
    # so any desired independent endpoint column has a unique local preimage.
    targets=[1<<i for i in range(W)]
    for t,target in enumerate(targets):
        # Solve by brute basis propagation inverse through later maps using matrices.
        P=mat_identity(W)
        for u in range(t+1,W):P=mat_compose(As[u],P,W)
        Pinv=invert_square(P,W)
        ds[t]=mat_apply(Pinv,target)
        chosen.append(target)
    return ds


def build_case(W):
    As=[make_mixing_A(W,t%3) for t in range(W)]
    assert all(mat_rank_rows(A,W)==W for A in As)
    ds=choose_directions(W,As)
    cs=[rotl((0x9E3779B97F4A7C15 ^ (t*0xD1B54A32D192ED03)) & ((1<<W)-1),t%W,W) for t in range(W)]
    cols=propagated_columns(W,W,As,ds)
    M=columns_to_rows(cols,W)
    return As,ds,cs,M


def main():
    rng=random.Random(20260914)
    for W in (8,16,32,63):
        As,ds,cs,M=build_case(W)
        rank=mat_rank_rows(M,W)
        assert rank==W,(W,rank)
        # basis and deterministic random vectors prove decoder algebraically/numerically
        tests=[tuple((i==j) for i in range(W)) for j in range(W)]
        tests += [tuple(rng.randrange(2) for _ in range(W)) for _ in range(200)]
        tests += [tuple(0 for _ in range(W)),tuple(1 for _ in range(W))]
        for bits in tests:
            y=encode(bits,W,As,ds,cs)
            got=decode(y,W,W,As,ds,cs)
            assert got==bits,(W,bits,y,got)
        print('FULL_CAPACITY_DIRECT_ENDPOINT','W',W,'rank',rank,
              'tests',len(tests),'state_bits',W,'input_bits',W,
              'no_rank_no_history_no_table',True)

if __name__=='__main__':main()

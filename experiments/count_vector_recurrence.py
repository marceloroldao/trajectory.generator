"""Derive compact recurrences for the public count field C_t(P).

We use the standalone four-bit time-driven law.  The horizon-free endpoint
address currently recomputes the full sparse vector C_t(P) by dynamic
programming.  This experiment asks whether the count field can be propagated
by a small fixed linear recurrence.

Because phase = t mod 3 is public, we build one 16x16 integer transition matrix
M_phi for each phase.  Then
    C_{t+1} = M_phi C_t.
We also build the 3-step Floquet operator
    F = M_2 M_1 M_0
so that
    C_{t+3} = F C_t
for phase-aligned slices.  We measure the reachable Krylov dimension and derive
an exact scalar recurrence for the total number of histories using rational
linear algebra.
"""
from __future__ import annotations

from fractions import Fraction
from standalone_four_bit_codec import INITIAL, allowed, step
from horizon_free_endpoint_rank import counts_at

STATES = tuple((a,b,c,d) for a in (0,1) for b in (0,1) for c in (0,1) for d in (0,1))
IDX = {p:i for i,p in enumerate(STATES)}


def mat_phase(phi:int):
    M=[[0]*16 for _ in range(16)]
    for p in STATES:
        j=IDX[p]
        for z in (0,1):
            if allowed(p,z,phi):
                q=step(p,z,phi)
                i=IDX[q]
                M[i][j]+=1
    return M


def mm(A,B):
    return [[sum(A[i][k]*B[k][j] for k in range(len(B))) for j in range(len(B[0]))] for i in range(len(A))]


def mv(A,v):
    return [sum(A[i][j]*v[j] for j in range(len(v))) for i in range(len(A))]


def vec0():
    v=[0]*16
    for p in INITIAL:
        v[IDX[p]] += 1
    return v


def rank_q(cols):
    if not cols:
        return 0
    A=[[Fraction(cols[j][i]) for j in range(len(cols))] for i in range(len(cols[0]))]
    m=len(A); n=len(A[0]); r=0
    for c in range(n):
        pivot=next((i for i in range(r,m) if A[i][c]),None)
        if pivot is None: continue
        A[r],A[pivot]=A[pivot],A[r]
        q=A[r][c]
        A[r]=[x/q for x in A[r]]
        for i in range(m):
            if i!=r and A[i][c]:
                q=A[i][c]
                A[i]=[A[i][j]-q*A[r][j] for j in range(n)]
        r+=1
        if r==m: break
    return r


def solve_linear(cols,target):
    # Solve sum_j coeff_j cols[j] = target, exact rationals; return one solution or None.
    m=len(target); n=len(cols)
    A=[[Fraction(cols[j][i]) for j in range(n)] + [Fraction(target[i])] for i in range(m)]
    r=0; pivots=[]
    for c in range(n):
        pivot=next((i for i in range(r,m) if A[i][c]),None)
        if pivot is None: continue
        A[r],A[pivot]=A[pivot],A[r]
        q=A[r][c]; A[r]=[x/q for x in A[r]]
        for i in range(m):
            if i!=r and A[i][c]:
                q=A[i][c]
                A[i]=[A[i][j]-q*A[r][j] for j in range(n+1)]
        pivots.append(c); r+=1
    for i in range(r,m):
        if all(A[i][c]==0 for c in range(n)) and A[i][n]!=0:
            return None
    x=[Fraction(0) for _ in range(n)]
    for i,c in enumerate(pivots):
        x[c]=A[i][n]
    return x


def minimal_vector_recurrence(F,v0,max_order=16):
    seq=[v0]
    for _ in range(max_order): seq.append(mv(F,seq[-1]))
    for d in range(1,max_order+1):
        coeff=solve_linear(seq[:d],seq[d])
        if coeff is not None:
            return d,coeff,seq
    return None,None,seq


def total_seq(nmax=120):
    return [sum(counts_at(t).values()) for t in range(nmax+1)]


def scalar_recurrence(seq,max_order=32):
    # Solve a_n = sum_{i=1}^d c_i a_{n-i} over rationals and validate globally.
    for d in range(1,max_order+1):
        rows=[]; rhs=[]
        for n in range(d, min(len(seq), d+2*d+8)):
            rows.append([seq[n-i] for i in range(1,d+1)])
            rhs.append(seq[n])
        # transpose columns for solve_linear
        cols=[[row[j] for row in rows] for j in range(d)]
        coeff=solve_linear(cols,rhs)
        if coeff is None: continue
        ok=True
        for n in range(d,len(seq)):
            val=sum(coeff[i-1]*seq[n-i] for i in range(1,d+1))
            if val != seq[n]: ok=False; break
        if ok: return d,coeff
    return None,None


def main():
    M=[mat_phase(p) for p in range(3)]
    # Column-vector convention: phase 0 then 1 then 2 => F=M2*M1*M0.
    F=mm(M[2],mm(M[1],M[0]))
    v=vec0()
    # Validate matrix propagation against existing DP for all t <= 30.
    cur=v[:]
    for t in range(31):
        expected=[counts_at(t).get(p,0) for p in STATES]
        assert cur==expected,(t,cur,expected)
        cur=mv(M[t%3],cur)
    print('matrix_dp_equivalence_0_30 ok')

    d,coeff,krylov=minimal_vector_recurrence(F,v)
    print('floquet_krylov_rank',rank_q(krylov[:16]))
    print('vector_recurrence_order_3step',d)
    print('vector_recurrence_coeff',coeff)
    assert d is not None
    # Validate recurrence through 100 Floquet periods.
    vs=[v]
    for _ in range(100): vs.append(mv(F,vs[-1]))
    for n in range(d,len(vs)):
        rec=[sum(coeff[i]*vs[n-d+i][j] for i in range(d)) for j in range(16)]
        assert rec==vs[n],n
    print('vector_recurrence_100_periods ok')

    totals=total_seq(220)
    sd,sc=scalar_recurrence(totals,32)
    print('scalar_total_recurrence_order',sd)
    print('scalar_total_recurrence_coeff',sc)
    if sd is not None:
        print('scalar_recurrence_220_steps ok')

    print('count218',totals[218])
    print('count219',totals[219])

if __name__=='__main__':
    main()

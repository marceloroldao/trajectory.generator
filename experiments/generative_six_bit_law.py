"""Synthesize a table-free local generator on a minimal 6-bit raw coordinate.

The previous experiment found 8 direct 6-bit projections of the full causal
state that preserve the exact 37-state/49-edge operational automaton.  Here we
search those 8 candidates for the simplest Boolean laws for:

    A(R,z)      -- whether label z is locally admissible;
    R' = F(R,z) -- next coordinate, on admissible pairs.

A is fit on the COMPLETE 7-bit domain (all 64 coordinates x z in {0,1}), with
unused/non-operational coordinates explicitly rejected.  F is fit only where
A=1 (other inputs are don't-cares).  We then regenerate the universe from the
8 public initial coordinates using only A and F, with no graph/table lookup.
"""
from __future__ import annotations

from collections import defaultdict, deque
from itertools import product

from binary_reversible_edge_label import labeled_records
from local_label_formula_search import gf2_solve, monomial_specs, design_matrix, expression
from minimal_generative_coordinate import bits, project, reference
from nonlinear_ablation import path_counts, frontier

CANDIDATES = (
 ('h0','h1','h2','q2','p0','p1'),
 ('h0','h1','q1','q2','p0','p1'),
 ('h0','h2','q0','q2','p0','p1'),
 ('h0','h2','q1','q2','p0','p1'),
 ('h0','q0','q1','q2','p0','p1'),
 ('h1','h2','q0','q2','p0','p1'),
 ('h1','q0','q1','q2','p0','p1'),
 ('h2','q0','q1','q2','p0','p1'),
)


def solve(rows, inputs, target, max_degree):
    vectors=[[r[n] for n in inputs] for r in rows]
    y=[r[target] for r in rows]
    for d in range(0,max_degree+1):
        specs=monomial_specs(inputs,d)
        A=design_matrix(vectors,specs)
        sol=gf2_solve(A,y)
        if sol is None: continue
        pred=[sum(a*b for a,b in zip(row,sol))&1 for row in A]
        if pred==y:
            expr,terms=expression(inputs,specs,sol)
            active=[spec for spec,c in zip(specs,sol) if c]
            return {'degree':d,'terms':terms,'expression':expr,'active':active}
    return None


def eval_law(law, env):
    out=0
    for spec in law['active']:
        term=1
        for name in spec:
            term &= env[name]
        out ^= term
    return out


def training(coord):
    nodes,edges,initials=reference()
    allowed={}
    nxt={}
    for s in nodes:
        r=project(s,coord)
        for z,d in edges.get(s,()):
            allowed[(r,z)]=1
            nxt[(r,z)]=project(d,coord)

    rows_a=[]
    for r in product((0,1),repeat=6):
        for z in (0,1):
            row={f'r{i}':r[i] for i in range(6)}; row['z']=z
            row['A']=allowed.get((r,z),0)
            rows_a.append(row)

    rows_f=[]
    for (r,z),nr in sorted(nxt.items()):
        row={f'r{i}':r[i] for i in range(6)}; row['z']=z
        for i,b in enumerate(nr): row[f'n{i}']=b
        rows_f.append(row)
    pinit=tuple(project(s,coord) for s in initials)
    return rows_a,rows_f,pinit


def synth(coord):
    rows_a,rows_f,pinit=training(coord)
    ins=[f'r{i}' for i in range(6)]+['z']
    alaw=solve(rows_a,ins,'A',7)
    fl=[]
    for i in range(6): fl.append(solve(rows_f,ins,f'n{i}',7))
    return alaw,fl,pinit


def generate(alaw,fl,pinit):
    seen=set(pinit); q=deque(pinit); edges={}
    while q:
        r=q.popleft(); outs=[]
        for z in (0,1):
            env={f'r{i}':r[i] for i in range(6)}; env['z']=z
            if not eval_law(alaw,env): continue
            nr=tuple(eval_law(law,env) for law in fl)
            outs.append((z,nr))
            if nr not in seen:
                seen.add(nr); q.append(nr)
        edges[r]=outs
    return edges,seen


def score(alaw,fl):
    laws=[alaw]+fl
    return (max(x['degree'] for x in laws),sum(x['terms'] for x in laws),alaw['degree'],alaw['terms'])


def main():
    _,ref_edges,initials=reference(); ref_counts=path_counts(ref_edges,initials)
    rows=[]
    for coord in CANDIDATES:
        alaw,fl,pinit=synth(coord)
        gen,seen=generate(alaw,fl,pinit)
        counts=path_counts(gen,pinit)
        same_counts=all(
            counts[i]==ref_counts[i]
            for i in range(min(len(counts),len(ref_counts)))
        )
        row={
          'coordinate':coord,'score':score(alaw,fl),
          'A':{'degree':alaw['degree'],'terms':alaw['terms'],'expression':alaw['expression']},
          'F':[(x['degree'],x['terms'],x['expression']) for x in fl],
          'states':len(seen),'edges':sum(len(v) for v in gen.values()),
          'frontier':frontier(counts),
          'same_counts':same_counts,
        }
        rows.append(row)
    rows.sort(key=lambda r:(r['score'],r['coordinate']))
    for r in rows: print(r)
    best=rows[0]
    print('BEST',best)
    assert best['states']==37 and best['edges']==49 and best['frontier']==218 and best['same_counts']

if __name__=='__main__':
    main()

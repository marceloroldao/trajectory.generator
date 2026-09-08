"""Synthesize a table-free generator with 4 private bits + public phase.

For each of the eight minimal private projections found by
`time_driven_generative_coordinate.py`, fit separate Boolean laws per public
phase p=t mod 3:

    A_p(P,z)      admissibility
    P' = F_p(P,z) next private state

The phase advance itself is public/deterministic and therefore not stored.
Admissibility is fit over the complete 5-bit domain (16 P x 2 z) for each phase,
rejecting every pair that is not an operational edge.  F is fit only on allowed
pairs (don't-cares elsewhere).  The generated phase-lifted universe must match
all path counts and the 218/219 frontier.
"""
from __future__ import annotations

from collections import deque
from itertools import product

from generative_six_bit_law import solve, eval_law
from minimal_generative_coordinate import bits, reference
from nonlinear_ablation import path_counts, frontier

CANDIDATES=(
 ('h0','h1','h2','q2'),
 ('h0','h1','q1','q2'),
 ('h0','h2','q0','q2'),
 ('h0','h2','q1','q2'),
 ('h0','q0','q1','q2'),
 ('h1','h2','q0','q2'),
 ('h1','q0','q1','q2'),
 ('h2','q0','q1','q2'),
)


def proj(node,coord):
    b=bits(node)
    return tuple(b[n] for n in coord)


def training(coord):
    nodes,edges,initials=reference()
    allowed={(p,r,z):0 for p in range(3) for r in product((0,1),repeat=4) for z in (0,1)}
    nxt={}
    for s in nodes:
        p=int(s[2]); r=proj(s,coord)
        for z,d in edges.get(s,()):
            allowed[(p,r,z)]=1
            nxt[(p,r,z)]=proj(d,coord)
    pinit=tuple((proj(s,coord),int(s[2])) for s in initials)
    return allowed,nxt,pinit


def synth(coord):
    allowed,nxt,pinit=training(coord)
    ins=[f'r{i}' for i in range(4)]+['z']
    out={}
    for p in range(3):
        ra=[]
        for r in product((0,1),repeat=4):
            for z in (0,1):
                row={f'r{i}':r[i] for i in range(4)}; row['z']=z
                row['A']=allowed[(p,r,z)]
                ra.append(row)
        rf=[]
        for (pp,r,z),nr in sorted(nxt.items()):
            if pp!=p: continue
            row={f'r{i}':r[i] for i in range(4)}; row['z']=z
            for i,b in enumerate(nr): row[f'n{i}']=b
            rf.append(row)
        A=solve(ra,ins,'A',5)
        F=[solve(rf,ins,f'n{i}',5) for i in range(4)]
        assert A is not None and all(x is not None for x in F)
        out[p]=(A,F)
    return out,pinit


def generate(laws,pinit):
    seen=set(pinit); q=deque(pinit); edges={}
    while q:
        r,p=q.popleft(); outs=[]
        A,F=laws[p]
        for z in (0,1):
            env={f'r{i}':r[i] for i in range(4)}; env['z']=z
            if not eval_law(A,env): continue
            nr=tuple(eval_law(f,env) for f in F)
            d=(nr,(p+1)%3)
            outs.append((z,d))
            if d not in seen:
                seen.add(d); q.append(d)
        edges[(r,p)]=outs
    return edges,seen


def score(laws):
    all_l=[]
    for A,F in laws.values(): all_l.extend([A]+F)
    return (
      max(x['degree'] for x in all_l),
      sum(x['terms'] for x in all_l),
      sum(laws[p][0]['terms'] for p in range(3)),
    )


def main():
    _,ref_edges,initials=reference(); ref_counts=path_counts(ref_edges,initials)
    rows=[]
    for coord in CANDIDATES:
        laws,pinit=synth(coord)
        gen,seen=generate(laws,pinit)
        counts=path_counts(gen,pinit)
        same=all(counts[i]==ref_counts[i] for i in range(min(len(counts),len(ref_counts))))
        row={
          'coordinate':coord,'score':score(laws),
          'phase_laws':{
            p:{
              'A':(laws[p][0]['degree'],laws[p][0]['terms'],laws[p][0]['expression']),
              'F':[(f['degree'],f['terms'],f['expression']) for f in laws[p][1]],
            } for p in range(3)
          },
          'states_with_phase':len(seen),
          'edges':sum(len(v) for v in gen.values()),
          'frontier':frontier(counts),'same_counts':same,
        }
        rows.append(row)
    rows.sort(key=lambda r:(r['score'],r['coordinate']))
    for r in rows: print(r)
    best=rows[0]; print('BEST',best)
    assert best['states_with_phase']==37 and best['edges']==49
    assert best['frontier']==218 and best['same_counts']

if __name__=='__main__':
    main()

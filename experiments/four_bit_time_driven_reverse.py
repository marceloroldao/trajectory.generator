"""Synthesize reverse laws for the minimal 4-bit time-driven generator.

Use the best forward coordinate from four_bit_time_driven_law:
    P=(h2,q0,q1,q2)
with public phase p=t mod 3 and binary edge label z.

For each phase p, fit exact Boolean laws
    P_t = R_p(P_{t+1}, z)
on the operational edge domain.  Also verify the round trip against all 49
reference edges and report algebraic degree/term counts per output.
"""
from __future__ import annotations

from four_bit_time_driven_law import proj
from generative_six_bit_law import solve, eval_law
from minimal_generative_coordinate import reference

COORD=('h2','q0','q1','q2')


def training_rows():
    nodes,edges,_=reference()
    by_phase={0:[],1:[],2:[]}
    for s in nodes:
        p=int(s[2])
        ps=proj(s,COORD)
        for z,d in edges.get(s,()):
            pd=proj(d,COORD)
            row={f'n{i}':pd[i] for i in range(4)}
            row['z']=z
            for i,b in enumerate(ps): row[f'p{i}']=b
            by_phase[p].append(row)
    return by_phase


def synthesize():
    ins=[f'n{i}' for i in range(4)]+['z']
    rows=training_rows()
    laws={}
    for p in range(3):
        laws[p]=[solve(rows[p],ins,f'p{i}',5) for i in range(4)]
        assert all(x is not None for x in laws[p])
    return laws,rows


def validate(laws,rows):
    bad=0
    for p in range(3):
        for r in rows[p]:
            env={k:r[k] for k in [f'n{i}' for i in range(4)]+['z']}
            got=tuple(eval_law(law,env) for law in laws[p])
            exp=tuple(r[f'p{i}'] for i in range(4))
            bad += int(got!=exp)
    return bad


def main():
    laws,rows=synthesize()
    print('coordinate',COORD)
    print('edges',sum(len(v) for v in rows.values()))
    print('roundtrip_mismatches',validate(laws,rows))
    for p in range(3):
        print('phase',p)
        for i,law in enumerate(laws[p]):
            print(' prev',i,'degree',law['degree'],'terms',law['terms'],'expr',law['expression'])
        print(' nonlinear_outputs',sum(law['degree']>1 for law in laws[p]))

if __name__=='__main__':
    main()

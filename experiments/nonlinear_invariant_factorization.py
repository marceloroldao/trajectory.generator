"""Factor the five-term nonlinear forward core into composite invariants.

Goal: replace raw monomials with a small set of semantically grouped composite
bits while preserving the exact gate on the validated operational domain.

We start from the five nonlinear terms of q0:
  t0 = g1&g4
  t1 = g1&g5
  t2 = g0&g3&g5
  t3 = g1&g4&g5
  t4 = g2&g4&g5

Candidate composites are built from the functional roles suggested by the
leave-one-out analysis:
  identity_pair      = t0 ^ t3
  identity_side      = t1
  orbital_structure  = t2
  entropy_brake      = t4
  identity_bundle    = t0 ^ t1 ^ t3
  geometry_bundle    = t2 ^ t4

We test whether the exact nonlinear gate can be expressed as an ANF of degree
<=3 over 1, 2, or 3 composite invariants.  This is a representation test only;
semantic names are provisional and do not imply physical meaning.
"""
from __future__ import annotations

from itertools import combinations

from binary_reversible_edge_label import labeled_records
from compact_geometric_coordinate import state_features
from nonlinear_correction_support import COORD
from local_label_formula_search import gf2_solve, monomial_specs, design_matrix, expression


def base_rows():
    _, _, records, _, _ = labeled_records()
    rows=[]
    for r in records:
        sf=state_features(r['src'])
        g=[int(sf[n]) for n in COORD]
        g0,g1,g2,g3,g4,g5=g
        t0=g1 & g4
        t1=g1 & g5
        t2=g0 & g3 & g5
        t3=g1 & g4 & g5
        t4=g2 & g4 & g5
        gate=t0 ^ t1 ^ t2 ^ t3 ^ t4
        rows.append({
            't0':t0,'t1':t1,'t2':t2,'t3':t3,'t4':t4,'gate':gate,
            'identity_pair':t0 ^ t3,
            'identity_side':t1,
            'orbital_structure':t2,
            'entropy_brake':t4,
            'identity_bundle':t0 ^ t1 ^ t3,
            'geometry_bundle':t2 ^ t4,
            'g1':g1,'g4':g4,'g5':g5,
        })
    return rows


def exact_law(rows, names, max_degree=3):
    vectors=[[r[n] for n in names] for r in rows]
    target=[r['gate'] for r in rows]
    for degree in range(1, min(max_degree,len(names))+1):
        specs=monomial_specs(list(names), degree)
        A=design_matrix(vectors,specs)
        sol=gf2_solve(A,target)
        if sol is not None:
            pred=[sum(a*b for a,b in zip(row,sol)) & 1 for row in A]
            if pred==target:
                expr,terms=expression(list(names),specs,sol)
                return {'degree':degree,'terms':terms,'expression':expr}
    return None


def determines(rows,names):
    seen={}
    for r in rows:
        key=tuple(r[n] for n in names)
        if key in seen and seen[key] != r['gate']:
            return False
        seen[key]=r['gate']
    return True


def main():
    rows=base_rows()
    semantic=[
        'identity_pair','identity_side','orbital_structure','entropy_brake',
        'identity_bundle','geometry_bundle'
    ]
    exact=[]
    for k in range(1,4):
        for subset in combinations(semantic,k):
            if not determines(rows,subset):
                continue
            law=exact_law(rows,subset,max_degree=3)
            if law:
                exact.append({'inputs':subset,**law})
        if exact:
            break
    exact.sort(key=lambda x:(len(x['inputs']),x['degree'],x['terms'],x['inputs']))
    print('rows',len(rows))
    print('minimal_semantic_inputs', len(exact[0]['inputs']) if exact else None)
    print('exact_solutions',len(exact))
    for r in exact[:20]: print(r)

    # Also report the hand-motivated two-channel decomposition.
    names=('identity_bundle','geometry_bundle')
    print('two_channel_determines', determines(rows,names))
    print('two_channel_law', exact_law(rows,names,max_degree=2) if determines(rows,names) else None)


if __name__=='__main__':
    main()

"""Derive the two nonlinear channels I and G directly from local geometric invariants.

For the validated compact coordinate
    G = (h1, orientation, phase0, phase1, q0, q1)
we target the two composite nonlinear channels
    I = t0 ^ t1 ^ t3
    Gc = t2 ^ t4
and ask whether they can be computed directly from the semantic local
invariants defined in `geometric_invariant_label_search.py`.
"""
from __future__ import annotations

from itertools import combinations

from binary_reversible_edge_label import labeled_records
from compact_geometric_coordinate import state_features
from geometric_invariant_label_search import invariants
from local_label_formula_search import gf2_solve

COORD = ('h1','orientation','phase0','phase1','q0','q1')


def term_values(g):
    g0,g1,g2,g3,g4,g5 = map(int,g)
    return (
        g1 & g4,
        g1 & g5,
        g0 & g3 & g5,
        g1 & g4 & g5,
        g2 & g4 & g5,
    )


def targets(r):
    sf = state_features(r['src'])
    g = tuple(int(sf[n]) for n in COORD)
    t = term_values(g)
    return {'I': t[0] ^ t[1] ^ t[3], 'G': t[2] ^ t[4]}


def determines(records, subset, target):
    seen = {}
    for r in records:
        inv = invariants(r)
        key = tuple(inv[n] for n in subset)
        y = targets(r)[target]
        if key in seen and seen[key] != y:
            return False
        seen[key] = y
    return True


def encode_subset(records, subset):
    domains = {n: sorted({invariants(r)[n] for r in records}) for n in subset}
    widths = {n: max(1, (max(domains[n]) if domains[n] else 0).bit_length()) for n in subset}
    names=[]; rows=[]
    for n in subset:
        for b in range(widths[n]): names.append(f'{n}_b{b}')
    for r in records:
        inv=invariants(r); row=[]
        for n in subset:
            v=int(inv[n])
            for b in range(widths[n]): row.append((v>>b)&1)
        rows.append(row)
    return names, rows


def specs(names, degree):
    out=[()]
    for d in range(1, degree+1): out.extend(combinations(range(len(names)), d))
    return out


def matrix(rows, mons):
    return [[1 if not m else int(all(row[i] for i in m)) for m in mons] for row in rows]


def expression(names, mons, sol):
    terms=[]
    for m,c in zip(mons,sol):
        if not c: continue
        terms.append('1' if not m else '&'.join(names[i] for i in m))
    return ' ^ '.join(terms) if terms else '0', len(terms)


def fit(records, subset, target):
    names, rows = encode_subset(records, subset)
    y=[targets(r)[target] for r in records]
    for degree in range(1, min(4,len(names))+1):
        mons=specs(names,degree); A=matrix(rows,mons); sol=gf2_solve(A,y)
        if sol is None: continue
        pred=[sum(a*b for a,b in zip(row,sol))&1 for row in A]
        if pred==y:
            expr,nterms=expression(names,mons,sol)
            return {'degree':degree,'terms':nterms,'expression':expr,'binary_inputs':names}
    return None


def analyze_target(records,target):
    inv_names=sorted(invariants(records[0]))
    exact=[]
    for k in range(1,len(inv_names)+1):
        for subset in combinations(inv_names,k):
            if determines(records,subset,target):
                law=fit(records,subset,target)
                exact.append({'invariants':subset,'law':law})
        if exact: break
    exact.sort(key=lambda x:(x['law'] is None, x['law']['degree'] if x['law'] else 99,
                             x['law']['terms'] if x['law'] else 999, x['invariants']))
    return {'minimum_invariant_count':len(exact[0]['invariants']),
            'exact_subsets':len(exact),'best':exact[0],'top5':exact[:5]}


def main():
    _,_,records,_,_=labeled_records()
    print('edges',len(records))
    print('I',analyze_target(records,'I'))
    print('G',analyze_target(records,'G'))

if __name__=='__main__': main()

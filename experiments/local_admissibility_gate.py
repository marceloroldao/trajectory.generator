"""Derive the missing local admissibility gate A(G,z).

The unrestricted local law L+I+G generates 48 states / 96 labeled edges, while
the validated universe contains 37 states / 49 edges and is a strict subgraph.
We label each generated (G,z)->G' edge as admissible iff it belongs to the
validated graph, then search for the smallest subset of the 7 local inputs
(g0..g5,z) that determines admissibility exactly.  We also fit the lowest-degree
ANF on that minimal subset.

This experiment uses the reference graph only to assign training/validation
labels.  The resulting candidate gate itself is purely local in (G,z).
"""
from __future__ import annotations

from itertools import combinations

from emergent_geometry_from_local_law import grow, edge_set
from nonlinear_ablation import full_graph
from local_label_formula_search import gf2_solve

INPUTS = tuple([f'g{i}' for i in range(6)] + ['z'])


def records():
    ref,initial=full_graph()
    gen,_=grow(initial)
    refset=edge_set(ref)
    rows=[]
    for s,outs in sorted(gen.items()):
        for z,d in sorted(outs):
            row={f'g{i}':int(s[i]) for i in range(6)}
            row['z']=int(z)
            row['allowed']=int((s,z,d) in refset)
            row['dst']=d
            rows.append(row)
    return rows,ref,gen,initial


def determines(rows, subset):
    seen={}
    for r in rows:
        k=tuple(r[n] for n in subset)
        y=r['allowed']
        if k in seen and seen[k]!=y:
            return False
        seen[k]=y
    return True


def monomial_specs(names, degree):
    specs=[()]
    for d in range(1,degree+1):
        specs.extend(combinations(range(len(names)),d))
    return specs


def design(rows,names,specs):
    X=[]
    for r in rows:
        vals=[r[n] for n in names]
        X.append([1 if not m else int(all(vals[i] for i in m)) for m in specs])
    return X


def format_expr(names,specs,sol):
    terms=[]
    for m,c in zip(specs,sol):
        if not c: continue
        terms.append('1' if not m else '&'.join(names[i] for i in m))
    return ' ^ '.join(terms) if terms else '0',len(terms)


def fit(rows,subset):
    y=[r['allowed'] for r in rows]
    for degree in range(1,len(subset)+1):
        specs=monomial_specs(subset,degree)
        X=design(rows,subset,specs)
        sol=gf2_solve(X,y)
        if sol is None: continue
        pred=[sum(a*b for a,b in zip(x,sol))&1 for x in X]
        if pred==y:
            expr,nterms=format_expr(subset,specs,sol)
            return {'degree':degree,'terms':nterms,'expression':expr}
    return None


def analyze():
    rows,ref,gen,initial=records()
    minimal=[]
    for k in range(1,len(INPUTS)+1):
        for sub in combinations(INPUTS,k):
            if determines(rows,sub):
                minimal.append(sub)
        if minimal: break
    fitted=[]
    for sub in minimal:
        law=fit(rows,sub)
        fitted.append((sub,law))
    fitted.sort(key=lambda x:(x[1] is None,x[1]['degree'] if x[1] else 99,x[1]['terms'] if x[1] else 999,x[0]))
    return rows,minimal,fitted


def main():
    rows,minimal,fitted=analyze()
    allowed=sum(r['allowed'] for r in rows)
    print('generated_edges',len(rows),'allowed',allowed,'rejected',len(rows)-allowed)
    print('minimum_local_inputs',len(minimal[0]) if minimal else None)
    print('exact_minimal_subsets',len(minimal))
    for sub,law in fitted[:10]:
        print({'inputs':sub,'law':law})


if __name__=='__main__':
    main()

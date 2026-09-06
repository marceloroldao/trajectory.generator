"""Ablate the two composite nonlinear channels I and G.

Exact factorization on the operational domain:
    N = I ^ G
where
    I = t0 ^ t1 ^ t3
    G = t2 ^ t4
and t0..t4 are the five nonlinear monomials from nonlinear_term_ablation.

We compare four cases on the exact observed (state,label) domain:
    00: no nonlinear channel
    10: identity only
    01: geometry only
    11: full N
and measure graph fidelity, reverse ambiguity, path growth and spectral radius.
"""
from __future__ import annotations

from collections import defaultdict
import math
import numpy as np

from nonlinear_ablation import full_graph
from nonlinear_term_ablation import step
from nonlinear_leave_one_out import observed_domain, edge_set, reverse_ambiguity, path_counts, frontier, tarjan, spectral_radius


def enabled_for(identity: bool, geometry: bool):
    s=set()
    if identity: s.update((0,1,3))
    if geometry: s.update((2,4))
    return s


def build(reference_edges, identity, geometry):
    edges=defaultdict(list)
    for s,z in observed_domain(reference_edges):
        edges[s].append((z,step(s,z,enabled_for(identity,geometry))))
    return dict(edges)


def summarize(name, reference_edges, initial, identity, geometry):
    e=build(reference_edges,identity,geometry)
    es=edge_set(e); ref=edge_set(reference_edges)
    amb,maxp=reverse_ambiguity(e)
    c=path_counts(e,initial)
    comps=tarjan(e)
    rec=[]
    for comp in comps:
        rho=spectral_radius(e,comp)
        if rho>0:
            rec.append((rho,len(comp)))
    rec.sort(reverse=True)
    return {
        'name':name,'I':identity,'G':geometry,
        'edges':len(es),'agreement':len(es&ref),'missing':len(ref-es),'extra':len(es-ref),
        'reverse_ambiguous':amb,'max_reverse_preimages':maxp,'reversible':amb==0,
        'frontier':frontier(c),'rate200':math.log2(c[200])/200 if c[200] else float('-inf'),
        'scc_count':len(comps),'dominant_rho':rec[0][0] if rec else 0.0,
        'dominant_scc_size':rec[0][1] if rec else 0,
    }


def main():
    ref,initial=full_graph()
    rows=[
        summarize('L_only',ref,initial,False,False),
        summarize('L_plus_I',ref,initial,True,False),
        summarize('L_plus_G',ref,initial,False,True),
        summarize('L_plus_I_plus_G',ref,initial,True,True),
    ]
    for r in rows: print(r)

if __name__=='__main__':
    main()

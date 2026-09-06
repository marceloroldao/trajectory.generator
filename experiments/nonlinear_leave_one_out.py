"""Leave-one-out analysis of the five nonlinear q0 monomials.

Runs on the exact observed (G,z) operational domain so the full five-term law
reproduces the validated 49-edge graph exactly.  One nonlinear monomial is
removed at a time and we measure edge changes, reverse ambiguity, path growth,
63-bit frontier, SCC structure, and dominant spectral radius.
"""
from __future__ import annotations

import math
from collections import defaultdict
import numpy as np

from nonlinear_ablation import full_graph
from nonlinear_term_ablation import NONLINEAR, step

LIMIT = 1 << 63


def observed_domain(reference_edges):
    return {(s, z) for s, outs in reference_edges.items() for z, _ in outs}


def build_edges(reference_edges, enabled):
    domain = observed_domain(reference_edges)
    edges = defaultdict(list)
    for s, z in domain:
        edges[s].append((z, step(s, z, enabled)))
    return dict(edges)


def edge_set(edges):
    return {(s, z, d) for s, outs in edges.items() for z, d in outs}


def reverse_ambiguity(edges):
    rev = defaultdict(set)
    for s, outs in edges.items():
        for z, d in outs:
            rev[(d, z)].add(s)
    amb = sum(len(v) > 1 for v in rev.values())
    return amb, max((len(v) for v in rev.values()), default=0)


def path_counts(edges, initial, max_steps=300):
    dist = defaultdict(int)
    for s in initial:
        dist[s] += 1
    out = [sum(dist.values())]
    for _ in range(max_steps):
        nxt = defaultdict(int)
        for s, c in dist.items():
            for _, d in edges.get(s, ()):
                nxt[d] += c
        dist = nxt
        out.append(sum(dist.values()))
    return out


def frontier(counts):
    last = 0
    for i, n in enumerate(counts):
        if n == 0 or n > LIMIT:
            return i - 1
        last = i
    return last


def tarjan(edges):
    nodes = set(edges)
    for outs in edges.values():
        for _, d in outs:
            nodes.add(d)
    adj = {n: [d for _, d in edges.get(n, ())] for n in nodes}
    index = 0
    stack = []
    on = set()
    idx = {}
    low = {}
    comps = []
    def dfs(v):
        nonlocal index
        idx[v] = low[v] = index; index += 1
        stack.append(v); on.add(v)
        for w in adj[v]:
            if w not in idx:
                dfs(w); low[v] = min(low[v], low[w])
            elif w in on:
                low[v] = min(low[v], idx[w])
        if low[v] == idx[v]:
            c=[]
            while True:
                w=stack.pop(); on.remove(w); c.append(w)
                if w == v: break
            comps.append(c)
    for v in nodes:
        if v not in idx: dfs(v)
    return comps


def spectral_radius(edges, comp):
    if not comp:
        return 0.0
    pos={n:i for i,n in enumerate(comp)}
    a=np.zeros((len(comp),len(comp)), dtype=float)
    for s in comp:
        for _,d in edges.get(s,()):
            if d in pos: a[pos[s],pos[d]] += 1.0
    vals=np.linalg.eigvals(a)
    return float(max(abs(v) for v in vals)) if len(vals) else 0.0


def summarize(name, enabled, reference_edges, initial):
    e=build_edges(reference_edges, enabled)
    es=edge_set(e); ref=edge_set(reference_edges)
    amb,maxp=reverse_ambiguity(e)
    counts=path_counts(e, initial)
    comps=tarjan(e)
    recurrent=[]
    for c in comps:
        rho=spectral_radius(e,c)
        if rho > 0:
            recurrent.append((rho,len(c),sum(1 for s in c for _,d in e.get(s,()) if d in set(c))))
    recurrent.sort(reverse=True)
    return {
        'name': name,
        'enabled': tuple(sorted(enabled)),
        'removed': tuple(NONLINEAR[i] for i in range(5) if i not in enabled),
        'edges': len(es),
        'edge_agreement': len(es & ref),
        'missing': len(ref-es),
        'extra': len(es-ref),
        'reverse_ambiguous': amb,
        'max_reverse_preimages': maxp,
        'reversible': amb == 0,
        'frontier': frontier(counts),
        'rate200': math.log2(counts[200])/200 if counts[200] else float('-inf'),
        'scc_count': len(comps),
        'dominant_rho': recurrent[0][0] if recurrent else 0.0,
        'dominant_scc_size': recurrent[0][1] if recurrent else 0,
        'top_recurrent': recurrent[:4],
    }


def main():
    reference_edges, initial = full_graph()
    full = summarize('full', set(range(5)), reference_edges, initial)
    print('terms', list(enumerate(NONLINEAR)))
    print('baseline', full)
    rows=[]
    for removed in range(5):
        enabled=set(range(5))-{removed}
        row=summarize(f'without_{removed}', enabled, reference_edges, initial)
        row['delta_frontier']=row['frontier']-full['frontier']
        row['delta_rate200']=row['rate200']-full['rate200']
        row['delta_rho']=row['dominant_rho']-full['dominant_rho']
        row['delta_scc_count']=row['scc_count']-full['scc_count']
        rows.append(row)
    print('leave_one_out')
    for r in rows:
        print(r)


if __name__ == '__main__':
    main()

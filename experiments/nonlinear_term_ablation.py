"""Exhaustively ablate the five nonlinear forward monomials on the fixed operational manifold.

The exact ANF laws were learned only on the validated 37-state operational
manifold.  Therefore this ablation never extrapolates them to arbitrary 6-bit
states.  Candidate transitions that leave the validated manifold are rejected.

We keep the affine part of q0 fixed and evaluate all 2^5 subsets of nonlinear
terms.  For every submachine we measure reachable admissible states, local
reverse ambiguity, path growth, and the 63-bit frontier.
"""
from __future__ import annotations

import math
from collections import defaultdict, deque

from nonlinear_ablation import full_graph

LIMIT = 1 << 63

AFFINE = ('g2', 'g3', 'g5', 'z')
NONLINEAR = (
    'g1&g4',
    'g1&g5',
    'g0&g3&g5',
    'g1&g4&g5',
    'g2&g4&g5',
)


def eval_term(term, env):
    v = 1
    for p in term.split('&'):
        v &= env[p]
    return v


def step(g, z, enabled):
    g0,g1,g2,g3,g4,g5 = g
    env = {f'g{i}': int(v) for i,v in enumerate(g)}
    env['z'] = int(z)
    ng4 = 0
    for t in AFFINE:
        ng4 ^= env[t]
    for i,t in enumerate(NONLINEAR):
        if i in enabled:
            ng4 ^= eval_term(t, env)
    return (
        g0 ^ g4,
        g0 ^ g4 ^ g5,
        1 ^ g2 ^ g3,
        g2,
        ng4,
        g4,
    )


def graph(initial, enabled, admissible):
    seen=set(initial); q=deque(initial); edges={}
    while q:
        g=q.popleft(); outs=[]
        for z in (0,1):
            ng=step(g,z,enabled)
            if ng not in admissible:
                continue
            outs.append((z,ng))
            if ng not in seen:
                seen.add(ng); q.append(ng)
        edges[g]=outs
    return edges


def reverse_ambiguity(edges):
    rev=defaultdict(set)
    for s,outs in edges.items():
        for z,d in outs:
            rev[(d,z)].add(s)
    amb=sum(len(v)>1 for v in rev.values())
    maxp=max((len(v) for v in rev.values()), default=0)
    return amb,maxp


def counts(edges, initial, max_steps=300):
    dist=defaultdict(int)
    for s in initial: dist[s]+=1
    out=[sum(dist.values())]
    for _ in range(max_steps):
        nxt=defaultdict(int)
        for s,c in dist.items():
            for _,d in edges.get(s,()): nxt[d]+=c
        dist=nxt; out.append(sum(dist.values()))
    return out


def frontier(c):
    last_valid=0
    for i,n in enumerate(c):
        if n == 0:
            return i-1
        if n > LIMIT:
            return i-1
        last_valid=i
    return last_valid


def edge_set(edges):
    return {(s,z,d) for s,outs in edges.items() for z,d in outs}


def run(enabled, initial, admissible, reference_edges):
    e=graph(initial,enabled,admissible); c=counts(e,initial)
    amb,maxp=reverse_ambiguity(e)
    es=edge_set(e)
    ref=edge_set(reference_edges)
    rate = math.log2(c[200])/200 if c[200] else float('-inf')
    return {
        'enabled': tuple(sorted(enabled)),
        'terms': tuple(NONLINEAR[i] for i in sorted(enabled)),
        'states': len(e),
        'edges': len(es),
        'reverse_ambiguous': amb,
        'max_reverse_preimages': maxp,
        'reversible': amb==0,
        'frontier': frontier(c),
        'rate200': rate,
        'edge_agreement': len(es & ref),
        'missing_reference_edges': len(ref-es),
        'extra_edges': len(es-ref),
        'exact_reference_graph': es==ref,
    }


def main():
    reference_edges, initial = full_graph()
    admissible=set(reference_edges)
    for outs in reference_edges.values():
        for _,d in outs: admissible.add(d)
    rows=[]
    for mask in range(1<<len(NONLINEAR)):
        enabled={i for i in range(len(NONLINEAR)) if mask&(1<<i)}
        rows.append(run(enabled,initial,admissible,reference_edges))
    rows.sort(key=lambda r:(-r['frontier'], r['rate200'], len(r['enabled'])))
    print('nonlinear_terms', list(enumerate(NONLINEAR)))
    print('configs', len(rows))
    print('full_mask', next(r for r in rows if len(r['enabled'])==5))
    print('top_by_frontier')
    for r in rows[:12]: print(r)
    rev=[r for r in rows if r['reversible']]
    exact=[r for r in rows if r['exact_reference_graph']]
    print('summary', {
        'reversible_configs': len(rev),
        'exact_reference_configs': len(exact),
        'fewest_terms_reversible': min((len(r['enabled']) for r in rev), default=None),
        'fewest_terms_exact_reference': min((len(r['enabled']) for r in exact), default=None),
    })
    if rev:
        m=min(len(r['enabled']) for r in rev)
        print('minimal_reversible_configs')
        for r in rev:
            if len(r['enabled'])==m: print(r)
    if exact:
        m=min(len(r['enabled']) for r in exact)
        print('minimal_exact_reference_configs')
        for r in exact:
            if len(r['enabled'])==m: print(r)


if __name__=='__main__':
    main()

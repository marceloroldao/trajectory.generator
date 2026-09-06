"""Exhaustively ablate the five nonlinear forward monomials in the balanced universe.

The validated forward nonlinear channel is q0 with five nonlinear terms.  We keep
its affine part fixed and evaluate all 2^5 subsets of nonlinear terms.  For each
submachine we start from the same eight public initial states and measure:

- reachable states and labeled edges;
- local reverse ambiguity under (G_next,z);
- 63-bit frontier;
- information-rate proxy log2(path_count[200])/200.

This identifies which nonlinear interactions are responsible for entropy
restriction versus reverse disambiguation.
"""
from __future__ import annotations

import math
from collections import defaultdict, deque
from itertools import combinations

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


def graph(initial, enabled):
    seen=set(initial); q=deque(initial); edges={}
    while q:
        g=q.popleft(); outs=[]
        for z in (0,1):
            ng=step(g,z,enabled); outs.append((z,ng))
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
            for _,d in edges[s]: nxt[d]+=c
        dist=nxt; out.append(sum(dist.values()))
    return out


def frontier(c):
    for i,n in enumerate(c):
        if n > LIMIT: return i-1
    return len(c)-1


def run(enabled, initial):
    e=graph(initial,enabled); c=counts(e,initial)
    amb,maxp=reverse_ambiguity(e)
    return {
        'enabled': tuple(sorted(enabled)),
        'terms': tuple(NONLINEAR[i] for i in sorted(enabled)),
        'states': len(e),
        'edges': sum(len(v) for v in e.values()),
        'reverse_ambiguous': amb,
        'max_reverse_preimages': maxp,
        'reversible': amb==0,
        'frontier': frontier(c),
        'rate200': math.log2(c[200])/200,
    }


def main():
    _, initial = full_graph()
    rows=[]
    for mask in range(1<<len(NONLINEAR)):
        enabled={i for i in range(len(NONLINEAR)) if mask&(1<<i)}
        rows.append(run(enabled,initial))
    rows.sort(key=lambda r:(-r['frontier'], r['rate200'], len(r['enabled'])))
    print('nonlinear_terms', list(enumerate(NONLINEAR)))
    print('configs', len(rows))
    print('top_by_frontier')
    for r in rows[:12]: print(r)
    rev=[r for r in rows if r['reversible']]
    print('summary', {
        'reversible_configs': len(rev),
        'nonreversible_configs': len(rows)-len(rev),
        'best_reversible': rev[0] if rev else None,
        'fewest_terms_reversible': min((len(r['enabled']) for r in rev), default=None),
    })
    if rev:
        m=min(len(r['enabled']) for r in rev)
        print('minimal_reversible_configs')
        for r in rev:
            if len(r['enabled'])==m: print(r)


if __name__=='__main__':
    main()

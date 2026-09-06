"""Exhaustively ablate the five nonlinear forward monomials on the exact observed domain.

The ANF law is only certified on the 49 operational (G,z) source-label pairs.
This experiment therefore keeps that domain fixed.  For each of the 2^5
nonlinear-term subsets, we recompute only the destination produced by the law.
If a candidate destination leaves the validated 37-state manifold, that edge is
rejected.  The full five-term mask must reproduce the reference graph exactly;
otherwise the experiment is invalid.
"""
from __future__ import annotations

import math
from collections import defaultdict

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


def reference_domain(reference_edges):
    return {(s, z) for s, outs in reference_edges.items() for z, _ in outs}


def build_graph(enabled, reference_edges, admissible):
    domain = reference_domain(reference_edges)
    edges = defaultdict(list)
    for s, z in sorted(domain):
        d = step(s, z, enabled)
        if d in admissible:
            edges[s].append((z, d))
    for s in admissible:
        edges.setdefault(s, [])
    return dict(edges)


def reverse_ambiguity(edges):
    rev = defaultdict(set)
    for s, outs in edges.items():
        for z, d in outs:
            rev[(d, z)].add(s)
    amb = sum(len(v) > 1 for v in rev.values())
    maxp = max((len(v) for v in rev.values()), default=0)
    return amb, maxp


def counts(edges, initial, max_steps=300):
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


def frontier(c):
    last_valid = 0
    for i, n in enumerate(c):
        if n == 0 or n > LIMIT:
            return i - 1
        last_valid = i
    return last_valid


def edge_set(edges):
    return {(s, z, d) for s, outs in edges.items() for z, d in outs}


def run(enabled, initial, admissible, reference_edges):
    e = build_graph(enabled, reference_edges, admissible)
    c = counts(e, initial)
    amb, maxp = reverse_ambiguity(e)
    es, ref = edge_set(e), edge_set(reference_edges)
    rate = math.log2(c[200]) / 200 if c[200] else float('-inf')
    return {
        'enabled': tuple(sorted(enabled)),
        'terms': tuple(NONLINEAR[i] for i in sorted(enabled)),
        'edges': len(es),
        'reverse_ambiguous': amb,
        'max_reverse_preimages': maxp,
        'reversible': amb == 0,
        'frontier': frontier(c),
        'rate200': rate,
        'edge_agreement': len(es & ref),
        'missing_reference_edges': len(ref - es),
        'extra_edges': len(es - ref),
        'exact_reference_graph': es == ref,
    }


def main():
    reference_edges, initial = full_graph()
    admissible = set(reference_edges)
    for outs in reference_edges.values():
        for _, d in outs:
            admissible.add(d)

    rows = []
    for mask in range(1 << len(NONLINEAR)):
        enabled = {i for i in range(len(NONLINEAR)) if mask & (1 << i)}
        rows.append(run(enabled, initial, admissible, reference_edges))

    full = next(r for r in rows if len(r['enabled']) == len(NONLINEAR))
    if not full['exact_reference_graph']:
        raise RuntimeError(f'full nonlinear mask failed to reproduce reference graph: {full}')

    rows.sort(key=lambda r: (-r['frontier'], r['rate200'], len(r['enabled'])))
    print('nonlinear_terms', list(enumerate(NONLINEAR)))
    print('configs', len(rows))
    print('full_mask', full)
    print('top_by_frontier')
    for r in rows[:12]:
        print(r)

    rev = [r for r in rows if r['reversible']]
    exact = [r for r in rows if r['exact_reference_graph']]
    print('summary', {
        'reversible_configs': len(rev),
        'exact_reference_configs': len(exact),
        'fewest_terms_reversible': min((len(r['enabled']) for r in rev), default=None),
        'fewest_terms_exact_reference': min((len(r['enabled']) for r in exact), default=None),
    })
    if rev:
        m = min(len(r['enabled']) for r in rev)
        print('minimal_reversible_configs')
        for r in rev:
            if len(r['enabled']) == m:
                print(r)
    if exact:
        m = min(len(r['enabled']) for r in exact)
        print('minimal_exact_reference_configs')
        for r in exact:
            if len(r['enabled']) == m:
                print(r)


if __name__ == '__main__':
    main()

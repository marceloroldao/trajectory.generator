"""Ablate the nonlinear channel across the 18 controlled perturbed universes.

For each universe from structural_perturbation_scan.neighborhood():
- build the exact reachable raw graph from the eight public initial states;
- construct the binary reversible edge label;
- fit the validated six-bit semantic coordinate G;
- obtain the exact ANF forward law for each coordinate bit;
- construct L by deleting all ANF monomials of degree >= 2;
- run L on the same public initial G states with z in {0,1};
- compare reverse ambiguity, growth rate and 63-bit frontier against L+N.

No per-universe coordinate search is allowed.  The same semantic coordinate is
used throughout, so this is a structural ablation rather than a re-optimization.
"""
from __future__ import annotations

import math
from collections import defaultdict, deque

from structural_perturbation_scan import COORD, neighborhood, labeled_records
from compact_geometric_coordinate import state_features, transition_laws
from topological_transition_state import initial_topology

LIMIT = 1 << 63


def encode_g(node):
    f = state_features(node)
    return tuple(int(f[n]) for n in COORD)


def eval_term(term: str, env: dict[str, int]) -> int:
    term = term.strip()
    if not term:
        return 0
    if term == '1':
        return 1
    v = 1
    for p in term.split('&'):
        v &= env[p.strip()]
    return v


def affine_expression(expr: str) -> str:
    terms = []
    for raw in expr.split('^'):
        term = raw.strip()
        if not term:
            continue
        degree = 0 if term == '1' else len(term.split('&'))
        if degree <= 1:
            terms.append(term)
    return ' ^ '.join(terms) if terms else '0'


def eval_expr(expr: str, g, z: int) -> int:
    env = {f'g{i}': int(v) for i, v in enumerate(g)}
    env['z'] = int(z)
    if expr.strip() == '0':
        return 0
    out = 0
    for term in expr.split('^'):
        out ^= eval_term(term, env)
    return out


def exact_graph(params):
    nodes, records, _, _ = labeled_records(params)
    g_of = {n: encode_g(n) for n in nodes}
    edges = defaultdict(list)
    for r in records:
        edges[g_of[r['src']]].append((int(r['label']), g_of[r['dst']]))
    # exactly the eight public raw initial states
    initials_raw = tuple((s, initial_topology(s), 0) for s in range(8))
    initial = tuple(g_of[n] for n in initials_raw if n in g_of)
    return tuple(nodes), tuple(records), dict(edges), initial


def linear_laws(records):
    fw, _ = transition_laws(records, COORD)
    laws = []
    for _, meta in fw:
        expr = meta.get('expression', '') if meta else ''
        laws.append(affine_expression(expr))
    return tuple(laws)


def linear_graph(initial, laws):
    seen = set(initial)
    q = deque(initial)
    edges = {}
    while q:
        g = q.popleft()
        outs = []
        for z in (0, 1):
            ng = tuple(eval_expr(laws[i], g, z) for i in range(6))
            outs.append((z, ng))
            if ng not in seen:
                seen.add(ng)
                q.append(ng)
        edges[g] = outs
    return edges


def reverse_ambiguity(edges):
    rev = defaultdict(set)
    for src, outs in edges.items():
        for z, dst in outs:
            rev[(dst, z)].add(src)
    ambiguous = sum(1 for v in rev.values() if len(v) > 1)
    max_pre = max((len(v) for v in rev.values()), default=0)
    return ambiguous, max_pre


def path_counts(edges, initial, max_steps=400):
    dist = defaultdict(int)
    for s in initial:
        dist[s] += 1
    counts = [sum(dist.values())]
    for _ in range(max_steps):
        nxt = defaultdict(int)
        for s, c in dist.items():
            for _, d in edges.get(s, ()):
                nxt[d] += c
        dist = nxt
        counts.append(sum(dist.values()))
    return counts


def frontier(counts):
    for i, n in enumerate(counts):
        if n > LIMIT:
            return i - 1
    return len(counts) - 1


def summarize(edges, initial):
    counts = path_counts(edges, initial)
    fr = frontier(counts)
    amb, max_pre = reverse_ambiguity(edges)
    return {
        'states': len(edges),
        'edges': sum(len(v) for v in edges.values()),
        'reverse_ambiguous': amb,
        'max_reverse_preimages': max_pre,
        'frontier': fr,
        'rate_200': math.log2(counts[200]) / 200 if counts[200] else float('-inf'),
    }


def run_one(params):
    nodes, records, full_edges, initial = exact_graph(params)
    laws = linear_laws(records)
    lin_edges = linear_graph(initial, laws)
    full = summarize(full_edges, initial)
    lin = summarize(lin_edges, initial)
    full_rev_ok = full['reverse_ambiguous'] == 0
    lin_rev_ok = lin['reverse_ambiguous'] == 0
    return {
        'params': params,
        'full': full,
        'linear': lin,
        'full_reverse_ok': full_rev_ok,
        'linear_reverse_ok': lin_rev_ok,
        'reversibility_lost': full_rev_ok and not lin_rev_ok,
        'frontier_delta_linear_minus_full': lin['frontier'] - full['frontier'],
        'rate_delta_linear_minus_full': lin['rate_200'] - full['rate_200'],
    }


def main():
    rows = [run_one(p) for p in neighborhood()]
    print('universes', len(rows))
    print('params full_rev linear_rev full_front linear_front full_rate linear_rate full_states linear_states')
    for r in rows:
        f, l = r['full'], r['linear']
        print(r['params'], r['full_reverse_ok'], r['linear_reverse_ok'],
              f['frontier'], l['frontier'], round(f['rate_200'], 6), round(l['rate_200'], 6),
              f['states'], l['states'])
    lost = [r for r in rows if r['reversibility_lost']]
    preserved = [r for r in rows if r['linear_reverse_ok']]
    print('summary', {
        'universes': len(rows),
        'full_reversible': sum(r['full_reverse_ok'] for r in rows),
        'linear_reversible': len(preserved),
        'reversibility_lost_after_ablation': len(lost),
        'loss_fraction': len(lost) / len(rows) if rows else 0.0,
        'median_frontier_delta_linear_minus_full': sorted(r['frontier_delta_linear_minus_full'] for r in rows)[len(rows)//2],
        'mean_rate_delta_linear_minus_full': sum(r['rate_delta_linear_minus_full'] for r in rows) / len(rows),
    })


if __name__ == '__main__':
    main()

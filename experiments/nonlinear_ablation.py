"""Ablate the single nonlinear geometric channel in the validated balanced universe.

Compare the exact operational dynamics U_full = L + N with U_linear = L, using
compact coordinate G=(h1,orientation,phase0,phase1,q0,q1) and the public binary
edge label z.

We measure:
- whether each labeled step remains bidirectionally reversible;
- reachable geometric states/edges from the public initial set;
- path-count growth and 63-bit frontier;
- recurrent SCC structure and spectral growth.

The ablated machine is defined on all 64 six-bit G values by the affine parts of
the learned forward laws.  We keep only transitions with z in {0,1}; no extra
metadata is introduced.
"""
from __future__ import annotations

import math
from collections import defaultdict, deque

from binary_reversible_edge_label import labeled_records
from compact_geometric_coordinate import state_features
from nonlinear_correction_support import COORD

LIMIT = 1 << 63

# Exact forward affine part for best coordinate from compact_geometric_coordinate.py.
# g'0=g0^g4
# g'1=g0^g4^g5
# g'2=1^g2^g3
# g'3=g2
# g'4=g2^g3^g5^z   (nonlinear terms removed)
# g'5=g4

def encode_g(node):
    f = state_features(node)
    return tuple(int(f[n]) for n in COORD)


def linear_step(g, z):
    g0,g1,g2,g3,g4,g5 = g
    return (
        g0 ^ g4,
        g0 ^ g4 ^ g5,
        1 ^ g2 ^ g3,
        g2,
        g2 ^ g3 ^ g5 ^ z,
        g4,
    )


def full_graph():
    reachable, _, records, _, _ = labeled_records()
    g_of = {node: encode_g(node) for node in reachable}
    edges = defaultdict(list)
    for r in records:
        edges[g_of[r['src']]].append((int(r['label']), g_of[r['dst']]))
    initial_nodes = sorted(n for n in reachable if n[2] == 0)
    initial = tuple(g_of[n] for n in initial_nodes)
    return dict(edges), initial


def linear_graph(initial):
    seen = set(initial)
    q = deque(initial)
    edges = {}
    while q:
        g = q.popleft()
        outs = []
        for z in (0,1):
            ng = linear_step(g,z)
            outs.append((z,ng))
            if ng not in seen:
                seen.add(ng); q.append(ng)
        edges[g] = outs
    return edges, tuple(sorted(seen))


def reverse_closure(edges):
    f = defaultdict(set); r = defaultdict(set)
    for src, outs in edges.items():
        for z,dst in outs:
            f[(src,z)].add(dst)
            r[(dst,z)].add(src)
    return {
        'forward_ambiguous': sum(len(v)>1 for v in f.values()),
        'reverse_ambiguous': sum(len(v)>1 for v in r.values()),
        'max_reverse_preimages': max((len(v) for v in r.values()), default=0),
    }


def path_counts(edges, initial, max_steps=400):
    dist = {s:1 for s in initial}
    out = [sum(dist.values())]
    for _ in range(max_steps):
        nxt = defaultdict(int)
        for s,c in dist.items():
            for _,d in edges.get(s,()):
                nxt[d] += c
        dist = dict(nxt)
        out.append(sum(dist.values()))
    return out


def frontier(counts):
    last = len(counts)-1
    for i,n in enumerate(counts):
        if n > LIMIT:
            return i-1
    return last


def sccs(edges):
    adj = {v:[d for _,d in outs] for v,outs in edges.items()}
    for outs in list(adj.values()):
        for w in outs:
            adj.setdefault(w,[])
    index=0; stack=[]; on=set(); idx={}; low={}; comps=[]
    def visit(v):
        nonlocal index
        idx[v]=low[v]=index; index+=1; stack.append(v); on.add(v)
        for w in adj[v]:
            if w not in idx:
                visit(w); low[v]=min(low[v],low[w])
            elif w in on:
                low[v]=min(low[v],idx[w])
        if low[v]==idx[v]:
            c=set()
            while True:
                w=stack.pop(); on.remove(w); c.add(w)
                if w==v: break
            comps.append(c)
    for v in adj:
        if v not in idx: visit(v)
    return comps, adj


def spectral_radius(adj, comp, iters=200):
    nodes=list(comp); pos={v:i for i,v in enumerate(nodes)}
    if not nodes: return 0.0
    x=[1.0/len(nodes)]*len(nodes); lam=0.0
    for _ in range(iters):
        y=[0.0]*len(nodes)
        for v,i in pos.items():
            for w in adj[v]:
                if w in pos: y[pos[w]] += x[i]
        norm=max(y, default=0.0)
        if norm==0: return 0.0
        x=[v/norm for v in y]; lam=norm
    return lam


def recurrent_profile(edges):
    comps, adj = sccs(edges)
    rows=[]
    for c in comps:
        internal=sum(1 for v in c for w in adj[v] if w in c)
        exits=sum(1 for v in c for w in adj[v] if w not in c)
        lam=spectral_radius(adj,c)
        rows.append((lam,len(c),internal,exits))
    rows.sort(reverse=True)
    return rows[:5]


def summarize(name, edges, initial):
    counts=path_counts(edges,initial)
    fr=frontier(counts)
    rp=recurrent_profile(edges)
    return {
        'name':name,
        'states':len(edges),
        'edges':sum(len(v) for v in edges.values()),
        'closure':reverse_closure(edges),
        'frontier':fr,
        'count_at_frontier':counts[fr],
        'count_next':counts[fr+1] if fr+1<len(counts) else None,
        'rate_200': math.log2(counts[200])/200 if counts[200] else float('-inf'),
        'top_recurrent':rp,
    }


def main():
    full, initial = full_graph()
    lin, lin_nodes = linear_graph(initial)
    print('initial_states', len(set(initial)))
    print('full', summarize('full',full,initial))
    print('linear_only', summarize('linear_only',lin,initial))
    # exact edge agreement on the original operational domain
    same=0; total=0
    for src, outs in full.items():
        for z,dst in outs:
            total+=1; same += int(linear_step(src,z)==dst)
    print('full_edges_reproduced_by_linear', same, '/', total)
    print('linear_reachable_states', len(lin_nodes))

if __name__=='__main__':
    main()

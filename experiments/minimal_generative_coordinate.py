"""Search the smallest raw causal projection that is generatively sufficient.

Full causal state is (h,q,phase) with h,q in 0..7 and phase in 0..2.  Encode it
with eight Boolean coordinates:
    h0 h1 h2 q0 q1 q2 p0 p1
where p0,p1 are the two binary bits of phase.

A candidate projection is accepted when, on the operational universe reachable
from the eight public initial states:
  1. projected states are sufficient to determine the complete labeled local
     future: for each projected state the set of (z,next_projected_state) is
     unique, independent of which full state represented it;
  2. starting from projected public initials and repeatedly applying that local
     transition relation regenerates exactly the projected operational graph;
  3. the projected graph preserves path counts and the 63-bit frontier.

We search all subsets of the 8 raw bits.  This is deliberately stricter than
finding an arbitrary injective 6-bit encoding learned after the manifold is
known: the coordinate must be a direct projection of the generative causal
state itself.
"""
from __future__ import annotations

from collections import defaultdict, deque
from itertools import combinations

from binary_reversible_edge_label import labeled_records
from nonlinear_ablation import path_counts, frontier
from topological_transition_state import initial_topology

RAW = ('h0','h1','h2','q0','q1','q2','p0','p1')


def bits(node):
    h,q,p = map(int,node)
    return {
        'h0': (h>>0)&1, 'h1': (h>>1)&1, 'h2': (h>>2)&1,
        'q0': (q>>0)&1, 'q1': (q>>1)&1, 'q2': (q>>2)&1,
        'p0': (p>>0)&1, 'p1': (p>>1)&1,
    }


def project(node, coord):
    b=bits(node)
    return tuple(b[n] for n in coord)


def reference():
    reachable, _, records, _, _ = labeled_records()
    nodes=set(reachable)
    edges=defaultdict(list)
    for r in records:
        edges[r['src']].append((int(r['label']),r['dst']))
    initials=tuple((s,initial_topology(s),0) for s in range(8))
    return nodes,dict(edges),initials


def projected_graph(nodes,edges,initials,coord):
    # Full-state representatives sharing the same projected state must have the
    # same projected labeled future. Otherwise the projection is not Markov /
    # locally generative.
    signatures=defaultdict(set)
    for s in nodes:
        ps=project(s,coord)
        sig=tuple(sorted((z,project(d,coord)) for z,d in edges.get(s,())))
        signatures[ps].add(sig)
    conflicts={p:sigs for p,sigs in signatures.items() if len(sigs)>1}
    if conflicts:
        return None, {'conflicts':len(conflicts)}

    pedges={p:list(next(iter(sigs))) for p,sigs in signatures.items()}
    pinit=tuple(project(s,coord) for s in initials)

    seen=set(pinit); q=deque(pinit)
    while q:
        s=q.popleft()
        for _,d in pedges.get(s,()):
            if d not in seen:
                seen.add(d); q.append(d)

    # Exact closure: every projected operational state must be reachable and no
    # extra state can be introduced because pedges only uses the candidate's
    # own local state relation.
    exact_nodes=seen==set(pedges)
    return (pedges,pinit), {
        'conflicts':0,
        'projected_states':len(pedges),
        'reachable_projected_states':len(seen),
        'exact_nodes':exact_nodes,
    }


def reverse_ambiguity(edges):
    rev=defaultdict(set)
    for s,outs in edges.items():
        for z,d in outs:
            rev[(d,z)].add(s)
    amb=sum(len(v)>1 for v in rev.values())
    maxp=max((len(v) for v in rev.values()),default=0)
    return amb,maxp


def analyze_coord(nodes,edges,initials,coord,ref_counts):
    built,meta=projected_graph(nodes,edges,initials,coord)
    if built is None or not meta['exact_nodes']:
        return None
    pedges,pinit=built
    counts=path_counts(pedges,pinit)
    same_counts=all(counts[i]==ref_counts[i] for i in range(min(len(counts),len(ref_counts))))
    amb,maxp=reverse_ambiguity(pedges)
    return {
        'coordinate':coord,
        **meta,
        'projected_edges':sum(len(v) for v in pedges.values()),
        'reverse_ambiguous':amb,
        'max_reverse_preimages':maxp,
        'frontier':frontier(counts),
        'same_path_counts':same_counts,
        'injective_on_operational':meta['projected_states']==len(nodes),
    }


def main():
    nodes,edges,initials=reference()
    ref_counts=path_counts(edges,initials)
    print('reference_states',len(nodes),'reference_edges',sum(len(v) for v in edges.values()),'frontier',frontier(ref_counts))
    winners=[]
    for k in range(1,len(RAW)+1):
        level=[]
        for coord in combinations(RAW,k):
            row=analyze_coord(nodes,edges,initials,coord,ref_counts)
            if row and row['same_path_counts']:
                level.append(row)
        print('bits',k,'generatively_sufficient',len(level))
        if level:
            winners=level
            break
    print('minimum_raw_bits',len(winners[0]['coordinate']) if winners else None)
    print('solutions',len(winners))
    for row in winners[:20]:
        print(row)

if __name__=='__main__':
    main()

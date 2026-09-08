"""Regenerate the balanced operational universe in the full causal coordinate.

The compact 6-bit coordinate G is only injective on the validated 37-state
manifold.  Extending its fitted law outside that manifold created spurious
states.  This experiment therefore returns to the complete public causal state

    X = (history3, topology3, phase3)

and applies only the original local universe rule:

    policy <- policy_index(topology, phase, params)
    action <- ACTIONS[(history, phase, policy)]
    bit in _allowed(action)
    X' <- (_next_state, update_topology, next_phase)

Starting from the eight public initial states, no reachable-state whitelist or
edge table is used.  The resulting graph is compared only afterwards with the
validated operational graph.
"""
from __future__ import annotations

from collections import deque

from topological_transition_state import (
    ACTIONS, _allowed, _next_state, initial_topology,
    policy_index, update_topology,
)
from basin_potential_coordinate import EDGES as REFERENCE, PARAMS
from causal_coordinate_refinement import INITIAL


def grow():
    seen=set(INITIAL)
    q=deque(INITIAL)
    edges={}
    while q:
        state,topology,phase=q.popleft()
        pidx=policy_index(topology,phase,PARAMS)
        action=ACTIONS[(state,phase,pidx)]
        outs=[]
        for bit in _allowed(action):
            ns=_next_state(state,bit)
            nq=update_topology(topology,state,bit)
            nxt=(ns,nq,(phase+1)%3)
            outs.append((int(bit),nxt))
            if nxt not in seen:
                seen.add(nxt); q.append(nxt)
        edges[(state,topology,phase)]=tuple(outs)
    return edges,frozenset(seen)


def edge_set_labeled(edges):
    return {(s,b,d) for s,outs in edges.items() for b,d in outs}


def reference_labeled():
    # Recompute edge labels from the same public local rule, but only for the
    # already validated reachable reference nodes. This is for comparison only.
    reachable=set(INITIAL)
    q=deque(INITIAL)
    out={}
    while q:
        node=q.popleft()
        state,topology,phase=node
        pidx=policy_index(topology,phase,PARAMS)
        action=ACTIONS[(state,phase,pidx)]
        rows=[]
        for bit in _allowed(action):
            ns=_next_state(state,bit); nq=update_topology(topology,state,bit)
            nxt=(ns,nq,(phase+1)%3)
            # keep only edges that exist in the validated full graph
            if nxt in REFERENCE[node]:
                rows.append((int(bit),nxt))
                if nxt not in reachable:
                    reachable.add(nxt); q.append(nxt)
        out[node]=tuple(rows)
    return out,frozenset(reachable)


def path_counts(edges,max_steps=220):
    dist={s:1 for s in INITIAL}
    seq=[sum(dist.values())]
    for _ in range(max_steps):
        nxt={}
        for s,c in dist.items():
            for _,d in edges.get(s,()):
                nxt[d]=nxt.get(d,0)+c
        dist=nxt; seq.append(sum(dist.values()))
    return seq


def main():
    gen,nodes=grow()
    ref,refnodes=reference_labeled()
    ge=edge_set_labeled(gen); re=edge_set_labeled(ref)
    counts=path_counts(gen,220)
    limit=1<<63
    frontier=max(i for i,n in enumerate(counts) if n<=limit)
    print('params',PARAMS)
    print('generated_states',len(nodes),'reference_reachable_states',len(refnodes))
    print('generated_edges',len(ge),'reference_edges',len(re))
    print('node_exact',nodes==refnodes)
    print('edge_exact',ge==re)
    print('extra_nodes',len(nodes-refnodes),'missing_nodes',len(refnodes-nodes))
    print('extra_edges',len(ge-re),'missing_edges',len(re-ge))
    print('frontier_from_full_causal_rule',frontier)
    print('count218',counts[218] if len(counts)>218 else None)
    print('count219',counts[219] if len(counts)>219 else None)


if __name__=='__main__':
    main()

"""Exact entropy decomposition of the full information-clock path family.

For a fixed physical length n, assume a uniform distribution over all admissible
causal paths of that length.  By the chain rule, log2(|A_n|) can be decomposed
into:

- initial causal-state choice;
- transient branch decisions outside the dominant recurrent core;
- exit decisions at core nodes with one internal and one external successor;
- internal recurrent-core branch decisions.

This measures where the path-family information is actually created.
"""
from __future__ import annotations

import math
from collections import defaultdict
from functools import lru_cache

from recurrent_orbit_core import graph, strongly_connected_components, spectral_radius
from topological_transition_state import initial_topology

PARAMS=(0,2,4,4)
EDGES=graph(PARAMS)
INITIAL=tuple((s,initial_topology(s),0) for s in range(8))
COMPONENT=max(strongly_connected_components(EDGES),key=lambda c:spectral_radius(EDGES,c))


@lru_cache(maxsize=None)
def suffix(node,remaining):
    if remaining==0:return 1
    return sum(suffix(nxt,remaining-1) for nxt in EDGES[node])


def total_count(steps):
    return sum(suffix(node,steps) for node in INITIAL)


def entropy(weights):
    total=sum(weights)
    if total==0:return 0.0
    return -sum((w/total)*math.log2(w/total) for w in weights if w)


def decompose(steps):
    total=total_count(steps)
    total_h=math.log2(total)
    init_weights=[suffix(node,steps) for node in INITIAL]
    parts=defaultdict(float)
    expected_events=defaultdict(float)
    parts["initial_state"]=entropy(init_weights)

    forward={node:1 for node in INITIAL}
    for t in range(steps):
        remaining=steps-t
        for node,prefix_count in forward.items():
            outs=EDGES[node]
            if len(outs)<=1:
                continue
            weights=[suffix(nxt,remaining-1) for nxt in outs]
            continuation=sum(weights)
            if continuation==0:
                continue
            probability=(prefix_count*continuation)/total
            local_h=entropy(weights)
            internal=sum(nxt in COMPONENT for nxt in outs)
            if node in COMPONENT and internal>1:
                category="core_internal_branch"
            elif node in COMPONENT:
                category="core_exit_branch"
            else:
                category="transient_branch"
            parts[category]+=probability*local_h
            expected_events[category]+=probability

        nxt_forward={}
        for node,count in forward.items():
            for nxt in EDGES[node]:
                nxt_forward[nxt]=nxt_forward.get(nxt,0)+count
        forward=nxt_forward

    return total,total_h,dict(parts),dict(expected_events)


def main():
    steps=218
    total,total_h,parts,events=decompose(steps)
    print("physical_steps",steps)
    print("total_bits",steps+3)
    print("admissible",total)
    print("entropy_bits",f"{total_h:.12f}")
    print("component_nodes",len(COMPONENT))
    for key in ("initial_state","transient_branch","core_exit_branch","core_internal_branch"):
        value=parts.get(key,0.0)
        print(key,f"{value:.12f}",f"{100*value/total_h:.6f}%")
    print("chain_rule_sum",f"{sum(parts.values()):.12f}")
    for key,value in sorted(events.items()):
        print("expected_events",key,f"{value:.12f}")

if __name__=="__main__":main()

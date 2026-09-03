"""Map asymptotic basin choices in the full causal graph.

The full graph is reducible.  The dominant 14-state information-producing SCC
has spectral radius > 1 but has exits; the true sink recurrent classes are
subdominant rho=1 cycles.  This experiment builds the SCC condensation DAG and
asks which terminal recurrent basins are reachable from every causal state.

A state with one reachable sink is already basin-committed.  A state with more
than one reachable sink lies before a basin separatrix and still carries a
future orbit-class choice.
"""
from __future__ import annotations

from functools import lru_cache

import numpy as np

from recurrent_orbit_core import graph, strongly_connected_components
from topological_transition_state import initial_topology

PARAMS=(0,2,4,4)


def radius(edges,comp):
    nodes=list(comp); idx={n:i for i,n in enumerate(nodes)}
    A=np.zeros((len(nodes),len(nodes)))
    for u in nodes:
        for v in edges[u]:
            if v in idx:A[idx[u],idx[v]]+=1
    vals=np.linalg.eigvals(A)
    return float(max((abs(v) for v in vals),default=0.0))


def analyze():
    edges=graph(PARAMS)
    comps=strongly_connected_components(edges)
    node_comp={n:i for i,c in enumerate(comps) for n in c}
    dag={i:set() for i in range(len(comps))}
    for u,outs in edges.items():
        cu=node_comp[u]
        for v in outs:
            cv=node_comp[v]
            if cv!=cu:dag[cu].add(cv)
    sinks=tuple(i for i,outs in dag.items() if not outs)

    @lru_cache(maxsize=None)
    def reachable_sinks(ci):
        if ci in sinks:return frozenset((ci,))
        out=set()
        for nxt in dag[ci]:out.update(reachable_sinks(nxt))
        return frozenset(out)

    sink_info={i:(len(comps[i]),radius(edges,comps[i])) for i in sinks}
    dominant=max(range(len(comps)),key=lambda i:radius(edges,comps[i]))
    initials=tuple((s,initial_topology(s),0) for s in range(8))
    initial_rows=[]
    for node in initials:
        rs=reachable_sinks(node_comp[node])
        initial_rows.append((node,tuple(sorted(rs)),len(rs)))

    counts={}
    for n in edges:
        k=len(reachable_sinks(node_comp[n]))
        counts[k]=counts.get(k,0)+1

    return edges,comps,dag,sinks,sink_info,dominant,reachable_sinks,initial_rows,counts


def main():
    edges,comps,dag,sinks,sink_info,dominant,reachable,initial_rows,counts=analyze()
    print('causal_states',len(edges))
    print('scc_count',len(comps))
    print('sink_recurrent_classes',len(sinks))
    for rank,ci in enumerate(sinks):
        size,rho=sink_info[ci]
        print('sink',rank,'component_id',ci,'nodes',size,'rho',f'{rho:.15f}')
    print('dominant_component',dominant,'nodes',len(comps[dominant]),'reachable_sinks',len(reachable(dominant)),tuple(sorted(reachable(dominant))))
    print('states_by_number_of_reachable_sinks',dict(sorted(counts.items())))
    print('public_initial_state reachable_sink_components basin_count')
    for row in initial_rows:print(*row)

if __name__=='__main__':main()

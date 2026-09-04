"""Test whether basin label + spectral potential is sufficient as a causal coordinate.

For the selected topological universe params=(0,2,4,4), define:

- B(X): the set of terminal recurrent attractors reachable from causal state X;
- Phi(X): log2 of the dominant Perron right-eigenvector coordinate, on the
  reverse-reachable basin of the maximal-growth recurrent core.

The experiment groups states by (B, Phi) and then checks whether states in the
same group have identical future-count profiles for horizons 0..H.  If not,
(B,Phi) is not a sufficient causal coordinate even though it is spectrally
meaningful.
"""
from __future__ import annotations

import math
from collections import Counter, defaultdict
from functools import lru_cache

import numpy as np

from recurrent_orbit_core import graph, strongly_connected_components

PARAMS = (0, 2, 4, 4)
EDGES = graph(PARAMS)
NODES = tuple(EDGES)


def component_graph():
    comps = strongly_connected_components(EDGES)
    cid = {v: i for i, comp in enumerate(comps) for v in comp}
    outgoing = {i: set() for i in range(len(comps))}
    for v, outs in EDGES.items():
        for w in outs:
            if cid[v] != cid[w]:
                outgoing[cid[v]].add(cid[w])
    attractors = tuple(i for i, outs in outgoing.items() if not outs)
    return comps, cid, outgoing, attractors


def basin_signatures(cid, outgoing, attractors):
    @lru_cache(maxsize=None)
    def reach(ci):
        if ci in attractors:
            return frozenset((ci,))
        out = set()
        for nxt in outgoing[ci]:
            out.update(reach(nxt))
        return frozenset(out)

    return {node: tuple(sorted(reach(cid[node]))) for node in NODES}


def dominant_potential():
    idx = {node: i for i, node in enumerate(NODES)}
    A = np.zeros((len(NODES), len(NODES)), dtype=float)
    for node, outs in EDGES.items():
        i = idx[node]
        for nxt in outs:
            A[i, idx[nxt]] += 1.0

    vals, vecs = np.linalg.eig(A)
    k = int(np.argmax(np.abs(vals)))
    lam = float(abs(vals[k]))
    r = np.real(vecs[:, k])
    if r.sum() < 0:
        r = -r
    r[np.abs(r) < 1e-12] = 0.0
    m = float(r.max())
    r = r / m
    phi = {
        NODES[i]: math.log2(float(r[i]))
        for i in range(len(NODES))
        if r[i] > 1e-10
    }
    return lam, phi


def future_count_profiles(horizon: int = 20):
    profiles = {node: [1] for node in NODES}
    current = {node: 1 for node in NODES}
    for _ in range(horizon):
        current = {
            node: sum(current[nxt] for nxt in EDGES[node])
            for node in NODES
        }
        for node in NODES:
            profiles[node].append(current[node])
    return {node: tuple(values) for node, values in profiles.items()}


def analyze(horizon: int = 20):
    comps, cid, outgoing, attractors = component_graph()
    basin = basin_signatures(cid, outgoing, attractors)
    lam, phi = dominant_potential()
    profiles = future_count_profiles(horizon)

    groups = defaultdict(list)
    for node, value in phi.items():
        groups[(basin[node], round(value, 12))].append(node)

    ambiguous_groups = 0
    causally_mixed_groups = 0
    largest = 0
    for nodes in groups.values():
        largest = max(largest, len(nodes))
        if len(nodes) > 1:
            ambiguous_groups += 1
        if len({profiles[node] for node in nodes}) > 1:
            causally_mixed_groups += 1

    return {
        "states": len(NODES),
        "attractors": len(attractors),
        "lambda": lam,
        "positive_potential_states": len(phi),
        "coordinate_classes": len(groups),
        "ambiguous_coordinate_classes": ambiguous_groups,
        "causally_mixed_coordinate_classes": causally_mixed_groups,
        "largest_coordinate_class": largest,
        "basin_signature_counts": Counter(basin.values()),
    }


def main():
    result = analyze()
    for key, value in result.items():
        print(key, value)


if __name__ == "__main__":
    main()

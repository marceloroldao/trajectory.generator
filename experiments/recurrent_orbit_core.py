"""Analyze recurrent orbit-like cores in topological transition universes.

This experiment does not add another causal variable. It inspects the finite
phase-lifted causal graph of an already selected topological universe and asks:

- which strongly connected components (SCCs) support recurrent trajectories?
- which SCC dominates asymptotic trajectory growth?
- how many internal branch points does that recurrent core contain?
- what is its spectral growth rate?

The public phase is included in graph nodes, so a node is:

    (history3, topology3, phase3)

The graph has at most 8*8*3 = 192 nodes.
"""

from __future__ import annotations

import math
from collections import defaultdict

from topological_transition_state import (
    ACTIONS,
    _allowed,
    _next_state,
    policy_index,
    update_topology,
)


def graph(params: tuple[int, int, int, int]):
    edges = defaultdict(list)
    for state in range(8):
        for q in range(8):
            for phase in range(3):
                node = (state, q, phase)
                pidx = policy_index(q, phase, params)
                action = ACTIONS[(state, phase, pidx)]
                for bit in _allowed(action):
                    ns = _next_state(state, bit)
                    nq = update_topology(q, state, bit)
                    edges[node].append((ns, nq, (phase + 1) % 3))
    return edges


def strongly_connected_components(edges):
    index = 0
    stack = []
    on_stack = set()
    indices = {}
    low = {}
    result = []

    def visit(v):
        nonlocal index
        indices[v] = low[v] = index
        index += 1
        stack.append(v)
        on_stack.add(v)
        for w in edges[v]:
            if w not in indices:
                visit(w)
                low[v] = min(low[v], low[w])
            elif w in on_stack:
                low[v] = min(low[v], indices[w])
        if low[v] == indices[v]:
            comp = set()
            while True:
                w = stack.pop()
                on_stack.remove(w)
                comp.add(w)
                if w == v:
                    break
            result.append(comp)

    for v in list(edges):
        if v not in indices:
            visit(v)
    return result


def spectral_radius(edges, component, iterations: int = 200) -> float:
    nodes = list(component)
    if not nodes:
        return 0.0
    idx = {node: i for i, node in enumerate(nodes)}
    x = [1.0 / len(nodes)] * len(nodes)
    scale = 1.0
    for _ in range(iterations):
        y = [0.0] * len(nodes)
        for node, i in idx.items():
            for nxt in edges[node]:
                j = idx.get(nxt)
                if j is not None:
                    y[j] += x[i]
        norm = max(y, default=0.0)
        if norm == 0.0:
            return 0.0
        x = [v / norm for v in y]
        scale = norm
    return scale


def analyze(params: tuple[int, int, int, int]):
    edges = graph(params)
    rows = []
    for comp in strongly_connected_components(edges):
        lam = spectral_radius(edges, comp)
        internal_edges = sum(
            1 for node in comp for nxt in edges[node] if nxt in comp
        )
        exits = sum(
            1 for node in comp for nxt in edges[node] if nxt not in comp
        )
        branch_nodes = sum(
            1
            for node in comp
            if sum(1 for nxt in edges[node] if nxt in comp) > 1
        )
        rows.append((lam, len(comp), internal_edges, exits, branch_nodes))
    rows.sort(reverse=True)
    return rows


def main() -> None:
    candidates = {
        "robust_208": (1, 0, 0, 2),
        "balanced_221": (0, 2, 4, 4),
        "long_239": (3, 2, 4, 4),
    }
    print("name lambda bits_per_step nodes internal exits branch_nodes")
    for name, params in candidates.items():
        rows = analyze(params)
        lam, nodes, internal, exits, branches = rows[0]
        print(
            name,
            f"{lam:.9f}",
            f"{math.log2(lam):.9f}" if lam > 0 else "-inf",
            nodes,
            internal,
            exits,
            branches,
        )


if __name__ == "__main__":
    main()

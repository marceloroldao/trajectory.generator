"""Global information-potential diagnostic for the full causal graph.

This experiment asks whether the recurrent-core identity

    -log2 p(i->j) = h + Phi(i) - Phi(j)

can be extended from the dominant recurrent orbit to the complete phase-lifted
causal graph of the selected topological universe ``params=(0,2,4,4)``.

For a finite directed graph with adjacency matrix A, the max-entropy (Parry)
construction uses the Perron root lambda and a non-negative right eigenvector r:

    A r = lambda r
    p_ij = A_ij * r_j / (lambda * r_i)
    Phi(i) = log2 r_i
    h = log2 lambda

Whenever r_i>0 and r_j>0, the edge identity is exact by construction.  For a
reducible graph, however, the Perron eigenvector may vanish outside the basin
that feeds the maximal-growth recurrent class.  Those zero-support states do
not have a finite Phi under the global max-entropy measure.

The script therefore reports:
- global spectral radius and entropy rate;
- SCC spectral classes;
- support of the dominant right eigenvector;
- stochastic-row and potential residuals on positive support;
- edges that leave positive support toward zero-support states;
- whether every public initial state lies in the positive-support basin.

This is a structural diagnostic.  A zero-support state is not 'invalid'; it
means the global maximal-entropy measure assigns asymptotically zero weight to
that dynamical region.  Such a region may still admit its own local potential
with its own spectral rate.
"""
from __future__ import annotations

import math
from collections import defaultdict

import numpy as np

from recurrent_orbit_core import graph, strongly_connected_components
from topological_transition_state import initial_topology

PARAMS = (0, 2, 4, 4)
EPS = 1e-10


def adjacency(edges):
    nodes = tuple(sorted(edges))
    idx = {node: i for i, node in enumerate(nodes)}
    A = np.zeros((len(nodes), len(nodes)), dtype=float)
    for source, targets in edges.items():
        i = idx[source]
        for target in targets:
            A[i, idx[target]] += 1.0
    return nodes, idx, A


def spectral_data(A):
    values, vectors = np.linalg.eig(A)
    k = int(np.argmax(np.abs(values)))
    lam = float(abs(values[k]))
    r = np.real(vectors[:, k])
    # Eigenvectors are defined up to sign.  Numerical eigensolvers can also
    # return tiny negative noise for a theoretically non-negative PF vector.
    if np.sum(r) < 0:
        r = -r
    r[np.abs(r) < EPS] = 0.0
    r[r < 0] = 0.0
    if np.max(r) > 0:
        r = r / np.max(r)
    return lam, r


def component_radius(A, indices):
    if not indices:
        return 0.0
    sub = A[np.ix_(indices, indices)]
    values = np.linalg.eigvals(sub)
    return float(max((abs(v) for v in values), default=0.0))


def analyze():
    edges = graph(PARAMS)
    nodes, idx, A = adjacency(edges)
    lam, r = spectral_data(A)
    h = math.log2(lam) if lam > 0 else float('-inf')

    support = {nodes[i] for i, value in enumerate(r) if value > EPS}
    zero = set(nodes) - support
    phi = {
        nodes[i]: math.log2(value)
        for i, value in enumerate(r)
        if value > EPS
    }

    row_residuals = []
    edge_residuals = []
    support_exits = []
    for source in support:
        i = idx[source]
        probs = []
        for target in edges[source]:
            j = idx[target]
            if r[j] <= EPS:
                support_exits.append((source, target))
                probs.append(0.0)
                continue
            p = r[j] / (lam * r[i])
            probs.append(p)
            surprise = -math.log2(p)
            predicted = h + phi[source] - phi[target]
            edge_residuals.append(abs(surprise - predicted))
        row_residuals.append(abs(sum(probs) - 1.0))

    comps = strongly_connected_components(edges)
    comp_rows = []
    node_to_comp = {}
    for ci, comp in enumerate(comps):
        for node in comp:
            node_to_comp[node] = ci
        indices = [idx[node] for node in comp]
        rho = component_radius(A, indices)
        internal_edges = sum(1 for node in comp for target in edges[node] if target in comp)
        exits = sum(1 for node in comp for target in edges[node] if target not in comp)
        supported = sum(node in support for node in comp)
        comp_rows.append((rho, len(comp), internal_edges, exits, supported, ci, comp))
    comp_rows.sort(reverse=True, key=lambda row: (row[0], row[1]))

    initial = tuple((state, initial_topology(state), 0) for state in range(8))
    initial_supported = tuple(node for node in initial if node in support)

    return {
        'nodes': nodes,
        'lambda': lam,
        'h': h,
        'support': support,
        'zero': zero,
        'phi': phi,
        'row_residual_max': max(row_residuals, default=0.0),
        'edge_residual_max': max(edge_residuals, default=0.0),
        'support_exits': support_exits,
        'components': comp_rows,
        'initial': initial,
        'initial_supported': initial_supported,
    }


def main():
    result = analyze()
    print('nodes', len(result['nodes']))
    print('lambda_global', f"{result['lambda']:.15f}")
    print('h_global_bits_per_step', f"{result['h']:.15f}")
    print('positive_support_nodes', len(result['support']))
    print('zero_support_nodes', len(result['zero']))
    print('public_initial_nodes', len(result['initial']))
    print('supported_initial_nodes', len(result['initial_supported']))
    print('max_row_probability_residual', f"{result['row_residual_max']:.3e}")
    print('max_edge_potential_residual', f"{result['edge_residual_max']:.3e}")
    print('positive_to_zero_support_edges', len(result['support_exits']))
    print('scc rank rho nodes internal_edges exits supported_nodes')
    for rank, row in enumerate(result['components'][:20]):
        rho, size, internal, exits, supported, ci, _ = row
        print(rank, f"{rho:.15f}", size, internal, exits, supported)

    # A finite global Phi under the maximal-entropy Parry measure requires the
    # relevant state to lie on positive support.  If support is strict, the
    # mathematically clean interpretation is piecewise: dominant-basin Phi plus
    # local potentials for subdominant recurrent classes.
    if len(result['support']) == len(result['nodes']):
        print('global_finite_potential', True)
    else:
        print('global_finite_potential', False)
        print('interpretation', 'dominant-basin potential + local subdominant potentials')


if __name__ == '__main__':
    main()

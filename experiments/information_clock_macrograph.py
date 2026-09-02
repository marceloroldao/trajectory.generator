"""Condense recurrent trajectory cores into an information-clock macrograph.

A physical trajectory may spend many deterministic transitions between the few
states where more than one admissible successor exists.  This experiment
collapses each deterministic flight into one macro-edge between branch states.

For the balanced topological candidate params=(0,2,4,4), the dominant recurrent
core is analyzed.  The macrograph preserves the physical-time growth rate by
using edge lengths explicitly.
"""

from __future__ import annotations

import math

from recurrent_orbit_core import graph, strongly_connected_components, spectral_radius

PARAMS = (0, 2, 4, 4)


def dominant_component():
    edges = graph(PARAMS)
    comps = strongly_connected_components(edges)
    comp = max(comps, key=lambda c: spectral_radius(edges, c))
    return edges, comp


def internal(edges, comp, node):
    return [nxt for nxt in edges[node] if nxt in comp]


def macro_edges(edges, comp):
    branches = [node for node in comp if len(internal(edges, comp, node)) > 1]
    out = []
    for source in branches:
        for first in internal(edges, comp, source):
            path = [source, first]
            current = first
            seen = {source}
            while current not in branches:
                if current in seen:
                    raise RuntimeError("deterministic cycle without branch encountered")
                seen.add(current)
                nxt = internal(edges, comp, current)
                if len(nxt) != 1:
                    raise RuntimeError("unexpected non-branch internal degree")
                current = nxt[0]
                path.append(current)
            out.append((source, current, len(path) - 1, tuple(path)))
    return branches, out


def transfer_matrix(branches, macros, lam: float):
    idx = {node: i for i, node in enumerate(branches)}
    m = [[0.0 for _ in branches] for _ in branches]
    for source, target, length, _ in macros:
        m[idx[source]][idx[target]] += lam ** (-length)
    return m


def radius_2x2(m):
    a, b = m[0]
    c, d = m[1]
    tr = a + d
    det = a * d - b * c
    disc = max(0.0, tr * tr - 4.0 * det)
    return max(abs((tr + math.sqrt(disc)) / 2.0), abs((tr - math.sqrt(disc)) / 2.0))


def solve_lambda(branches, macros):
    lo, hi = 1.0, 2.0
    for _ in range(100):
        mid = (lo + hi) / 2.0
        rho = radius_2x2(transfer_matrix(branches, macros, mid))
        if rho > 1.0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def parry_statistics(branches, macros, lam: float):
    # For the current two-branch macrograph, solve the positive right
    # eigenvector W r = r and left eigenvector l W = l analytically up to scale.
    w = transfer_matrix(branches, macros, lam)
    a, b = w[0]
    c, d = w[1]
    r = [b, 1.0 - a]
    l = [c, 1.0 - a]
    norm = sum(l[i] * r[i] for i in range(2))
    pi = [l[i] * r[i] / norm for i in range(2)]
    idx = {node: i for i, node in enumerate(branches)}

    avg_length = 0.0
    event_entropy = 0.0
    probabilities = []
    for source in branches:
        i = idx[source]
        local = []
        for edge in [e for e in macros if e[0] == source]:
            _, target, length, _ = edge
            j = idx[target]
            p = lam ** (-length) * r[j] / r[i]
            local.append((length, target, p))
            avg_length += pi[i] * p * length
            if p > 0:
                event_entropy += pi[i] * (-p * math.log2(p))
        probabilities.append((source, tuple(local)))
    return pi, avg_length, event_entropy, probabilities


def main():
    edges, comp = dominant_component()
    branches, macros = macro_edges(edges, comp)
    lam_core = spectral_radius(edges, comp)
    lam_macro = solve_lambda(branches, macros)
    pi, avg_len, h_event, probs = parry_statistics(branches, macros, lam_macro)

    print("dominant_core_nodes", len(comp))
    print("branch_states", branches)
    print("macro_edges")
    for source, target, length, _ in macros:
        print(" ", source, "->", target, "physical_length=", length)
    print("lambda_core", f"{lam_core:.12f}")
    print("lambda_macro", f"{lam_macro:.12f}")
    print("bits_per_physical_step", f"{math.log2(lam_macro):.12f}")
    print("branch_stationary", [round(v, 12) for v in pi])
    print("avg_physical_steps_per_information_event", f"{avg_len:.12f}")
    print("bits_per_information_event", f"{h_event:.12f}")
    print("check_bits_per_step", f"{h_event / avg_len:.12f}")
    print("edge_probabilities")
    for source, local in probs:
        print(" ", source, local)

    # For this candidate the lengths are A->B=1, A->A=12,
    # B->A=2 and B->A=5. Therefore det(I-W)=0 gives:
    #   1 - lambda^-12 - lambda^-3 - lambda^-6 = 0
    # or equivalently lambda^12-lambda^9-lambda^6-1=0.
    residual = lam_macro**12 - lam_macro**9 - lam_macro**6 - 1.0
    print("characteristic_residual", f"{residual:.3e}")


if __name__ == "__main__":
    main()

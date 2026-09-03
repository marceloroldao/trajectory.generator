"""Information-time coordinates for the recurrent orbit macrograph.

This experiment separates two notions that were previously conflated:

1) horizon-conditioned information time

    tau_H(t) = -sum log2 P(choice_k | recovered prefix, final horizon t)

   Under a uniform distribution over all admissible trajectories of fixed
   physical length t, this telescopes to log2 |A_t| for every trajectory. It is
   therefore a family-level entropy coordinate, not a path-specific age.

2) intrinsic recurrent-orbit information time

   tau_orb = -sum log2 p(edge_k)

   where p(edge) is the Parry/max-entropy transition probability on the
   variable-length recurrent macrograph. For a macro-edge i->j of physical
   length L,

       p(i->j,L) = lambda^-L * r_j / r_i

   and therefore

       -log2 p = h*L + Phi(i) - Phi(j)

   with h=log2(lambda), Phi(i)=log2(r_i).

   Along a macro-path, the potential terms telescope:

       tau_orb = h*T + Phi(start) - Phi(end)

   This gives a path coordinate that depends on physical duration and boundary
   orbit state, while being independent of the internal decomposition into
   macro-edges.
"""

from __future__ import annotations

import math

from information_clock_macrograph import dominant_component, macro_edges, solve_lambda


def intrinsic_coordinate():
    edges, comp = dominant_component()
    branches, macros = macro_edges(edges, comp)
    branches = tuple(sorted(branches))
    idx = {node: i for i, node in enumerate(branches)}
    lam = solve_lambda(branches, macros)
    h = math.log2(lam)

    # Two-state transfer matrix W(lambda) with spectral radius 1.
    W = [[0.0 for _ in branches] for _ in branches]
    for source, target, length, _ in macros:
        W[idx[source]][idx[target]] += lam ** (-length)

    if len(branches) != 2:
        raise RuntimeError("current experiment expects two recurrent branch states")
    a, b = W[0]
    # Positive right eigenvector of W r = r, up to scale.
    r = [b, 1.0 - a]
    phi = [math.log2(v) for v in r]

    rows = []
    for source, target, length, _ in sorted(
        macros, key=lambda e: (idx[e[0]], idx[e[1]], e[2])
    ):
        i, j = idx[source], idx[target]
        p = lam ** (-length) * r[j] / r[i]
        surprise = -math.log2(p)
        predicted = h * length + phi[i] - phi[j]
        rows.append((i, j, length, p, surprise, predicted))

    return lam, h, r, phi, rows


def main():
    lam, h, r, phi, rows = intrinsic_coordinate()
    print("lambda", f"{lam:.15f}")
    print("bits_per_physical_step", f"{h:.15f}")
    print("right_eigenvector", [f"{v:.15f}" for v in r])
    print("orbit_potential_bits", [f"{v:.15f}" for v in phi])
    print("boundary_potential_gap", f"{phi[0]-phi[1]:.15f}")
    print("edge source target length probability surprise predicted residual")
    for i, j, length, p, surprise, predicted in rows:
        print(
            i,
            j,
            length,
            f"{p:.15f}",
            f"{surprise:.15f}",
            f"{predicted:.15f}",
            f"{surprise-predicted:.3e}",
        )

    # For any complete recurrent macro-path:
    # tau_orb = h*T + Phi(start)-Phi(end).
    print("coordinate_formula")
    print("tau_orb = h*T + Phi(start) - Phi(end)")


if __name__ == "__main__":
    main()

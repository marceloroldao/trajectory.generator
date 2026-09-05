"""Search for a table-free local formula for the reversible edge label.

The canonical binary edge coloring proves that a one-bit reversible label z
exists, but that construction uses the global incidence graph.  This experiment
asks whether the resulting z can be computed directly from local observables of
a transition, without using the causal-class IDs c/cn.

We test increasingly expressive Boolean algebraic normal forms (ANF) over GF(2)
using physical/local primitive bits only.  An exact degree-1 solution is an
affine formula; degree-2/3 allow pair/triple interactions.  The system is solved
only on the 49 operational edges, so an exact formula is evidence of a compact
local law on the observed operational domain, not a proof outside that domain.
"""
from __future__ import annotations

from itertools import combinations

from binary_reversible_edge_label import labeled_records


def primitive_vector(r):
    """Return named local bits; deliberately excludes causal class IDs."""
    vals = {
        "phase": int(r["phase"]) & 1,
        "next_phase": int(r["next_phase"]) & 1,
        "history_lsb": int(r["history_lsb"]) & 1,
        "next_history_lsb": int(r["next_history_lsb"]) & 1,
        "ordinal": int(r["ordinal"]) & 1,
        "branching": int(int(r["outdegree"]) > 1),
    }
    for prefix, value, width in (
        ("hdelta", int(r["history_delta"]), 3),
        ("top", int(r["topology"]), 3),
        ("ntop", int(r["next_topology"]), 3),
        ("tdelta", int(r["topology_delta"]), 3),
    ):
        for i in range(width):
            vals[f"{prefix}{i}"] = (value >> i) & 1
    return vals


def gf2_solve(rows, rhs):
    """Return one solution x to A x=b over GF(2), or None if inconsistent."""
    if not rows:
        return [] if not any(rhs) else None
    m = len(rows)
    n = len(rows[0])
    aug = [sum((bit & 1) << j for j, bit in enumerate(row)) | ((rhs[i] & 1) << n)
           for i, row in enumerate(rows)]
    pivot_cols = []
    rr = 0
    for col in range(n):
        pivot = next((i for i in range(rr, m) if (aug[i] >> col) & 1), None)
        if pivot is None:
            continue
        aug[rr], aug[pivot] = aug[pivot], aug[rr]
        for i in range(m):
            if i != rr and ((aug[i] >> col) & 1):
                aug[i] ^= aug[rr]
        pivot_cols.append(col)
        rr += 1
        if rr == m:
            break
    coeff_mask = (1 << n) - 1
    for row in aug:
        if (row & coeff_mask) == 0 and ((row >> n) & 1):
            return None
    x = [0] * n
    # Free variables fixed to zero; RREF makes pivot values immediate.
    for i, col in enumerate(pivot_cols):
        x[col] = (aug[i] >> n) & 1
    return x


def monomial_specs(names, degree):
    specs = [()]  # constant 1
    for d in range(1, degree + 1):
        specs.extend(combinations(range(len(names)), d))
    return specs


def design_matrix(vectors, specs):
    matrix = []
    for v in vectors:
        row = []
        for spec in specs:
            bit = 1
            for idx in spec:
                bit &= v[idx]
            row.append(bit)
        matrix.append(row)
    return matrix


def expression(names, specs, solution):
    terms = []
    for spec, enabled in zip(specs, solution):
        if not enabled:
            continue
        if not spec:
            terms.append("1")
        else:
            terms.append("&".join(names[i] for i in spec))
    return " ^ ".join(terms) if terms else "0", len(terms)


def analyze():
    _, _, records, _, _ = labeled_records()
    primitives = [primitive_vector(r) for r in records]
    names = sorted(primitives[0])
    vectors = [[p[n] for n in names] for p in primitives]
    target = [int(r["label"]) for r in records]

    # Detect whether identical local observations ever demand opposite labels.
    local_to_labels = {}
    conflicts = 0
    for vec, z in zip(vectors, target):
        key = tuple(vec)
        labels = local_to_labels.setdefault(key, set())
        labels.add(z)
    conflicts = sum(len(v) > 1 for v in local_to_labels.values())

    degree_results = []
    for degree in (1, 2, 3):
        specs = monomial_specs(names, degree)
        A = design_matrix(vectors, specs)
        sol = gf2_solve(A, target)
        if sol is None:
            degree_results.append({
                "degree": degree,
                "features": len(specs),
                "exact": False,
            })
            continue
        expr, terms = expression(names, specs, sol)
        pred = [sum(a * b for a, b in zip(row, sol)) & 1 for row in A]
        degree_results.append({
            "degree": degree,
            "features": len(specs),
            "exact": pred == target,
            "terms": terms,
            "expression": expr,
        })
        if pred == target:
            break

    return {
        "operational_edges": len(records),
        "primitive_bits": len(names),
        "primitive_names": names,
        "unique_local_observations": len(local_to_labels),
        "local_observation_conflicts": conflicts,
        "table_free_local_function_exists_on_domain": conflicts == 0,
        "degree_search": degree_results,
    }


def main():
    result = analyze()
    for key, value in result.items():
        print(key, value)


if __name__ == "__main__":
    main()

"""Search for a table-free local formula for the reversible edge label.

The canonical binary edge coloring proves that a one-bit reversible label z
exists, but that construction uses the global incidence graph. This experiment
asks whether the resulting z can be computed directly from local observables of
a transition, without causal-class IDs and, in stricter families, without
branch ordinal/outdegree metadata.

We test Boolean algebraic normal forms (ANF) over GF(2). Exact fits are evidence
for a compact local law on the observed 49-edge operational domain; they are not
a proof outside that domain.
"""
from __future__ import annotations

from itertools import combinations

from binary_reversible_edge_label import labeled_records


def primitive_vector(r):
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
    for i, col in enumerate(pivot_cols):
        x[col] = (aug[i] >> n) & 1
    return x


def monomial_specs(names, degree):
    specs = [()]
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
        terms.append("1" if not spec else "&".join(names[i] for i in spec))
    return " ^ ".join(terms) if terms else "0", len(terms)


def family_result(primitives, target, names, max_degree):
    vectors = [[p[n] for n in names] for p in primitives]
    local_to_labels = {}
    for vec, z in zip(vectors, target):
        local_to_labels.setdefault(tuple(vec), set()).add(z)
    conflicts = sum(len(v) > 1 for v in local_to_labels.values())

    out = {
        "primitive_bits": len(names),
        "primitive_names": names,
        "unique_observations": len(local_to_labels),
        "conflicts": conflicts,
        "function_exists": conflicts == 0,
        "degree_search": [],
    }
    if conflicts:
        return out

    for degree in range(1, max_degree + 1):
        specs = monomial_specs(names, degree)
        A = design_matrix(vectors, specs)
        sol = gf2_solve(A, target)
        if sol is None:
            out["degree_search"].append({"degree": degree, "features": len(specs), "exact": False})
            continue
        pred = [sum(a * b for a, b in zip(row, sol)) & 1 for row in A]
        expr, terms = expression(names, specs, sol)
        row = {"degree": degree, "features": len(specs), "exact": pred == target,
               "terms": terms, "expression": expr}
        out["degree_search"].append(row)
        if pred == target:
            break
    return out


def analyze():
    _, _, records, _, _ = labeled_records()
    primitives = [primitive_vector(r) for r in records]
    target = [int(r["label"]) for r in records]
    all_names = sorted(primitives[0])

    families = {
        "all_local_no_class_ids": all_names,
        "no_branch_metadata": [n for n in all_names if n not in {"ordinal", "branching"}],
        "relation_phase_only": [
            n for n in all_names
            if n in {"phase", "next_phase", "history_lsb", "next_history_lsb"}
            or n.startswith("hdelta") or n.startswith("tdelta")
        ],
        "state_phase_no_branch": [
            n for n in all_names if n not in {"ordinal", "branching"}
        ],
    }

    return {
        "operational_edges": len(records),
        "families": {
            name: family_result(primitives, target, names, 4)
            for name, names in families.items()
        },
    }


def main():
    result = analyze()
    print("operational_edges", result["operational_edges"])
    for name, row in result["families"].items():
        print(name, row)


if __name__ == "__main__":
    main()

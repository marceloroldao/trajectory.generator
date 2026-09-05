"""Find the smallest relation/phase variable subset that computes z locally.

Starting from the 10-variable relation_phase_only family, exhaustively scan all
subsets. For each subset we first require zero observation conflicts; then test
ANF degree 1..3 for an exact fit to the canonical reversible edge label.
"""
from __future__ import annotations

from itertools import combinations

from binary_reversible_edge_label import labeled_records
from local_label_formula_search import primitive_vector, monomial_specs, design_matrix, gf2_solve, expression


def exact_for_subset(primitives, target, names, max_degree=3):
    vectors = [[p[n] for n in names] for p in primitives]
    seen = {}
    for vec, z in zip(vectors, target):
        seen.setdefault(tuple(vec), set()).add(z)
    if any(len(v) > 1 for v in seen.values()):
        return None
    for degree in range(1, max_degree + 1):
        specs = monomial_specs(names, degree)
        A = design_matrix(vectors, specs)
        sol = gf2_solve(A, target)
        if sol is None:
            continue
        pred = [sum(a * b for a, b in zip(row, sol)) & 1 for row in A]
        if pred == target:
            expr, terms = expression(names, specs, sol)
            return {"degree": degree, "terms": terms, "expression": expr}
    return None


def analyze():
    _, _, records, _, _ = labeled_records()
    primitives = [primitive_vector(r) for r in records]
    target = [int(r["label"]) for r in records]
    candidates = sorted([
        n for n in primitives[0]
        if n in {"phase", "next_phase", "history_lsb", "next_history_lsb"}
        or n.startswith("hdelta") or n.startswith("tdelta")
    ])

    winners = []
    for size in range(1, len(candidates) + 1):
        level = []
        for subset in combinations(candidates, size):
            result = exact_for_subset(primitives, target, list(subset), 3)
            if result is not None:
                row = {"variables": list(subset), **result}
                level.append(row)
        if level:
            level.sort(key=lambda r: (r["degree"], r["terms"], r["variables"]))
            winners = level
            break

    return {
        "operational_edges": len(records),
        "candidate_variables": candidates,
        "minimum_variable_count": len(winners[0]["variables"]) if winners else None,
        "exact_subsets_at_minimum": len(winners),
        "best": winners[0] if winners else None,
        "top5": winners[:5],
    }


def main():
    for k, v in analyze().items():
        print(k, v)


if __name__ == "__main__":
    main()

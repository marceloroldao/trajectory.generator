"""Minimize the Boolean gate that activates the single nonlinear channel.

For the best compact coordinate G=(h1,orientation,phase0,phase1,q0,q1), the
exact forward/reverse dynamics each contain one nonlinear output.  The XOR of
all degree>=2 ANF terms is treated as a gate a(G,z).  We search the smallest
subset of the seven inputs (g0..g5,z) that determines that gate exactly and
report the lowest ANF degree/term count on that subset.
"""
from __future__ import annotations

from itertools import combinations

from binary_reversible_edge_label import labeled_records
from compact_geometric_coordinate import state_features, transition_laws
from local_label_formula_search import gf2_solve, monomial_specs, design_matrix, expression
from nonlinear_correction_support import COORD, split_expr, eval_terms

INPUTS = [f'g{i}' for i in range(6)] + ['z']


def build_rows(records, reverse=False):
    fw, rv = transition_laws(records, COORD)
    laws = rv if reverse else fw
    nonlinear = [(i, meta) for i, (_, meta) in enumerate(laws) if meta and meta['degree'] >= 2]
    assert len(nonlinear) == 1
    idx, meta = nonlinear[0]
    _, nonlinear_terms = split_expr(meta['expression'])
    rows = []
    for r in records:
        node = r['dst'] if reverse else r['src']
        sf = state_features(node)
        row = {f'g{i}': int(sf[n]) for i, n in enumerate(COORD)}
        row['z'] = int(r['label'])
        row['gate'] = eval_terms(nonlinear_terms, row)
        rows.append(row)
    return idx, meta, rows


def determines(rows, subset):
    seen = {}
    for r in rows:
        key = tuple(r[n] for n in subset)
        v = r['gate']
        if key in seen and seen[key] != v:
            return False
        seen[key] = v
    return True


def solve_gate(rows, subset):
    vectors = [[r[n] for n in subset] for r in rows]
    target = [r['gate'] for r in rows]
    for degree in range(1, len(subset) + 1):
        specs = monomial_specs(list(subset), degree)
        A = design_matrix(vectors, specs)
        sol = gf2_solve(A, target)
        if sol is not None:
            pred = [sum(a*b for a,b in zip(row, sol)) & 1 for row in A]
            if pred == target:
                expr, terms = expression(list(subset), specs, sol)
                return {'degree': degree, 'terms': terms, 'expression': expr}
    return None


def analyze_direction(records, reverse=False):
    idx, meta, rows = build_rows(records, reverse=reverse)
    exact = []
    for k in range(1, len(INPUTS)+1):
        for subset in combinations(INPUTS, k):
            if determines(rows, subset):
                law = solve_gate(rows, subset)
                exact.append({'inputs': list(subset), **law})
        if exact:
            break
    exact.sort(key=lambda x: (x['degree'], x['terms'], x['inputs']))
    return {
        'nonlinear_output': idx,
        'coordinate_name': COORD[idx],
        'original_degree': meta['degree'],
        'minimum_gate_inputs': len(exact[0]['inputs']),
        'exact_minimal_subsets': len(exact),
        'best_gate': exact[0],
        'top5': exact[:5],
    }


def main():
    _, _, records, _, _ = labeled_records()
    print('coordinate', list(COORD))
    print('forward', analyze_direction(records, False))
    print('reverse', analyze_direction(records, True))


if __name__ == '__main__':
    main()

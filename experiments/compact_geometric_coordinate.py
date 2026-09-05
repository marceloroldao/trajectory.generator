"""Search for a compact semantic coordinate for the 37 operational states.

Because reversible partition refinement proves that no two operational causal
states can be merged, any exact binary coordinate needs at least ceil(log2 37)=6
bits.  We search semantic/state-local Boolean features for an injective 6-bit
coordinate, then test whether forward and reverse coordinate updates under the
binary edge label z admit low-degree ANF laws.
"""
from __future__ import annotations

from itertools import combinations

from binary_reversible_edge_label import labeled_records
from local_label_formula_search import gf2_solve, monomial_specs, design_matrix, expression


def parity(x: int) -> int:
    return x.bit_count() & 1


def state_features(node):
    h, q, p = map(int, node)
    f = {
        'h0': (h >> 0) & 1,
        'h1': (h >> 1) & 1,
        'h2': (h >> 2) & 1,
        'q0': (q >> 0) & 1,
        'q1': (q >> 1) & 1,
        'q2': (q >> 2) & 1,
        'h_parity': parity(h),
        'q_parity': parity(q),
        'orientation': parity(h) ^ parity(q),
        'phase0': int(p == 0),
        'phase1': int(p == 1),
        'phase2': int(p == 2),
        'phase_lsb': p & 1,
        'phase_hi': (p >> 1) & 1,
        'h_weight_hi': int(h.bit_count() >= 2),
        'q_weight_hi': int(q.bit_count() >= 2),
    }
    return f


def unique_nodes(records):
    nodes = {r['src'] for r in records} | {r['dst'] for r in records}
    return sorted(nodes)


def injective_subset(nodes, names):
    seen = {}
    for n in nodes:
        f = state_features(n)
        key = tuple(f[x] for x in names)
        if key in seen:
            return False
        seen[key] = n
    return True


def find_min_coordinate(nodes):
    names = sorted(state_features(nodes[0]))
    lower = 6
    exact = []
    for k in range(lower, len(names)+1):
        for sub in combinations(names, k):
            if injective_subset(nodes, sub):
                exact.append(sub)
        if exact:
            return names, exact
    return names, []


def anf_law(rows, input_names, outputs, max_degree=3):
    vectors = [[r[n] for n in input_names] for r in rows]
    out = []
    for out_name in outputs:
        target = [r[out_name] for r in rows]
        solved = None
        for degree in range(1, max_degree+1):
            specs = monomial_specs(input_names, degree)
            A = design_matrix(vectors, specs)
            sol = gf2_solve(A, target)
            if sol is not None:
                pred = [sum(a*b for a,b in zip(row, sol)) & 1 for row in A]
                if pred == target:
                    expr, terms = expression(input_names, specs, sol)
                    solved = {'degree': degree, 'terms': terms, 'expression': expr}
                    break
        out.append((out_name, solved))
    return out


def transition_laws(records, coord):
    rows_f = []
    rows_r = []
    for r in records:
        sf = state_features(r['src']); df = state_features(r['dst'])
        rowf = {f'g{i}': sf[n] for i,n in enumerate(coord)}
        rowf['z'] = int(r['label'])
        for i,n in enumerate(coord): rowf[f'ng{i}'] = df[n]
        rows_f.append(rowf)
        rowr = {f'g{i}': df[n] for i,n in enumerate(coord)}
        rowr['z'] = int(r['label'])
        for i,n in enumerate(coord): rowr[f'pg{i}'] = sf[n]
        rows_r.append(rowr)
    ins = [f'g{i}' for i in range(len(coord))] + ['z']
    fw = anf_law(rows_f, ins, [f'ng{i}' for i in range(len(coord))])
    rv = anf_law(rows_r, ins, [f'pg{i}' for i in range(len(coord))])
    return fw, rv


def score_laws(laws):
    if any(v is None for _,v in laws):
        return (99, 10**9)
    return (max(v['degree'] for _,v in laws), sum(v['terms'] for _,v in laws))


def analyze():
    _, _, records, _, _ = labeled_records()
    nodes = unique_nodes(records)
    candidates, exact = find_min_coordinate(nodes)
    evaluated = []
    for coord in exact:
        fw, rv = transition_laws(records, coord)
        evaluated.append({
            'coordinate': list(coord),
            'forward_score': score_laws(fw),
            'reverse_score': score_laws(rv),
            'forward': fw,
            'reverse': rv,
        })
    evaluated.sort(key=lambda x: (max(x['forward_score'][0],x['reverse_score'][0]),
                                  x['forward_score'][1]+x['reverse_score'][1],
                                  x['coordinate']))
    return {
        'states': len(nodes),
        'information_lower_bound_bits': 6,
        'candidate_features': candidates,
        'minimum_coordinate_bits': len(exact[0]) if exact else None,
        'coordinates_at_minimum': len(exact),
        'best': evaluated[0] if evaluated else None,
        'top5': evaluated[:5],
    }


def main():
    result = analyze()
    for k,v in result.items():
        print(k, v)


if __name__ == '__main__':
    main()

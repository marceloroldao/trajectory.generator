"""Test whether the compact 6-bit state evolves affinely for each edge label z.

For every injective 6-feature semantic coordinate, fit
    G' = A_z G + c_z   over GF(2)
separately for z=0 and z=1 on the operational edges.  If A_z has rank 6, the
law extends to a globally reversible affine permutation of all 64 binary states.
We also report the best quadratic fallback when affine closure fails.
"""
from __future__ import annotations

from itertools import combinations

from binary_reversible_edge_label import labeled_records
from compact_geometric_coordinate import state_features, unique_nodes, injective_subset
from local_label_formula_search import gf2_solve, monomial_specs, design_matrix


def gf2_rank(rows):
    rows = [sum((b & 1) << j for j,b in enumerate(row)) for row in rows]
    rank = 0
    col = 0
    while rows and col < 64:
        pivot = next((i for i,r in enumerate(rows) if (r >> col) & 1), None)
        if pivot is None:
            col += 1; continue
        p = rows.pop(pivot)
        rows = [r ^ p if (r >> col) & 1 else r for r in rows]
        rank += 1; col += 1
    return rank


def fit_map(records, coord, z, degree):
    subset = [r for r in records if int(r['label']) == z]
    ins = [f'g{i}' for i in range(6)]
    specs = monomial_specs(ins, degree)
    vectors = []
    outputs = [[] for _ in range(6)]
    for r in subset:
        sf, df = state_features(r['src']), state_features(r['dst'])
        x = [sf[n] for n in coord]
        vectors.append(x)
        for j,n in enumerate(coord): outputs[j].append(df[n])
    A = design_matrix(vectors, specs)
    sols = []
    for target in outputs:
        sol = gf2_solve(A, target)
        if sol is None:
            return None
        pred = [sum(a*b for a,b in zip(row, sol)) & 1 for row in A]
        if pred != target:
            return None
        sols.append(sol)
    result = {'degree': degree, 'terms': sum(sum(sol) for sol in sols)}
    if degree == 1:
        # specs = constant + six linear monomials.
        matrix = []
        const = []
        for sol in sols:
            const.append(sol[0])
            matrix.append(sol[1:7])
        result['rank'] = gf2_rank(matrix)
        result['invertible'] = result['rank'] == 6
        result['A'] = matrix
        result['c'] = const
    return result


def analyze():
    _, _, records, _, _ = labeled_records()
    nodes = unique_nodes(records)
    feature_names = sorted(state_features(nodes[0]))
    coords = [c for c in combinations(feature_names,6) if injective_subset(nodes,c)]
    affine = []
    quadratic = []
    for coord in coords:
        fits1 = [fit_map(records, coord, z, 1) for z in (0,1)]
        if all(f is not None for f in fits1):
            affine.append({'coordinate': list(coord), 'z0': fits1[0], 'z1': fits1[1]})
            continue
        fits2 = [fit_map(records, coord, z, 2) for z in (0,1)]
        if all(f is not None for f in fits2):
            quadratic.append({'coordinate': list(coord), 'z0': fits2[0], 'z1': fits2[1],
                              'terms': fits2[0]['terms']+fits2[1]['terms']})
    affine.sort(key=lambda r: (not (r['z0']['invertible'] and r['z1']['invertible']),
                               r['z0']['terms']+r['z1']['terms'], r['coordinate']))
    quadratic.sort(key=lambda r: (r['terms'], r['coordinate']))
    return {
        'semantic_coordinates_tested': len(coords),
        'affine_coordinates': len(affine),
        'globally_reversible_affine_coordinates': sum(
            r['z0']['invertible'] and r['z1']['invertible'] for r in affine),
        'best_affine': affine[0] if affine else None,
        'quadratic_coordinates': len(quadratic),
        'best_quadratic': quadratic[0] if quadratic else None,
    }


def main():
    for k,v in analyze().items(): print(k,v)

if __name__ == '__main__': main()

"""Map where the minimal nonlinear correction acts in the best 6-bit coordinate.

Best compact coordinate found previously:
    G = (h1, orientation, phase0, phase1, q0, q1)

Forward has exactly one nonlinear output (g4 / q0) and reverse has exactly one
nonlinear output (g1 / orientation).  This experiment separates each exact ANF
law into affine and nonlinear parts and counts on which operational edges the
nonlinear remainder is actually active.
"""
from __future__ import annotations

from collections import Counter, defaultdict

from binary_reversible_edge_label import labeled_records
from compact_geometric_coordinate import state_features, transition_laws

COORD = ('h1', 'orientation', 'phase0', 'phase1', 'q0', 'q1')


def eval_term(term: str, values: dict[str, int]) -> int:
    term = term.strip()
    if term == '1':
        return 1
    v = 1
    for name in term.split('&'):
        v &= int(values[name.strip()])
    return v


def split_expr(expr: str):
    terms = [x.strip() for x in expr.split('^')]
    affine = [x for x in terms if x == '1' or '&' not in x]
    nonlinear = [x for x in terms if '&' in x]
    return affine, nonlinear


def eval_terms(terms, values):
    out = 0
    for term in terms:
        out ^= eval_term(term, values)
    return out


def rows(records, reverse=False):
    out = []
    for r in records:
        src = r['dst'] if reverse else r['src']
        dst = r['src'] if reverse else r['dst']
        sf, df = state_features(src), state_features(dst)
        row = {f'g{i}': sf[n] for i, n in enumerate(COORD)}
        row['z'] = int(r['label'])
        row['phase_raw'] = int(src[2])
        row['dst_phase_raw'] = int(dst[2])
        row['src'] = src
        row['dst'] = dst
        row['bit'] = int(r.get('bit', r.get('next_history_lsb', 0)))
        for i, n in enumerate(COORD):
            row[f'o{i}'] = df[n]
        out.append(row)
    return out


def analyze_direction(records, reverse=False):
    fw, rv = transition_laws(records, COORD)
    laws = rv if reverse else fw
    nonlinear = [(i, meta) for i, (_, meta) in enumerate(laws) if meta and meta['degree'] >= 2]
    assert len(nonlinear) == 1
    idx, meta = nonlinear[0]
    affine_terms, nonlinear_terms = split_expr(meta['expression'])

    support = []
    for row in rows(records, reverse=reverse):
        n = eval_terms(nonlinear_terms, row)
        a = eval_terms(affine_terms, row)
        exact = a ^ n
        assert exact == row[f'o{idx}']
        if n:
            support.append(row)

    by_z = Counter(r['z'] for r in support)
    by_phase = Counter(r['phase_raw'] for r in support)
    by_phase_z = Counter((r['phase_raw'], r['z']) for r in support)
    by_bit = Counter(r['bit'] for r in support)

    return {
        'output_index': idx,
        'coordinate_name': COORD[idx],
        'degree': meta['degree'],
        'terms_total': meta['terms'],
        'affine_terms': affine_terms,
        'nonlinear_terms': nonlinear_terms,
        'active_edges': len(support),
        'inactive_edges': len(records) - len(support),
        'active_fraction': len(support) / len(records),
        'support_by_z': dict(sorted(by_z.items())),
        'support_by_phase': dict(sorted(by_phase.items())),
        'support_by_phase_z': {str(k): v for k, v in sorted(by_phase_z.items())},
        'support_by_bit': dict(sorted(by_bit.items())),
        'support_edges': [(r['src'], r['dst'], r['z']) for r in support],
    }


def analyze():
    _, _, records, _, _ = labeled_records()
    return {
        'coordinate': list(COORD),
        'operational_edges': len(records),
        'forward': analyze_direction(records, reverse=False),
        'reverse': analyze_direction(records, reverse=True),
    }


def main():
    result = analyze()
    print('coordinate', result['coordinate'])
    print('operational_edges', result['operational_edges'])
    for direction in ('forward', 'reverse'):
        d = result[direction]
        print(direction, {k: v for k, v in d.items() if k != 'support_edges'})
        print(direction + '_support_edges', d['support_edges'])


if __name__ == '__main__':
    main()

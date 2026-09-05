"""Measure how concentrated the irreducible nonlinearity is in compact 6-bit coordinates.

For every injective semantic 6-bit coordinate, solve exact forward and reverse
ANF laws with input (G,z), then count how many output coordinates require degree
>=2, >=3 and >=4.  We seek coordinates where all nonlinear behavior is confined
to the fewest output channels in both directions.
"""
from __future__ import annotations

from itertools import combinations

from binary_reversible_edge_label import labeled_records
from compact_geometric_coordinate import (
    state_features, unique_nodes, injective_subset, transition_laws
)


def degree_profile(laws):
    degrees = [v['degree'] if v is not None else 99 for _, v in laws]
    terms = [v['terms'] if v is not None else 10**9 for _, v in laws]
    return {
        'degrees': degrees,
        'nonlinear_outputs': sum(d >= 2 for d in degrees),
        'cubic_or_more_outputs': sum(d >= 3 for d in degrees),
        'quartic_or_more_outputs': sum(d >= 4 for d in degrees),
        'max_degree': max(degrees),
        'terms': sum(terms),
    }


def analyze():
    _, _, records, _, _ = labeled_records()
    nodes = unique_nodes(records)
    names = sorted(state_features(nodes[0]))
    coords = [c for c in combinations(names, 6) if injective_subset(nodes, c)]
    rows = []
    for coord in coords:
        fw, rv = transition_laws(records, coord)
        fp, rp = degree_profile(fw), degree_profile(rv)
        rows.append({
            'coordinate': list(coord),
            'forward': fp,
            'reverse': rp,
            'nonlinear_channels_total': fp['nonlinear_outputs'] + rp['nonlinear_outputs'],
            'worst_nonlinear_channels': max(fp['nonlinear_outputs'], rp['nonlinear_outputs']),
            'max_degree': max(fp['max_degree'], rp['max_degree']),
            'terms': fp['terms'] + rp['terms'],
        })
    rows.sort(key=lambda r: (
        r['worst_nonlinear_channels'], r['nonlinear_channels_total'],
        r['max_degree'], r['terms'], r['coordinate']))
    best = rows[0]
    one_each = [r for r in rows if r['forward']['nonlinear_outputs'] == 1 and
                               r['reverse']['nonlinear_outputs'] == 1]
    return {
        'coordinates_tested': len(rows),
        'minimum_worst_nonlinear_channels': best['worst_nonlinear_channels'],
        'minimum_total_nonlinear_channels': best['nonlinear_channels_total'],
        'coordinates_with_one_nonlinear_channel_each_direction': len(one_each),
        'best': best,
        'top10': rows[:10],
    }


def main():
    for k, v in analyze().items():
        print(k, v)


if __name__ == '__main__':
    main()

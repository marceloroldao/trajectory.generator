"""Test whether the compact nonlinear-core signature survives nearby universes.

We perturb the four public selector parameters around the balanced universe
(0,2,4,4), plus include the previously studied robust/long candidates.  For each
universe we:

- build the phase-lifted causal graph;
- restrict to states reachable from the eight public initial states;
- construct a canonical binary bidirectionally-reversible edge coloring directly
  on the raw reachable state graph;
- test the previously discovered compact semantic coordinate
  G=(h1,orientation,phase0,phase1,q0,q1);
- when G is injective, solve exact forward/reverse ANF laws;
- count nonlinear output channels and test whether any nonlinear ANF monomial
  contains the reversible edge label z.

This is deliberately a robustness test, not a new search for a best coordinate.
If the same compact coordinate fails, that is recorded rather than repaired by
per-universe optimization.
"""
from __future__ import annotations

from collections import deque

from recurrent_orbit_core import graph
from topological_transition_state import initial_topology
from compact_geometric_coordinate import injective_subset, transition_laws
from binary_reversible_edge_label import binary_edge_coloring

COORD = ('h1', 'orientation', 'phase0', 'phase1', 'q0', 'q1')
BASE = (0, 2, 4, 4)
KNOWN = ((1, 0, 0, 2), BASE, (3, 2, 4, 4))


def neighborhood(base=BASE):
    out = set(KNOWN)
    for i in range(4):
        for v in range(5):
            if v == base[i]:
                continue
            p = list(base)
            p[i] = v
            out.add(tuple(p))
    return tuple(sorted(out))


def reachable_for(params):
    edges = graph(params)
    initial = tuple((s, initial_topology(s), 0) for s in range(8))
    seen = set(initial)
    q = deque(initial)
    while q:
        x = q.popleft()
        for y in edges[x]:
            if y not in seen:
                seen.add(y)
                q.append(y)
    return edges, tuple(sorted(seen))


def labeled_records(params):
    edges, nodes = reachable_for(params)
    node_set = set(nodes)
    raw = []
    for src in nodes:
        outs = [dst for dst in edges[src] if dst in node_set]
        for ordinal, dst in enumerate(outs):
            raw.append({
                'src': src, 'dst': dst,
                'c': src, 'cn': dst,
                'ordinal': ordinal,
                'next_history_lsb': dst[0] & 1,
                'history_delta': src[0] ^ dst[0],
                'topology_delta': src[1] ^ dst[1],
                'phase': src[2],
            })
    raw.sort(key=lambda r: (r['src'], r['dst'], r['ordinal']))
    labels, max_out, max_in = binary_edge_coloring(raw)
    if labels is None:
        return nodes, (), max_out, max_in
    records = []
    for i, r in enumerate(raw):
        rr = dict(r)
        rr['label'] = labels[i]
        records.append(rr)
    return nodes, tuple(records), max_out, max_in


def nonlinear_profile(laws):
    degrees = []
    nonlinear_outputs = 0
    nonlinear_uses_z = False
    nonlinear_indices = []
    for i, (_, meta) in enumerate(laws):
        degree = meta['degree'] if meta else 99
        degrees.append(degree)
        if degree >= 2:
            nonlinear_outputs += 1
            nonlinear_indices.append(i)
            expr = meta.get('expression', '') if meta else ''
            for term in (x.strip() for x in expr.split('^')):
                if '&' in term and 'z' in {p.strip() for p in term.split('&')}:
                    nonlinear_uses_z = True
    return degrees, nonlinear_outputs, nonlinear_indices, nonlinear_uses_z


def profile(params):
    nodes, records, max_out, max_in = labeled_records(params)
    row = {
        'params': params,
        'states': len(nodes),
        'edges': len(records),
        'max_out': max_out,
        'max_in': max_in,
        'binary_label': bool(records),
        'coord_injective': False,
    }
    if not records or not injective_subset(nodes, COORD):
        return row
    row['coord_injective'] = True
    fw, rv = transition_laws(records, COORD)
    fdeg, fnl, findices, fz = nonlinear_profile(fw)
    rdeg, rnl, rindices, rz = nonlinear_profile(rv)
    row.update({
        'forward_degrees': fdeg,
        'reverse_degrees': rdeg,
        'forward_nonlinear_channels': fnl,
        'reverse_nonlinear_channels': rnl,
        'forward_nonlinear_indices': findices,
        'reverse_nonlinear_indices': rindices,
        'forward_nonlinear_uses_z': fz,
        'reverse_nonlinear_uses_z': rz,
        'forward_max_degree': max(fdeg),
        'reverse_max_degree': max(rdeg),
        'same_one_channel_signature': fnl == 1 and rnl == 1,
        'nonlinear_independent_of_z': not fz and not rz,
    })
    return row


def main():
    rows = [profile(p) for p in neighborhood()]
    print('universes', len(rows))
    print('params states edges injective fnl rnl fdeg rdeg findx rindx zfree one_each')
    for r in rows:
        print(r['params'], r['states'], r['edges'], r['coord_injective'],
              r.get('forward_nonlinear_channels'), r.get('reverse_nonlinear_channels'),
              r.get('forward_max_degree'), r.get('reverse_max_degree'),
              r.get('forward_nonlinear_indices'), r.get('reverse_nonlinear_indices'),
              r.get('nonlinear_independent_of_z'), r.get('same_one_channel_signature'))
    viable = [r for r in rows if r['coord_injective']]
    one = [r for r in viable if r.get('same_one_channel_signature')]
    zfree = [r for r in one if r.get('nonlinear_independent_of_z')]
    print('summary', {
        'universes': len(rows),
        'binary_label_universes': sum(r['binary_label'] for r in rows),
        'same_coordinate_injective': len(viable),
        'one_nonlinear_channel_each_direction': len(one),
        'z_independent_nonlinear_core': len(zfree),
        'one_channel_fraction_among_injective': len(one)/len(viable) if viable else 0.0,
        'z_independent_fraction_among_one_channel': len(zfree)/len(one) if one else 0.0,
    })


if __name__ == '__main__':
    main()

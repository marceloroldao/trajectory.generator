"""Derive the smallest state partition closed under the reversible binary label.

Starting from one coarse class, refine operational causal states by the labeled
forward and reverse transition structure.  Two states remain equivalent only if,
for each z in {0,1}, they see the same existence/target-class pattern forward
and reverse, and the same recovered data-bit pattern.  The fixed point is a
candidate internal geometric state G that can evolve locally as

    G_{t+1} = Gamma(G_t, z_t)
    G_t     = Gamma^{-1}(G_{t+1}, z_t)

without requiring the original 37 causal-state IDs.
"""
from __future__ import annotations

from collections import defaultdict, Counter

from binary_reversible_edge_label import labeled_records


def canonical_partition(states, sig):
    keys = sorted({sig[s] for s in states}, key=repr)
    kid = {k: i for i, k in enumerate(keys)}
    return {s: kid[sig[s]] for s in states}


def refine(include_bit: bool = True):
    reachable, coord, records, _, _ = labeled_records()
    classes = sorted(set(coord.values()))

    by_out = defaultdict(dict)
    by_in = defaultdict(dict)
    for r in records:
        c, cn, z, b = r['c'], r['cn'], int(r['label']), int(r['next_history_lsb'])
        by_out[c][z] = (cn, b)
        by_in[cn][z] = (c, b)

    part = {c: 0 for c in classes}
    rounds = 0
    while True:
        def signature(c):
            f = []
            rv = []
            for z in (0, 1):
                if z in by_out[c]:
                    dst, b = by_out[c][z]
                    f.append((z, 1, part[dst], b if include_bit else None))
                else:
                    f.append((z, 0, None, None))
                if z in by_in[c]:
                    src, b = by_in[c][z]
                    rv.append((z, 1, part[src], b if include_bit else None))
                else:
                    rv.append((z, 0, None, None))
            return tuple(f), tuple(rv)

        new = canonical_partition(classes, {c: signature(c) for c in classes})
        rounds += 1
        if all(new[c] == part[c] for c in classes):
            break
        # canonical IDs may renumber; compare equivalence relation instead.
        old_groups = sorted(sorted(c for c in classes if part[c] == k) for k in set(part.values()))
        new_groups = sorted(sorted(c for c in classes if new[c] == k) for k in set(new.values()))
        part = new
        if old_groups == new_groups:
            break

    return classes, records, part, rounds


def closure(records, part):
    f = defaultdict(set)
    r = defaultdict(set)
    bitf = defaultdict(set)
    bitr = defaultdict(set)
    for rec in records:
        g = part[rec['c']]
        gn = part[rec['cn']]
        z = int(rec['label'])
        b = int(rec['next_history_lsb'])
        f[(g, z)].add(gn)
        r[(gn, z)].add(g)
        bitf[(g, z)].add(b)
        bitr[(gn, z)].add(b)
    def amb(t): return sum(len(v) > 1 for v in t.values())
    return {
        'forward_ambiguous': amb(f),
        'reverse_ambiguous': amb(r),
        'bit_forward_ambiguous': amb(bitf),
        'bit_reverse_ambiguous': amb(bitr),
    }


def analyze():
    out = {}
    for include_bit in (False, True):
        classes, records, part, rounds = refine(include_bit=include_bit)
        sizes = Counter(part.values())
        out['with_bit' if include_bit else 'structure_only'] = {
            'causal_states': len(classes),
            'geometric_states': len(sizes),
            'rounds': rounds,
            'class_sizes': sorted(sizes.values(), reverse=True),
            'closure': closure(records, part),
        }
    return out


def main():
    for k, v in analyze().items():
        print(k, v)


if __name__ == '__main__':
    main()

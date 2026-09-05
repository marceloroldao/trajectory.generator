"""Search semantic/geometric invariants that reproduce the reversible edge label.

We already have a minimal 7-variable Boolean description in terms of raw local
bits. This experiment groups those bits into more interpretable invariants:
phase relation, history direction, transition parity, topology-motion class,
and orientation change. We test whether a small invariant tuple uniquely
predicts the canonical binary reversible label on all 49 operational edges.
"""
from __future__ import annotations

from itertools import combinations
from collections import defaultdict

from binary_reversible_edge_label import labeled_records


def parity(x: int) -> int:
    return x.bit_count() & 1


def invariants(r):
    h = int(r["src"][0])
    hn = int(r["dst"][0])
    q = int(r["topology"])
    qn = int(r["next_topology"])
    hd = int(r["history_delta"])
    qd = int(r["topology_delta"])
    p = int(r["phase"])
    pn = int(r["next_phase"])

    # Interpretations are intentionally simple and local.
    return {
        "phase_flip": p ^ pn,
        "phase_now": p & 1,
        "history_parity": parity(h),
        "history_next_parity": parity(hn),
        "history_delta_parity": parity(hd),
        "history_step_weight": hd.bit_count(),
        "history_direction": ((hn > h) - (hn < h)) + 1,  # {0,1,2}
        "topology_parity": parity(q),
        "topology_next_parity": parity(qn),
        "topology_delta_parity": parity(qd),
        "topology_step_weight": qd.bit_count(),
        "topology_direction": ((qn > q) - (qn < q)) + 1,
        "orientation_match": parity(h) ^ parity(q),
        "next_orientation_match": parity(hn) ^ parity(qn),
        "orientation_flip": (parity(h) ^ parity(q)) ^ (parity(hn) ^ parity(qn)),
        "delta_alignment": parity(hd) ^ parity(qd),
        "history_lsb": h & 1,
        "next_history_lsb": hn & 1,
    }


def subset_stats(records, names):
    table = defaultdict(set)
    for r in records:
        inv = invariants(r)
        key = tuple(inv[n] for n in names)
        table[key].add(int(r["label"]))
    conflicts = sum(len(v) > 1 for v in table.values())
    return conflicts, len(table)


def analyze():
    _, _, records, _, _ = labeled_records()
    inv_names = sorted(invariants(records[0]))
    exact = []
    for k in range(1, len(inv_names) + 1):
        for subset in combinations(inv_names, k):
            conflicts, unique = subset_stats(records, subset)
            if conflicts == 0:
                exact.append((subset, unique))
        if exact:
            break
    return {
        "operational_edges": len(records),
        "candidate_invariants": inv_names,
        "minimum_invariant_count": len(exact[0][0]) if exact else None,
        "exact_subsets_at_minimum": len(exact),
        "top10": [
            {"invariants": list(s), "unique_observations": u}
            for s, u in exact[:10]
        ],
    }


def main():
    for k, v in analyze().items():
        print(k, v)


if __name__ == "__main__":
    main()

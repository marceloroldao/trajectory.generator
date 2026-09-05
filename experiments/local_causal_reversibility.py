"""Test a single binary relation label in both causal directions.

The exact reverse-partition search found the minimal topology relation

    r = 0 for topology_delta in {0,1,2,3}
    r = 1 for topology_delta in {4,5,6,7}

which is simply the high bit of the 3-bit topology XOR delta.  This experiment
tests whether that same r labels the operational causal automaton injectively in
both directions, and whether it also determines the transition/data bit.
"""
from __future__ import annotations

from collections import defaultdict

from local_causal_coordinate import operational_coordinate, edge_records


def relation_bit(record):
    return (record["topology_delta"] >> 2) & 1


def table_stats(records, key_fn, value_fn):
    table = defaultdict(set)
    for rec in records:
        table[key_fn(rec)].add(value_fn(rec))
    ambiguous = {k: v for k, v in table.items() if len(v) > 1}
    return table, {
        "keys": len(table),
        "ambiguous_keys": len(ambiguous),
        "max_values": max((len(v) for v in table.values()), default=0),
        "closed": not ambiguous,
    }


def analyze():
    reachable, coord = operational_coordinate()
    records = edge_records(reachable, coord)

    _, f_rel = table_stats(
        records,
        lambda r: (r["c"], relation_bit(r)),
        lambda r: r["cn"],
    )
    _, r_rel = table_stats(
        records,
        lambda r: (r["cn"], relation_bit(r)),
        lambda r: r["c"],
    )

    # Does the same relation label also recover the input/output bit on the edge?
    _, bit_from_forward = table_stats(
        records,
        lambda r: (r["c"], relation_bit(r)),
        lambda r: r["next_history_lsb"],
    )
    _, bit_from_reverse = table_stats(
        records,
        lambda r: (r["cn"], relation_bit(r)),
        lambda r: r["next_history_lsb"],
    )

    relation_counts = {0: 0, 1: 0}
    mismatches = 0
    for rec in records:
        rb = relation_bit(rec)
        relation_counts[rb] += 1
        mismatches += rb != rec["next_history_lsb"]

    return {
        "reachable_states": len(reachable),
        "operational_edges": len(records),
        "relation_counts": relation_counts,
        "relation_vs_bit_mismatches": mismatches,
        "forward_same_relation": f_rel,
        "reverse_same_relation": r_rel,
        "bit_from_forward_relation": bit_from_forward,
        "bit_from_reverse_relation": bit_from_reverse,
        "same_relation_bidirectional": f_rel["closed"] and r_rel["closed"],
        "same_relation_is_complete_edge_label": (
            f_rel["closed"]
            and r_rel["closed"]
            and bit_from_forward["closed"]
            and bit_from_reverse["closed"]
        ),
    }


def main():
    for key, value in analyze().items():
        print(key, value)


if __name__ == "__main__":
    main()

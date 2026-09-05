"""Test how much local transition information is required for reversibility.

Forward closure already showed:

    (C_t, next_history_lsb) -> C_{t+1}

is single-valued on the 37-state operational graph.  Here we scan reverse keys
of increasing richness to determine the smallest relational observation that
makes

    (C_{t+1}, local_relation) -> C_t

single-valued, without supplying the raw previous-state tuple.
"""
from __future__ import annotations

from collections import defaultdict

from local_causal_coordinate import operational_coordinate, edge_records


def ambiguity(records, fields):
    table = defaultdict(set)
    for r in records:
        key = tuple(r[f] for f in fields)
        table[key].add(r["c"])
    ambiguous = {k: v for k, v in table.items() if len(v) > 1}
    return {
        "keys": len(table),
        "ambiguous_keys": len(ambiguous),
        "max_prev_classes": max((len(v) for v in table.values()), default=0),
        "closed": not ambiguous,
    }


def analyze():
    reachable, coord = operational_coordinate()
    records = edge_records(reachable, coord)

    forward = defaultdict(set)
    for r in records:
        forward[(r["c"], r["next_history_lsb"])].add(r["cn"])
    forward_ambiguous = sum(len(v) > 1 for v in forward.values())

    reverse_candidates = {
        "Cnext_bit": ("cn", "next_history_lsb"),
        "Cnext_ordinal": ("cn", "ordinal"),
        "Cnext_history_delta": ("cn", "history_delta"),
        "Cnext_topology_delta": ("cn", "topology_delta"),
        "Cnext_relation": ("cn", "history_delta", "topology_delta"),
        "Cnext_bit_history_delta": ("cn", "next_history_lsb", "history_delta"),
        "Cnext_bit_topology_delta": ("cn", "next_history_lsb", "topology_delta"),
        "Cnext_bit_relation": (
            "cn", "next_history_lsb", "history_delta", "topology_delta"
        ),
        "Cnext_relation_phase": (
            "cn", "history_delta", "topology_delta", "phase"
        ),
        "Cnext_full_local_no_raw_prev": (
            "cn", "next_history_lsb", "history_delta", "topology_delta", "phase"
        ),
    }

    return {
        "reachable_states": len(reachable),
        "operational_edges": len(records),
        "forward_keys": len(forward),
        "forward_ambiguous": forward_ambiguous,
        "forward_closed": forward_ambiguous == 0,
        "reverse_tests": {
            name: ambiguity(records, fields)
            for name, fields in reverse_candidates.items()
        },
    }


def main():
    result = analyze()
    print("reachable_states", result["reachable_states"])
    print("operational_edges", result["operational_edges"])
    print("forward_keys", result["forward_keys"])
    print("forward_ambiguous", result["forward_ambiguous"])
    print("forward_closed", result["forward_closed"])
    for name, row in result["reverse_tests"].items():
        print(name, row)


if __name__ == "__main__":
    main()

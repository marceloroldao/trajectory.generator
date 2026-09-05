"""Test how much local transition information is required for reversibility.

Forward closure already showed:

    (C_t, next_history_lsb) -> C_{t+1}

is single-valued on the 37-state operational graph.  Here we scan reverse keys
and coarsenings of the topology relation to find the smallest local relation
that makes

    (C_{t+1}, local_relation) -> C_t

single-valued, without supplying the raw previous-state tuple.
"""
from __future__ import annotations

from collections import Counter, defaultdict

from local_causal_coordinate import operational_coordinate, edge_records


def ambiguity_from_key(records, key_fn):
    table = defaultdict(set)
    for r in records:
        table[key_fn(r)].add(r["c"])
    ambiguous = {k: v for k, v in table.items() if len(v) > 1}
    return {
        "keys": len(table),
        "ambiguous_keys": len(ambiguous),
        "max_prev_classes": max((len(v) for v in table.values()), default=0),
        "closed": not ambiguous,
    }


def ambiguity(records, fields):
    return ambiguity_from_key(records, lambda r: tuple(r[f] for f in fields))


def analyze():
    reachable, coord = operational_coordinate()
    records = edge_records(reachable, coord)

    forward = defaultdict(set)
    for r in records:
        forward[(r["c"], r["next_history_lsb"])].add(r["cn"])
    forward_ambiguous = sum(len(v) > 1 for v in forward.values())

    reverse_candidates = {
        "Cnext_bit": lambda r: (r["cn"], r["next_history_lsb"]),
        "Cnext_ordinal": lambda r: (r["cn"], r["ordinal"]),
        "Cnext_history_delta": lambda r: (r["cn"], r["history_delta"]),
        "Cnext_topology_delta": lambda r: (r["cn"], r["topology_delta"]),
        "Cnext_topology_changed": lambda r: (r["cn"], int(r["topology_delta"] != 0)),
        "Cnext_topology_parity": lambda r: (r["cn"], r["topology_delta"] & 1),
        "Cnext_topology_popcount": lambda r: (r["cn"], int(r["topology_delta"]).bit_count()),
        "Cnext_bit_topology_changed": lambda r: (
            r["cn"], r["next_history_lsb"], int(r["topology_delta"] != 0)
        ),
        "Cnext_bit_topology_parity": lambda r: (
            r["cn"], r["next_history_lsb"], r["topology_delta"] & 1
        ),
        "Cnext_bit_topology_popcount": lambda r: (
            r["cn"], r["next_history_lsb"], int(r["topology_delta"]).bit_count()
        ),
        "Cnext_relation": lambda r: (
            r["cn"], r["history_delta"], r["topology_delta"]
        ),
    }

    topology_values = Counter(r["topology_delta"] for r in records)
    results = {
        name: ambiguity_from_key(records, fn)
        for name, fn in reverse_candidates.items()
    }

    return {
        "reachable_states": len(reachable),
        "operational_edges": len(records),
        "forward_keys": len(forward),
        "forward_ambiguous": forward_ambiguous,
        "forward_closed": forward_ambiguous == 0,
        "topology_delta_values": dict(sorted(topology_values.items())),
        "topology_delta_alphabet": len(topology_values),
        "reverse_tests": results,
    }


def main():
    result = analyze()
    print("reachable_states", result["reachable_states"])
    print("operational_edges", result["operational_edges"])
    print("forward_keys", result["forward_keys"])
    print("forward_ambiguous", result["forward_ambiguous"])
    print("forward_closed", result["forward_closed"])
    print("topology_delta_values", result["topology_delta_values"])
    print("topology_delta_alphabet", result["topology_delta_alphabet"])
    for name, row in result["reverse_tests"].items():
        print(name, row)


if __name__ == "__main__":
    main()

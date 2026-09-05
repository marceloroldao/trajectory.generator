"""Test whether the operational causal coordinate is locally reversible.

Forward closure already showed that the next causal class is determined by
(current causal class, transition bit).  Here we test the reverse direction:

    (next causal class, transition bit) -> previous causal class

using the same bit-like local observation: the least-significant bit of the
next history3 state.  If both maps are single-valued on all operational edges,
the causal-class dynamics is locally reversible when the transition bit is
known.
"""
from __future__ import annotations

from collections import defaultdict

from local_causal_coordinate import operational_coordinate, edge_records


def build_tables():
    reachable, coord = operational_coordinate()
    records = edge_records(reachable, coord)

    forward = defaultdict(set)
    reverse = defaultdict(set)
    for r in records:
        b = r["next_history_lsb"]
        forward[(r["c"], b)].add(r["cn"])
        reverse[(r["cn"], b)].add(r["c"])

    f_amb = {k: v for k, v in forward.items() if len(v) != 1}
    r_amb = {k: v for k, v in reverse.items() if len(v) != 1}

    return {
        "reachable_states": len(reachable),
        "operational_edges": len(records),
        "forward_keys": len(forward),
        "reverse_keys": len(reverse),
        "forward_ambiguous": len(f_amb),
        "reverse_ambiguous": len(r_amb),
        "forward_closed": not f_amb,
        "reverse_closed": not r_amb,
        "locally_reversible": (not f_amb) and (not r_amb),
        "forward_table": {k: next(iter(v)) for k, v in forward.items() if len(v) == 1},
        "reverse_table": {k: next(iter(v)) for k, v in reverse.items() if len(v) == 1},
    }


def main():
    result = build_tables()
    for key in (
        "reachable_states",
        "operational_edges",
        "forward_keys",
        "reverse_keys",
        "forward_ambiguous",
        "reverse_ambiguous",
        "forward_closed",
        "reverse_closed",
        "locally_reversible",
    ):
        print(key, result[key])


if __name__ == "__main__":
    main()

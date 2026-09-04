"""Test whether the bidirectional causal coordinate can be updated locally.

We already know that offline bidirectional partition refinement is injective on
the 37 operationally reachable states.  This experiment asks a stronger
question: is the next causal class a deterministic function of only

    (current causal class, local transition observation)

where the observation does NOT contain the raw next-state tuple?

Several increasingly rich public/local observations are tested.  A coordinate
is considered locally closed when every observed key maps to exactly one next
causal class.
"""
from __future__ import annotations

from collections import defaultdict, deque

from basin_potential_coordinate import EDGES, basin_signatures, component_graph, dominant_potential
from causal_coordinate_refinement import INITIAL, canonical_ids, reachable_nodes, refine


def operational_coordinate():
    comps, cid, outgoing, attractors = component_graph()
    basin = basin_signatures(cid, outgoing, attractors)
    _, phi = dominant_potential()
    reachable = reachable_nodes()
    base = {
        node: (basin[node], round(phi[node], 12) if node in phi else None)
        for node in reachable
    }
    coord, _ = refine(reachable, base, include_predecessors=True)
    return reachable, canonical_ids(coord)


def edge_records(reachable, coord):
    node_set = set(reachable)
    records = []
    for src in reachable:
        outs = tuple(dst for dst in EDGES[src] if dst in node_set)
        for ordinal, dst in enumerate(outs):
            # Nodes are (history3, topology_state, phase).
            sh, sq, sp = src
            dh, dq, dp = dst
            records.append({
                "src": src,
                "dst": dst,
                "c": coord[src],
                "cn": coord[dst],
                "ordinal": ordinal,
                "outdegree": len(outs),
                "phase": sp,
                "next_phase": dp,
                "history_lsb": sh & 1,
                "next_history_lsb": dh & 1,
                "history_delta": sh ^ dh,
                "topology": sq,
                "next_topology": dq,
                "topology_delta": sq ^ dq,
            })
    return records


def ambiguity(records, fields):
    table = defaultdict(set)
    for r in records:
        key = tuple(r[f] for f in fields)
        table[key].add(r["cn"])
    ambiguous = {k: v for k, v in table.items() if len(v) > 1}
    return len(table), len(ambiguous), max((len(v) for v in table.values()), default=0)


def analyze():
    reachable, coord = operational_coordinate()
    records = edge_records(reachable, coord)
    candidates = {
        "C_only": ("c",),
        "C_phase": ("c", "phase"),
        "C_branch_ordinal": ("c", "ordinal"),
        "C_outdegree_ordinal": ("c", "outdegree", "ordinal"),
        "C_bitlike": ("c", "next_history_lsb"),
        "C_relation": ("c", "history_delta", "topology_delta"),
        "C_relation_phase": ("c", "history_delta", "topology_delta", "phase"),
        "C_local_full_no_raw_next": (
            "c", "ordinal", "history_delta", "topology_delta", "phase"
        ),
    }
    results = {}
    for name, fields in candidates.items():
        keys, amb, max_targets = ambiguity(records, fields)
        results[name] = {
            "keys": keys,
            "ambiguous_keys": amb,
            "max_next_classes": max_targets,
            "closed": amb == 0,
        }
    return {
        "reachable_states": len(reachable),
        "causal_classes": len(set(coord.values())),
        "operational_edges": len(records),
        "tests": results,
    }


def main():
    result = analyze()
    print("reachable_states", result["reachable_states"])
    print("causal_classes", result["causal_classes"])
    print("operational_edges", result["operational_edges"])
    for name, row in result["tests"].items():
        print(name, row)


if __name__ == "__main__":
    main()

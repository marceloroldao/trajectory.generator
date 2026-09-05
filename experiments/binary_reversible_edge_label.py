"""Construct a minimal bidirectionally reversible edge label on the operational graph.

Treat the operational causal graph as a bipartite incidence graph: a left copy
of each source causal class and a right copy of each destination causal class.
A valid edge label must be unique among edges leaving the same source and among
edges entering the same destination. For a bipartite graph the edge chromatic
number equals the maximum degree (Konig line-coloring theorem).

The construction below is canonicalized by sorting records and component starts,
so the public binary label is reproducible across Python processes.
"""
from __future__ import annotations

from collections import defaultdict

from local_causal_coordinate import operational_coordinate, edge_records


def canonical_records():
    reachable, coord = operational_coordinate()
    records = edge_records(reachable, coord)
    records = sorted(
        records,
        key=lambda r: (
            r["c"], r["cn"], r["next_history_lsb"], r["history_delta"],
            r["topology_delta"], r["phase"], r["ordinal"]
        ),
    )
    return reachable, coord, records


def build_incidence(records):
    by_source = defaultdict(list)
    by_dest = defaultdict(list)
    for i, r in enumerate(records):
        by_source[r["c"]].append(i)
        by_dest[r["cn"]].append(i)
    return by_source, by_dest


def binary_edge_coloring(records):
    by_source, by_dest = build_incidence(records)
    max_out = max(map(len, by_source.values()), default=0)
    max_in = max(map(len, by_dest.values()), default=0)
    delta = max(max_out, max_in)
    if delta > 2:
        return None, max_out, max_in

    adjacency = defaultdict(list)
    for i, r in enumerate(records):
        u = ("L", r["c"])
        v = ("R", r["cn"])
        adjacency[u].append((v, i))
        adjacency[v].append((u, i))
    for node in adjacency:
        adjacency[node].sort(key=lambda pair: (repr(pair[0]), pair[1]))

    color = {}
    seen_edges = set()
    for start in sorted(adjacency, key=repr):
        if all(e in seen_edges for _, e in adjacency[start]):
            continue
        component_nodes = set()
        stack = [start]
        while stack:
            x = stack.pop()
            if x in component_nodes:
                continue
            component_nodes.add(x)
            for y, _ in adjacency[x]:
                stack.append(y)
        endpoints = sorted(
            (x for x in component_nodes if len(adjacency[x]) == 1), key=repr
        )
        current = endpoints[0] if endpoints else min(component_nodes, key=repr)
        prev_edge = None
        next_color = 0
        while True:
            options = [
                (n, e) for n, e in adjacency[current]
                if e != prev_edge and e not in seen_edges
            ]
            if not options:
                break
            nxt, edge = min(options, key=lambda pair: (pair[1], repr(pair[0])))
            color[edge] = next_color
            seen_edges.add(edge)
            next_color ^= 1
            prev_edge = edge
            current = nxt

    if len(color) != len(records):
        raise RuntimeError("failed to color every operational edge")
    return color, max_out, max_in


def closure_stats(records, labels):
    f = defaultdict(set)
    r = defaultdict(set)
    bf = defaultdict(set)
    br = defaultdict(set)
    counts = defaultdict(int)
    for i, rec in enumerate(records):
        z = labels[i]
        counts[z] += 1
        f[(rec["c"], z)].add(rec["cn"])
        r[(rec["cn"], z)].add(rec["c"])
        bf[(rec["c"], z)].add(rec["next_history_lsb"])
        br[(rec["cn"], z)].add(rec["next_history_lsb"])

    def stats(table):
        amb = sum(len(v) > 1 for v in table.values())
        return {"keys": len(table), "ambiguous": amb, "closed": amb == 0}

    return {
        "label_counts": dict(sorted(counts.items())),
        "forward": stats(f),
        "reverse": stats(r),
        "bit_from_forward": stats(bf),
        "bit_from_reverse": stats(br),
    }


def labeled_records():
    reachable, coord, records = canonical_records()
    labels, max_out, max_in = binary_edge_coloring(records)
    if labels is None:
        raise RuntimeError("operational graph requires more than two labels")
    out = []
    for i, rec in enumerate(records):
        row = dict(rec)
        row["label"] = labels[i]
        out.append(row)
    return reachable, coord, tuple(out), max_out, max_in


def analyze():
    reachable, coord, records = canonical_records()
    labels, max_out, max_in = binary_edge_coloring(records)
    result = {
        "reachable_states": len(reachable),
        "operational_edges": len(records),
        "max_outdegree": max_out,
        "max_indegree": max_in,
        "minimum_possible_alphabet_lower_bound": max(max_out, max_in),
    }
    if labels is None:
        result["binary_coloring_exists"] = False
        return result
    result["binary_coloring_exists"] = True
    result.update(closure_stats(records, labels))
    result["complete_binary_reversible_label"] = all(
        result[k]["closed"]
        for k in ("forward", "reverse", "bit_from_forward", "bit_from_reverse")
    )
    return result


def main():
    for key, value in analyze().items():
        print(key, value)


if __name__ == "__main__":
    main()

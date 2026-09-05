"""Construct a minimal bidirectionally reversible edge label on the operational graph.

Treat the operational causal graph as a bipartite incidence graph: a left copy
of each source causal class and a right copy of each destination causal class.
A valid edge label must be unique among edges leaving the same source and among
edges entering the same destination.  For a bipartite graph the edge chromatic
number equals the maximum degree (Konig line-coloring theorem).  Here we test
whether the 49 operational edges admit a 2-label coloring and whether that
label also uniquely identifies the transition/data bit at either endpoint.

This is a structural existence test.  A later experiment must determine whether
the resulting label can be computed by a simple local formula rather than by a
precomputed edge table.
"""
from __future__ import annotations

from collections import defaultdict, deque

from local_causal_coordinate import operational_coordinate, edge_records


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

    # Incidence graph vertices are ('L', source_class) and ('R', dest_class).
    adjacency = defaultdict(list)
    for i, r in enumerate(records):
        u = ("L", r["c"])
        v = ("R", r["cn"])
        adjacency[u].append((v, i))
        adjacency[v].append((u, i))

    color = {}
    # Every component of a graph of maximum degree <=2 is a path or cycle;
    # alternate colors along each component's edges.
    seen_edges = set()
    for start in list(adjacency):
        if all(e in seen_edges for _, e in adjacency[start]):
            continue
        # Prefer an endpoint for paths; otherwise arbitrary node for cycles.
        component_nodes = set()
        q = [start]
        while q:
            x = q.pop()
            if x in component_nodes:
                continue
            component_nodes.add(x)
            for y, _ in adjacency[x]:
                q.append(y)
        endpoints = [x for x in component_nodes if len(adjacency[x]) == 1]
        current = endpoints[0] if endpoints else start
        prev_edge = None
        next_color = 0
        while True:
            options = [(n, e) for n, e in adjacency[current] if e != prev_edge and e not in seen_edges]
            if not options:
                break
            nxt, edge = options[0]
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


def analyze():
    reachable, coord = operational_coordinate()
    records = edge_records(reachable, coord)
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

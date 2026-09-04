"""Refine basin/potential coordinates into a minimal causal structural coordinate.

The full phase-lifted graph has 192 formal states, but only a subset is reachable
from the eight public initial causal states.  This experiment restricts to that
operational reachable graph and asks whether a state can be identified by
structural context rather than by its raw tuple label.

Refinement starts from a coarse spectral coordinate:

    (basin_signature, dominant_potential_class)

and repeatedly partitions states according to the classes of their successors.
A second variant also includes predecessor classes.  Stable partitions measure
future-language equivalence and bidirectional causal equivalence respectively.
"""
from __future__ import annotations

from collections import Counter, defaultdict, deque

from basin_potential_coordinate import (
    EDGES,
    NODES,
    basin_signatures,
    component_graph,
    dominant_potential,
)
from topological_transition_state import initial_topology


INITIAL = tuple((state, initial_topology(state), 0) for state in range(8))


def reachable_nodes():
    seen = set(INITIAL)
    q = deque(INITIAL)
    while q:
        node = q.popleft()
        for nxt in EDGES[node]:
            if nxt not in seen:
                seen.add(nxt)
                q.append(nxt)
    return frozenset(seen)


def partition_sets(labels):
    groups = defaultdict(set)
    for node, label in labels.items():
        groups[label].add(node)
    return {frozenset(group) for group in groups.values()}


def canonical_ids(raw):
    values = sorted(set(raw.values()), key=repr)
    ids = {value: i for i, value in enumerate(values)}
    return {node: ids[value] for node, value in raw.items()}


def refine(nodes, base_labels, *, include_predecessors: bool):
    nodes = tuple(sorted(nodes))
    node_set = set(nodes)
    edges = {node: tuple(n for n in EDGES[node] if n in node_set) for node in nodes}
    pred = {node: [] for node in nodes}
    for node, outs in edges.items():
        for nxt in outs:
            pred[nxt].append(node)

    labels = dict(base_labels)
    history = [len(set(labels.values()))]
    for _ in range(64):
        old = canonical_ids(labels)
        raw = {}
        for node in nodes:
            succ_signature = tuple(sorted(old[n] for n in edges[node]))
            if include_predecessors:
                pred_signature = tuple(sorted(old[n] for n in pred[node]))
                raw[node] = (old[node], succ_signature, pred_signature)
            else:
                raw[node] = (old[node], succ_signature)
        new = canonical_ids(raw)
        history.append(len(set(new.values())))
        if partition_sets(new) == partition_sets(labels):
            return new, tuple(history)
        labels = new
    raise RuntimeError("partition refinement did not stabilize")


def analyze():
    comps, cid, outgoing, attractors = component_graph()
    basin = basin_signatures(cid, outgoing, attractors)
    _, phi = dominant_potential()
    reachable = reachable_nodes()

    base = {
        node: (basin[node], round(phi[node], 12) if node in phi else None)
        for node in reachable
    }
    future, future_history = refine(reachable, base, include_predecessors=False)
    bidir, bidir_history = refine(reachable, base, include_predecessors=True)

    return {
        "formal_states": len(NODES),
        "reachable_states": len(reachable),
        "reachable_positive_potential": sum(node in phi for node in reachable),
        "base_coordinate_classes": len(set(base.values())),
        "base_largest_class": max(Counter(base.values()).values()),
        "future_equivalence_classes": len(set(future.values())),
        "future_largest_class": max(Counter(future.values()).values()),
        "future_refinement_history": future_history,
        "bidirectional_classes": len(set(bidir.values())),
        "bidirectional_largest_class": max(Counter(bidir.values()).values()),
        "bidirectional_refinement_history": bidir_history,
        "bidirectional_is_injective": len(set(bidir.values())) == len(reachable),
    }


def main():
    for key, value in analyze().items():
        print(key, value)


if __name__ == "__main__":
    main()

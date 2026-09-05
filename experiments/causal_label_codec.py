"""Exact enumerative codec on the 37-state causal-coordinate automaton.

The operational trajectory graph has 37 reachable causal classes and 49 edges.
A canonical 2-edge-coloring gives every edge a binary relational label z such
that both maps are single-valued:

    (C_t, z_t)     -> C_{t+1}
    (C_{t+1}, z_t) -> C_t

and the original transition/data bit is recoverable from either endpoint plus z.

This module ranks/unranks complete admissible paths of an exact physical length
and maps the rank through a reversible 63-bit affine permutation.  The public
decoder receives only (final_state, physical_steps) plus the public machine.

It is an enumerative codec for the constrained trajectory language, not a claim
of lossless compression of arbitrary binary strings beyond the counting bound.
"""
from __future__ import annotations

from collections import defaultdict
from functools import lru_cache

from binary_reversible_edge_label import labeled_records
from causal_coordinate_refinement import INITIAL

WIDTH = 63
MODULUS = 1 << WIDTH
MASK = MODULUS - 1
MUL = 0x5B
SEED = 0x243F6A8885A308D3 & MASK

REACHABLE, COORD, RECORDS, MAX_OUT, MAX_IN = labeled_records()

OUT = defaultdict(list)
IN = defaultdict(list)
EDGE_BY_FORWARD = {}
EDGE_BY_REVERSE = {}
for rec in RECORDS:
    OUT[rec["c"]].append(rec)
    IN[rec["cn"]].append(rec)
    EDGE_BY_FORWARD[(rec["c"], rec["label"])] = rec
    EDGE_BY_REVERSE[(rec["cn"], rec["label"])] = rec
for c in OUT:
    OUT[c].sort(key=lambda r: r["label"])
for c in IN:
    IN[c].sort(key=lambda r: r["label"])

INITIAL_ROWS = tuple(
    (node, COORD[node]) for node in INITIAL
)


@lru_cache(maxsize=None)
def suffix_count(causal_class: int, remaining_steps: int) -> int:
    if remaining_steps < 0:
        return 0
    if remaining_steps == 0:
        return 1
    return sum(
        suffix_count(rec["cn"], remaining_steps - 1)
        for rec in OUT.get(causal_class, ())
    )


def admissible_count(physical_steps: int) -> int:
    if physical_steps < 0:
        raise ValueError("physical_steps must be non-negative")
    return sum(suffix_count(c, physical_steps) for _, c in INITIAL_ROWS)


def capacity_ok(physical_steps: int) -> bool:
    return admissible_count(physical_steps) <= MODULUS


def unrank_path(rank: int, physical_steps: int):
    total = admissible_count(physical_steps)
    if not 0 <= rank < total:
        raise ValueError("rank outside admissible causal path family")

    initial_node = None
    current = None
    for node, c in INITIAL_ROWS:
        count = suffix_count(c, physical_steps)
        if rank < count:
            initial_node, current = node, c
            break
        rank -= count
    if current is None:
        raise RuntimeError("failed to resolve initial causal class")

    classes = [current]
    labels = []
    bits = [
        (initial_node[0] >> 2) & 1,
        (initial_node[0] >> 1) & 1,
        initial_node[0] & 1,
    ]
    remaining = physical_steps
    while remaining:
        chosen = None
        for rec in OUT[current]:
            count = suffix_count(rec["cn"], remaining - 1)
            if rank < count:
                chosen = rec
                break
            rank -= count
        if chosen is None:
            raise RuntimeError("no edge can complete requested length")
        labels.append(chosen["label"])
        bits.append(chosen["next_history_lsb"])
        current = chosen["cn"]
        classes.append(current)
        remaining -= 1

    return initial_node, tuple(classes), tuple(labels), tuple(bits)


def rank_path(initial_node, classes, labels, physical_steps: int) -> int:
    classes = tuple(classes)
    labels = tuple(labels)
    if len(classes) != physical_steps + 1 or len(labels) != physical_steps:
        raise ValueError("path length does not match physical_steps")
    if initial_node not in dict(INITIAL_ROWS):
        raise ValueError("invalid public initial node")
    initial_class = COORD[initial_node]
    if classes[0] != initial_class:
        raise ValueError("initial causal class mismatch")

    rank = 0
    for node, c in INITIAL_ROWS:
        if node == initial_node:
            break
        rank += suffix_count(c, physical_steps)

    current = initial_class
    remaining = physical_steps
    for step, label in enumerate(labels):
        selected = EDGE_BY_FORWARD.get((current, label))
        if selected is None:
            raise ValueError("invalid binary edge label from current class")
        expected_next = selected["cn"]
        if classes[step + 1] != expected_next:
            raise ValueError("class path disagrees with binary label")
        for rec in OUT[current]:
            if rec["label"] == label:
                break
            rank += suffix_count(rec["cn"], remaining - 1)
        current = expected_next
        remaining -= 1
    return rank


def inverse_walk(final_class: int, labels):
    current = final_class
    reversed_classes = [current]
    reversed_bits = []
    for label in reversed(tuple(labels)):
        rec = EDGE_BY_REVERSE.get((current, label))
        if rec is None:
            raise ValueError("invalid reverse binary edge label")
        reversed_bits.append(rec["next_history_lsb"])
        current = rec["c"]
        reversed_classes.append(current)
    return tuple(reversed(reversed_classes)), tuple(reversed(reversed_bits))


def _time_word(steps: int) -> int:
    z = (steps + SEED) & MASK
    z ^= (z << 13) & MASK
    z ^= z >> 7
    z ^= (z << 17) & MASK
    return z & MASK


def _forward(rank: int, steps: int) -> int:
    return (rank * MUL + _time_word(steps)) & MASK


def _inverse(final_state: int, steps: int) -> int:
    inv = pow(MUL, -1, MODULUS)
    return ((final_state - _time_word(steps)) * inv) & MASK


def encode_path(initial_node, classes, labels, physical_steps: int):
    if not capacity_ok(physical_steps):
        raise ValueError("causal path family exceeds 63-bit capacity")
    rank = rank_path(initial_node, classes, labels, physical_steps)
    return _forward(rank, physical_steps), physical_steps


def decode_path(final_state: int, physical_steps: int):
    if not capacity_ok(physical_steps):
        raise ValueError("causal path family exceeds 63-bit capacity")
    rank = _inverse(final_state & MASK, physical_steps)
    total = admissible_count(physical_steps)
    if rank >= total:
        raise ValueError("invalid address for this physical length")
    initial, classes, labels, bits = unrank_path(rank, physical_steps)
    inv_classes, inv_edge_bits = inverse_walk(classes[-1], labels)
    assert inv_classes == classes
    assert tuple(bits[3:]) == inv_edge_bits
    return initial, classes, labels, bits


def self_test(max_steps: int = 32, per_length: int = 256):
    for n in range(max_steps + 1):
        total = admissible_count(n)
        for rank in range(min(total, per_length)):
            initial, classes, labels, bits = unrank_path(rank, n)
            assert rank_path(initial, classes, labels, n) == rank
            final = _forward(rank, n)
            recovered = decode_path(final, n)
            assert recovered == (initial, classes, labels, bits)
            assert len(bits) == n + 3
    return True


def main():
    print("reachable_classes", len(REACHABLE))
    print("operational_edges", len(RECORDS))
    print("max_outdegree", MAX_OUT)
    print("max_indegree", MAX_IN)
    print("self_test", self_test())
    for n in (216, 217, 218, 219, 220):
        count = admissible_count(n)
        print(n, count, count <= MODULUS)


if __name__ == "__main__":
    main()

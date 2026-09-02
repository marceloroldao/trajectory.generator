"""Operational branch-event codec for the dominant recurrent orbit core.

Scope: branch-aligned segments of the recurrent core for the topological
candidate params=(0,2,4,4).  The decoder receives only

    (final_state, physical_steps)

plus this public machine definition.  The internal macro-event sequence is
recovered by exact rank/unrank over variable-length branch-to-branch flights.

This is an enumerative codec for the constrained recurrent path language, not
compression of arbitrary binary data.
"""

from __future__ import annotations

from functools import lru_cache

from information_clock_macrograph import dominant_component, macro_edges

WIDTH = 63
MODULUS = 1 << WIDTH
MASK = MODULUS - 1
UNIVERSE_MUL = 0x5B
UNIVERSE_SEED = 0xBB67AE85


EDGES, COMPONENT = dominant_component()
BRANCHES, MACROS_RAW = macro_edges(EDGES, COMPONENT)
BRANCHES = tuple(sorted(BRANCHES))
BRANCH_INDEX = {node: i for i, node in enumerate(BRANCHES)}
MACROS = tuple(
    sorted(
        MACROS_RAW,
        key=lambda e: (BRANCH_INDEX[e[0]], BRANCH_INDEX[e[1]], e[2], e[3]),
    )
)
MACROS_BY_SOURCE = {
    i: tuple(e for e in MACROS if BRANCH_INDEX[e[0]] == i)
    for i in range(len(BRANCHES))
}


@lru_cache(maxsize=None)
def suffix_count(branch_index: int, remaining_steps: int) -> int:
    if remaining_steps == 0:
        return 1
    if remaining_steps < 0:
        return 0
    total = 0
    for edge in MACROS_BY_SOURCE[branch_index]:
        _, target, length, _ = edge
        total += suffix_count(BRANCH_INDEX[target], remaining_steps - length)
    return total


def admissible_count(physical_steps: int) -> int:
    if physical_steps < 0:
        raise ValueError("physical_steps must be non-negative")
    return sum(suffix_count(i, physical_steps) for i in range(len(BRANCHES)))


def capacity_ok(physical_steps: int) -> bool:
    return admissible_count(physical_steps) <= MODULUS


def unrank_macro_path(rank: int, physical_steps: int):
    total = admissible_count(physical_steps)
    if not 0 <= rank < total:
        raise ValueError("rank outside recurrent macro-path family")

    start_index = None
    for i in range(len(BRANCHES)):
        count = suffix_count(i, physical_steps)
        if rank < count:
            start_index = i
            break
        rank -= count
    assert start_index is not None

    current = start_index
    remaining = physical_steps
    chosen = []
    while remaining:
        for edge in MACROS_BY_SOURCE[current]:
            _, target, length, _ = edge
            count = suffix_count(BRANCH_INDEX[target], remaining - length)
            if rank < count:
                chosen.append(edge)
                current = BRANCH_INDEX[target]
                remaining -= length
                break
            rank -= count
        else:
            raise RuntimeError("no macro edge can complete requested physical length")
    return BRANCHES[start_index], tuple(chosen)


def rank_macro_path(start_branch, macro_path, physical_steps: int) -> int:
    if start_branch not in BRANCH_INDEX:
        raise ValueError("start branch is not part of the recurrent macrograph")
    start_index = BRANCH_INDEX[start_branch]
    rank = sum(suffix_count(i, physical_steps) for i in range(start_index))
    current = start_index
    remaining = physical_steps

    for selected in macro_path:
        found = False
        for edge in MACROS_BY_SOURCE[current]:
            _, target, length, _ = edge
            if edge == selected:
                if suffix_count(BRANCH_INDEX[target], remaining - length) == 0:
                    raise ValueError("selected edge cannot complete requested length")
                current = BRANCH_INDEX[target]
                remaining -= length
                found = True
                break
            rank += suffix_count(BRANCH_INDEX[target], remaining - length)
        if not found:
            raise ValueError("macro path is invalid from current branch")

    if remaining != 0:
        raise ValueError("macro path does not match physical_steps")
    return rank


def expand_causal_path(start_branch, macro_path):
    nodes = [start_branch]
    current = start_branch
    for edge in macro_path:
        source, target, _, path = edge
        if source != current or path[0] != source or path[-1] != target:
            raise ValueError("inconsistent macro edge")
        nodes.extend(path[1:])
        current = target
    return tuple(nodes)


def causal_path_to_bits(nodes):
    if not nodes:
        return []
    state0 = nodes[0][0]
    bits = [(state0 >> 2) & 1, (state0 >> 1) & 1, state0 & 1]
    for node in nodes[1:]:
        bits.append(node[0] & 1)
    return bits


def _time_word(steps: int) -> int:
    z = (steps + UNIVERSE_SEED) & MASK
    z ^= (z << 13) & MASK
    z ^= z >> 7
    z ^= (z << 17) & MASK
    return z & MASK


def _forward(rank: int, steps: int) -> int:
    return (rank * UNIVERSE_MUL + _time_word(steps)) & MASK


def _inverse(final_state: int, steps: int) -> int:
    inv = pow(UNIVERSE_MUL, -1, MODULUS)
    return ((final_state - _time_word(steps)) * inv) & MASK


def encode_macro_path(start_branch, macro_path, physical_steps: int):
    if not capacity_ok(physical_steps):
        raise ValueError("recurrent macro-path family exceeds 63-bit capacity")
    rank = rank_macro_path(start_branch, tuple(macro_path), physical_steps)
    return _forward(rank, physical_steps), physical_steps


def decode_macro_path(final_state: int, physical_steps: int):
    if not capacity_ok(physical_steps):
        raise ValueError("recurrent macro-path family exceeds 63-bit capacity")
    rank = _inverse(final_state & MASK, physical_steps)
    total = admissible_count(physical_steps)
    if rank >= total:
        raise ValueError("invalid address for this physical length")
    start, macro_path = unrank_macro_path(rank, physical_steps)
    causal = expand_causal_path(start, macro_path)
    return start, macro_path, causal, causal_path_to_bits(causal)


def self_test(max_steps: int = 40, per_length: int = 128):
    for n in range(max_steps + 1):
        total = admissible_count(n)
        for rank in range(min(total, per_length)):
            start, path = unrank_macro_path(rank, n)
            assert rank_macro_path(start, path, n) == rank
            final_state = _forward(rank, n)
            dstart, dpath, causal, bits = decode_macro_path(final_state, n)
            assert dstart == start
            assert dpath == path
            assert len(causal) == n + 1
            assert len(bits) == n + 3
    return True


def main():
    print("branches", BRANCHES)
    print("macro_lengths", [edge[2] for edge in MACROS])
    print("self_test", self_test())
    for n in (221, 230, 231, 232, 233, 234, 235, 236):
        count = admissible_count(n)
        print(n, count, count <= MODULUS)


if __name__ == "__main__":
    main()

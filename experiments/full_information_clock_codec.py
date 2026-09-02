"""Full information-clock codec for the topological trajectory universe.

Unlike ``information_clock_codec.py``, which only covers branch-aligned paths
inside the dominant recurrent core, this experiment covers the *complete*
finite causal graph for the selected topological universe params=(0,2,4,4).

The trajectory is represented internally as:

    transient entry -> branch events -> deterministic flights -> partial tail

The decoder still receives only:

    (final_state, physical_steps)

plus the public machine definition.  Entry offsets, branch-event history and a
possible final partial flight are reconstructed from the rank.

This is an exact enumerative codec for a constrained trajectory language, not
compression of arbitrary binary strings.
"""

from __future__ import annotations

from functools import lru_cache

from recurrent_orbit_core import graph
from topological_transition_state import initial_topology

PARAMS = (0, 2, 4, 4)
WIDTH = 63
MODULUS = 1 << WIDTH
MASK = MODULUS - 1
UNIVERSE_MUL = 0x5B
UNIVERSE_SEED = 0x3C6EF372

EDGES = graph(PARAMS)
BRANCH_NODES = frozenset(node for node, nxt in EDGES.items() if len(nxt) > 1)
INITIAL_NODES = tuple((state, initial_topology(state), 0) for state in range(8))


def _follow_choice(source, first, max_steps: int | None = None):
    """Follow one chosen edge until the next branch or a deterministic cycle.

    Returns (path, target_branch_or_none, deterministic_cycle_start_index).
    ``path`` includes source and every visited node.
    """
    path = [source, first]
    seen = {source: 0, first: 1}
    current = first
    while current not in BRANCH_NODES:
        if max_steps is not None and len(path) - 1 >= max_steps:
            return tuple(path), None, None
        nxts = EDGES[current]
        if len(nxts) != 1:
            # Out-degree zero is not expected in this graph, but treating it as
            # a deterministic terminal keeps the helper total.
            return tuple(path), None, None
        nxt = nxts[0]
        if nxt in seen:
            path.append(nxt)
            return tuple(path), None, seen[nxt]
        path.append(nxt)
        seen[nxt] = len(path) - 1
        current = nxt
    return tuple(path), current, None


@lru_cache(maxsize=None)
def macro_choices(node):
    """Public branch choices expanded through deterministic flights."""
    if node not in BRANCH_NODES:
        raise ValueError("macro_choices requires a branch node")
    out = []
    for first in EDGES[node]:
        path, target, cycle_at = _follow_choice(node, first)
        out.append((target, len(path) - 1, path, cycle_at))
    return tuple(out)


def _deterministic_prefix(node, steps: int):
    """Follow exactly ``steps`` deterministic transitions from a non-branch.

    Returns the causal path including the start node.  Raises if a branch is
    reached before the requested number of transitions.
    """
    path = [node]
    current = node
    for _ in range(steps):
        if current in BRANCH_NODES:
            raise ValueError("branch reached before deterministic prefix ended")
        nxts = EDGES[current]
        if len(nxts) != 1:
            raise ValueError("unexpected non-deterministic/non-total node")
        current = nxts[0]
        path.append(current)
    return tuple(path)


def _distance_to_branch_or_cycle(node):
    """Return deterministic prefix to first branch, or detect branchless cycle."""
    if node in BRANCH_NODES:
        return tuple([node]), node, None
    path = [node]
    seen = {node: 0}
    current = node
    while current not in BRANCH_NODES:
        nxts = EDGES[current]
        if len(nxts) != 1:
            return tuple(path), None, None
        nxt = nxts[0]
        path.append(nxt)
        if nxt in seen:
            return tuple(path), None, seen[nxt]
        seen[nxt] = len(path) - 1
        current = nxt
    return tuple(path), current, None


@lru_cache(maxsize=None)
def suffix_count(node, remaining_steps: int) -> int:
    """Exact number of complete physical paths of a fixed remaining length.

    Deterministic time is skipped in chunks.  Only branch events create a sum.
    A path may end in the middle of a deterministic flight; that contributes
    exactly one completion for the selected branch choice.
    """
    if remaining_steps < 0:
        return 0
    if remaining_steps == 0:
        return 1

    if node not in BRANCH_NODES:
        prefix, target, cycle_at = _distance_to_branch_or_cycle(node)
        distance = len(prefix) - 1
        if target is not None:
            if remaining_steps <= distance:
                return 1
            return suffix_count(target, remaining_steps - distance)
        # No branch is ever reached: the continuation is unique forever if it
        # enters a deterministic cycle, or unique until a terminal node.
        if cycle_at is not None:
            return 1
        return 1 if remaining_steps <= distance else 0

    total = 0
    for target, length, path, cycle_at in macro_choices(node):
        if remaining_steps < length:
            # This chosen branch edge has one unique partial deterministic tail.
            total += 1
        elif remaining_steps == length:
            total += 1
        elif target is not None:
            total += suffix_count(target, remaining_steps - length)
        elif cycle_at is not None:
            total += 1
        # A non-cyclic deterministic terminal contributes nothing beyond length.
    return total


def admissible_count(physical_steps: int) -> int:
    if physical_steps < 0:
        raise ValueError("physical_steps must be non-negative")
    return sum(suffix_count(node, physical_steps) for node in INITIAL_NODES)


def capacity_ok(physical_steps: int) -> bool:
    return admissible_count(physical_steps) <= MODULUS


def _take_partial(path, transitions: int):
    if transitions < 0 or transitions >= len(path):
        raise ValueError("invalid partial-flight length")
    return tuple(path[: transitions + 1])


def _unrank_from(node, rank: int, remaining_steps: int):
    """Return full causal node path from one known start node."""
    causal = [node]
    current = node
    remaining = remaining_steps

    while remaining:
        if current not in BRANCH_NODES:
            prefix, target, cycle_at = _distance_to_branch_or_cycle(current)
            distance = len(prefix) - 1
            if remaining <= distance:
                causal.extend(prefix[1 : remaining + 1])
                remaining = 0
                break
            causal.extend(prefix[1:])
            remaining -= distance
            if target is not None:
                current = target
                continue
            if cycle_at is None:
                raise ValueError("requested path extends beyond deterministic terminal")
            # Continue uniquely around deterministic cycle.
            cycle_nodes = prefix[cycle_at:-1]
            if not cycle_nodes:
                raise RuntimeError("empty deterministic cycle")
            idx = 0
            while remaining:
                nxt = EDGES[causal[-1]][0]
                causal.append(nxt)
                remaining -= 1
                idx += 1
            break

        selected = None
        for choice in macro_choices(current):
            target, length, path, cycle_at = choice
            if remaining <= length:
                count = 1
            elif target is not None:
                count = suffix_count(target, remaining - length)
            elif cycle_at is not None:
                count = 1
            else:
                count = 0
            if rank < count:
                selected = choice
                break
            rank -= count

        if selected is None:
            raise ValueError("rank outside suffix family")

        target, length, path, cycle_at = selected
        if remaining <= length:
            causal.extend(path[1 : remaining + 1])
            remaining = 0
            break

        causal.extend(path[1:])
        remaining -= length
        if target is not None:
            current = target
            continue
        if cycle_at is None:
            raise ValueError("selected deterministic terminal cannot complete path")
        while remaining:
            nxt = EDGES[causal[-1]][0]
            causal.append(nxt)
            remaining -= 1
        break

    return tuple(causal)


def unrank_causal_path(rank: int, physical_steps: int):
    total = admissible_count(physical_steps)
    if not 0 <= rank < total:
        raise ValueError("rank outside full information-clock family")
    for start in INITIAL_NODES:
        count = suffix_count(start, physical_steps)
        if rank < count:
            return _unrank_from(start, rank, physical_steps)
        rank -= count
    raise RuntimeError("failed to resolve initial causal state")


def rank_causal_path(causal_path) -> int:
    path = tuple(causal_path)
    if not path:
        raise ValueError("causal path cannot be empty")
    if path[0] not in INITIAL_NODES:
        raise ValueError("path does not begin at a public initial state")
    physical_steps = len(path) - 1

    # Validate edge-by-edge first.
    for a, b in zip(path, path[1:]):
        if b not in EDGES[a]:
            raise ValueError("invalid causal transition")

    start_index = INITIAL_NODES.index(path[0])
    rank = sum(suffix_count(node, physical_steps) for node in INITIAL_NODES[:start_index])
    current = path[0]
    pos = 0
    remaining = physical_steps

    while remaining:
        if current not in BRANCH_NODES:
            nxt = path[pos + 1]
            if EDGES[current] != [nxt] and tuple(EDGES[current]) != (nxt,):
                raise ValueError("path deviates from deterministic transition")
            current = nxt
            pos += 1
            remaining -= 1
            continue

        actual_next = path[pos + 1]
        found = False
        for choice in macro_choices(current):
            target, length, macro_path, cycle_at = choice
            if macro_path[1] == actual_next:
                found = True
                # Validate as much of this macro as lies inside the requested path.
                take = min(remaining, length)
                expected = macro_path[: take + 1]
                actual = path[pos : pos + take + 1]
                if actual != expected:
                    raise ValueError("path does not follow selected deterministic flight")
                current = actual[-1]
                pos += take
                remaining -= take
                break

            if remaining <= length:
                rank += 1
            elif target is not None:
                rank += suffix_count(target, remaining - length)
            elif cycle_at is not None:
                rank += 1
        if not found:
            raise ValueError("branch choice not represented by macrograph")

    return rank


def causal_path_to_bits(nodes):
    if not nodes:
        return []
    state0 = nodes[0][0]
    bits = [(state0 >> 2) & 1, (state0 >> 1) & 1, state0 & 1]
    bits.extend(node[0] & 1 for node in nodes[1:])
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


def encode_causal_path(causal_path):
    physical_steps = len(tuple(causal_path)) - 1
    if not capacity_ok(physical_steps):
        raise ValueError("full information-clock family exceeds 63-bit capacity")
    rank = rank_causal_path(causal_path)
    return _forward(rank, physical_steps), physical_steps


def decode_causal_path(final_state: int, physical_steps: int):
    if not capacity_ok(physical_steps):
        raise ValueError("full information-clock family exceeds 63-bit capacity")
    rank = _inverse(final_state & MASK, physical_steps)
    total = admissible_count(physical_steps)
    if rank >= total:
        raise ValueError("invalid address for this physical length")
    causal = unrank_causal_path(rank, physical_steps)
    return causal, causal_path_to_bits(causal)


def stepwise_reference_count(physical_steps: int) -> int:
    """Independent one-transition-at-a-time reference count."""
    dist = {node: 1 for node in INITIAL_NODES}
    for _ in range(physical_steps):
        nxt = {}
        for node, count in dist.items():
            for target in EDGES[node]:
                nxt[target] = nxt.get(target, 0) + count
        dist = nxt
    return sum(dist.values())


def self_test(max_steps: int = 40, per_length: int = 256):
    for n in range(max_steps + 1):
        macro_total = admissible_count(n)
        step_total = stepwise_reference_count(n)
        assert macro_total == step_total, (n, macro_total, step_total)
        for rank in range(min(macro_total, per_length)):
            causal = unrank_causal_path(rank, n)
            assert len(causal) == n + 1
            assert rank_causal_path(causal) == rank
            final = _forward(rank, n)
            decoded, bits = decode_causal_path(final, n)
            assert decoded == causal
            assert len(bits) == n + 3
    return True


def main():
    print("initial_nodes", len(INITIAL_NODES))
    print("branch_nodes", len(BRANCH_NODES))
    print("self_test", self_test())
    limit = 1 << WIDTH
    last_ok = None
    first_permanent_cross = None
    run = 0
    for n in range(0, 301):
        count = admissible_count(n)
        if count <= limit:
            last_ok = n
            run = 0
        else:
            run += 1
            if run >= 20 and first_permanent_cross is None:
                first_permanent_cross = n - 19
    print("last_ok_through_300", last_ok)
    print("first_20_consecutive_crossings", first_permanent_cross)
    for n in range(215, 226):
        print(n, admissible_count(n), admissible_count(n) <= limit)


if __name__ == "__main__":
    main()

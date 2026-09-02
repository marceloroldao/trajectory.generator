"""Search discrete structural orbit classes for the memory-3 universe.

Unlike scalar coherence accumulators, the causal variable Q_t represents a
small structural class derived from relations between recent transitions. Q_t
is deterministically regenerated from the recovered prefix and is not side
metadata.

Scanned four 4-class definitions:

- relpair: last two transition-relation bits;
- curvature: current relation plus whether relation changed;
- state_relation: parity class of current 3-bit state plus current relation;
- direction: current data bit plus current relation.

For each definition the experiment scans all non-trivial 4-bucket maps over the
five public policy profiles used by the memory-3 policy experiments. Exact
family counts are propagated over (history3, orbit_class); selected candidates
can then be checked with exact rank/unrank for perturbation survival.
"""

from __future__ import annotations

import itertools
import math
import random
from functools import lru_cache

from trajectory_generator.policy_universe import (
    ALL_RULES,
    BALANCED_POLICY_WEIGHTS,
    RIGID_LONG_POLICY_WEIGHTS,
    _allowed,
    _feature_vector,
    _next_state,
)

POLICIES = (
    BALANCED_POLICY_WEIGHTS,
    RIGID_LONG_POLICY_WEIGHTS,
    (2, 3, 1, 3, 1, 2, 0, 3, 0),
    (0, 2, 3, 1, 2, 2, 1, 5, 0),
    (0, 0, 3, 4, 0, 2, 2, 3, 0),
)


def selected_actions() -> dict[tuple[int, int, int], int]:
    out = {}
    for state in range(8):
        for phase in range(3):
            for pidx, weights in enumerate(POLICIES):
                best_index = 0
                best_score = None
                for index, rule in enumerate(ALL_RULES):
                    score = sum(
                        a * b
                        for a, b in zip(
                            _feature_vector(rule, index, state, phase), weights
                        )
                    )
                    if best_score is None or score > best_score:
                        best_score = score
                        best_index = index
                out[(state, phase, pidx)] = ALL_RULES[best_index][state]
    return out


ACTIONS = selected_actions()


def initial_q(state: int, mode: str) -> int:
    newest = state & 1
    middle = (state >> 1) & 1
    oldest = (state >> 2) & 1
    previous_relation = middle ^ oldest
    current_relation = newest ^ middle
    if mode == "relpair":
        return (previous_relation << 1) | current_relation
    if mode == "curvature":
        return ((previous_relation ^ current_relation) << 1) | current_relation
    if mode == "state_relation":
        return ((state.bit_count() & 1) << 1) | current_relation
    if mode == "direction":
        return (newest << 1) | current_relation
    raise ValueError("unknown orbit-class mode")


def update_q(q: int, state: int, bit: int, mode: str) -> int:
    newest = state & 1
    middle = (state >> 1) & 1
    relation = bit ^ newest
    previous_relation = newest ^ middle
    if mode == "relpair":
        return ((q & 1) << 1) | relation
    if mode == "curvature":
        return ((previous_relation ^ relation) << 1) | relation
    if mode == "state_relation":
        nxt = _next_state(state, bit)
        return ((nxt.bit_count() & 1) << 1) | relation
    if mode == "direction":
        return (bit << 1) | relation
    raise ValueError("unknown orbit-class mode")


def counts(mode: str, policy_map: tuple[int, int, int, int], max_steps: int = 320) -> list[int]:
    dist = {(state, initial_q(state, mode)): 1 for state in range(8)}
    out = [1, 2, 4, 8]
    for t in range(3, max_steps):
        nxt = {}
        for (state, q), count in dist.items():
            action = ACTIONS[(state, t % 3, policy_map[q])]
            for bit in _allowed(action):
                ns = _next_state(state, bit)
                nq = update_q(q, state, bit, mode)
                nxt[(ns, nq)] = nxt.get((ns, nq), 0) + count
        dist = nxt
        out.append(sum(dist.values()))
    return out


def make_codec(mode: str, policy_map: tuple[int, int, int, int]):
    @lru_cache(maxsize=None)
    def suffix(state: int, q: int, t: int, remaining: int) -> int:
        if remaining == 0:
            return 1
        action = ACTIONS[(state, t % 3, policy_map[q])]
        total = 0
        for bit in _allowed(action):
            ns = _next_state(state, bit)
            nq = update_q(q, state, bit, mode)
            total += suffix(ns, nq, t + 1, remaining - 1)
        return total

    def total(steps: int) -> int:
        if steps <= 3:
            return 1 << steps
        return sum(
            suffix(state, initial_q(state, mode), 3, steps - 3)
            for state in range(8)
        )

    def unrank(rank: int, steps: int) -> list[int]:
        if steps <= 3:
            return [((rank >> (steps - 1 - i)) & 1) for i in range(steps)] if steps else []
        remaining = steps - 3
        prefix = None
        for state in range(8):
            n = suffix(state, initial_q(state, mode), 3, remaining)
            if rank < n:
                prefix = state
                break
            rank -= n
        assert prefix is not None
        bits = [(prefix >> 2) & 1, (prefix >> 1) & 1, prefix & 1]
        state = prefix
        q = initial_q(state, mode)
        for t in range(3, steps):
            rem_after = steps - t - 1
            for bit in _allowed(ACTIONS[(state, t % 3, policy_map[q])]):
                ns = _next_state(state, bit)
                nq = update_q(q, state, bit, mode)
                n = suffix(ns, nq, t + 1, rem_after)
                if rank < n:
                    bits.append(bit)
                    state, q = ns, nq
                    break
                rank -= n
        return bits

    def validate(bits: list[int]) -> bool:
        if len(bits) <= 3:
            return True
        state = (bits[0] << 2) | (bits[1] << 1) | bits[2]
        q = initial_q(state, mode)
        for t, bit in enumerate(bits[3:], start=3):
            if bit not in _allowed(ACTIONS[(state, t % 3, policy_map[q])]):
                return False
            q = update_q(q, state, bit, mode)
            state = _next_state(state, bit)
        return True

    return total, unrank, validate


def flip_survival(mode: str, policy_map: tuple[int, int, int, int], samples: int = 256, steps: int = 64, seed: int = 123) -> float:
    total, unrank, validate = make_codec(mode, policy_map)
    family = total(steps)
    rng = random.Random(seed)
    survived = tested = 0
    for _ in range(min(samples, family)):
        bits = unrank(rng.randrange(family), steps)
        for pos in range(steps):
            trial = bits.copy()
            trial[pos] ^= 1
            tested += 1
            survived += int(validate(trial))
    return survived / tested if tested else 0.0


def main() -> None:
    limit = 1 << 63
    rows = []
    for mode in ("relpair", "curvature", "state_relation", "direction"):
        for pmap in itertools.product(range(5), repeat=4):
            if len(set(pmap)) < 2:
                continue
            seq = counts(mode, pmap)
            frontier = len(seq) - 1
            for n, value in enumerate(seq):
                if value > limit:
                    frontier = n - 1
                    break
            rate300 = math.log2(seq[300]) / 300
            if 0.25 <= rate300 <= 0.45 and frontier > 187:
                rows.append((frontier, rate300, mode, pmap, seq[64]))

    rows.sort(reverse=True)
    print("frontier rate300 flip64 count64 mode policy_map")
    for frontier, rate, mode, pmap, c64 in rows[:40]:
        flip = flip_survival(mode, pmap, samples=256)
        print(frontier, f"{rate:.7f}", f"{flip:.5f}", c64, mode, pmap)


if __name__ == "__main__":
    main()

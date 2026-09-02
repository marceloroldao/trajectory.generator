"""Topological transition-state search for trajectory.generator.

The causal variable is an 8-state relation-history topology rather than a
scalar coherence score or a single 4-state class. It keeps the last three
relation/motion bits in Q_t. The initial oldest relation seed is derived from
the recovered prefix, so Q_t is regenerated during decoding and is not side
metadata.

Policy selection is deliberately low-dimensional rather than an arbitrary
5^8 lookup table:

    policy = (a*popcount(Q) + b*Q + c*phase + d) mod 5

with a,b,c,d in 0..4. All 5^4 = 625 selector formulas are scanned. This keeps
the selector public, compact, and reproducible while allowing the topology to
influence the active law.
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


def initial_topology(state: int) -> int:
    oldest = (state >> 2) & 1
    middle = (state >> 1) & 1
    newest = state & 1
    r1 = oldest ^ middle
    r2 = middle ^ newest
    return (oldest << 2) | (r1 << 1) | r2


def update_topology(q: int, state: int, bit: int) -> int:
    relation = bit ^ (state & 1)
    return ((q << 1) & 0b111) | relation


def policy_index(q: int, t: int, params: tuple[int, int, int, int]) -> int:
    a, b, c, d = params
    return (a * q.bit_count() + b * q + c * (t % 3) + d) % len(POLICIES)


def counts(params: tuple[int, int, int, int], max_steps: int = 320) -> list[int]:
    dist = {(state, initial_topology(state)): 1 for state in range(8)}
    out = [1, 2, 4, 8]
    for t in range(3, max_steps):
        nxt = {}
        for (state, q), count in dist.items():
            pidx = policy_index(q, t, params)
            action = ACTIONS[(state, t % 3, pidx)]
            for bit in _allowed(action):
                ns = _next_state(state, bit)
                nq = update_topology(q, state, bit)
                nxt[(ns, nq)] = nxt.get((ns, nq), 0) + count
        dist = nxt
        out.append(sum(dist.values()))
    return out


def make_codec(params: tuple[int, int, int, int]):
    @lru_cache(maxsize=None)
    def suffix(state: int, q: int, t: int, remaining: int) -> int:
        if remaining == 0:
            return 1
        pidx = policy_index(q, t, params)
        total = 0
        for bit in _allowed(ACTIONS[(state, t % 3, pidx)]):
            ns = _next_state(state, bit)
            nq = update_topology(q, state, bit)
            total += suffix(ns, nq, t + 1, remaining - 1)
        return total

    def total(steps: int) -> int:
        if steps <= 3:
            return 1 << steps
        return sum(
            suffix(state, initial_topology(state), 3, steps - 3)
            for state in range(8)
        )

    def unrank(rank: int, steps: int) -> list[int]:
        if steps <= 3:
            return [((rank >> (steps - 1 - i)) & 1) for i in range(steps)] if steps else []
        remaining = steps - 3
        prefix = None
        for state in range(8):
            n = suffix(state, initial_topology(state), 3, remaining)
            if rank < n:
                prefix = state
                break
            rank -= n
        assert prefix is not None
        bits = [(prefix >> 2) & 1, (prefix >> 1) & 1, prefix & 1]
        state = prefix
        q = initial_topology(state)
        for t in range(3, steps):
            rem_after = steps - t - 1
            pidx = policy_index(q, t, params)
            for bit in _allowed(ACTIONS[(state, t % 3, pidx)]):
                ns = _next_state(state, bit)
                nq = update_topology(q, state, bit)
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
        q = initial_topology(state)
        for t, bit in enumerate(bits[3:], start=3):
            pidx = policy_index(q, t, params)
            if bit not in _allowed(ACTIONS[(state, t % 3, pidx)]):
                return False
            q = update_topology(q, state, bit)
            state = _next_state(state, bit)
        return True

    return total, unrank, validate


def flip_survival(params: tuple[int, int, int, int], samples: int = 256, steps: int = 64, seed: int = 123) -> float:
    total, unrank, validate = make_codec(params)
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
    for params in itertools.product(range(5), repeat=4):
        seq = counts(params)
        frontier = len(seq) - 1
        for n, value in enumerate(seq):
            if value > limit:
                frontier = n - 1
                break
        rate300 = math.log2(seq[300]) / 300
        if 0.25 <= rate300 <= 0.45 and frontier > 187:
            rows.append((frontier, rate300, params, seq[64]))

    rows.sort(reverse=True)
    print("frontier rate300 flip64 count64 params")
    for frontier, rate, params, c64 in rows[:40]:
        flip = flip_survival(params, samples=256)
        print(frontier, f"{rate:.7f}", f"{flip:.5f}", c64, params)


if __name__ == "__main__":
    main()

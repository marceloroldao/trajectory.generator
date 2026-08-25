"""Search causal coherence variables built from transition relations.

Instead of exposing more raw past bits, this experiment carries a four-bucket
causal variable derived from relations between consecutive transitions. The
variable is regenerated from the recovered prefix and is not side metadata.

Three update modes are scanned over all nontrivial four-bucket policy maps:

- repeat: reward persistence of the current transition relation;
- phase: accumulate a public relation/phase consistency test;
- rolling_rel: finite rolling accumulator over current/previous relations.

The experiment reports exact 63-bit frontier, finite-length entropy rate and
admissible count at 64 steps. Perturbation survival for selected candidates is
measured separately with exact rank/unrank using the same finite-state grammar.
"""

from __future__ import annotations

import itertools
import math

from trajectory_generator.policy_universe import (
    ALL_RULES,
    _allowed,
    _feature_vector,
    _next_state,
)

POLICIES = (
    (0, 1, 3, 3, 0, 1, 0, 3, 0),
    (3, 3, 0, 3, 1, 2, 2, 0, 1),
    (2, 3, 1, 3, 1, 2, 0, 3, 0),
    (0, 2, 3, 1, 2, 2, 1, 5, 0),
    (0, 0, 3, 4, 0, 2, 2, 3, 0),
)


def selected_actions() -> dict[tuple[int, int, int], int]:
    out: dict[tuple[int, int, int], int] = {}
    for state in range(8):
        for phase in range(3):
            for pidx, weights in enumerate(POLICIES):
                best_index = 0
                best_score = None
                for index, rule in enumerate(ALL_RULES):
                    features = _feature_vector(rule, index, state, phase)
                    score = sum(a * b for a, b in zip(features, weights))
                    if best_score is None or score > best_score:
                        best_score = score
                        best_index = index
                out[(state, phase, pidx)] = ALL_RULES[best_index][state]
    return out


ACTIONS = selected_actions()


def initial_coherence(state: int) -> int:
    last = state & 1
    prev = (state >> 1) & 1
    return (last ^ prev) * 2 + ((state >> 2) & 1)


def update_coherence(c: int, state: int, bit: int, mode: str) -> int:
    last = state & 1
    prev = (state >> 1) & 1
    relation = bit ^ last
    previous_relation = last ^ prev
    if mode == "repeat":
        return min(3, c + 1) if relation == previous_relation else max(0, c - 1)
    if mode == "phase":
        return (c + (1 if relation == (state.bit_count() & 1) else -1)) % 4
    if mode == "rolling_rel":
        return ((c << 1) ^ relation ^ previous_relation) % 4
    raise ValueError("unknown mode")


def counts(mode: str, policy_map: tuple[int, int, int, int], max_steps: int = 400) -> list[int]:
    dist = {(state, initial_coherence(state)): 1 for state in range(8)}
    out = [1, 2, 4, 8]
    for t in range(3, max_steps):
        nxt = {}
        for (state, coherence), count in dist.items():
            action = ACTIONS[(state, t % 3, policy_map[coherence])]
            for bit in _allowed(action):
                ns = _next_state(state, bit)
                nc = update_coherence(coherence, state, bit, mode)
                nxt[(ns, nc)] = nxt.get((ns, nc), 0) + count
        dist = nxt
        out.append(sum(dist.values()))
    return out


def main() -> None:
    rows = []
    limit = 1 << 63
    for mode in ("repeat", "phase", "rolling_rel"):
        for pmap in itertools.product(range(5), repeat=4):
            if len(set(pmap)) < 2:
                continue
            seq = counts(mode, pmap)
            frontier = 400
            for n, value in enumerate(seq):
                if value > limit:
                    frontier = n - 1
                    break
            rate300 = math.log2(seq[300]) / 300
            if 0.25 <= rate300 <= 0.45:
                rows.append((frontier, rate300, seq[64], mode, pmap))

    rows.sort(reverse=True)
    print("frontier rate300 count64 mode policy_map")
    for row in rows[:40]:
        print(row)


if __name__ == "__main__":
    main()

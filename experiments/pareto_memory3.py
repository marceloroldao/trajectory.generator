"""Pareto analysis for all 3^8 memory-3 local admissibility laws.

Objectives are intentionally conflicting:
- maximize entropy rate h = log2(lambda),
- maximize exact 63-bit frontier,
- maximize one-mutation law robustness.

A small sampled trajectory-perturbation check is then run only for selected
representative rules. This avoids pretending that one scalar score defines a
unique 'best universe'.
"""

from __future__ import annotations

import argparse
import itertools
import math
import random
from functools import lru_cache

import numpy as np

ACTIONS = (0, 1, 2)  # force 0, force 1, free
MEMORY = 3
STATES = 1 << MEMORY


def allowed(action: int) -> tuple[int, ...]:
    return (0,) if action == 0 else (1,) if action == 1 else (0, 1)


def transition_matrix(rule: tuple[int, ...]) -> np.ndarray:
    m = np.zeros((STATES, STATES), dtype=float)
    for state, action in enumerate(rule):
        for bit in allowed(action):
            nxt = ((state << 1) & (STATES - 1)) | bit
            m[state, nxt] += 1.0
    return m


def spectral_radius(rule: tuple[int, ...]) -> float:
    return float(max(abs(np.linalg.eigvals(transition_matrix(rule)))))


def exact_frontier(rule: tuple[int, ...], width: int = 63, max_steps: int = 1000) -> int | None:
    limit = 1 << width
    counts = [1] * STATES  # all 3-bit prefixes
    if STATES > limit:
        return MEMORY - 1
    for steps in range(MEMORY + 1, max_steps + 1):
        new = [0] * STATES
        for state, count in enumerate(counts):
            if not count:
                continue
            for bit in allowed(rule[state]):
                nxt = ((state << 1) & (STATES - 1)) | bit
                new[nxt] += count
        counts = new
        if sum(counts) > limit:
            return steps - 1
    return None


def law_robustness(rule: tuple[int, ...], rate_lookup: dict[tuple[int, ...], float]) -> float:
    target = round(rate_lookup[rule], 9)
    same = 0
    for pos in range(STATES):
        for action in ACTIONS:
            if action == rule[pos]:
                continue
            mutant = list(rule)
            mutant[pos] = action
            if round(rate_lookup[tuple(mutant)], 9) == target:
                same += 1
    return same / 16.0


def pareto_indices(rows: list[dict]) -> list[int]:
    out: list[int] = []
    for i, a in enumerate(rows):
        if a["lambda"] <= 1.000001:
            continue
        dominated = False
        for j, b in enumerate(rows):
            if i == j or b["lambda"] <= 1.000001:
                continue
            fa = a["frontier"] if a["frontier"] is not None else 10_000
            fb = b["frontier"] if b["frontier"] is not None else 10_000
            if (
                b["entropy"] >= a["entropy"]
                and fb >= fa
                and b["law_robustness"] >= a["law_robustness"]
                and (
                    b["entropy"] > a["entropy"]
                    or fb > fa
                    or b["law_robustness"] > a["law_robustness"]
                )
            ):
                dominated = True
                break
        if not dominated:
            out.append(i)
    return out


def validate(rule: tuple[int, ...], bits: list[int]) -> bool:
    if len(bits) <= MEMORY:
        return True
    state = (bits[0] << 2) | (bits[1] << 1) | bits[2]
    for bit in bits[MEMORY:]:
        if bit not in allowed(rule[state]):
            return False
        state = ((state << 1) & 7) | bit
    return True


def suffix_counter(rule: tuple[int, ...]):
    @lru_cache(maxsize=None)
    def count(state: int, remaining: int) -> int:
        if remaining == 0:
            return 1
        return sum(count(((state << 1) & 7) | bit, remaining - 1) for bit in allowed(rule[state]))
    return count


def total_count(rule: tuple[int, ...], steps: int) -> int:
    if steps <= MEMORY:
        return 1 << steps
    count = suffix_counter(rule)
    rem = steps - MEMORY
    return sum(count(state, rem) for state in range(STATES))


def unrank(rule: tuple[int, ...], steps: int, rank: int) -> list[int]:
    if steps <= MEMORY:
        return [((rank >> (steps - 1 - i)) & 1) for i in range(steps)]
    count = suffix_counter(rule)
    rem = steps - MEMORY
    prefix = None
    for state in range(STATES):
        c = count(state, rem)
        if rank < c:
            prefix = state
            break
        rank -= c
    assert prefix is not None
    bits = [(prefix >> 2) & 1, (prefix >> 1) & 1, prefix & 1]
    state = prefix
    for left in range(rem, 0, -1):
        for bit in allowed(rule[state]):
            nxt = ((state << 1) & 7) | bit
            c = count(nxt, left - 1)
            if rank < c:
                bits.append(bit)
                state = nxt
                break
            rank -= c
    return bits


def sampled_trajectory_robustness(rule: tuple[int, ...], steps: int = 64, samples: int = 256, seed: int = 123) -> float:
    rng = random.Random(seed)
    total = total_count(rule, steps)
    survived = 0
    trials = 0
    for _ in range(samples):
        bits = unrank(rule, steps, rng.randrange(total))
        for pos in range(steps):
            mutant = bits.copy()
            mutant[pos] ^= 1
            survived += int(validate(rule, mutant))
            trials += 1
    return survived / trials


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--width", type=int, default=63)
    p.add_argument("--frontier-max", type=int, default=1000)
    args = p.parse_args()

    rules = list(itertools.product(ACTIONS, repeat=STATES))
    rates = {rule: spectral_radius(rule) for rule in rules}
    rows = []
    for rule in rules:
        lam = rates[rule]
        rows.append({
            "rule": rule,
            "lambda": lam,
            "entropy": math.log2(max(lam, 1.0)),
            "frontier": exact_frontier(rule, args.width, args.frontier_max),
            "law_robustness": law_robustness(rule, rates),
        })

    pareto = pareto_indices(rows)
    print(f"rules={len(rows)} pareto={len(pareto)}")

    finite = [r for r in rows if r["lambda"] > 1.000001 and r["frontier"] is not None]
    hmin, hmax = min(r["entropy"] for r in finite), max(r["entropy"] for r in finite)
    fmin, fmax = min(r["frontier"] for r in finite), max(r["frontier"] for r in finite)
    for r in finite:
        hn = (r["entropy"] - hmin) / (hmax - hmin)
        fn = (r["frontier"] - fmin) / (fmax - fmin)
        r["maximin"] = min(hn, fn, r["law_robustness"])

    best = sorted(finite, key=lambda r: r["maximin"], reverse=True)[:10]
    print("\nBalanced maximin candidates:")
    for r in best:
        print(r)

    print("\nTrajectory-perturbation check for top two:")
    for r in best[:2]:
        tr = sampled_trajectory_robustness(r["rule"])
        print(r["rule"], "trajectory_robustness=", tr)


if __name__ == "__main__":
    main()

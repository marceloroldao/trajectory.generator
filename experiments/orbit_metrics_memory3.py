"""Orbit-style metrics for representative memory-3 admissibility laws.

Measures five independent properties:
- spectral growth rate lambda;
- entropy rate log2(lambda);
- exact 63-bit frontier;
- normalized Perron occupancy entropy over the 8 history states;
- spectral-gap-like mixing index 1-|lambda2|/|lambda1|;
- one-bit perturbation survival and error propagation.

These are combinatorial diagnostics of finite local laws, not physical claims.
"""

from __future__ import annotations

import argparse
import math
import random
from functools import lru_cache

import numpy as np

FORCE_0, FORCE_1, FREE = 0, 1, 2
MEMORY = 3
NSTATES = 1 << MEMORY
MASK = NSTATES - 1

RULES = {
    "plastic": (0, 0, 1, 0, 0, 2, 1, 0),
    "phi": (0, 0, 1, 2, 0, 2, 1, 2),
    "tribonacci": (0, 2, 2, 2, 1, 2, 2, 2),
    "balanced_1p285199": (1, 1, 1, 1, 0, 0, 0, 2),
}


def allowed(action: int) -> tuple[int, ...]:
    if action == FORCE_0:
        return (0,)
    if action == FORCE_1:
        return (1,)
    return (0, 1)


def next_state(state: int, bit: int) -> int:
    return ((state << 1) & MASK) | bit


def adjacency(rule: tuple[int, ...]) -> np.ndarray:
    a = np.zeros((NSTATES, NSTATES), dtype=float)
    for state, action in enumerate(rule):
        for bit in allowed(action):
            a[state, next_state(state, bit)] += 1.0
    return a


def spectral_metrics(rule: tuple[int, ...]) -> tuple[float, float, float, float]:
    a = adjacency(rule)
    vals, right = np.linalg.eig(a)
    order = np.argsort(np.abs(vals))[::-1]
    i = int(order[0])
    lam = float(abs(vals[i]))
    second = float(abs(vals[int(order[1])])) if len(order) > 1 else 0.0
    gap = 0.0 if lam == 0.0 else max(0.0, 1.0 - second / lam)

    vals_l, left = np.linalg.eig(a.T)
    j = int(np.argmin(np.abs(vals_l - vals[i])))
    rv = np.abs(np.real(right[:, i]))
    lv = np.abs(np.real(left[:, j]))
    weights = rv * lv
    if float(weights.sum()) == 0.0:
        pi = np.ones(NSTATES) / NSTATES
    else:
        pi = weights / weights.sum()
    nz = pi[pi > 1e-15]
    occupancy_entropy = float(-(nz * np.log2(nz)).sum() / math.log2(NSTATES))
    entropy_rate = math.log2(lam) if lam > 0.0 else float("-inf")
    return lam, entropy_rate, occupancy_entropy, gap


def count_trajectories(rule: tuple[int, ...], steps: int) -> int:
    if steps < 0:
        raise ValueError("steps must be non-negative")
    if steps <= MEMORY:
        return 1 << steps
    counts = [1] * NSTATES
    for _ in range(MEMORY, steps):
        nxt = [0] * NSTATES
        for state, action in enumerate(rule):
            for bit in allowed(action):
                nxt[next_state(state, bit)] += counts[state]
        counts = nxt
    return sum(counts)


def frontier(rule: tuple[int, ...], width: int = 63, max_steps: int = 5000) -> int | None:
    limit = 1 << width
    last = 0
    for steps in range(max_steps + 1):
        if count_trajectories(rule, steps) <= limit:
            last = steps
        else:
            return last
    return None


def unrank(rule: tuple[int, ...], rank: int, steps: int) -> list[int]:
    total = count_trajectories(rule, steps)
    if not 0 <= rank < total:
        raise ValueError("rank outside family")
    if steps <= MEMORY:
        return [(rank >> (steps - 1 - i)) & 1 for i in range(steps)]

    @lru_cache(maxsize=None)
    def suffix(state: int, remaining: int) -> int:
        if remaining == 0:
            return 1
        return sum(suffix(next_state(state, bit), remaining - 1) for bit in allowed(rule[state]))

    remaining = steps - MEMORY
    prefix = 0
    for state in range(NSTATES):
        c = suffix(state, remaining)
        if rank < c:
            prefix = state
            break
        rank -= c

    bits = [(prefix >> (MEMORY - 1 - i)) & 1 for i in range(MEMORY)]
    state = prefix
    for rem in range(remaining, 0, -1):
        for bit in allowed(rule[state]):
            c = suffix(next_state(state, bit), rem - 1)
            if rank < c:
                bits.append(bit)
                state = next_state(state, bit)
                break
            rank -= c
    return bits


def violation_positions(bits: list[int], rule: tuple[int, ...]) -> list[int]:
    if len(bits) <= MEMORY:
        return []
    state = 0
    for bit in bits[:MEMORY]:
        state = (state << 1) | bit
    violations: list[int] = []
    for pos, bit in enumerate(bits[MEMORY:], start=MEMORY):
        if bit not in allowed(rule[state]):
            violations.append(pos)
        state = next_state(state, bit)
    return violations


def perturbation_metrics(rule: tuple[int, ...], steps: int, samples: int, seed: int) -> tuple[float, float, float]:
    total = count_trajectories(rule, steps)
    rng = random.Random(seed)
    survived = 0
    trials = 0
    violation_sum = 0
    span_sum = 0

    for _ in range(samples):
        bits = unrank(rule, rng.randrange(total), steps)
        for pos in range(steps):
            perturbed = bits.copy()
            perturbed[pos] ^= 1
            violations = violation_positions(perturbed, rule)
            trials += 1
            if not violations:
                survived += 1
            else:
                violation_sum += len(violations)
                span_sum += violations[-1] - violations[0] + 1

    return survived / trials, violation_sum / trials, span_sum / trials


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", type=int, default=64)
    parser.add_argument("--samples", type=int, default=1024)
    parser.add_argument("--seed", type=int, default=123)
    args = parser.parse_args()

    print("name,lambda,h_bits_per_step,frontier63,occupancy_entropy,mixing_gap,flip_survival,mean_violations,mean_error_span")
    for name, rule in RULES.items():
        lam, h, occ, gap = spectral_metrics(rule)
        front = frontier(rule)
        survival, mean_viol, mean_span = perturbation_metrics(rule, args.steps, args.samples, args.seed)
        print(
            f"{name},{lam:.12f},{h:.12f},{front},{occ:.6f},{gap:.6f},"
            f"{survival:.6f},{mean_viol:.6f},{mean_span:.6f}"
        )


if __name__ == "__main__":
    main()

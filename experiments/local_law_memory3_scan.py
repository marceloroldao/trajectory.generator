"""Exhaustive scan of all ternary local admissibility laws with memory 3.

Each of the 8 history states (000..111) maps to one of:
- force 0
- force 1
- free {0,1}

Total laws: 3^8 = 6561.

For each law, compute:
- transition matrix over 3-bit history states;
- spectral radius (asymptotic trajectory-count growth factor);
- approximate entropy rate log2(lambda);
- exact 63-bit frontier by dynamic counting up to a practical cap;
- proximity to selected reference algebraic constants for reporting only.

No reference constant is used by the laws themselves.
"""

from __future__ import annotations

from collections import Counter
from itertools import product
from math import log2, sqrt

import numpy as np

ACTIONS = (0, 1, 2)  # force0, force1, free
PHI = (1 + sqrt(5)) / 2
PLASTIC = 1.3247179572447458
TRIBONACCI = 1.8392867552141612
LIMIT63 = 1 << 63


def next_bits(action: int):
    if action == 0:
        return (0,)
    if action == 1:
        return (1,)
    return (0, 1)


def transition_matrix(rule: tuple[int, ...]) -> np.ndarray:
    m = np.zeros((8, 8), dtype=float)
    for state in range(8):
        for bit in next_bits(rule[state]):
            nxt = ((state << 1) & 0b111) | bit
            m[state, nxt] += 1.0
    return m


def spectral_radius(rule: tuple[int, ...]) -> float:
    vals = np.linalg.eigvals(transition_matrix(rule))
    return float(max(abs(v) for v in vals))


def count_trajectories(rule: tuple[int, ...], steps: int) -> int:
    if steps < 0:
        raise ValueError("steps must be non-negative")
    if steps == 0:
        return 1
    if steps <= 3:
        return 1 << steps

    counts = [1] * 8  # every 3-bit history occurs once initially
    for _ in range(3, steps):
        nxt = [0] * 8
        for state, c in enumerate(counts):
            if not c:
                continue
            for bit in next_bits(rule[state]):
                ns = ((state << 1) & 0b111) | bit
                nxt[ns] += c
        counts = nxt
    return sum(counts)


def frontier_63(rule: tuple[int, ...], max_steps: int = 1000) -> int | None:
    for n in range(max_steps + 1):
        if count_trajectories(rule, n) > LIMIT63:
            return n - 1
    return None


def scan():
    rates = Counter()
    frontiers = Counter()
    hits = Counter()

    for rule in product(ACTIONS, repeat=8):
        lam = spectral_radius(rule)
        rates[round(lam, 9)] += 1
        if abs(lam - PHI) < 1e-8:
            hits["phi"] += 1
        if abs(lam - PLASTIC) < 1e-8:
            hits["plastic"] += 1
        if abs(lam - TRIBONACCI) < 1e-8:
            hits["tribonacci"] += 1

        fr = frontier_63(rule)
        frontiers["unreached<=1000" if fr is None else fr] += 1

    print("laws:", 3**8)
    print("distinct spectral radii (rounded 1e-9):", len(rates))
    print("selected recurrence counts:", dict(hits))
    print("most common rates:")
    for lam, count in rates.most_common(20):
        h = 0.0 if lam <= 1.0 else log2(lam)
        print(f"  lambda={lam:.9f}  laws={count:4d}  entropy_rate={h:.9f}")

    print("most common 63-bit frontiers:")
    for frontier, count in frontiers.most_common(20):
        print(f"  frontier={frontier}  laws={count}")


if __name__ == "__main__":
    scan()

#!/usr/bin/env python3
"""Scan the endogenous coherence-universe selector."""

from __future__ import annotations

from collections import Counter
from math import log2

from trajectory_generator.coherence_universe import (
    DEFAULT_COHERENCE_UNIVERSE_CONFIG as CFG,
    admissible_count,
    select_law,
)

NAMES = ("plastic", "phi", "tribonacci")


def allowed(action: int):
    return (0,) if action == 0 else (1,) if action == 1 else (0, 1)


def next_state(state: int, bit: int) -> int:
    return ((state << 1) & 7) | bit


def weighted_law_usage(steps: int):
    if steps <= CFG.memory:
        return {name: 0.0 for name in NAMES}
    counts = [1] * 8
    usage = Counter()
    for t in range(CFG.memory, steps):
        nxt_counts = [0] * 8
        for state, count in enumerate(counts):
            if not count:
                continue
            j = select_law(state, t, CFG)
            usage[j] += count
            action = CFG.laws[j][state]
            for bit in allowed(action):
                nxt_counts[next_state(state, bit)] += count
        counts = nxt_counts
    total = sum(usage.values())
    return {NAMES[j]: usage[j] / total for j in range(3)}


def frontier(width: int = 63, max_steps: int = 1000):
    limit = 1 << width
    best = 0
    for n in range(max_steps + 1):
        if admissible_count(n, CFG) <= limit:
            best = n
        else:
            return best
    return best


def main():
    steps_for_rate = 300
    total = admissible_count(steps_for_rate, CFG)
    rate = log2(total) / steps_for_rate
    growth = 2 ** rate
    f = frontier()
    usage = weighted_law_usage(f)

    print("coherence universe")
    print(f"effective bits/step ~= {rate:.12f}")
    print(f"effective growth    ~= {growth:.12f}")
    print(f"63-bit frontier     = {f}")
    print(f"N({f})               = {admissible_count(f, CFG)}")
    print(f"N({f+1})             = {admissible_count(f+1, CFG)}")
    print("weighted law usage at frontier:")
    for name, frac in usage.items():
        print(f"  {name:10s}: {frac:.6f}")


if __name__ == "__main__":
    main()

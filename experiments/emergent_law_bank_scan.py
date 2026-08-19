from collections import defaultdict
from math import log2

import numpy as np

from trajectory_generator.emergent_law_bank import (
    ALL_RULES,
    RULE_FEATURES,
    active_action,
    admissible_count,
    selected_rule_index,
)


def allowed(action):
    return (0, 1) if action == 2 else (action,)


def next_state(state, bit):
    return ((state << 1) & 7) | bit


def spectral_radius(rule):
    M = np.zeros((8, 8), dtype=float)
    for state, action in enumerate(rule):
        for bit in allowed(action):
            M[state, next_state(state, bit)] += 1.0
    return float(max(abs(np.linalg.eigvals(M))))


def frontier(width=63, max_steps=1000):
    limit = 1 << width
    last = 0
    for steps in range(max_steps + 1):
        if admissible_count(steps) <= limit:
            last = steps
        else:
            return last
    return last


def weighted_usage(steps):
    if steps <= 3:
        return {}
    counts = [1] * 8
    usage = defaultdict(int)
    for t in range(3, steps):
        nxt = [0] * 8
        for state, count in enumerate(counts):
            idx = selected_rule_index(state, t % 3)
            usage[idx] += count
            action = active_action(state, t)
            for bit in allowed(action):
                nxt[next_state(state, bit)] += count
        counts = nxt
    total = sum(usage.values())
    return {idx: value / total for idx, value in usage.items()}


def main():
    f = frontier()
    c0 = admissible_count(f)
    c1 = admissible_count(f + 1)
    rate300 = log2(admissible_count(300)) / 300
    lam_eff = 2 ** rate300
    usage = weighted_usage(f)

    print("bank laws:", len(ALL_RULES))
    print("frontier63:", f)
    print("count(frontier):", c0)
    print("count(frontier+1):", c1)
    print("rate@300 bits/step:", rate300)
    print("effective lambda@300:", lam_eff)
    print("selected laws:", len(usage))
    print()
    print("index usage lambda structural_features")
    for idx, frac in sorted(usage.items(), key=lambda item: -item[1]):
        print(idx, f"{frac:.6f}", f"{spectral_radius(ALL_RULES[idx]):.9f}", RULE_FEATURES[idx])


if __name__ == "__main__":
    main()

"""One-mutation robustness scan for all memory-3 local admissibility laws.

Each of the 8 history states maps to force-0, force-1, or free. For every one
of the 3^8 laws, inspect the 16 Hamming-distance-1 neighboring laws obtained by
changing one action to one of the other two actions.
"""

from __future__ import annotations

from collections import defaultdict, deque
from itertools import product

import numpy as np

ACTIONS = (0, 1, 2)  # force 0, force 1, free
MEMORY = 3
STATES = 1 << MEMORY
ROUND_DIGITS = 9


def transition_matrix(rule: tuple[int, ...]) -> np.ndarray:
    m = np.zeros((STATES, STATES), dtype=float)
    mask = STATES - 1
    for state, action in enumerate(rule):
        allowed = (0,) if action == 0 else (1,) if action == 1 else (0, 1)
        for bit in allowed:
            nxt = ((state << 1) & mask) | bit
            m[state, nxt] += 1.0
    return m


def spectral_radius(rule: tuple[int, ...]) -> float:
    return float(np.max(np.abs(np.linalg.eigvals(transition_matrix(rule)))))


def neighbors(rule: tuple[int, ...]):
    for pos in range(STATES):
        for action in ACTIONS:
            if action == rule[pos]:
                continue
            out = list(rule)
            out[pos] = action
            yield tuple(out)


def connected_components(indices: set[int], rules, index, rounded_radii):
    components = []
    remaining = set(indices)
    while remaining:
        start = remaining.pop()
        stack = [start]
        comp = [start]
        target = rounded_radii[start]
        while stack:
            current = stack.pop()
            for candidate in neighbors(rules[current]):
                j = index[candidate]
                if j in remaining and rounded_radii[j] == target:
                    remaining.remove(j)
                    stack.append(j)
                    comp.append(j)
        components.append(comp)
    return sorted((len(c) for c in components), reverse=True)


def main() -> None:
    rules = list(product(ACTIONS, repeat=STATES))
    index = {rule: i for i, rule in enumerate(rules)}
    radii = np.array([spectral_radius(rule) for rule in rules])
    rounded = np.round(radii, ROUND_DIGITS)

    same_fraction = np.zeros(len(rules), dtype=float)
    mean_delta = np.zeros(len(rules), dtype=float)

    for i, rule in enumerate(rules):
        vals = np.array([radii[index[n]] for n in neighbors(rule)])
        same_fraction[i] = np.mean(np.round(vals, ROUND_DIGITS) == rounded[i])
        mean_delta[i] = np.mean(np.abs(vals - radii[i]))

    classes = defaultdict(list)
    for i, value in enumerate(rounded):
        classes[float(value)].append(i)

    targets = {
        "plastic": 1.324717957,
        "phi": 1.618033989,
        "tribonacci": 1.839286755,
    }

    print(f"laws={len(rules)} distinct_rates={len(classes)}")
    print("\nselected classes")
    for name, target in targets.items():
        ids = np.array(classes[target], dtype=int)
        comps = connected_components(set(ids.tolist()), rules, index, rounded)
        print(
            f"{name:10s} lambda={target:.9f} laws={len(ids):4d} "
            f"same_neighbor={same_fraction[ids].mean():.6f} "
            f"mean_abs_delta={mean_delta[ids].mean():.6f} "
            f"components={len(comps):3d} largest={comps[:5]}"
        )

    print("\nmost common growth classes")
    rows = []
    for value, ids_list in classes.items():
        ids = np.array(ids_list, dtype=int)
        rows.append((len(ids), value, same_fraction[ids].mean(), mean_delta[ids].mean()))
    for count, value, robust, delta in sorted(rows, reverse=True)[:15]:
        print(
            f"lambda={value:.9f} laws={count:4d} "
            f"same_neighbor={robust:.6f} mean_abs_delta={delta:.6f}"
        )


if __name__ == "__main__":
    main()

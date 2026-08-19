"""Enumerate all memory-2 binary admissibility laws.

Each 2-bit history state (00,01,10,11) chooses one of three public actions:
- force next bit 0
- force next bit 1
- leave next bit free (0 or 1)

There are 3^4 = 81 distinct laws. For each law we build the 4x4 transition
matrix, count admissible trajectories exactly, estimate the asymptotic growth
rate from the spectral radius, and compute the maximum length that fits in a
63-bit final address.
"""

from __future__ import annotations

from itertools import product
from math import log2

STATES = ((0, 0), (0, 1), (1, 0), (1, 1))
STATE_INDEX = {s: i for i, s in enumerate(STATES)}
ACTIONS = ((0,), (1,), (0, 1))
ACTION_NAMES = ("force0", "force1", "free")


def transition_matrix(rule: tuple[int, int, int, int]) -> list[list[int]]:
    m = [[0] * 4 for _ in range(4)]
    for i, (a, b) in enumerate(STATES):
        for c in ACTIONS[rule[i]]:
            m[i][STATE_INDEX[(b, c)]] += 1
    return m


def matvec(v: list[int], m: list[list[int]]) -> list[int]:
    out = [0] * 4
    for i, vi in enumerate(v):
        for j in range(4):
            out[j] += vi * m[i][j]
    return out


def admissible_count(rule: tuple[int, int, int, int], steps: int) -> int:
    if steps < 0:
        raise ValueError("steps must be non-negative")
    if steps == 0:
        return 1
    if steps == 1:
        return 2
    v = [1, 1, 1, 1]  # all 2-bit prefixes
    m = transition_matrix(rule)
    for _ in range(3, steps + 1):
        v = matvec(v, m)
    return sum(v)


def frontier(rule: tuple[int, int, int, int], width: int = 63, max_steps: int = 10000) -> int:
    cap = 1 << width
    best = 0
    for n in range(max_steps + 1):
        if admissible_count(rule, n) <= cap:
            best = n
        else:
            break
    return best


def growth_ratio(rule: tuple[int, int, int, int], n: int = 200) -> float:
    a = admissible_count(rule, n - 1)
    b = admissible_count(rule, n)
    return b / a if a else 0.0


def describe_rule(rule: tuple[int, int, int, int]) -> str:
    return " ".join(f"{''.join(map(str, s))}:{ACTION_NAMES[a]}" for s, a in zip(STATES, rule))


def main() -> None:
    rows = []
    for rule in product(range(3), repeat=4):
        ratio = growth_ratio(rule)
        rows.append((ratio, frontier(rule), rule, admissible_count(rule, 20)))

    groups: dict[float, list[tuple[int, tuple[int, ...], int]]] = {}
    for ratio, front, rule, n20 in rows:
        key = round(ratio, 12)
        groups.setdefault(key, []).append((front, rule, n20))

    print("memory-2 law scan")
    print("laws:", len(rows))
    print("distinct asymptotic ratios:", len(groups))
    print()
    for ratio in sorted(groups):
        entries = groups[ratio]
        front, rule, n20 = entries[0]
        entropy = log2(ratio) if ratio > 0 else float("-inf")
        print(f"lambda={ratio:.12f}  entropy={entropy:.6f} bit/step  laws={len(entries):2d}  frontier63={front}")
        print("  representative:", describe_rule(rule))
        print("  N(20):", n20)


if __name__ == "__main__":
    main()

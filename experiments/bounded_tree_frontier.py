"""Conservative frontier for a depth-bounded self-resolving tree.

Unlike unrestricted recursion, bounded recursion can reject trajectories: once the
public tree-depth budget is exhausted, the remaining block must be leaf-admissible.
This produces a genuinely constrained structured family for sufficiently long inputs.

The numeric recurrence here is still a conservative address-envelope count because
leaf/split overlaps are not subtracted. It is useful for comparing structural freedom
under a fixed 63-bit budget.
"""

from __future__ import annotations

import argparse
from functools import lru_cache
from math import comb


def leaf_radix(length: int, max_deviations: int, max_level: int) -> int:
    k = min(max_deviations, length - 1)
    per_level = 2 * sum(comb(length - 1, j) for j in range(k + 1))
    return (max_level + 1) * per_level


def bounded_envelope(
    length: int,
    tree_depth: int,
    *,
    max_deviations: int = 5,
    max_level: int = 3,
) -> int:
    @lru_cache(maxsize=None)
    def count(n: int, depth: int) -> int:
        leaves = leaf_radix(n, max_deviations, max_level)
        if depth <= 0 or n < 2:
            return leaves
        left = n // 2
        right = n - left
        return leaves + count(left, depth - 1) * count(right, depth - 1)

    if length < 1:
        return 1
    return count(length, tree_depth)


def frontier(width: int, tree_depth: int, max_deviations: int, max_level: int) -> int:
    limit = 1 << width
    n = 1
    while bounded_envelope(
        n,
        tree_depth,
        max_deviations=max_deviations,
        max_level=max_level,
    ) <= limit:
        n += 1
    return n - 1


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--width", type=int, default=63)
    p.add_argument("--max-tree-depth", type=int, default=4)
    p.add_argument("--max-deviations", type=int, default=5)
    p.add_argument("--max-level", type=int, default=3)
    args = p.parse_args()

    print("tree_depth,conservative_frontier")
    for d in range(args.max_tree_depth + 1):
        f = frontier(args.width, d, args.max_deviations, args.max_level)
        print(f"{d},{f}")


if __name__ == "__main__":
    main()

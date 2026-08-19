"""Exact semantic-family scan for the self-resolving tree.

This experiment distinguishes two quantities:

1. the conservative numeric envelope used by the current address layout;
2. the number of distinct binary trajectories that are actually admissible under
   the canonical rule "leaf if possible, otherwise split recursively".

Because atomic blocks of length 1 are always leaf-admissible, unrestricted recursive
splitting makes every binary sequence admissible. Therefore the exact semantic family
has size 2**n, even when the conservative address envelope is much larger.
"""

from __future__ import annotations

import argparse

from trajectory_generator.self_resolving_tree import (
    DEFAULT_SELF_RESOLVING_CONFIG,
    address_envelope_count,
)


def semantic_family_count(steps: int) -> int:
    """Exact family size for unrestricted recursion to atomic leaves."""
    if steps < 0:
        raise ValueError("steps must be non-negative")
    return 1 << steps


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--max-bits", type=int, default=24)
    args = p.parse_args()

    cfg = DEFAULT_SELF_RESOLVING_CONFIG
    print("steps,semantic_family,conservative_envelope,overhead_ratio")
    for n in range(args.max_bits + 1):
        semantic = semantic_family_count(n)
        envelope = address_envelope_count(n, cfg)
        ratio = envelope / semantic if semantic else 1.0
        print(f"{n},{semantic},{envelope},{ratio:.6f}")


if __name__ == "__main__":
    main()

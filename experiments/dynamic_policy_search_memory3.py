"""Compare fixed and second-order context-dependent policy universes.

The dynamic policy changes selector weights deterministically from current
history class and public phase. It is compared against the frozen balanced
policy from policy_universe.py.
"""

from __future__ import annotations

import math
import random

from trajectory_generator.dynamic_policy_universe import (
    admissible_count,
    active_action,
    selected_rule_index,
    unrank_trajectory,
    validate,
)


def frontier(width: int = 63, max_steps: int = 1000) -> int:
    limit = 1 << width
    last = 0
    for n in range(max_steps + 1):
        if admissible_count(n) > limit:
            return n - 1
        last = n
    return last


def flip_survival(steps: int = 64, samples: int = 1024, seed: int = 123) -> float:
    rng = random.Random(seed)
    total = admissible_count(steps)
    survived = 0
    tested = 0
    for _ in range(samples):
        bits = unrank_trajectory(rng.randrange(total), steps)
        for i in range(steps):
            perturbed = bits.copy()
            perturbed[i] ^= 1
            survived += int(validate(perturbed))
            tested += 1
    return survived / tested


def main() -> None:
    f = frontier()
    count_f = admissible_count(f)
    count_next = admissible_count(f + 1)
    rate300 = math.log2(admissible_count(300)) / 300
    used = {
        selected_rule_index(state, phase)
        for state in range(8)
        for phase in range(3)
    }
    free_contexts = sum(
        active_action(state, phase) == 2
        for state in range(8)
        for phase in range(3)
    )
    print("dynamic second-order policy")
    print("frontier63:", f)
    print("count(frontier):", count_f)
    print("count(frontier+1):", count_next)
    print("rate300:", rate300)
    print("active laws:", len(used))
    print("free contexts:", free_contexts, "/ 24")
    print("flip survival:", flip_survival())


if __name__ == "__main__":
    main()

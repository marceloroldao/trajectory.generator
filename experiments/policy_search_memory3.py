"""Seeded exploratory policy search over the complete memory-3 law bank.

This experiment searches selector-weight vectors.  It does not optimize for any
named algebraic constant.  Candidate policies are compared by exact 63-bit
frontier plus simple diversity/rigidity diagnostics.  The frozen balanced policy
in trajectory_generator.policy_universe was selected from this exploratory run.

Because this is a search over policies, reported winners are exploratory and may
overfit these metrics.  They must be re-tested on independent criteria.
"""

from __future__ import annotations

import argparse
import math
import random

from trajectory_generator.policy_universe import (
    ALL_RULES,
    PolicyUniverseConfig,
    admissible_count,
    active_action,
    selected_rule_index,
)


def frontier(cfg: PolicyUniverseConfig, max_steps: int = 1000) -> int:
    limit = 1 << cfg.width
    last = 0
    for steps in range(max_steps + 1):
        if admissible_count(steps, cfg) > limit:
            return steps - 1
        last = steps
    return last


def policy_diagnostics(weights: tuple[int, ...], width: int = 63) -> dict[str, float | int]:
    cfg = PolicyUniverseConfig(width=width, weights=weights)
    f = frontier(cfg)
    c300 = admissible_count(300, cfg)
    rate = math.log2(c300) / 300 if c300 > 0 else 0.0
    used = {
        selected_rule_index(state, phase, weights)
        for state in range(8)
        for phase in range(3)
    }
    free_contexts = sum(
        active_action(state, phase, weights) == 2
        for state in range(8)
        for phase in range(3)
    )
    return {
        "frontier": f,
        "rate300": rate,
        "used_laws": len(used),
        "free_context_fraction": free_contexts / 24.0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=300)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    rows = []
    for _ in range(args.samples):
        weights = (
            rng.randint(0, 8),
            rng.randint(0, 8),
            rng.randint(0, 5),
            rng.randint(0, 3),
            rng.randint(0, 3),
            rng.randint(0, 3),
            rng.randint(0, 3),
            rng.randint(0, 3),
            rng.randint(0, 3),
        )
        if not any(weights):
            continue
        d = policy_diagnostics(weights)
        rows.append((d["frontier"], d["rate300"], d["used_laws"], d["free_context_fraction"], weights))

    # Prefer long frontier, then nontrivial diversity, then a nonzero information rate.
    rows.sort(reverse=True)
    print("frontier  rate300  laws  free_ctx  weights")
    for row in rows[:30]:
        print(f"{row[0]:8d}  {row[1]:7.4f}  {row[2]:4d}  {row[3]:8.4f}  {row[4]}")


if __name__ == "__main__":
    main()

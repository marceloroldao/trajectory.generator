"""Sample one-bit perturbation robustness for representative memory-3 laws.

This measures geometry inside an admissible trajectory family, not robustness of
the rule itself. For sampled valid trajectories, flip each bit in turn and ask
whether the perturbed sequence remains valid under the same public local law.
"""

from __future__ import annotations

import argparse
import random

from trajectory_generator.finite_law_codec import (
    FiniteLawConfig,
    MEMORY3_PHI_RULE,
    MEMORY3_PLASTIC_RULE,
    MEMORY3_TRIBONACCI_RULE,
    admissible_count,
    unrank_trajectory,
    validate,
)

RULES = {
    "plastic": MEMORY3_PLASTIC_RULE,
    "phi": MEMORY3_PHI_RULE,
    "tribonacci": MEMORY3_TRIBONACCI_RULE,
}


def measure(name: str, steps: int, samples: int, seed: int) -> None:
    cfg = FiniteLawConfig(rule=RULES[name], memory=3)
    total = admissible_count(steps, cfg)
    rng = random.Random(seed)
    survivors = 0
    trials = 0
    by_position = [0] * steps

    for _ in range(samples):
        rank = rng.randrange(total)
        bits = unrank_trajectory(rank, steps, cfg)
        for pos in range(steps):
            mutated = bits.copy()
            mutated[pos] ^= 1
            ok = validate(mutated, cfg)
            survivors += int(ok)
            by_position[pos] += int(ok)
            trials += 1

    print(
        f"{name:10s} steps={steps} samples={samples} family={total} "
        f"survival={survivors / trials:.9f}"
    )
    rates = [x / samples for x in by_position]
    print(
        f"  position survival: min={min(rates):.6f} "
        f"mean={sum(rates)/len(rates):.6f} max={max(rates):.6f}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", type=int, default=64)
    parser.add_argument("--samples", type=int, default=2048)
    parser.add_argument("--seed", type=int, default=123)
    args = parser.parse_args()
    for name in RULES:
        measure(name, args.steps, args.samples, args.seed)


if __name__ == "__main__":
    main()

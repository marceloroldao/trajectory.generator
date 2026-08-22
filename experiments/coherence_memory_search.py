"""Exhaustive search of the public four-bucket coherence-memory dynamics.

The search does not target phi or another named constant. It evaluates all
5^4 policy maps for each of the three public coherence-update modes and compares
exact 63-bit frontier, finite-length entropy rate, policy diversity, and sampled
trajectory perturbation survival.

The scan is intentionally small enough to be exhaustive: 625 maps * 3 modes =
1,875 public configurations.
"""

from __future__ import annotations

import argparse
import itertools
import math
import random

from trajectory_generator.coherence_memory_universe import (
    CoherenceMemoryConfig,
    POLICY_BANK,
    admissible_count,
    unrank_trajectory,
    validate,
)


def frontier(cfg: CoherenceMemoryConfig, max_steps: int = 600) -> int:
    limit = 1 << cfg.width
    last = 0
    for n in range(max_steps + 1):
        if admissible_count(n, cfg) > limit:
            return n - 1
        last = n
    return last


def policy_diversity(cfg: CoherenceMemoryConfig) -> int:
    return len(set(cfg.policy_map))


def flip_survival(cfg: CoherenceMemoryConfig, steps: int, samples: int, seed: int) -> float:
    total = admissible_count(steps, cfg)
    if total == 0:
        return 0.0
    rng = random.Random(seed)
    tested = 0
    survived = 0
    for _ in range(min(samples, total)):
        rank = rng.randrange(total)
        bits = unrank_trajectory(rank, steps, cfg)
        for pos in range(steps):
            trial = bits.copy()
            trial[pos] ^= 1
            tested += 1
            survived += int(validate(trial, cfg))
    return survived / tested if tested else 0.0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--samples", type=int, default=64)
    parser.add_argument("--min-rate", type=float, default=0.25)
    parser.add_argument("--max-rate", type=float, default=0.50)
    parser.add_argument("--top", type=int, default=40)
    args = parser.parse_args()

    rows = []
    maps = itertools.product(range(len(POLICY_BANK)), repeat=4)
    for mode in ("occupancy", "signed_bit", "rolling"):
        for pmap in maps if mode == "occupancy" else itertools.product(range(len(POLICY_BANK)), repeat=4):
            cfg = CoherenceMemoryConfig(policy_map=tuple(pmap), update_mode=mode)
            f = frontier(cfg)
            c300 = admissible_count(300, cfg)
            rate = math.log2(c300) / 300 if c300 > 0 else 0.0
            if not args.min_rate <= rate <= args.max_rate:
                continue
            survival = flip_survival(cfg, min(64, f), args.samples, args.seed)
            rows.append((f, survival, rate, policy_diversity(cfg), mode, tuple(pmap)))

    # Frontier first, then perturbation survival. This keeps the capacity extreme
    # visible while also exposing more balanced Pareto candidates.
    rows.sort(reverse=True)
    print("frontier  flip_survival  rate300  policies  mode        policy_map")
    for row in rows[: args.top]:
        print(f"{row[0]:8d}  {row[1]:13.4f}  {row[2]:7.4f}  {row[3]:8d}  {row[4]:10s}  {row[5]}")

    print("\nBest perturbation survival among configs that beat 184 steps:")
    better = [row for row in rows if row[0] > 184]
    better.sort(key=lambda row: (row[1], row[0]), reverse=True)
    for row in better[: min(args.top, 20)]:
        print(f"{row[0]:8d}  {row[1]:13.4f}  {row[2]:7.4f}  {row[3]:8d}  {row[4]:10s}  {row[5]}")


if __name__ == "__main__":
    main()

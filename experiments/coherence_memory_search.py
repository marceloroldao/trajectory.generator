"""Search small public coherence-memory dynamics.

The search does not target phi or another named constant.  It compares exact
63-bit frontier, finite-length entropy rate, policy diversity, and trajectory
perturbation survival.  Results are exploratory and should be revalidated on
independent seeds/metrics before freezing a default.
"""

from __future__ import annotations

import argparse
import itertools
import math
import random

from trajectory_generator.coherence_memory_universe import (
    CoherenceMemoryConfig,
    POLICY_BANK,
    active_action,
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
    used = set()
    for state in range(8):
        for phase in range(3):
            for c in range(cfg.coherence_levels):
                used.add(cfg.policy_map[c])
    return len(used)


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
    parser.add_argument("--max-configs", type=int, default=500)
    parser.add_argument("--seed", type=int, default=19)
    parser.add_argument("--samples", type=int, default=128)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    maps = list(itertools.product(range(len(POLICY_BANK)), repeat=4))
    rng.shuffle(maps)
    maps = maps[: args.max_configs]

    rows = []
    for mode in ("occupancy", "signed_bit", "rolling"):
        for pmap in maps:
            if len(set(pmap)) < 2:
                continue
            cfg = CoherenceMemoryConfig(policy_map=pmap, update_mode=mode)
            f = frontier(cfg)
            c300 = admissible_count(300, cfg)
            rate = math.log2(c300) / 300 if c300 > 0 else 0.0
            # Avoid rewarding nearly deterministic universes.
            if not 0.20 <= rate <= 0.60:
                continue
            survival = flip_survival(cfg, min(64, f), args.samples, args.seed)
            rows.append((f, survival, rate, policy_diversity(cfg), mode, pmap))

    rows.sort(reverse=True)
    print("frontier  flip_survival  rate300  policies  mode        policy_map")
    for row in rows[:30]:
        print(f"{row[0]:8d}  {row[1]:13.4f}  {row[2]:7.4f}  {row[3]:8d}  {row[4]:10s}  {row[5]}")


if __name__ == "__main__":
    main()

"""Multi-seed validation for the controlled memory-order ablation.

Repeats the canonical-bank comparison at memory orders 2, 3, and 4 across
multiple deterministic seeds.  The purpose is to detect bank-specific artifacts
before attributing a result to memory order itself.
"""

from __future__ import annotations

import argparse
import math
import statistics

from memory_order_compare import Config, build, frontier, flip_survival


def summarize(values: list[float]) -> tuple[float, float, float]:
    return min(values), statistics.median(values), max(values)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bank-size", type=int, default=256)
    ap.add_argument("--seeds", type=int, default=8)
    ap.add_argument("--max-steps", type=int, default=1000)
    ap.add_argument("--samples", type=int, default=128)
    ap.add_argument("--base-seed", type=int, default=0xC0FFEE)
    args = ap.parse_args()

    seeds = [args.base_seed + i * 0x9E3779B1 for i in range(args.seeds)]

    print("memory  frontier[min,med,max]  rate300[min,med,max]  flip64[min,med,max]  noncross")
    for memory in (2, 3, 4):
        frontiers: list[float] = []
        rates: list[float] = []
        flips: list[float] = []
        noncross = 0

        for seed in seeds:
            cfg = Config(memory=memory, bank_size=args.bank_size, seed=seed)
            count, validate, unrank = build(cfg)
            f, crossed = frontier(count, cfg.width, args.max_steps)
            if not crossed:
                noncross += 1
            frontiers.append(float(f))
            c300 = count(300)
            rates.append(math.log2(c300) / 300 if c300 else 0.0)
            c64 = count(64)
            flips.append(flip_survival(validate, unrank, c64, 64, args.samples, seed))

        f0, fm, f1 = summarize(frontiers)
        r0, rm, r1 = summarize(rates)
        p0, pm, p1 = summarize(flips)
        print(
            f"{memory:6d}  "
            f"[{f0:6.0f},{fm:6.1f},{f1:6.0f}]  "
            f"[{r0:7.4f},{rm:7.4f},{r1:7.4f}]  "
            f"[{p0:7.4f},{pm:7.4f},{p1:7.4f}]  "
            f"{noncross}/{args.seeds}"
        )


if __name__ == "__main__":
    main()

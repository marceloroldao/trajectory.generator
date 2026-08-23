"""Targeted policy-map search for the controlled memory-4 canonical bank.

This script reuses the controlled benchmark machinery from memory_order_compare
and searches the 3 * 5^4 coherence dynamics induced by:

- update_mode in {occupancy, signed_bit, rolling}
- a four-bucket policy_map over the five public selector profiles

The goal is not to maximize frontier alone. Candidates are first screened by
finite-length information rate and exact 63-bit frontier; perturbation survival
is then measured for the top candidates.
"""

from __future__ import annotations

import argparse
import itertools
import math

from memory_order_compare import Config, build, frontier, flip_survival


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=12648430)
    ap.add_argument("--bank-size", type=int, default=256)
    ap.add_argument("--min-rate", type=float, default=0.20)
    ap.add_argument("--max-rate", type=float, default=0.45)
    ap.add_argument("--top", type=int, default=30)
    ap.add_argument("--samples", type=int, default=256)
    args = ap.parse_args()

    rows = []
    for mode in ("occupancy", "signed_bit", "rolling"):
        for pmap in itertools.product(range(5), repeat=4):
            if len(set(pmap)) < 2:
                continue
            cfg = Config(
                memory=4,
                bank_size=args.bank_size,
                seed=args.seed,
                policy_map=pmap,
                update_mode=mode,
            )
            count, validate, unrank = build(cfg)
            f, crossed = frontier(count, cfg.width, max_steps=1000)
            c300 = count(300)
            rate = math.log2(c300) / 300 if c300 else 0.0
            if not args.min_rate <= rate <= args.max_rate:
                continue
            rows.append((f, crossed, rate, mode, pmap, count, validate, unrank))

    rows.sort(key=lambda r: (r[0], r[2]), reverse=True)

    print("frontier crossed rate300 flip64 count64 mode policy_map")
    for f, crossed, rate, mode, pmap, count, validate, unrank in rows[: args.top]:
        c64 = count(64)
        flip = flip_survival(validate, unrank, c64, 64, args.samples, args.seed)
        marker = str(f) if crossed else f">={f}"
        print(f"{marker:>8s} {str(crossed):>7s} {rate:7.4f} {flip:7.4f} {c64:10d} {mode:10s} {pmap}")


if __name__ == "__main__":
    main()

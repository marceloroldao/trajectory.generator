#!/usr/bin/env python3

import math

from trajectory_generator.dynamic_law_codec import (
    DynamicLawConfig,
    MEMORY3_PHI_RULE,
    MEMORY3_PLASTIC_RULE,
    MEMORY3_TRIBONACCI_RULE,
    admissible_count,
)


def frontier(cfg: DynamicLawConfig, limit: int = 2000):
    cap = 1 << cfg.width
    last = 0
    for n in range(limit + 1):
        count = admissible_count(n, cfg)
        if count > cap:
            return last, admissible_count(last, cfg), n, count
        last = n
    return None


def effective_lambda(cfg: DynamicLawConfig, n0: int = 240, n1: int = 300) -> float:
    a = admissible_count(n0, cfg)
    b = admissible_count(n1, cfg)
    return (b / a) ** (1.0 / (n1 - n0))


def main():
    cases = {
        "plastic+phi": (MEMORY3_PLASTIC_RULE, MEMORY3_PHI_RULE),
        "phi+tribonacci": (MEMORY3_PHI_RULE, MEMORY3_TRIBONACCI_RULE),
        "plastic+tribonacci": (MEMORY3_PLASTIC_RULE, MEMORY3_TRIBONACCI_RULE),
        "plastic+phi+tribonacci": (
            MEMORY3_PLASTIC_RULE,
            MEMORY3_PHI_RULE,
            MEMORY3_TRIBONACCI_RULE,
        ),
    }

    print("dynamic state-and-phase universe")
    print("selector = (popcount(history) + t % period) % number_of_rules")
    print()
    print(f"{'case':28s} {'lambda_eff':>12s} {'h(bits/step)':>14s} {'frontier63':>12s}")
    print("-" * 72)

    for name, bank in cases.items():
        cfg = DynamicLawConfig(rule_bank=bank, memory=3, period=3, width=63)
        lam = effective_lambda(cfg)
        h = math.log2(lam)
        fr = frontier(cfg)
        fr_n = fr[0] if fr else ">=2000"
        print(f"{name:28s} {lam:12.9f} {h:14.9f} {str(fr_n):>12s}")


if __name__ == "__main__":
    main()

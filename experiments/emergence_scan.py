"""Analyze orbit statistics without inserting preferred ratios into the dynamics.

Reference constants, including phi, appear only in this analysis script. They are not
used by the state machine and therefore cannot force the trajectory itself.
"""

from __future__ import annotations

import math
import statistics

from trajectory_generator import encode_bits


def hamming(a: int, b: int) -> int:
    return (a ^ b).bit_count()


def analyze(bits: list[int]) -> None:
    _, _, trajectory = encode_bits(bits, return_trajectory=True)
    _, _, baseline = encode_bits([0] * len(bits), return_trajectory=True)

    radii = [hamming(x, c) for x, c in zip(trajectory, baseline)]
    positive_pairs = [
        radii[i + 1] / radii[i]
        for i in range(1, len(radii) - 1)
        if radii[i] > 0 and radii[i + 1] > 0
    ]

    print("trajectory bits :", len(bits))
    print("radii           :", radii)

    if not positive_pairs:
        print("No positive consecutive-radius ratios available.")
        return

    median_ratio = statistics.median(positive_pairs)
    references = {
        "sqrt(2)": math.sqrt(2),
        "3/2": 1.5,
        "phi": (1 + math.sqrt(5)) / 2,
        "sqrt(3)": math.sqrt(3),
        "e": math.e,
    }

    print("median ratio    :", median_ratio)
    print("reference distances (analysis only):")
    for name, value in sorted(references.items(), key=lambda kv: abs(median_ratio - kv[1])):
        print(f"  {name:7s} value={value:.12f} abs_error={abs(median_ratio - value):.12f}")


if __name__ == "__main__":
    # Deterministic test trajectory; no preferred irrational is used to generate it.
    analyze([1, 0, 1, 1, 0, 0, 1, 0, 1, 0, 0, 1, 1, 1, 0, 1])

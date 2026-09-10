"""Online emergence of the exact trajectory address.

This experiment updates a 63-bit address accumulator causally while the
trajectory is traversed.  It does not rank the finished path afterward.
The accumulator uses only:
  - current private state P=(h2,q0,q1,q2)
  - public phase t mod 3
  - current edge label z
  - known total horizon T and current step k
  - suffix counts generated from the same local four-bit law

For a fixed T, the final accumulator is exactly the enumerative address, so
(address_final, T) reconstructs the entire path by unrank().
"""
from __future__ import annotations

import random

from standalone_four_bit_codec import (
    LIMIT,
    allowed,
    initial_private,
    rank,
    step,
    suffix,
    total,
    unrank,
)


def initial_offset(initial: int, transitions: int) -> int:
    """Address mass occupied by lexicographically earlier initial states."""
    return sum(
        suffix(initial_private(s), 0, transitions)
        for s in range(initial)
    )


def online_address(path):
    """Accumulate the exact address during traversal, never ranking afterward."""
    if len(path) < 3:
        raise ValueError("path must include the 3-bit initial prefix")

    transitions = len(path) - 3
    initial = (path[0] << 2) | (path[1] << 1) | path[2]
    address = initial_offset(initial, transitions)

    p = initial_private(initial)
    phase = 0
    trace = [(0, address, p, phase)]

    for k, z_actual in enumerate(path[3:]):
        if not allowed(p, z_actual, phase):
            raise ValueError("inadmissible path")

        left = transitions - k - 1

        # If the actual branch is 1, every admissible branch 0 at this state
        # precedes it lexicographically.  Add exactly the number of complete
        # trajectories living below that skipped branch.
        if z_actual == 1 and allowed(p, 0, phase):
            p0 = step(p, 0, phase)
            address += suffix(p0, (phase + 1) % 3, left)

        p = step(p, z_actual, phase)
        phase = (phase + 1) % 3
        trace.append((k + 1, address, p, phase))

    return address, trace


def reconstruct_from_final(address: int, transitions: int):
    """The final accumulator plus T is sufficient to reconstruct the path."""
    return unrank(address, transitions)


def main():
    rng = random.Random(20260909)

    tested = 0
    max_seen = 0
    monotone_failures = 0
    for transitions in (0, 1, 2, 16, 64, 128, 218):
        n = total(transitions)
        samples = min(250, n)
        for _ in range(samples):
            target = rng.randrange(n)
            path = unrank(target, transitions)
            emerged, trace = online_address(path)
            reconstructed = reconstruct_from_final(emerged, transitions)

            assert emerged == target
            assert emerged == rank(path)
            assert reconstructed == path
            assert emerged < LIMIT

            values = [x[1] for x in trace]
            if any(b < a for a, b in zip(values, values[1:])):
                monotone_failures += 1
            max_seen = max(max_seen, max(values))
            tested += 1

        print(
            "T", transitions,
            "family", n,
            "samples", samples,
            "online_roundtrip", "ok",
        )

    assert monotone_failures == 0

    # Boundary addresses prove the full frontier, not just random samples.
    for address in (0, total(218) - 1):
        path = unrank(address, 218)
        emerged, trace = online_address(path)
        assert emerged == address
        assert reconstruct_from_final(emerged, 218) == path
        print(
            "boundary",
            address,
            "final_private", trace[-1][2],
            "phase", trace[-1][3],
            "symbols", len(path),
        )

    print("tested_paths", tested + 2)
    print("monotone_failures", monotone_failures)
    print("max_accumulator_seen", max_seen)
    print("frontier_T218", total(218))
    print("frontier_T219", total(219))
    print("contract", "(R_final,T) -> exact trajectory")
    print("important_limit", "R update depends on known horizon T via suffix counts")


if __name__ == "__main__":
    main()

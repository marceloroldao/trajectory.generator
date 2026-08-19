from __future__ import annotations

import argparse
from collections import Counter

from trajectory_generator import DEFAULT_CONFIG, encode_bits, int_to_bits


def scan(n_bits: int) -> dict[str, int | float]:
    seen: dict[int, int] = {}
    collisions = 0
    multiplicity = Counter()

    for value in range(1 << n_bits):
        state, steps = encode_bits(int_to_bits(value, n_bits), DEFAULT_CONFIG)
        if steps != n_bits:
            raise AssertionError("step count mismatch")
        if state in seen:
            collisions += 1
            multiplicity[state] += 1
        else:
            seen[state] = value
            multiplicity[state] = 1

    unique_states = len(seen)
    total = 1 << n_bits
    return {
        "bits": n_bits,
        "trajectories": total,
        "unique_states": unique_states,
        "collisions": collisions,
        "injective_fraction": unique_states / total,
        "max_multiplicity": max(multiplicity.values(), default=0),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-bits", type=int, default=4)
    parser.add_argument("--max-bits", type=int, default=20)
    args = parser.parse_args()

    if args.min_bits < 1 or args.max_bits < args.min_bits:
        raise SystemExit("invalid bit range")

    print("bits,trajectories,unique_states,collisions,injective_fraction,max_multiplicity")
    for n in range(args.min_bits, args.max_bits + 1):
        r = scan(n)
        print(
            f"{r['bits']},{r['trajectories']},{r['unique_states']},"
            f"{r['collisions']},{r['injective_fraction']:.12f},{r['max_multiplicity']}"
        )


if __name__ == "__main__":
    main()

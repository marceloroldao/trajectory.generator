from __future__ import annotations

import argparse

from trajectory_generator.core import DEFAULT_CONFIG, step_forward


def bits_of(value: int, n: int) -> str:
    return format(value, f"0{n}b")


def scan_frontier(max_bits: int) -> list[dict[str, int | bool | str | None]]:
    """Enumerate the full trajectory frontier incrementally.

    Each state stores one representative trajectory encoded as an integer. At the
    next step every representative branches with bit 0 and bit 1. A duplicate final
    state proves non-injectivity for that trajectory length and records a witness pair.

    This avoids recomputing each length from t=0 and therefore extends exhaustive
    testing farther than experiments/exhaustive_scan.py while preserving exactness.
    """
    if max_bits < 1:
        raise ValueError("max_bits must be >= 1")

    states: dict[int, int] = {DEFAULT_CONFIG.initial_state & DEFAULT_CONFIG.mask: 0}
    rows: list[dict[str, int | bool | str | None]] = []

    for t in range(max_bits):
        next_states: dict[int, int] = {}
        collision_count = 0
        witness_a: int | None = None
        witness_b: int | None = None
        witness_state: int | None = None

        for state, prefix in states.items():
            for bit in (0, 1):
                final_state = step_forward(state, bit, t, DEFAULT_CONFIG)
                trajectory = (prefix << 1) | bit
                previous = next_states.get(final_state)
                if previous is None:
                    next_states[final_state] = trajectory
                else:
                    collision_count += 1
                    if witness_a is None:
                        witness_a = previous
                        witness_b = trajectory
                        witness_state = final_state

        n = t + 1
        total = 1 << n
        rows.append(
            {
                "bits": n,
                "trajectories": total,
                "unique_states": len(next_states),
                "collisions": collision_count,
                "injective": collision_count == 0,
                "witness_a": None if witness_a is None else bits_of(witness_a, n),
                "witness_b": None if witness_b is None else bits_of(witness_b, n),
                "collision_state": witness_state,
            }
        )
        states = next_states

    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-bits", type=int, default=21)
    parser.add_argument("--from-bits", type=int, default=1)
    args = parser.parse_args()

    if args.from_bits < 1 or args.from_bits > args.max_bits:
        raise SystemExit("invalid bit range")

    rows = scan_frontier(args.max_bits)
    print("bits,trajectories,unique_states,collisions,injective,witness_a,witness_b,collision_state")
    for row in rows:
        if int(row["bits"]) < args.from_bits:
            continue
        print(
            f"{row['bits']},{row['trajectories']},{row['unique_states']},"
            f"{row['collisions']},{row['injective']},{row['witness_a'] or ''},"
            f"{row['witness_b'] or ''},{'' if row['collision_state'] is None else row['collision_state']}"
        )


if __name__ == "__main__":
    main()

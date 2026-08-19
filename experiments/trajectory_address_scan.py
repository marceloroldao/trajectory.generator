from __future__ import annotations

import argparse

from trajectory_generator import (
    TrajectoryAddressConfig,
    decode_trajectory_address,
    encode_trajectory_address,
    int_to_bits,
)


def scan(width: int, steps: int | None = None) -> dict[str, int | bool]:
    cfg = TrajectoryAddressConfig(width=width)
    n = width if steps is None else steps
    if n > width:
        raise ValueError("steps cannot exceed width for arbitrary exact recovery")

    seen: set[int] = set()
    decode_failures = 0

    for value in range(1 << n):
        bits = int_to_bits(value, n)
        final_state, count = encode_trajectory_address(bits, cfg)
        if count != n:
            raise AssertionError("step count mismatch")
        seen.add(final_state)
        if decode_trajectory_address(final_state, n, cfg) != bits:
            decode_failures += 1

    total = 1 << n
    return {
        "width": width,
        "steps": n,
        "trajectories": total,
        "unique_states": len(seen),
        "collisions": total - len(seen),
        "decode_failures": decode_failures,
        "injective": len(seen) == total,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--widths", type=int, nargs="+", default=[8, 12, 16])
    args = parser.parse_args()

    print("width,steps,trajectories,unique_states,collisions,decode_failures,injective")
    for width in args.widths:
        r = scan(width)
        print(
            f"{r['width']},{r['steps']},{r['trajectories']},{r['unique_states']},"
            f"{r['collisions']},{r['decode_failures']},{r['injective']}"
        )


if __name__ == "__main__":
    main()

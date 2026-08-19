from __future__ import annotations

import argparse
import time

from trajectory_generator import decode_mitm, encode_bits, int_to_bits


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bits", type=int, default=22)
    parser.add_argument("--value", type=int, default=None)
    args = parser.parse_args()

    n = args.bits
    if n < 0:
        raise SystemExit("--bits must be non-negative")

    value = args.value if args.value is not None else ((1 << n) - 3 if n else 0)
    if value < 0 or value >= (1 << n if n else 1):
        raise SystemExit("--value does not fit --bits")

    bits = int_to_bits(value, n)
    final_state, steps = encode_bits(bits)

    start = time.perf_counter()
    result = decode_mitm(final_state, steps, max_matches=2)
    elapsed = time.perf_counter() - start

    print("method:", result.method)
    print("steps:", steps)
    print("final_state:", final_state)
    print("searched_half_candidates:", result.searched)
    print("unique:", result.unique)
    print("recovered_value:", int("".join(map(str, result.bits or [])), 2) if result.bits else 0)
    print("matches_original:", result.bits == bits)
    print("elapsed_seconds:", f"{elapsed:.6f}")


if __name__ == "__main__":
    main()

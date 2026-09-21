"""Acceptance gate for the algebraic root trajectory construction."""

from math import comb, factorial, log2
import itertools
import random

from trajectory_generator.algebraic_root_trajectory import (
    decode,
    encode,
    pack_state,
    state_width_bits,
)


REFERENCE_PRIMES_K5 = {
    # Largest primes found below the p**5 <= 2**W packing limit.
    63: 6203,
    128: 50858999,
    256: 2586638741762807,
    512: 6690699980388625489511488543441,
}


def sparse_family_size(steps, k):
    return sum(comb(steps, j) for j in range(k + 1))


def optimal_sparse_frontier(width, k):
    cap = 1 << width
    lo, hi = 0, 1
    while sparse_family_size(hi, k) <= cap:
        hi *= 2
    while lo + 1 < hi:
        mid = (lo + hi) // 2
        if sparse_family_size(mid, k) <= cap:
            lo = mid
        else:
            hi = mid
    return lo


def exhaustive_gate(p=17, k=3, steps=10):
    seen = set()
    checked = 0
    for count in range(k + 1):
        for positions in itertools.combinations(range(steps), count):
            bits = [0] * steps
            for i in positions:
                bits[i] = 1
            state = encode(bits, k, p)
            packed = pack_state(state, p)
            if packed in seen:
                return False, checked, "endpoint collision"
            seen.add(packed)
            if decode(state, steps, p) != bits:
                return False, checked, "decode mismatch"
            checked += 1
    return True, checked, None


def randomized_gate(p, k, steps, cases=64, seed=0xC0FFEE):
    rng = random.Random(seed)
    for case in range(cases):
        count = rng.randrange(k + 1)
        positions = rng.sample(range(steps), count)
        bits = [0] * steps
        for i in positions:
            bits[i] = 1
        state = encode(bits, k, p)
        if decode(state, steps, p) != bits:
            return False, case
    return True, cases


def main():
    ok, checked, error = exhaustive_gate()
    print(
        "ALGEBRAIC_ROOT_EXHAUSTIVE",
        "PASS", ok,
        "checked", checked,
        "error", error,
    )

    p63 = REFERENCE_PRIMES_K5[63]
    ok, checked = randomized_gate(p63, 5, p63 - 1)
    print(
        "ALGEBRAIC_ROOT_63BIT",
        "PASS", ok,
        "cases", checked,
        "K", 5,
        "p", p63,
        "T", p63 - 1,
        "width", state_width_bits(5, p63),
    )

    print(
        "ASYMPTOTIC_REDUNDANCY",
        "K", 5,
        "log2(K!)", log2(factorial(5)),
        "interpretation", "constant bits for fixed K",
    )

    for width, p in REFERENCE_PRIMES_K5.items():
        root_frontier = p - 1
        optimal = optimal_sparse_frontier(width, 5)
        print(
            "ALGEBRAIC_ROOT_CAPACITY",
            "W", width,
            "K", 5,
            "p", p,
            "packed_width", state_width_bits(5, p),
            "root_frontier", root_frontier,
            "optimal_sparse_frontier", optimal,
            "frontier_ratio", root_frontier / optimal,
        )


if __name__ == "__main__":
    main()

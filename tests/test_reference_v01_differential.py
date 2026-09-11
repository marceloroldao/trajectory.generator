from __future__ import annotations

import random

from trajectory_generator.reference_v01 import count, rank, unrank, append, access
from experiments.joint_dyadic_address import (
    total_count as oracle_count,
    rank_forest as oracle_rank_forest,
    unrank_forest as oracle_unrank_forest,
    append_joint as oracle_append,
    joint_bit_at as oracle_access,
)
from experiments.dyadic_online_forest import build_forest
from experiments.standalone_four_bit_codec import initial_private, allowed, step


def oracle_rank(path):
    prefix = (path[0] << 2) | (path[1] << 1) | path[2]
    _, _, forest = build_forest(path[:3], path[3:])
    return oracle_rank_forest(prefix, forest, len(path) - 3)


def oracle_unrank(address, T):
    prefix, forest = oracle_unrank_forest(address, T)
    out = [(prefix >> 2) & 1, (prefix >> 1) & 1, prefix & 1]
    for k in range(T):
        out.append(oracle_access(address, T, k)[0])
    return out


def test_counts_and_frontier():
    for T in range(0, 40):
        assert count(T) == oracle_count(T)
    assert count(218) == 9131204053820206208
    assert count(219) == 10214739716735776832
    assert count(218).bit_length() == 63
    assert count(219).bit_length() == 64


def test_exhaustive_small_roundtrip_and_oracle():
    for T in range(0, 9):
        n = count(T)
        for address in range(n):
            path = unrank(address, T)
            assert rank(path) == address
            assert oracle_rank(path) == address
            assert oracle_unrank(address, T) == path
            for k in range(T):
                assert access(address, T, k) == path[k + 3]
                assert access(address, T, k) == oracle_access(address, T, k)[0]


def test_random_large_differential():
    rng = random.Random(20260910)
    for T in (16, 64, 128, 218):
        n = count(T)
        for _ in range(40):
            address = rng.randrange(n)
            path = unrank(address, T)
            assert rank(path) == address
            assert oracle_rank(path) == address
            assert oracle_unrank(address, T) == path
            for _ in range(min(12, T)):
                k = rng.randrange(T)
                assert access(address, T, k) == path[k + 3]
                assert access(address, T, k) == oracle_access(address, T, k)[0]


def test_append_matches_oracle_and_direct_rank():
    rng = random.Random(20260910)
    for T in (0, 1, 2, 7, 16, 64, 127, 128, 217):
        n = count(T)
        for _ in range(min(30, n)):
            address = rng.randrange(n)
            path = unrank(address, T)
            prefix = (path[0] << 2) | (path[1] << 1) | path[2]
            p = initial_private(prefix)
            for t, z in enumerate(path[3:]):
                p = step(p, z, t % 3)
            for z in (0, 1):
                if not allowed(p, z, T % 3):
                    continue
                got = append(address, T, z)
                assert got == oracle_append(address, T, z)
                assert got == rank(path + [z])

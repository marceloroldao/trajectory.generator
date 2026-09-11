from __future__ import annotations

from hashlib import sha256
import random
import pytest

from trajectory_generator.reference_v01 import (
    count, rank, unrank, append, access, initial_private, allowed, step
)

# Immutable address-order vectors for the frozen v0.1 baseline.
# digest = sha256(ASCII bitstring of 3-bit prefix + T labels)
CANONICAL = [
    (0, 0, "2ac9a6746aca543af8dff39894cfe8173afba21eb01c6fae33d52947222855ef", []),
    (1, 0, "9af15b336e6a9619928537df30b2e6a2376569fcf9d7e773eccede65606529a0", [(0,0)]),
    (1, 7, "ab9828ca390581b72629069049793ba3c99bb8e5e9e7b97a55c71957e04df9a3", [(0,0)]),
    (8, 0, "88429df6e488a3bcf18d036f3c75091f6f1bd91fed938d3472df1983c3496c5f", [(0,0),(2,1),(4,0),(5,0),(7,0)]),
    (8, 31, "a12ef6e8355c73c0c42150bf054660b8665e96e739750c947d2ea7c87da00fb9", [(0,0),(2,0),(4,0),(5,1),(7,0)]),
    (16, 4, "97aaf7bec59d9c2fd206e526e56a2a1197fe0637f13759690776fce8ab518f12", [(0,0),(5,0),(8,0),(10,1),(15,0)]),
    (64, 319527, "083f47b079a0fdd05ee49c853ddf74532d05e31e4b59a1cc39490f96cd985001", [(0,0),(21,0),(32,0),(42,0),(63,1)]),
    (128, 387231520800, "0f48796153e1c69766d1bcfe375fb370619790260a609fbbb55644ca2159b086", [(0,0),(42,1),(64,1),(85,1),(127,0)]),
    (218, 0, "cf8db6ce1806da189dab8a2a1e93ac0206fcd63755b9fb9936208bd6efe752f2", [(0,0),(72,0),(109,0),(145,0),(217,0)]),
    (218, 81985529216486895, "eb20dc60047816daee0b3ac839068f6b03660c900e3666e980ffd1a248ddccc3", [(0,0),(72,0),(109,0),(145,0),(217,0)]),
    (218, 9131204053820206207, "6ba0265f753390079a52d08c60895ef1f518129dd45754c9c0ecb4772c768760", [(0,0),(72,0),(109,1),(145,0),(217,0)]),
]


def digest_path(path):
    return sha256("".join(map(str, path)).encode("ascii")).hexdigest()


def test_canonical_address_order_vectors():
    for T, address, expected_digest, probes in CANONICAL:
        path = unrank(address, T)
        assert len(path) == T + 3
        assert digest_path(path) == expected_digest
        assert rank(path) == address
        for k, bit in probes:
            assert access(address, T, k) == bit


def test_invalid_inputs_and_boundaries():
    with pytest.raises(ValueError): count(-1)
    with pytest.raises(ValueError): unrank(-1, 0)
    with pytest.raises(ValueError): unrank(count(8), 8)
    with pytest.raises(ValueError): rank([0, 1])
    with pytest.raises(ValueError): rank([0, 0, 0, 2])
    with pytest.raises(IndexError): access(0, 0, 0)
    with pytest.raises(IndexError): access(0, 8, -1)
    with pytest.raises(IndexError): access(0, 8, 8)
    with pytest.raises(ValueError): append(0, 0, 2)


def test_inadmissible_transition_rejected():
    # Find a reachable one-step prefix with a forbidden alternative and require
    # both direct ranking and append to reject that transition.
    for s in range(8):
        p = initial_private(s)
        forbidden = [z for z in (0,1) if not allowed(p,z,0)]
        if forbidden:
            prefix=[(s>>2)&1,(s>>1)&1,s&1]
            a=rank(prefix)
            z=forbidden[0]
            with pytest.raises(ValueError): rank(prefix+[z])
            with pytest.raises(ValueError): append(a,0,z)
            return
    raise AssertionError("expected at least one forbidden initial transition")


def test_frontier_stress_218():
    rng=random.Random(20260911)
    T=218; n=count(T)
    fixed=[0,1,n//4,n//2,(3*n)//4,n-2,n-1]
    addresses=fixed+[rng.randrange(n) for _ in range(121)]
    probes=(0,1,17,63,72,109,145,200,217)
    for a in addresses:
        path=unrank(a,T)
        assert rank(path)==a
        for k in probes:
            assert access(a,T,k)==path[k+3]


def test_append_chain_stress():
    rng=random.Random(20260911)
    for _ in range(32):
        s=rng.randrange(8)
        path=[(s>>2)&1,(s>>1)&1,s&1]
        a=rank(path)
        p=initial_private(s)
        for t in range(64):
            choices=[z for z in (0,1) if allowed(p,z,t%3)]
            z=rng.choice(choices)
            a=append(a,t,z)
            path.append(z)
            assert a==rank(path)
            p=step(p,z,t%3)

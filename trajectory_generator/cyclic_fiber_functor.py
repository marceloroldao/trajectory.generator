"""Functorial compatibility test for cyclic-group fiber structure.

A previous conditional result shows that inversion y -> -y is natural under
all automorphisms of a declared cyclic group Z_n.

For that structure to be intrinsic to the *dynamics*, not merely attached to
each fiber independently, causal edge injections should preserve the declared
structure.

For finite cyclic groups, an injective group homomorphism

    Z_n -> Z_m

exists iff n divides m.

Proof sketch:
- the image of a generator must have order n in Z_m;
- Z_m contains an element of order n iff n divides m.

The same divisibility condition is necessary for affine maps between cyclic
torsors whose linear part is injective.

Therefore any causal edge whose nonempty source fiber has size n and target
fiber has size m with n not dividing m is a certificate that the family of
cyclic groups cannot form a group-homomorphic fiber functor along every causal
transition.

This does not invalidate cyclic structure as a per-fiber gauge convention. It
rules out the stronger claim that the current causal embeddings canonically
preserve Z_n group structure.
"""

from __future__ import annotations


def cyclic_injection_homomorphism_exists(
    source_size: int,
    target_size: int,
) -> bool:
    if source_size < 1 or target_size < 1:
        raise ValueError("group sizes must be >= 1")
    return target_size % source_size == 0


def cyclic_torsor_affine_injection_possible(
    source_size: int,
    target_size: int,
) -> bool:
    """Necessary/sufficient cardinality condition for injective affine linear part."""
    return cyclic_injection_homomorphism_exists(
        source_size,
        target_size,
    )


def first_divisibility_obstruction(
    sizes: tuple[tuple[int, int], ...],
) -> tuple[int, int] | None:
    for source_size, target_size in sizes:
        if not cyclic_injection_homomorphism_exists(
            source_size,
            target_size,
        ):
            return source_size, target_size
    return None

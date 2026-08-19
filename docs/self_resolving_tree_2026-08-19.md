# Self-resolving trajectory tree — 2026-08-19

Status: pre-alpha experimental result

## Question

Can a trajectory tree be discovered deterministically from the trajectory itself, while the decoder still receives only `(final_state, steps)` and no external tree metadata?

## Canonical rule

A block is a **leaf** if at least one public recursive-relation level in `0..max_level` has at most `max_deviations` non-root deviations.

If no such leaf description exists, the block is split at the public midpoint and the same rule is applied recursively to both children.

This makes the tree canonical for the public configuration.

## Address layout

Leaf and split nodes occupy disjoint numeric ranges.

For a block of length `n`:

```text
A(n) = L(n) + A(floor(n/2)) * A(ceil(n/2))
```

where `L(n)` is the full leaf-address envelope across all allowed relation levels.

A decoder can therefore determine whether the root is a leaf or split by the numeric range of the recovered rank. If split, the child pair is recovered by mixed-radix division. No cut positions or level list are supplied externally.

The count is conservative: split ranges include some codes whose reconstructed sequence would also have been leaf-admissible. The canonical encoder never emits those duplicate structural descriptions, but they still consume envelope space. Capacity claims are therefore safe, not optimistic.

## Default capacity

Configuration:

```text
state width     = 63 bits
max deviations  = 5
relation levels = 0..3
split rule      = public midpoint
```

The conservative envelope gives:

```text
20 steps: fits in 2^63
21 steps: exceeds 2^63
```

So the current fully recursive self-resolving construction has a conservative frontier of **20 steps**.

This is much smaller than the one-level dyadic model because every node reserves both a complete leaf region and a complete recursive Cartesian-product split region.

## Structural witness

The 20-bit trajectory

```text
10001001001110101011
```

has global non-root deviation counts across levels 0..3 of:

```text
9, 12, 9, 12
```

so it is not a valid global leaf under `K=5`.

Its first half has counts:

```text
2, 5, 5, 8
```

and its second half:

```text
6, 6, 3, 4
```

so both midpoint children are independently leaf-admissible, at different relational depths. The canonical encoder therefore splits the root and the decoder reconstructs that split from the address range itself.

## Interpretation

This experiment demonstrates that a **data-dependent canonical tree can be reconstructed without external cut metadata**. However, a fully recursive union of leaf and split families has a severe address-space cost.

The important negative result is:

> making structure discoverable is not free; a generic recursive grammar can consume more information describing its admissible possibilities than it saves on the trajectories it explains.

The next research direction should therefore reduce the grammar itself. Promising options include deterministic split triggers derived from invariant properties, restricted tree depths, or a learned/public grammar whose branch possibilities are much smaller than the full Cartesian product.

## Reproduction

```bash
python -m unittest tests.test_self_resolving_tree -v
```

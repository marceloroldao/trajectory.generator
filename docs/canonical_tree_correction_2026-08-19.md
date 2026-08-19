# Canonical self-resolving tree correction — 2026-08-19

Status: methodological correction / pre-alpha

## What changed

The first self-resolving-tree report used the conservative numeric recurrence

```text
E(n) = LeafRange(n) + E(floor(n/2)) * E(ceil(n/2))
```

as if it were also the number of distinct admissible trajectories.

That interpretation is too pessimistic.

The split product contains many trajectories that are already representable as a
leaf. The canonical encoder never emits those duplicate split representations, but
the simple numeric layout reserves space for them anyway.

Therefore two different quantities must be kept separate:

1. **semantic family size** — number of distinct input trajectories admitted;
2. **address envelope size** — number of numeric codes reserved by the current layout.

## Exact semantic family for unrestricted recursion

The current canonical rule is:

```text
if a block is leaf-admissible:
    encode as leaf
else:
    split at the public midpoint and recurse
```

Recursion is allowed all the way down to blocks of length 1.

Every length-1 binary block is leaf-admissible. Consequently, every finite binary
sequence can always be recursively split until all leaves have length 1.

Hence, for a trajectory of fixed length `n`, the exact semantic family is

```text
S(n) = 2^n.
```

This is not an empirical observation; it follows directly from the construction.

## Consequence for a 63-bit final state

For arbitrary binary trajectories:

```text
S(n) = 2^n <= 2^63
```

holds only for

```text
n <= 63.
```

Therefore the unrestricted self-resolving tree does **not** create a constrained
low-entropy family for `n > 63`. It eventually admits every arbitrary bit string.

The previously reported 20-step frontier is only the frontier of the redundant
address layout `E(n)`, not an information-theoretic frontier of the canonical tree.

## Why this correction matters

This result exposes a general design rule:

> A recursive structural model only buys capacity beyond raw state width when the
> recursion itself is constrained strongly enough that not every arbitrary sequence
> remains admissible.

If every difficult block is allowed to split until single-bit leaves, the model has
full arbitrary-data entropy again.

## Next experiment

The next useful family should constrain at least one of:

- maximum tree depth;
- minimum leaf size;
- public split schedule;
- admissibility invariant that can reject branches rather than merely subdivide them.

Such a restriction can produce a true structured family with entropy below `n` while
still allowing the decoder to reconstruct structure from `(final_state, steps)` and
public rules.

## Reproduction

```bash
python experiments/canonical_tree_count.py --max-bits 24
```

The script prints both the exact semantic family `2^n` and the conservative numeric
envelope used by the current implementation.

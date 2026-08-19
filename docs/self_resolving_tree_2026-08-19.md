# Self-resolving trajectory tree — 2026-08-19

Status: pre-alpha experimental result

> **Methodological correction:** the previously reported 20-step frontier is the frontier of the current **redundant numeric address envelope**, not the information-theoretic size of the semantic trajectory family. Because unrestricted recursion may continue down to length-1 leaves, every binary sequence is eventually admissible; the exact semantic family at fixed length `n` is therefore `2^n`. See `docs/canonical_tree_correction_2026-08-19.md`.

## Question

Can a trajectory tree be discovered deterministically from the trajectory itself, while the decoder still receives only `(final_state, steps)` and no external tree metadata?

## Canonical rule

A block is a **leaf** if at least one public recursive-relation level in `0..max_level` has at most `max_deviations` non-root deviations.

If no such leaf description exists, the block is split at the public midpoint and the same rule is applied recursively to both children.

This makes the tree canonical for the public configuration.

## Address layout

Leaf and split nodes occupy disjoint numeric ranges.

For a block of length `n`, the current implementation reserves the conservative envelope

```text
E(n) = L(n) + E(floor(n/2)) * E(ceil(n/2))
```

where `L(n)` is the full leaf-address envelope across all allowed relation levels.

A decoder can therefore determine whether the root is a leaf or split by the numeric range of the recovered rank. If split, the child pair is recovered by mixed-radix division. No cut positions or level list are supplied externally.

The count is deliberately conservative: split ranges include many codes whose reconstructed sequence would already have been leaf-admissible. The canonical encoder never emits those duplicate structural descriptions, but the simple numeric layout still reserves space for them.

## Two different capacities

These quantities must not be conflated.

### 1. Semantic family size

Because recursion is unrestricted down to blocks of length 1, and every binary length-1 block is leaf-admissible, **every binary trajectory is eventually accepted**.

Therefore:

```text
S(n) = 2^n
```

for the unrestricted self-resolving grammar.

For a 63-bit final state, arbitrary exact addressing of this semantic family is possible only while:

```text
n <= 63.
```

### 2. Current numeric envelope

The present leaf/split mixed-radix layout over-reserves address space. With the default configuration:

```text
state width     = 63 bits
max deviations  = 5
relation levels = 0..3
split rule      = public midpoint
```

its redundant envelope gives:

```text
20 steps: fits in 2^63
21 steps: exceeds 2^63
```

Thus **20 steps is only an implementation-envelope frontier**, not a fundamental capacity frontier of the canonical rule.

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

so both midpoint children are independently leaf-admissible, at different relational depths. The canonical tree therefore splits the root for this trajectory.

## Interpretation

The experiment demonstrates that a **data-dependent canonical tree can be reconstructed without external cut metadata**. The correction shows something equally important:

> unrestricted recursive subdivision does not by itself create a low-entropy family; if every difficult block may keep splitting until atomic leaves, the grammar eventually admits all arbitrary bit strings.

Therefore a trajectory grammar can support `steps > width` only if it genuinely rejects enough trajectories. Useful restrictions include:

- bounded tree depth;
- minimum leaf size;
- restricted public split schedules;
- an invariant that rejects a branch rather than merely subdividing it.

A depth-bounded frontier experiment is available in `experiments/bounded_tree_frontier.py`.

## Reproduction

```bash
python experiments/canonical_tree_count.py --max-bits 24
python experiments/bounded_tree_frontier.py --width 63 --max-tree-depth 4
python -m unittest tests.test_self_resolving_tree -v
```

# Recursive trajectory relations — 2026-08-19

Status: pre-alpha constructive experiment

## Question

Can a long structured trajectory become sparse only after describing relations among relations, rather than in a single coordinate basis?

## Construction

The recursive machine applies the same invertible local relation transform repeatedly.

For a binary sequence `b`:

```text
L0 = b
L1[i] = L0[i] XOR L0[i-1]
L2[i] = L1[i] XOR L1[i-1]
...
```

The root coefficient is retained at every level, making each transformation bijective. Decoding applies the inverse relation transform the same number of times.

The encoder evaluates public levels `0..max_level`, selects the admissible level with the fewest non-root deviations, ranks that sparse coefficient vector combinatorially, and encodes the selected level inside the final state. The decoder still receives only:

```text
(final_state, steps)
```

plus the public machine definition.

## Pattern-of-pattern examples

For 32-bit examples under repeated local relations:

| trajectory | L0 non-root ones | L1 | L2 | L3 | best level |
|---|---:|---:|---:|---:|---:|
| `0101...` alternating | 16 | 31 | 1 | 2 | L2 |
| `00110011...` | 16 | 15 | 30 | 1 | L3 |
| `00001111...` | 16 | 7 | 14 | 14 | L1 |

The first two examples are the key result: they are not sparse in the original sequence and are not sparse after one local-difference layer, yet become nearly trivial after deeper relation layers.

This is a concrete instance of:

```text
state -> relation -> relation of relations -> relation of relations of relations
```

## Capacity accounting

Each recursive level is a separate admissible family. With `max_level = 3`, four public families must fit into one fixed-width final-state address space.

For each level, with trajectory length `n` and at most `K` non-root deviations:

```text
F(n,K) = 2 * sum(C(n-1,j), j=0..K)
```

The conservative union envelope used by the implementation is:

```text
R(n,K,L) = (L+1) * F(n,K)
```

where `L=max_level`.

For the default experiment:

```text
width = 63
K = 5
max_level = 3
```

the conservative full-family capacity frontier is:

```text
10,672 steps: fits
10,673 steps: exceeds 2^63
```

This frontier is smaller than the single-level hierarchical model because the address space reserves disjoint buckets for four representations. The benefit is not increased raw capacity; it is increased structural coverage.

## Interpretation

The recursive construction supports a stronger version of the trajectory hypothesis:

> information can reside not only in transitions between states, but in higher-order relations among those transitions.

However, the result remains enumerative coding of constrained low-entropy families. It is not arbitrary-data compression and does not violate fixed-state information bounds.

## Reproduction

```bash
python experiments/recursive_compare.py
python -m unittest tests.test_recursive_trajectory -v
```

## Next research direction

1. Replace the fixed set of whole-sequence levels with an adaptive tree where different blocks may stop at different depths.
2. Account exactly for the tree description cost, including branch/stop decisions.
3. Compare against standard run-length, delta, grammar, and LZ-style descriptions on synthetic trajectory families.
4. Test whether recursive relation trees provide a useful address for sensor/control streams, where long temporal traces often have low structural entropy.
5. Keep preferred constants such as phi out of the generator; any scale ratio must emerge from measured optimal tree structures rather than being inserted.

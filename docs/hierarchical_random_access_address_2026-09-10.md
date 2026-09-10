# Hierarchical random-access trajectory address — 2026-09-10

## Objective

Test whether a trajectory symbol `z_k` can be recovered from a final reversible address and the trajectory length without reconstructing all earlier/later symbols.

## Negative result for the existing endpoint/colex rank

The current horizon-free endpoint rank orders histories recursively by final state and immediate predecessor blocks. Multi-step composition does **not** preserve contiguity by midpoint state.

Experiment: `experiments/random_access_block_structure.py`.

The first counterexample appears already at `T=5`: the same midpoint state occupies two disjoint rank intervals. Therefore state-only binary lifting cannot be applied directly to the existing endpoint rank.

This is a structural property of the current ordering, not a failure of the underlying trajectory language.

## Hierarchical rank

A second address ordering was introduced in `experiments/hierarchical_random_access_address.py`.

For any segment `[l,r]`, let

```
m = floor((l+r)/2)
```

Paths are grouped first by the private state at the midpoint `P_m`. For each midpoint state, the number of complete segment paths is

```
L(P_m) * R(P_m)
```

where `L` is the number of valid left-half paths into the midpoint and `R` is the number of valid right-half paths out of the midpoint.

Inside a midpoint block, the pair of subranks is encoded by

```
rank = offset(P_m) + left_rank * R(P_m) + right_rank
```

The same construction is applied recursively to both halves.

## Exact language preservation

The hierarchical ordering changes only the enumeration of trajectories. It does not change the admissible language.

Exact counts were verified for every `T=0..218` against the existing public-field count implementation.

At the 63-bit frontier:

```
N(218) = 9,131,204,053,820,206,208
N(219) = 10,214,739,716,735,776,832
```

Hence the boundary remains exactly 218 physical transitions and the rank at `T=218` still requires 63 bits.

## Random access

Given only

```
(rank, T, k)
```

`bit_at()` descends only the half containing transition `k`.

Validation:

- exhaustive rank/unrank and direct-symbol checks for `T=0..8`;
- 200 random ranks per horizon for `T=16,64,128,200,218`;
- 8 random symbol positions per rank;
- 1,600 direct-symbol checks at each large horizon;
- zero mismatches.

Observed maximum recursive decision levels:

```
T=16   -> 5
T=64   -> 7
T=128  -> 8
T=200  -> 9
T=218  -> 9
```

Thus symbol access requires logarithmic-depth descent in the rank tree. The current exact segment-count oracle uses cached 16-state periodic transition matrices. Cold arithmetic includes matrix-power work; repeated queries reuse the public interval matrices.

## Two complementary addresses

The project now has two exact reversible enumerations of the same trajectory language.

### Endpoint / colex rank

Strengths:

- address evolves online as the trajectory happens;
- no final horizon is needed during encoding;
- natural reverse sequential decoding.

Weakness:

- midpoint-state blocks are not contiguous after multiple reverse steps;
- direct random access is not naturally logarithmic.

### Hierarchical rank

Strengths:

- exact random access to `z_k` by logarithmic-depth descent;
- exact rank/unrank;
- same 63-bit capacity frontier.

Weakness:

- rank is hierarchical and is not yet known to admit the same simple online accumulation law as the endpoint rank.

## Interpretation

The result separates two properties that should not be conflated:

1. **online-emergent addressability**;
2. **random-access addressability**.

Both can represent the same admissible trajectory set in 63 bits at `T=218`, but they induce different coordinate systems over that set.

A useful next problem is to determine whether a single coordinate system can satisfy both contracts simultaneously, or whether a reversible conversion between endpoint rank and hierarchical rank can be computed substantially faster than full trajectory reconstruction.

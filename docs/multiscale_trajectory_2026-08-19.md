# Multi-scale trajectory tree — 2026-08-19

Status: pre-alpha constructive experiment  
RSMS compatibility: pending central specification mapping

## Objective

Test whether a trajectory that is complex under one relation can become sparse under another public hierarchical relation, while preserving exact recovery from only:

1. `final_state`; and
2. `steps`.

No trajectory log, checksum, plaintext hint, or external scale selector is supplied to the decoder.

## Construction

`trajectory_generator/multiscale_trajectory.py` currently defines two public relation bases.

### Local basis

For `i > 0`:

```text
c_i = b_i XOR b_(i-1)
```

The non-root coefficient records an ordinary adjacent change.

### Fenwick/tree basis

For `i > 0`, define:

```text
parent(i) = i - lowbit(i)
```

where `lowbit(i)` is the least significant set bit of `i`. Then:

```text
c_i = b_i XOR b_parent(i)
```

This compares a state with a hierarchical ancestor rather than only its immediate predecessor.

Both transforms are exactly invertible because every parent index is smaller than its child index.

The encoder evaluates all configured public modes and chooses the one with the fewest non-root deviations. The mode itself is encoded inside the trajectory address as a rank bucket; the decoder receives no additional mode metadata.

## Example: scale changes the apparent complexity

For the 32-step trajectory

```text
00001111000011110000111100001111
```

the local representation has:

```text
7 adjacent changes
```

while the Fenwick/tree representation has:

```text
4 hierarchical deviations
```

With a public budget `K = 5`, the local-only model rejects this trajectory but the multi-scale model admits it through the hierarchical basis.

This is the key positive result of the experiment: structural simplicity depends on which relation is treated as primary.

## Capacity accounting

For one mode, with trajectory length `n` and at most `K` non-root deviations, the address family envelope is

```text
2 * sum(C(n-1, j), j=0..K)
```

for non-empty trajectories.

With two public modes, the implementation conservatively reserves two complete rank buckets. This avoids hidden side information but costs approximately one bit of address capacity.

For:

```text
width = 63
K = 5
modes = {local, fenwick}
```

the conservative capacity frontier is:

```text
12,259 steps : fits
12,260 steps : exceeds 2^63 envelope
```

For comparison, the single local relational model with the same `width=63, K=5` reaches 14,082 steps. The multi-scale model therefore does not improve raw family capacity; it broadens the kinds of structured trajectories representable under the same deviation budget.

## Interpretation

This result supports a more precise version of the trajectory hypothesis:

> Information structure is not determined only by states or by adjacent transitions; it can depend on the relational scale used to connect states across the trajectory.

The gain is not arbitrary compression. The multi-scale encoder spends address capacity to represent which relation basis made the trajectory sparse.

A useful architecture must therefore be evaluated on at least two axes:

1. **capacity** — how many admissible trajectories fit in the final state;
2. **coverage** — which structural trajectory families are admitted at a given complexity budget.

The Fenwick mode improves coverage for some repeated/block patterns, but the current two-mode envelope reduces maximum length relative to the local-only constrained family.

## Validation status

Independent checks performed during development confirmed:

- `transform -> inverse_transform` round-trips for multiple lengths and patterns;
- the 32-step block example has local deviation count 7 and Fenwick deviation count 4;
- the 63-bit/two-mode/K=5 capacity boundary is 12,259 / 12,260 steps.

Automated tests are included in `tests/test_multiscale_trajectory.py`.

The current execution environment could not clone GitHub due DNS/network resolution, so the full repository unit suite was not rerun locally in this session. This limitation is recorded rather than silently omitted.

## Next experiments

1. Add additional public tree bases only if they increase coverage enough to justify their address-bucket cost.
2. Measure representation sparsity over synthetic families: runs, periodic blocks, nested blocks, sparse impulses, and recursively generated sequences.
3. Replace fixed mode buckets with an exact union-ranking scheme to avoid wasting addresses on trajectories admissible in more than one basis.
4. Investigate recursive model selection: a coarse relation selects a basis for a sub-block, creating an actual tree of trajectory descriptions.
5. Compare all gains against explicit entropy bounds; no claim should rely on encoding more arbitrary information than the final state can hold.
6. Continue emergence analysis without placing phi or other preferred irrational constants into the generator.

# Intrinsic phase-reflection vertical gauge — 2026-09-20

## Result

After the general minimal reversible-completion gate established that internal vertical permutations are gauge freedom, the previous phase/merge law was simplified.

The new intrinsic vertical permutation is:

```text
sigma(t) = (-1)^(t mod P)
b        = 0

local' = sigma(t) * y mod |F(source,t)|
```

For the current topological universes:

```text
P = 3
```

So the internal orientation pattern is:

```text
phase 0 -> +1
phase 1 -> -1
phase 2 -> +1
```

No incoming-edge index, outgoing-edge index, graph-degree value, arbitrary coefficient, random seed, or trajectory-specific state enters the internal permutation.

## What still uses predecessor blocks

Exact reverse recovery still requires the target fiber to be partitioned by the unique final causal edge.

That partition is invariant in cardinality:

```text
|Image_t(e:u->v)| = |F_t(u)|
```

When the lifted state is serialized as one integer, those tagged edge blocks require some deterministic packing order. `incoming_offset` provides that chart convention.

The distinction is now explicit:

```text
intrinsic vertical dynamics:
    phase reflection only

integer chart / serialization:
    ordered predecessor blocks
```

Thus predecessor ordering is no longer part of the internal vertical law.

## Executed gate

GitHub Actions run:

```text
35554636742
workflow: reversible-pipeline-gate
conclusion: success
```

The complete workflow passed, including the general reversible-completion and natural-extension gauge gates.

### robust_208

```text
frontier                         208
frontier family                  8,484,982,157,878,442,411
small addresses checked          288
small mapping changes            263
frontier samples                 5
frontier mapping changes         5
exhaustive roundtrip             true
frontier roundtrip               true
decode inputs                    (final_state,steps)+public_law_only
```

### balanced_221

```text
frontier                         221
frontier family                  9,131,204,053,820,206,208
small addresses checked          270
small mapping changes            246
frontier samples                 5
frontier mapping changes         5
exhaustive roundtrip             true
frontier roundtrip               true
```

### long_239

```text
frontier                         239
frontier family                  8,736,326,121,603,609,111
small addresses checked          234
small mapping changes            213
frontier samples                 5
frontier mapping changes         5
exhaustive roundtrip             true
frontier roundtrip               true
```

## Interpretation

The phase-reflection gauge changes the trajectory represented by a given final integer in most tested small states and in all five sampled frontier states for every candidate.

Yet reverse and replay remain exact.

Therefore the vertical coordinate is dynamically active even without a predecessor-index rotation.

## Relation to the natural extension

The coordinate-free invariant object is the admissible history space.

The phase-reflection coordinate is one chart on that space. The previous static rank and phase/merge coordinates are other charts.

They are related by time-dependent fiber bijections and satisfy the gauge-conjugacy equation:

```text
G_(t+1) o F_e = F'_e o G_t
```

Thus the current preferred interpretation is:

```text
invariant:
    admissible history state
    causal projection
    fiber cardinalities
    predecessor-edge partition sizes

gauge choice:
    numerical vertical coordinate
    internal permutation
    integer block ordering
```

## Why phase reflection is preferred now

It is not claimed to be uniquely forced by reversibility.

It is preferred as the current reference gauge because it is:

- nontrivial;
- reversible for every positive fiber size;
- coefficient-free;
- periodic with the smallest existing public causal period;
- independent of predecessor ordering in its internal permutation;
- compatible with final-state-only recovery.

## Remaining question

The remaining mathematical problem is no longer to discover a unique vertical permutation from reversibility alone; the general gate shows that such uniqueness does not exist whenever fibers have more than one state.

The next meaningful search is for extra principles that select a gauge up to symmetry, for example graph-relabeling equivariance, locality, minimum description length, or information-clock compatibility.

# Scalar partition reverse — 2026-09-20

## Result

The full endpoint-count vector is no longer required during trajectory reverse.

The integer address decoder needs only scalar partition questions:

```text
How many paths lie before this endpoint bucket?
How large is this incoming-edge block?
What is the public translation Delta(edge,t)?
```

Each answer is an integer linear functional of the public count field.

Because the count field obeys the compact phase/Floquet recurrence, every
partition-boundary scalar obeys the same recurrence.

## Direct scalar evaluation

For physical time

```text
t = P*q + r
```

the scalar oracle does not construct `D(.,t)`.

Instead it:

1. projects the requested scalar functional across the small phase offset `r`
   onto the base-phase Floquet slice;
2. generates the first `d` scalar seed values from the public P-step graph;
3. evaluates the q-th value using the shared Floquet recurrence.

The target-time full endpoint vector is never materialized.

## Hard gate

The experiment explicitly disables:

```text
field.vector_at(...)
```

inside the scalar decoder by replacing it with a function that raises an
exception.

The complete reverse must therefore succeed without using the target-time full
count-vector API.

GitHub Actions run:

```text
35552323533
workflow: reversible-pipeline-gate
conclusion: success
```

Executed results:

```text
robust_208
  PASS=True
  frontier=208
  count identity=True
  frontier path identity=True
  exhaustive low-horizon identity=True
  small addresses checked=2,255
  Floquet order=11
  base-phase states=16
  full_vector_api_disabled=True

balanced_221
  PASS=True
  frontier=221
  count identity=True
  frontier path identity=True
  exhaustive low-horizon identity=True
  small addresses checked=1,965
  Floquet order=8
  base-phase states=13
  full_vector_api_disabled=True

long_239
  PASS=True
  frontier=239
  count identity=True
  frontier path identity=True
  exhaustive low-horizon identity=True
  small addresses checked=1,956
  Floquet order=8
  base-phase states=12
  full_vector_api_disabled=True
```

The successful run used a bounded cache of only 32 scalar functional seed
sequences. A later performance-only gate increases this cache to avoid repeated
seed regeneration; correctness does not depend on the larger cache.

## Reverse path

The reverse machine is now conceptually:

```text
(final integer S_t, public t)
        |
        v
scalar endpoint boundaries from recurrence
        |
        v
current endpoint node
        |
        v
scalar incoming-edge boundaries from recurrence
        |
        v
previous public edge e
        |
        v
S_(t-1) = S_t - Delta(e,t-1)
```

No trajectory history table is consulted.

No `D(v,t)` vector is reconstructed at the queried time.

## Memory/CPU tradeoff

The scalar oracle intentionally exchanges some CPU for lower structural state.

A scalar boundary query regenerates recurrence seeds from the small public
Floquet graph unless its seed sequence is already in the bounded LRU cache.

This means:

- memory remains independent of trajectory horizon;
- a larger fixed cache improves speed;
- the cache contains public scalar law sequences, not trajectory-specific data.

## Significance

The support machinery has now been reduced in stages:

```text
O(V*T) time-indexed count table
        ->
fixed vector recurrence
        ->
phase/Floquet recurrence
        ->
scalar recurrent partition boundaries
```

The evolving trajectory state itself remains one integer address.

The remaining question is no longer whether the decoder needs a historical
count map. It does not.

The remaining conceptual question is whether the integer address should be
regarded as an explicitly constructed coordinate of the universe or whether a
future causal law can make this coordinate emerge directly from the causal
state geometry.

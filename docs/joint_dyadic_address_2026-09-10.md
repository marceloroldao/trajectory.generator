# Joint dyadic trajectory address — 2026-09-10

## Result

A single jointly ranked dyadic address now combines the three properties that had previously required separate representations:

1. online/causal update as the trajectory grows;
2. exact 63-bit worst-case capacity at T=218;
3. logarithmic-depth random access to an individual trajectory symbol.

## Why the previous dyadic serialization exceeded 63 bits

The first dyadic forest stored, for each block, a raw 4-bit endpoint plus a fixed-width local rank.  At T=218 the forest shape is:

`[128, 64, 16, 8, 2]`

The exact worst-case practical serialization reached 80 bits because endpoint identities and local ranks were encoded independently even though they are strongly correlated.

## Joint enumeration

For each dyadic block, endpoint choice and local rank are enumerated jointly.  Suffix dynamic programming counts how many complete valid forests continue from each block-boundary state.  The entire forest is then assigned one integer rank in `[0, N(T))`.

Therefore no independent endpoint fields are stored.  The number of addresses is exactly the number of admissible trajectories.

## Exact capacity

The implementation reproduced the original language counts for T=0..219:

- `N(218) = 9,131,204,053,820,206,208`, requiring 63 bits;
- `N(219) = 10,214,739,716,735,776,832`, requiring 64 bits.

Thus the exact frontier remains 218 transitions.

## Online update

Given the current joint address at time T and the next admissible label z:

1. unrank only the O(log T) dyadic forest boundary/rank chain;
2. append one length-1 block;
3. merge equal-size blocks by binary carry;
4. jointly rerank the resulting forest for T+1.

The full symbol trajectory is never reconstructed.

Random online-update validation passed for 100 trajectories at T=16, 64, 128, and 218.

## Random access

Given `(A_T, T, k)`, the joint address is first unranked into at most `popcount(T) <= O(log T)` dyadic blocks.  The block containing k is then descended hierarchically.

At T=218, with blocks `[128,64,16,8,2]`, sampled random access required at most 8 internal hierarchical levels and returned all tested symbols exactly.

## Interpretation

This is the first tested representation in the project that simultaneously achieves:

- a single exact integer trajectory coordinate;
- no future horizon needed during online growth;
- no separate trajectory map/history;
- exact 63-bit boundary at 218 transitions;
- random symbol access without reconstructing the whole trajectory.

The address is not a cryptographic hash.  It is a reversible rank of a constrained finite-state trajectory language.

## Next questions

The principal remaining optimization questions are computational rather than informational:

- reduce the cost of joint unrank/rerank during each online append;
- replace suffix dynamic programming with closed-form or matrix-power counts from the already-derived scalar public field;
- quantify asymptotic update/query complexity including big-integer arithmetic;
- test robustness of the unified coordinate across perturbed universes, not only the baseline `(0,2,4,4)` machine.

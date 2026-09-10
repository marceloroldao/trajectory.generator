# Scalar public-field collapse — 2026-09-09

## Result

The public 3-amplitude growth sector of the horizon-free address codec can be represented by a single scalar recurrence.

Define

```text
g_0 = 1
g_1 = 0
g_2 = 0
g_{n+3} = 2 g_{n+2} - g_{n+1} + g_n
```

Then the modal amplitudes are recovered exactly by

```text
a_n = g_n
c_n = g_{n+1}
b_n = g_{n+2} - 2 g_{n+1}
```

Hence the 3 live modal values are not independent state variables.

## Stronger consequence

Because `n = floor(t/3)` is public, `(a_n,b_n,c_n)` is a deterministic function of elapsed time and fixed universe rules. Therefore the public dynamic memory needed by the codec can be reduced, conceptually, to **time only**. The scalar recurrence can be evaluated incrementally or recomputed from `t`; no trajectory-dependent public field state needs to be stored.

The first scalar values are:

```text
1, 0, 0, 1, 2, 3, 5, 9, 16, 28, 49, 86, 151, ...
```

This is not the Fibonacci recurrence; its characteristic polynomial is

```text
x^3 - 2x^2 + x - 1.
```

## Validation

`experiments/scalar_public_field.py` verified:

- exact identity with the previous three-amplitude modal recurrence for `n=0..99`;
- exact equality of every per-state count for physical times `t=0..220`;
- exhaustive address encode/decode roundtrip for `T=0..9`;
- 200 random address roundtrips for each of `T=16,64,128,200,218`;
- unchanged 63-bit frontier:
  - `N(218) = 9,131,204,053,820,206,208 < 2^63`;
  - `N(219) = 10,214,739,716,735,776,832 > 2^63`.

Focused GitHub Actions workflow: `Scalar public field`, run `34429072807`, passed.

## Current compact model

The reversible trajectory-address machine can now be described as:

```text
private causal state: 4 bits P_t
public phase:          t mod 3
public count field:    deterministic function of t through scalar g_n
trajectory address:    A_t (<= 63 bits up to T=218)
```

with

```text
(A_T, T) <-> complete admissible trajectory.
```

The important distinction remains that `A_T` is a reversible trajectory address, not a cryptographic hash, and the 63-bit capacity follows from the restricted language of admissible paths rather than compression of arbitrary 221-bit strings.

## Next experiment

Derive a fast exact evaluator for `g_n` from `n` using exponentiation by squaring / companion-matrix powering, so random access to the public field is `O(log n)` instead of iterating the recurrence from zero. Then verify that address decoding can reconstruct any required past count slice from time alone without cached dynamic state.

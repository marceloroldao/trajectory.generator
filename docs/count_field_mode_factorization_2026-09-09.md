# Count-field mode factorization — 2026-09-09

## Result

For the 3-step Floquet count operator restricted to the reachable Krylov subspace, the exact dimension is 8. The characteristic/minimal polynomial induced by the exact vector recurrence factors as

\[
\chi(x)=x(x-1)^2(x+1)^2(x^3-2x^2+x-1).
\]

Therefore the public count field decomposes over the rationals into invariant primary components of dimensions

\[
1+2+2+3=8.
\]

Interpretation inside this finite automaton:

- `x`: one transient mode, annihilated after one 3-step Floquet update;
- `(x-1)^2`: a 2D unit mode with a size-2 Jordan block, allowing constant + linear-in-period contribution;
- `(x+1)^2`: a 2D alternating unit mode with a size-2 Jordan block, allowing alternating constant + linear-in-period contribution;
- `x^3-2x^2+x-1`: a 3D irreducible growth/oscillation block over Q.

The cubic has one real dominant root

\[
\mu\approx1.7548776662466927
\]

per three physical steps and one complex-conjugate pair of modulus approximately `0.7548776662466926`.

The corresponding per-step dominant growth factor is

\[
\lambda=\mu^{1/3}\approx1.2061897001179,
\]

which matches the previously measured spectral growth of the operational machine.

## Consequence

The public count field does not require 16 independent state counts conceptually. Its phase-aligned evolution consists of four primary dynamical sectors:

\[
C_{3n}=C^{(0)}_n+C^{(+)}_n+C^{(-)}_n+C^{(g)}_n,
\]

with dimensions `1`, `2`, `2`, and `3` respectively.

The only exponentially growing sector is the 3D cubic block. The unit sectors encode neutral/periodic and linearly weighted structure; the zero sector is transient.

This is an exact algebraic property of the present automaton and should not be interpreted as a physical law without independent evidence.

## Reproduction

Experiment: `experiments/count_field_mode_factorization.py`

CI: workflow step `Factor count field into invariant modes` passed on run `34427421358`.

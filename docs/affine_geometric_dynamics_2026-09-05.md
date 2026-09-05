# Affine geometric dynamics test — 2026-09-05

## Question

Given an exact six-bit semantic coordinate `G` for the 37 operational states and the minimal reversible edge label `z`, can the labeled dynamics be reduced to affine maps

\[
G' = A_z G + c_z
\]

over GF(2), one map for `z=0` and one for `z=1`?

If so, the operational system could be embedded in two simple reversible affine permutations of the full 64-state six-bit space.

## Exhaustive semantic-coordinate result

The experiment `experiments/affine_geometric_dynamics.py` tested all 688 injective six-bit semantic coordinates found by the compact-coordinate search.

Results:

- semantic coordinates tested: **688**
- coordinates with both `z`-conditioned maps affine: **0**
- globally reversible affine coordinates: **0**
- coordinates with both `z`-conditioned maps quadratic: **0**

Thus, within the tested semantic coordinate family, degree 1 and degree 2 are insufficient. At least cubic nonlinearity is required to describe the labeled operational dynamics exactly.

## Relation to the compact coordinate

The best previously identified coordinate

\[
G=(h_1, orientation, phase_0, phase_1, q_0, q_1)
\]

still has a highly structured update: five of the six forward outputs are linear and one is cubic; five of the six reverse outputs are linear and one is quartic. The negative affine/quadratic search therefore indicates that this concentration of nonlinearity is not merely caused by a poor coordinate choice among the 688 semantic six-bit representations.

## Interpretation

The current operational automaton has a linear/shift-like skeleton plus an irreducible nonlinear correction. This is a computational statement about the present finite automaton, not evidence of a physical nonlinear law.

## Next test

Measure the nonlinear support across all 688 coordinates and determine whether one nonlinear output channel is the minimum possible simultaneously in the forward and reverse directions. Then try to represent that channel as a small reversible Boolean gate coupled to an otherwise linear six-bit transport.

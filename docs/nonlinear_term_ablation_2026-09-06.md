# Nonlinear term ablation — 2026-09-06

This note records the corrected exhaustive ablation of the five nonlinear
forward monomials of the balanced universe `(0,2,4,4)`.

## Methodological constraint

The learned ANF law is certified only on the 49 operational `(G,z)`
source-label pairs.  Earlier attempts that extrapolated the law to all 64
six-bit states, or allowed both values of `z` everywhere, were invalid for
causal interpretation.  The final experiment keeps the exact observed
source-label domain fixed and changes only which nonlinear monomials are
active.

The five nonlinear terms are:

1. `g1&g4`
2. `g1&g5`
3. `g0&g3&g5`
4. `g1&g4&g5`
5. `g2&g4&g5`

All `2^5 = 32` subsets were tested.

## Full five-term universe

The complete mask reproduces the reference dynamics exactly:

- edges: 49
- reverse ambiguity: 0
- exact edge agreement: 49/49
- extra edges: 0
- missing edges: 0
- 63-bit frontier: 218 transitions
- rate at 200 steps: `0.2905864402003887` bit/step

This is the only tested subset that reproduces the reference graph exactly.
Therefore all five nonlinear terms are necessary for the exact balanced
universe in this coordinate representation.

## Minimal subset for local reversibility only

A smaller reversible submachine exists with three nonlinear terms:

- `g1&g4`
- `g1&g5`
- `g1&g4&g5`

It has:

- edges: 48
- reverse ambiguity: 0
- edge agreement with reference: 39/49
- missing reference edges: 10
- extra edges: 9
- rate at 200 steps: `0.04147310374445813` bit/step
- no 63-bit crossing within the 300-step scan window

This is not a compressed representation of the same universe.  It is a
different, far more restrictive reversible universe.

## Interpretation

The experiment separates two notions that were previously conflated:

1. **reversibility requirement** — enough structure to make `(G_next,z)` map
   uniquely back to `G_prev`;
2. **geometric fidelity requirement** — enough structure to reproduce the
   same admissible trajectory family and its information-growth profile.

Three nonlinear monomials can be sufficient for reversibility, but all five
are required to preserve the original 49-edge geometry.

Thus the two additional terms are not redundant merely because reversibility
survives without them.  They control which reversible trajectories are
admissible and therefore participate in the entropy geometry of the universe.

## Current decomposition

For the balanced machine, the evidence now supports:

`U = L + z + N`

where:

- `L` supplies the near-linear transport;
- `z` labels the local reversible relation;
- `N` constrains the admissible transition geometry.

The nonlinear core is therefore not a single binary function with a single
role.  Its monomials split into at least two functional classes: terms needed
for reverse disambiguation and terms needed to preserve the full trajectory
geometry.

## Next experiment

Measure the marginal contribution of each monomial relative to the complete
five-term universe (leave-one-out), separating:

- lost reference edges;
- introduced edges;
- change in recurrent SCCs;
- change in spectral radius / entropy rate;
- change in reverse ambiguity.

This will identify which nonlinear interactions primarily regulate entropy
and which primarily stabilize causal invertibility.

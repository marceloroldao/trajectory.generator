# Nonlinear-channel ablation — 2026-09-06

## Question

What happens if the unique nonlinear geometric correction is removed while the compact six-bit coordinate and binary edge label are kept unchanged?

We compare:

- `U_full = L + N`: the validated balanced causal universe;
- `U_linear = L`: the same forward compact-coordinate laws with every degree >=2 term removed from the unique nonlinear output channel.

The corrected experiment uses exactly the eight public initial states `(state, initial_topology(state), phase=0)`.

## Reproducible experiment

- Script: `experiments/nonlinear_ablation.py`
- Workflow: `.github/workflows/nonlinear-ablation.yml`
- GitHub Actions run: `34066730660`

## Results

### Full universe

- initial states: 8
- reachable geometric states: 37
- labeled edges: 49
- forward ambiguity: 0
- reverse ambiguity: 0
- maximum reverse preimages for `(destination,z)`: 1
- 63-bit frontier: 218 physical transitions
- `N(218) = 9,131,204,053,820,206,208`
- `N(219) = 10,214,739,716,735,776,832`
- measured rate at 200 transitions: ~0.290586 bit/transition

### Linear-only ablation

- reachable geometric states: 48
- labeled edges: 96
- forward ambiguity: 0
- reverse ambiguous keys: 48
- maximum reverse preimages for `(destination,z)`: 2
- 63-bit frontier: 60 physical transitions
- `N(60) = 2^63`
- `N(61) = 2^64`
- measured rate at 200 transitions: ~1.015 bit/transition including the fixed eight-way initial multiplicity
- dominant recurrent component: all 48 reachable states, 96 internal edges, spectral radius 2

Only 25 of the 49 validated full-universe edges are reproduced by the affine-only law on the original operational domain. The nonlinear correction changes 24 of those 49 forward transitions, matching the previously measured forward nonlinear support.

## Interpretation

Removing the nonlinear channel does **not** remove branching. It does the opposite: it releases the dynamics into an almost maximally free binary shift. Every reachable state has two labeled outgoing transitions, trajectory count grows essentially as `2^t`, and the 63-bit address space is exhausted after 60 transitions (plus the eight-way initial multiplicity).

However, that extra freedom destroys local reversibility: `(G_{t+1}, z_t)` can have two distinct predecessors. The affine flow alone therefore does not retain enough causal structure to reconstruct the previous state uniquely.

The nonlinear correction acts as a **causal constraint / folding discriminator**. It removes or redirects exactly the transitions needed to keep the operational language sparse enough and the labeled dynamics invertible enough that a 63-bit address can index much longer trajectories.

A better current statement is therefore:

> The nonlinear channel is not the source of raw branching entropy. It is the mechanism that shapes branching so that distinguishable trajectories remain locally reversible.

For the current universe:

`linear transport + unconstrained binary choice -> high entropy, short 63-bit horizon, reverse ambiguity`

whereas

`linear transport + nonlinear geometric constraint -> lower entropy, long 63-bit horizon, unique labeled inverse`.

## Caveat

This is a structural statement about the present finite automaton family. It is not evidence of a physical law. The next useful test is to ablate the nonlinear channel across the previously tested 18 perturbed universes and measure whether loss of reverse uniqueness is systematic.

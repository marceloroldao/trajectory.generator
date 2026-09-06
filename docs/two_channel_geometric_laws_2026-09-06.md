# Direct geometric laws for the two nonlinear channels — 2026-09-06

## Context

The balanced universe had already been decomposed as

`U = L + z + I + G`

with:

- `I = t0 ^ t1 ^ t3`, the channel whose ablation restores/removes reverse uniqueness;
- `G = t2 ^ t4`, the channel whose ablation controls most recurrent expansion.

Those definitions still referenced the five original ANF monomials.  This experiment asks whether `I` and `G` can instead be computed directly from semantic local transition invariants.

The validated compact coordinate remains:

`Gstate = (h1, orientation, phase0, phase1, q0, q1)`

and all fitting is restricted to the 49 operational transitions.

## Result

Both channels are exactly determined by only **four semantic invariants**.

### Identity channel I

A best minimal set is:

- `history_step_weight`
- `orientation_match`
- `topology_delta_parity`
- `topology_direction`

No set of three or fewer tested semantic invariants determines `I` exactly on the operational domain.

An exact degree-3 Boolean law exists.  In the binary encoding used by the experiment it has only three terms:

`I = history_step_weight_b1 & orientation_match`
`  ^ history_step_weight_b0 & orientation_match & topology_delta_parity`
`  ^ history_step_weight_b0 & orientation_match & topology_direction_b1`

There are 175 minimal four-invariant sets that determine `I`; the expression above is the simplest one found under the current encoding/search criterion.

### Geometry channel G

A best minimal set is:

- `history_direction`
- `history_lsb`
- `history_parity`
- `phase_flip`

Only two four-invariant sets determine `G` exactly, so this channel is much more constrained semantically than `I`.

An exact degree-3 law exists with six ANF terms in the current binary encoding.

A second equivalent minimal set replaces `history_parity` by `next_orientation_match`.

## Functional interpretation

The direct laws preserve the earlier ablation-based functional split without referencing the five raw monomials:

- `I` is controlled by **orientation and the magnitude/direction class of the local change**;
- `G` is controlled by **history direction/state and phase evolution**.

This gives a cleaner computational decomposition:

`U = L + z + I(local geometry) + G(local phase/history geometry)`

The channels remain Boolean and local on the current operational manifold.

## What this establishes

For this finite automaton, the five discovered nonlinear monomials are not required as a conceptual representation.  They can be eliminated as an intermediate layer:

`local invariants -> (I,G) -> nonlinear correction N = I ^ G -> next geometric state`

This is an exact reparameterization on all 49 operational transitions.

## What this does not establish

The names identity/geometric, and the interpretations orientation/phase/history, are computational descriptions of this automaton.  They are not evidence that the same variables are physical invariants of nature.

## Reproduction

Experiment:

`experiments/two_channel_geometric_laws.py`

Validated by GitHub Actions run `34068126583` (success).

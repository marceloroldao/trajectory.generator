# Endogenous coherence universe — 2026-08-19

Status: pre-alpha experimental result

## Objective

Test whether the active local law can be selected by the current state and public time phase, without storing the law sequence externally and without targeting a preferred algebraic constant.

The decoder still receives only:

```text
(final_state, steps)
```

plus the public deterministic configuration.

## Selector

Candidate laws are the representative memory-3 plastic, golden-ratio, and tribonacci classes already used elsewhere in the repository. The selector does **not** target their spectral constants.

At each step it uses only:

- current three-bit history popcount;
- public phase `t mod 3`;
- whether a candidate law offers a free or forced transition;
- whether a forced transition moves the next three-bit state toward balanced occupancy.

Balanced histories (popcount 1 or 2) are allowed extra freedom only during phase 1. Otherwise the selector prefers a forced transition. A deterministic state/phase tie-break chooses among equally scored candidates.

Because the selector is a public function of `(history, time)`, the sequence of active laws is regenerated during decoding and does not require side metadata.

## Result

Exact integer counting gives:

```text
117 steps -> 9,005,678,117,819,947,261 admissible trajectories -> fits in 2^63
118 steps -> 10,806,813,713,839,367,713 admissible trajectories -> exceeds 2^63
```

So the exact 63-bit frontier is:

```text
117 steps
```

At 300 steps the finite-length information rate is approximately:

```text
0.53216 bit/step
```

corresponding to an effective growth factor near:

```text
1.4464 per step
```

(The experiment script recomputes the exact value rather than treating this rounded value as a constant.)

Weighted law usage at the 117-step frontier is approximately:

```text
plastic     43.48%
phi         26.09%
tribonacci  30.43%
```

No single candidate law dominates completely.

## Interpretation

This is the first experiment in the repository where the "universe" participates by selecting **which law of motion is active**, rather than merely perturbing a state after the data transition is chosen.

Conceptually:

```text
(history, time)
      -> coherence selector
      -> active local law
      -> allowed next states
      -> new history
```

The active-law history is therefore part of the trajectory's deterministic causal structure, not stored metadata.

The result does not establish a physical law or a new compression theorem. It demonstrates an exact finite-state construction in which law selection, admissibility, and trajectory reconstruction are coupled while respecting the final-state capacity bound.

## Reproduction

```bash
python experiments/coherence_universe_scan.py
python -m unittest tests.test_coherence_universe -v
```

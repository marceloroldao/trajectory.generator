# Emergent memory-3 law-bank universe — 2026-08-19

Status: pre-alpha experimental result

## Objective

Remove the hand-selected candidate set from the previous coherence-universe experiment.

Instead of choosing among three representative rules, the candidate bank now contains **all 3^8 = 6,561 memory-3 local laws**. No spectral target such as the golden ratio, plastic constant, tribonacci constant, or a preferred lambda is used by the selector.

The decoder still receives only:

```text
(final_state, steps)
```

plus the public deterministic machine definition.

## Structural selector

A law is evaluated using both its current action and global combinatorial features of its eight history-state actions.

Global features include:

- balance between free and forced actions, measured by `free_count * (8 - free_count)`;
- symmetry between force-0 and force-1 actions;
- number of forced transitions that land in balanced-popcount history states;
- coverage of reachable three-bit next states.

The current history and public phase `t mod 3` contribute the local coherence term. Extreme histories prefer a definite restoring transition. Balanced histories permit additional freedom on phase 1.

The selected law is therefore a deterministic function of `(history, phase)` and not stored as side metadata.

## Main result

Although the candidate bank contains 6,561 laws, only **7 distinct laws** are selected across the 24 possible `(three-bit history, phase)` contexts.

At the 63-bit frontier their weighted usage is approximately:

| rule index | usage | individual spectral radius |
|---:|---:|---:|
| 2420 | 34% | 1.465571232 |
| 2744 | 18% | 1.395336994 |
| 2426 | 18% | 1.465571232 |
| 3716 | 12% | 1.487081057 |
| 2510 | 8% | 1.443268791 |
| 4580 | 8% | 1.465571232 |
| 2670 | 2% | 1.573477688 |

None of these seven selected rules is exactly the previously highlighted golden-ratio, plastic, or tribonacci representative class.

This is useful because the selector was not constructed to rediscover those named constants.

## Capacity

Exact integer counting gives:

```text
80 steps -> 7,152,557,373,046,875,000 admissible trajectories -> fits in 2^63
81 steps -> 10,728,836,059,570,312,500 admissible trajectories -> exceeds 2^63
```

So the exact 63-bit frontier of this first full-bank selector is:

```text
80 steps
```

The finite-length rate around 300 steps is approximately 0.77 bit/step, so this selector currently preserves substantially more freedom than the earlier three-rule coherence universe and therefore reaches the 63-bit capacity sooner.

## Interpretation

This experiment demonstrates three separate points.

First, a large rule bank can collapse endogenously to a much smaller active subset when a public coherence criterion is applied.

Second, the active subset does not have to coincide with previously named algebraic growth classes.

Third, more endogenous choice does **not** automatically improve final-state capacity. The current selector is more permissive, so its admissible-family entropy rises faster and its 63-bit frontier is shorter than the previous 117-step coherence universe.

The useful research target is therefore not "maximize the number of candidate laws" but find a public selector that creates a favorable balance among:

```text
freedom
coherence
mixing
robustness
exact addressability
```

## Reproduction

```bash
python experiments/emergent_law_bank_scan.py
python -m unittest tests.test_emergent_law_bank -v
```

NumPy is required only by the experiment script for reporting the individual spectral radii of selected laws. The exact codec is pure Python.

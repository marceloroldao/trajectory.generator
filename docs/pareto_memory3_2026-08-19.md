# Memory-3 Pareto analysis — 2026-08-19

Status: pre-alpha experimental result

## Objective

Search all `3^8 = 6,561` memory-3 local admissibility laws for trade-offs rather than a single preferred constant.

The main objectives are deliberately conflicting:

1. maximize entropy rate `h = log2(lambda)` so the law retains information-carrying freedom;
2. maximize the exact complete-family frontier in a 63-bit final address;
3. maximize one-action mutation robustness of the law.

A separate sampled trajectory-perturbation metric is used only for selected representatives because equal spectral rates do not imply equal trajectory geometry.

## Exact scan

The frontier calculation uses iterative propagation of integer counts across the 8 history states, not repeated recursive enumeration.

Across the complete rule space:

- 6,561 laws were evaluated;
- 193 distinct spectral-radius values occur at `1e-9` rounding;
- 2,286 laws do not exceed `2^63` admissible trajectories within the first 1,000 steps, mostly zero-entropy or extremely low-growth systems;
- among laws that do cross the 63-bit limit within 1,000 steps, observed exact frontiers range from 63 to 452 steps.

The average one-mutation same-rate robustness across all laws is approximately `0.4002`.

## Pareto structure

Using the three objectives above and excluding effectively zero-growth laws, the non-dominated set contains many rules rather than one unique optimum. This is expected because entropy rate and 63-bit frontier pull in opposite directions.

A simple maximin normalization was used only as a diagnostic to locate balanced candidates. It is not claimed to be a physically privileged objective function.

The strongest balanced pair found by that diagnostic is the symmetry-related pair:

```text
(2,1,1,1,0,0,0,0)
(1,1,1,1,0,0,0,2)
```

where actions are ordered by history states `000..111` and mean `0=force 0`, `1=force 1`, `2=free`.

For both:

```text
lambda              ≈ 1.285199033245
entropy rate h       ≈ 0.361991800696 bits/step
exact 63-bit frontier = 170 steps
law robustness        = 0.375
```

So this candidate class sits in a genuine intermediate region: it carries much less than one independent bit per step, but retains far more freedom than a nearly deterministic law.

## Trajectory robustness caveat

The same balanced pair is locally rigid in trajectory space. In a fixed-seed sample of 256 exact 64-step trajectories, flipping every bit position once left only about `3.3%` of perturbed trajectories admissible.

For comparison, representative rules used elsewhere in the repository give approximately:

| representative growth class | lambda | 63-bit frontier | law robustness | one-bit trajectory survival |
|---|---:|---:|---:|---:|
| balanced `1.285199...` | 1.285199033 | 170 | 0.375 | ~0.033 |
| plastic | 1.324717957 | 152 | 0.625 | ~0.030 |
| golden ratio | 1.618033989 | 90 | 0.500 | ~0.557 |
| tribonacci | 1.839286755 | 71 | 0.1875 | ~0.767 |

These representative values show that the axes are genuinely different. A law may be robust in rule space but brittle in trajectory space, or vice versa.

## Interpretation

The current evidence does not support choosing a trajectory law by a single emergent irrational constant.

A more useful object is a multi-dimensional law phenotype:

```text
law -> (entropy rate, address frontier, mutation robustness, trajectory robustness, ...)
```

This produces a Pareto surface rather than a unique best law.

The balanced `lambda ≈ 1.285199` class is interesting because it was not targeted in advance and is not one of the named constants previously monitored. Its appearance is therefore a useful guard against confirmation bias around `phi`.

## Next step

Add further independent axes before selecting candidate laws, especially:

- mixing / state occupancy;
- recurrence and cycle structure;
- error propagation distance after a one-bit perturbation;
- decoding complexity;
- finite-length stability of the entropy rate.

A candidate 'computational universe' should be evaluated by this whole profile, not by `lambda` alone.

## Reproduction

```bash
python experiments/pareto_memory3.py
```

NumPy is required for spectral-radius calculation.

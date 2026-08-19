# Memory-3 trajectory perturbation — 2026-08-19

Status: pre-alpha sampled experiment

## Question

How robust is the **trajectory family itself** to a one-bit perturbation, when the public local law is held fixed?

This is different from mutating the law. Here the rule is unchanged and a valid trajectory is modified at one position.

## Method

For each representative memory-3 rule (`plastic`, `phi`, `tribonacci`):

1. choose 2,048 ranks uniformly from the exact admissible family at 64 steps using a fixed RNG seed;
2. unrank each trajectory exactly;
3. flip each of its 64 positions once;
4. test whether the perturbed trajectory is still admissible under the same rule.

Total perturbations per representative rule: `2,048 * 64 = 131,072`.

## Result

| representative rule | one-bit perturbations that remain admissible |
|---|---:|
| plastic | **0.03020** |
| phi | **0.55901** |
| tribonacci | **0.76838** |

The representative plastic rule is highly rigid: most interior single-bit flips violate a forced transition downstream. The phi representative has intermediate local tolerance. The tribonacci representative is much more permissive.

## Important limitation

These figures apply to the **specific representative rules** currently defined in `finite_law_codec.py`. They must not be generalized to every law having the same asymptotic spectral radius.

A growth class can contain many non-isomorphic transition graphs. Equal `lambda` therefore does not imply equal local geometry, perturbation tolerance, mixing, or error propagation.

## Interpretation

This adds a second axis to the project:

```text
spectral rate lambda      -> how fast the number of allowed trajectories grows
perturbation survival     -> how locally connected / tolerant the allowed family is
```

Two laws can have similar information rates but very different trajectory geometry. A useful future admissibility law may therefore need to optimize more than entropy rate alone.

## Reproduction

```bash
python experiments/trajectory_perturbation_memory3.py --steps 64 --samples 2048 --seed 123
```

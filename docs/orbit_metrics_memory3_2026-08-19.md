# Orbit-style metrics for memory-3 laws — 2026-08-19

Status: pre-alpha experimental result

## Objective

Extend the memory-3 law comparison beyond entropy and rule robustness by measuring three additional geometric/dynamical properties of the admissible trajectory family:

1. state-space occupancy under the Perron measure;
2. spectral mixing gap;
3. one-bit perturbation propagation.

These diagnostics are combinatorial properties of finite-state trajectory laws. They are not claims about physical vacuum dynamics.

## Definitions

For a law with adjacency matrix `A` and dominant eigenvalue `lambda_1`:

```text
entropy rate h = log2(lambda_1)
```

The normalized Perron occupancy entropy is the Shannon entropy of the state weights induced by the left/right Perron eigenvectors, divided by `log2(8)` for the eight memory-3 history states.

```text
occupancy = 0 -> concentrated on very few states
occupancy = 1 -> spread uniformly over all eight states
```

The mixing diagnostic is

```text
mixing_gap = 1 - |lambda_2| / |lambda_1|
```

where `lambda_2` is the second-largest eigenvalue magnitude. This is only a spectral diagnostic; periodic/reducible systems require care in interpretation.

For error propagation, admissible trajectories are sampled by exact rank/unrank. Every bit position is flipped once and the modified sequence is checked against the unchanged law. We record:

- fraction of single-bit flips that remain admissible;
- mean number of violated transitions per flip;
- mean span between the first and last violation.

## Representative results

Configuration for perturbation test:

```text
steps   = 64
samples = 1,024 exact admissible ranks
seed    = 123
```

| representative law | lambda | h bits/step | 63-bit frontier | occupancy | mixing gap | flip survival | mean violations | mean error span |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| balanced 1.285199 | 1.285199033 | 0.361992 | **170** | 0.739769 | 0.196370 | 0.032898 | 1.701279 | 2.171188 |
| plastic | 1.324717957 | 0.405685 | **152** | 0.634055 | 0.245122 | 0.029984 | 2.017792 | 2.235062 |
| golden ratio | 1.618033989 | 0.694242 | **90** | 0.746324 | 0.381966 | 0.559021 | 1.115585 | 1.212570 |
| tribonacci | 1.839286755 | 0.879146 | **71** | 0.923015 | 0.456311 | 0.769119 | 0.449631 | 0.532913 |

## Main observations

The lower-entropy laws support longer exact trajectories in a fixed 63-bit address space, as expected from information accounting.

However, low entropy does not imply broad state-space occupation. The representative plastic rule is relatively concentrated (`occupancy ~= 0.634`) and highly sensitive to trajectory perturbations.

The tribonacci representative has the highest occupancy and largest spectral gap among these four, but also the shortest 63-bit frontier because its admissible family grows much faster.

The balanced `lambda ~= 1.285199` representative sits between very low-growth rigid systems and high-growth permissive systems in occupancy, but it remains perturbation-rigid: only about 3.3% of one-bit flips stay admissible.

The golden-ratio representative is notable here not because of `phi` itself, but because its metrics fall between the plastic and tribonacci representatives on several axes: entropy, occupancy, mixing gap, frontier, and perturbation tolerance. This is one representative rule only; equal spectral radius does not imply equal geometry for all laws in the same growth class.

## Interpretation

A useful law cannot be characterized by one scalar such as `lambda` alone. The current project state suggests a multi-axis profile:

```text
U = (
    entropy_rate,
    exact_frontier,
    rule_robustness,
    trajectory_robustness,
    state_occupancy,
    mixing_gap,
    error_propagation
)
```

This gives a more precise computational analogue for the earlier idea of a stable orbit with internal freedom:

- too much freedom -> high entropy, short address frontier;
- too much constraint -> long frontier but rigid/fragile trajectories;
- intermediate laws may offer useful balance among diversity, coherence, and recoverability.

No single preferred constant has been established.

## Reproduction

```bash
python experiments/orbit_metrics_memory3.py --steps 64 --samples 1024 --seed 123
```

Requires NumPy for eigendecomposition.

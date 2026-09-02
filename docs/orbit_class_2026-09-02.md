# Structural orbit-class experiment — 2026-09-02

Status: pre-alpha / partial improvement

## Objective

Replace scalar causal coherence variables with a discrete structural class `Q_t` describing *which relation pattern* the trajectory currently occupies.

The decoder is still intended to require only:

```text
(final_state, steps)
```

plus the public machine definition. `Q_t` is regenerated from the recovered prefix and is not side metadata.

## Classes tested

Four four-state structural definitions were scanned:

```text
relpair         -> last two transition-relation bits
curvature       -> current relation + relation-change flag
state_relation  -> parity class of current 3-bit state + current relation
direction       -> current bit + current relation
```

For each class definition, all non-trivial maps from the four orbit classes to the five public memory-3 selector policies were evaluated.

## Best long-frontier class

Several `relpair` / `curvature` maps reached:

```text
frontier = 226 steps
rate300 ~= 0.27691 bit/step
```

but their one-bit perturbation survival remained low (~few percent).

## Best robustness-above-baseline-frontier candidate

The strongest candidate found with frontier above the current 187-step balanced reference was:

```text
mode       = state_relation
policy_map = (1, 0, 3, 4)
```

Exact family counts around the 63-bit boundary:

```text
N(200) = 7,930,919,754,233,053,072
N(201) = 9,681,753,296,247,848,518
2^63   = 9,223,372,036,854,775,808
```

Therefore:

```text
frontier = 200 steps
```

The finite-length information rate at 300 steps is approximately:

```text
0.3051962 bit/step
```

A fixed-seed sample of 1,024 admissible 64-step trajectories, testing every single-bit flip, gave approximately:

```text
9.57% perturbation survival
```

## Interpretation

This is better than the immediately preceding scalar/relational accumulators, which typically remained around 1–5% survival once frontier was pushed materially beyond 187 steps. The orbit-class representation therefore preserves more local structural tolerance than a simple scalar score.

However, it still does **not** dominate the current balanced memory-3 reference:

```text
balanced coherence-memory reference:
frontier ~= 187
flip survival ~= 32.8%

best orbit-class candidate:
frontier = 200
flip survival ~= 9.57%
```

So this experiment is a partial improvement, not a new default.

## Main lesson

A discrete structural class appears more promising than a scalar accumulated coherence value, but the current four-state definitions still discard too much information about the *shape* of the trajectory.

The next experiment should therefore retain a small **topological transition state**—for example, a finite graph class describing how relation states move between one another—rather than compressing the path into one four-valued label.

## Reproduction

```bash
python experiments/orbit_class_search.py
```

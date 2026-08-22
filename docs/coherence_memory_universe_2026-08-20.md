# Accumulated coherence-memory universe — 2026-08-20

Status: pre-alpha experimental result

## Objective

Extend the trajectory grammar with a causal variable that summarizes *how the current state was reached*, not only the last three bits.

The grammar state becomes

```text
(history_3bit, coherence_bucket, public_phase)
```

The coherence bucket evolves deterministically from the path and therefore is not side metadata. During decoding it is regenerated together with the trajectory.

The decoder contract remains:

```text
(final_state, steps)
```

plus the public configuration.

## Search space

The implementation exposes five public selector policies and three deterministic coherence updates:

```text
occupancy
signed_bit
rolling
```

With four coherence buckets, every bucket chooses one of five policies. The complete search therefore contains

```text
3 * 5^4 = 1,875
```

configurations.

The exhaustive scan does not target phi or any named spectral constant. Configurations are evaluated by exact 63-bit frontier, finite-length information rate, and sampled one-bit perturbation survival.

## New balanced result

The strongest configuration found that improves the prior 184-step moderate-entropy baseline without sacrificing its approximate perturbation tolerance is:

```text
update_mode = rolling
policy_map  = (1, 3, 4, 0)
```

Exact counts:

```text
187 steps -> 8,070,450,532,247,928,961 admissible trajectories
188 steps -> 16,140,901,064,495,857,795 admissible trajectories
```

Therefore the exact 63-bit frontier is:

```text
187 steps
```

At 300 steps the finite-length rate is approximately:

```text
0.3360245 bit/step
```

A fixed-seed sample of 1,024 admissible 64-step trajectories, with all 64 single-bit flips tested, gave approximately:

```text
32.80% perturbation survival
```

The configuration visited 3 policy profiles and 12 distinct selected laws in that sample.

This is a small but real Pareto improvement over the previous 184-step balanced policy universe, whose sampled perturbation survival was about 33%.

## Capacity-oriented extreme

The same exhaustive scan also found a much longer configuration:

```text
update_mode = signed_bit
policy_map  = (4, 0, 2, 1)
```

Exact counts:

```text
244 steps -> 8,887,676,923,343,977,346 admissible trajectories
245 steps -> 14,225,417,450,507,601,237 admissible trajectories
```

with finite-length rate near:

```text
0.2570568 bit/step
```

However, a 1,024-trajectory perturbation sample gave only about:

```text
1.31% one-bit survival
```

so this profile is treated as a capacity extreme rather than the default balanced universe.

## Interpretation

Adding a small causal memory does change the Pareto surface. It does not create a free storage channel: the coherence bucket is entirely derivable from the recovered prefix and is included in the dynamic programming state during exact rank/unrank.

The main result is therefore narrower:

> A deterministic finite memory of the trajectory can alter the geometry of the admissible family enough to improve the capacity/robustness Pareto frontier while preserving exact decode from `(final_state, steps)`.

The improvement is modest in the balanced regime (184 -> 187 steps), while the long-frontier regime reaches 244 steps only by becoming highly fragile. This supports the recurring trade-off observed throughout the project: longer addressable trajectories require lower independent information rate and/or greater structural rigidity.

## Reproduction

```bash
python experiments/coherence_memory_search.py --samples 64 --seed 123
python -m unittest tests.test_coherence_memory_universe -v
```

For higher-confidence perturbation estimates, increase `--samples`.

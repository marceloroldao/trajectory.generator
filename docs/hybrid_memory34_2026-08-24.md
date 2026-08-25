# Hybrid memory 3<->4 trajectory universe — 2026-08-24

Status: pre-alpha experimental result

## Objective

Test whether the current balanced memory-3 regime can gain causal depth by activating memory-4 **only when the reconstructed coherence state enters a public critical bucket**.

The machine concept is:

```text
stable coherence -> consult memory-3 local grammar
critical coherence -> consult memory-4 local grammar
```

The switch is not side metadata. The decoder can regenerate the same coherence bucket from the recovered prefix, so the intended final contract remains:

```text
(final_state, steps)
```

plus the public machine definition.

## Why this experiment

The controlled memory-order tests showed:

- memory 3 repeatedly produced the best balanced regime, including ~187 steps with ~31-33% sampled one-bit survival;
- memory 4 produced longer frontiers in some regimes, but was much more fragile;
- simply increasing local memory therefore does not improve the Pareto surface monotonically.

The hybrid test asks whether memory-4 can be used as an **exception path** rather than the default grammar.

## Search construction

`experiments/hybrid_memory34_search.py` keeps the most recent four bits in the causal state but chooses which local order is visible to the grammar from the coherence bucket.

With four coherence buckets, the experiment tests all 14 non-empty/non-full meaningful critical-bucket masks under each of three public coherence updates:

```text
occupancy
signed_bit
rolling
```

The policy map is the current balanced map:

```text
(1, 3, 4, 0)
```

and both memory orders use deterministic canonical law banks of equal size.

## Exact counting method

For search speed, total admissible-family counts are propagated iteratively over the finite causal state:

```text
(history4, coherence_bucket)
```

There are at most 16 * 4 = 64 such states before phase is accounted for by the public time index. This iterative propagation is exact for family counting.

The perturbation measurements below use exact suffix counts and unranking of admissible 64-step trajectories, followed by testing every one-bit flip in a fixed-seed sample.

## Results

The hybrid can increase the 63-bit frontier, but every longer candidate found in this scan loses most of the perturbation robustness of the balanced memory-3 baseline.

Representative Pareto points:

```text
frontier  rate300   flip64    update      memory-4 critical buckets
286       0.21964   2.02%     occupancy   (1, 2)
247       0.25009   2.51%     occupancy   (2,)
234       0.26653   3.99%     occupancy   (0, 1, 3)
233       0.26686   4.24%     occupancy   (0, 1)
206       0.30006   5.22%     occupancy   (2, 3)
199       0.31222   1.62%     signed_bit  (1, 3)
193       0.31901   0.92%     signed_bit  (1, 2, 3)
187       0.32782   1.45%     signed_bit  (1, 2)
```

The current balanced memory-3 reference remains:

```text
frontier 187
rate300  ~= 0.33602 bit/step
flip64   ~= 32.80%
```

The hybrid therefore does **not** improve the balanced Pareto frontier. Its best longer-frontier compromise in this scan is 206 steps with about 5.2% one-bit survival, still far below the memory-3 reference. The 286-step candidate is a capacity-oriented extreme and is highly fragile.

## Interpretation

This is a useful negative result.

Adaptive causal depth by itself does not preserve the stability advantage of memory 3. Switching to memory 4 only in coherence-defined critical states changes the admissible-family geometry enough to extend the frontier, but the resulting families become much more sensitive to local perturbation.

Therefore the hybrid 3<->4 scanner is **not promoted into the public codec API**.

The result supports a narrower hypothesis:

> The useful causal variable is not simply how much past state is exposed. The rule deciding which past information matters must itself preserve a stable geometry of admissible trajectories.

## Reproduction

```bash
python experiments/hybrid_memory34_search.py \
  --bank-size 256 \
  --seed 12648430 \
  --max-steps 1000 \
  --min-rate 0.20 \
  --max-rate 0.50 \
  --top 42 \
  --policy-map 1 3 4 0
```

A matching GitHub Actions workflow is available at:

```text
.github/workflows/hybrid-memory34.yml
```

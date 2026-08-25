# Hybrid memory 3<->4 trajectory universe — 2026-08-24

Status: pre-alpha experimental scanner

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

The initial policy map is the current balanced map:

```text
(1, 3, 4, 0)
```

and both memory orders use deterministic canonical law banks of equal size.

## Exact counting method

For search speed, total admissible-family counts are propagated iteratively over the finite causal state:

```text
(history4, coherence_bucket)
```

There are at most 16 * 4 = 64 such states before phase is accounted for by the public time index. This iterative propagation is exact for family counting and avoids the much more expensive recursive suffix recomputation used in rank/unrank codecs.

The experiment reports:

- exact 63-bit frontier within the search horizon;
- whether the family crossed 2^63;
- finite-length rate at 300 steps;
- admissible count at 64 steps;
- update mode;
- critical coherence buckets that activate memory-4.

## Promotion criterion

No hybrid codec is promoted to the public API yet.

A candidate should only be promoted if it demonstrates a real Pareto gain over the current memory-3 balanced reference, ideally:

```text
frontier > 187 steps
rate remains moderate
one-bit perturbation survival remains near the ~30% regime
```

If the hybrid only increases frontier by becoming highly rigid or fragile, it is a negative result rather than an architectural improvement.

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

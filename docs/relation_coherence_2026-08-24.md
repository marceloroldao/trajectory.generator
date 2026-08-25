# Relation-coherence trajectory universe — 2026-08-24

Status: pre-alpha experimental result

## Objective

Test whether the causal state should summarize **relations between transitions** instead of carrying more raw past bits.

The local grammar remains memory-3. A four-bucket causal variable is reconstructed from the recovered prefix and controls which public selector policy is active. No coherence history is stored externally.

Three public relation updates were scanned:

```text
repeat      -> rewards persistence of the current transition relation
phase       -> accumulates a relation/phase consistency test
rolling_rel -> rolling finite accumulator over current and previous relations
```

All nontrivial four-bucket policy maps over the same five public selector profiles were tested.

## Main results

The relation-based causal variable extends the frontier, but the longer regimes remain fragile under one-bit perturbation.

Representative candidates:

```text
frontier  rate300   flip64    mode        policy_map
250       0.25005   3.31%     phase       (2, 0, 0, 4)
247       0.25368   2.33%     repeat      (2, 1, 4, 0)
220       0.28381   3.83%     repeat      (2, 0, 2, 4)
217       0.28900   1.34%     phase       (1, 2, 1, 4)
217       0.28728   2.34%     rolling_rel (4, 1, 1, 2)
```

The current balanced memory-3 coherence baseline remains:

```text
frontier 187
rate300  ~= 0.33602 bit/step
flip64   ~= 32.80%
```

Therefore none of the relation-coherence candidates improves the balanced Pareto frontier.

## Interpretation

This is another useful negative result. A scalar causal summary of transition relations can lower the entropy rate and extend the addressable trajectory, but the tested summaries do not preserve the large local neighborhood of admissible trajectories associated with the balanced memory-3 regime.

The experiment suggests that the next causal variable should not merely be another scalar accumulator. A stronger candidate should preserve **structured equivalence classes of trajectories** or a reversible phase relation, so that nearby trajectories can remain admissible without restoring full unconstrained entropy.

## Reproduction

```bash
python experiments/relation_coherence_search.py
```

The scan does not target phi, the plastic constant, tribonacci, or any named spectral value.

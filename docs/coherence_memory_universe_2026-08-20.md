# Accumulated coherence-memory universe — 2026-08-20

Status: pre-alpha experimental infrastructure

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

## Motivation

Previous experiments showed saturation when adding more selector layers based only on current history and phase. A fixed selector and a second-order dynamic selector both reached a moderate-entropy frontier around 184 steps. This suggests that additional selector hierarchy alone does not create new information capacity.

The present experiment adds a qualitatively different variable: finite causal memory of the path.

## Current implementation

`trajectory_generator/coherence_memory_universe.py` provides:

- a 3-bit local history;
- a configurable finite coherence accumulator;
- deterministic policy selection from the accumulator;
- exact dynamic counting of admissible suffixes;
- exact rank/unrank;
- reversible final-state permutation;
- exact decode from `(final_state, steps)`.

Three public coherence updates are implemented:

```text
occupancy  -> saturating memory of balanced/extreme successor states
signed_bit -> modular accumulated bit bias
rolling    -> finite rolling path accumulator
```

A small public policy bank is used only as a first search substrate. No golden ratio, plastic constant, tribonacci constant, or target spectral value is used in the coherence update.

## Important status

This commit intentionally does **not** claim a new frontier record.

Preliminary exploration showed that poorly chosen coherence dynamics easily fall into two extremes:

```text
too free  -> short 63-bit frontier
very rigid -> extremely long trajectories with near-zero information rate
```

The correct next step is therefore a reproducible search over coherence update + policy map, constrained to a moderate entropy-rate interval and evaluated jointly by:

- exact 63-bit frontier;
- finite-length entropy rate;
- perturbation survival;
- number of active policies/laws;
- occupancy/mixing diagnostics.

The search harness is in:

```text
experiments/coherence_memory_search.py
```

## Scientific interpretation

The new variable should not be interpreted as a hidden storage channel. If it is not derivable from the recovered prefix during decoding, the construction is invalid for this project's primary objective.

The useful question is narrower:

> Does a small deterministic causal memory change the admissible trajectory geometry enough to improve the capacity/robustness Pareto frontier while remaining exactly decodable from the final address and step count?

Until the scan is completed and independently checked, the answer remains open.

# Memory-order comparison — 2026-08-22

Status: experimental methodology / benchmark scaffold

## Objective

Test whether the capacity/robustness gains seen with causal coherence memory are specific to a 3-bit local history or persist when the local history order changes.

The target comparison is:

```text
memory = 2
memory = 3
memory = 4
```

while preserving the project contract:

```text
(final_state, steps) -> exact admissible trajectory
```

with no externally stored trajectory history.

## Why a new controlled benchmark is needed

The complete local-law space grows as:

```text
3^(2^memory)
```

so:

```text
memory 2 -> 81 laws
memory 3 -> 6,561 laws
memory 4 -> 43,046,721 laws
```

The memory-2 and memory-3 spaces can be scanned exhaustively. Memory 4 cannot be treated the same way without changing the computational scale by several orders of magnitude.

Therefore `experiments/memory_order_compare.py` introduces a controlled ablation using a deterministic canonical law bank of fixed size at every memory order. The default bank contains 256 laws generated reproducibly from `(memory, rule_id, seed)`.

This benchmark does **not** replace the exhaustive memory-2 / memory-3 scans. It answers a narrower question:

> Holding the candidate-bank size and selector semantics fixed, what changes when the local causal memory grows from 2 to 3 to 4 bits?

## Shared structure

Across all memory orders, the benchmark keeps fixed:

- the same number of candidate laws;
- the same five selector-policy weight vectors;
- four causal coherence buckets;
- the same `rolling` coherence update;
- the same coherence-to-policy map `(1, 3, 4, 0)`;
- the same public period-3 phase;
- the same 63-bit final address width.

Only the local-history order changes.

## Interpretation rules

A larger frontier alone is not sufficient evidence of improvement. Results must be interpreted jointly with finite-length information rate and, in a follow-up run, trajectory perturbation survival.

In particular:

```text
long frontier + near-zero information rate != useful improvement
```

and

```text
more local memory != more independent information by itself
```

The purpose of this test is structural robustness of the phenomenon, not a compression claim.

## Reproduction

```bash
python experiments/memory_order_compare.py --bank-size 256 --seed 12648430
```

The next benchmark revision should add exact rank/unrank for the canonical-bank comparison and one-bit perturbation survival so that memory orders 2, 3, and 4 can be compared on the same Pareto axes used elsewhere in the project.

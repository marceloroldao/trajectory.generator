# Controlled memory-order benchmark — 2026-08-22

Status: pre-alpha controlled ablation

## Objective

Test whether the accumulated-coherence effect observed at local memory 3 persists at memory lengths 2 and 4 while keeping the candidate-law bank size fixed.

Because the complete law space grows as `3^(2^m)`, exhaustive comparison is not symmetric across memory orders:

```text
m=2 -> 81 laws
m=3 -> 6,561 laws
m=4 -> 43,046,721 laws
```

The controlled benchmark therefore uses a deterministic canonical bank of 256 laws for each memory order, the same four coherence buckets, the same rolling update, the same policy map `(1,3,4,0)`, period 3, and width 63.

## Results

With seed `0xC0FFEE`:

| memory | frontier within scan | crossed 2^63 by 5,000? | rate at 300 | admissible count at 64 | one-bit survival at 64 |
|---:|---:|:---:|---:|---:|---:|
| 2 | >= 5,000 | no | 0.02557 bit/step | 46 | ~1.43% |
| 3 | >= 5,000 | no | 0.04763 bit/step | 890 | ~3.05% |
| 4 | 358 | yes, at 359 | 0.17782 bit/step | 14,591 | ~1.97% |

For memory 4, the exact crossing observed in this controlled bank is:

```text
358 steps -> 8,214,565,720,323,784,705 admissible trajectories
359 steps -> 11,721,368,630,169,610,921 admissible trajectories
```

## Interpretation

The apparent very long frontiers for memory 2 and 3 are **not improvements**. Their finite information rates are extremely low and only 46 / 890 trajectories remain at 64 steps, respectively. Under this canonical bank/selector combination they have become nearly deterministic grammars.

Memory 4 carries substantially more freedom in the same controlled setup and therefore reaches the 63-bit capacity limit sooner, at 358 steps. This does not establish that memory 4 is universally better; it establishes that memory order interacts strongly with the law bank and selector.

The main conclusion is methodological:

> Memory order cannot be ranked by frontier alone. A long frontier can be caused simply by eliminating almost all admissible trajectories.

A meaningful comparison must use at least:

```text
(frontier, entropy rate, trajectory robustness, active-state/law diversity)
```

The previously discovered memory-3 balanced profile with frontier 187 and ~32.8% one-bit survival remains a stronger Pareto point than any of these fixed-bank ablation results.

## Reproduction

```bash
python experiments/memory_order_compare.py --bank-size 256 --seed 12648430 --max-steps 5000 --samples 512
```

The benchmark is deterministic except for the seeded perturbation sample.
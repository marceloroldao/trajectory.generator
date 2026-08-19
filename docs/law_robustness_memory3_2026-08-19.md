# Memory-3 law robustness basins — 2026-08-19

Status: pre-alpha experimental result

## Question

Do recurring growth factors such as the golden ratio, plastic constant, and tribonacci constant occupy robust neighborhoods in the finite rule space, or do they occur only at isolated laws?

## Rule space

Memory 3 gives 8 history states. Each state chooses one of three actions:

- force next bit to 0;
- force next bit to 1;
- leave the next bit free.

Therefore there are exactly `3^8 = 6,561` laws.

Two laws are one-mutation neighbors when they differ at exactly one history state. Since one action can be changed to either of the other two, every law has exactly 16 one-mutation neighbors.

No target growth constant is used in constructing the rules.

## Metrics

For each law with spectral radius `lambda`, measure:

1. **same-neighbor fraction** — fraction of its 16 one-mutation neighbors with the same spectral radius after rounding to `1e-9`;
2. **mean absolute delta** — mean `|lambda_neighbor - lambda|` across the 16 neighbors;
3. **connected-component size** — number of same-lambda laws reachable through repeated one-mutation steps.

## Selected results

| growth class | laws | mean same-neighbor fraction | mean |Δlambda| | largest same-class component |
|---|---:|---:|---:|---:|
| plastic `1.324717957` | 524 | **0.37834** | 0.12494 | **196** |
| golden ratio `1.618033989` | 264 | **0.20644** | 0.13256 | **106** |
| tribonacci `1.839286755` | 12 | **0.08333** | 0.13052 | **4** |

Additional topology:

- golden-ratio class: 58 connected components, 38 isolated rules, largest component 106;
- plastic class: 40 connected components, 24 isolated rules, two largest components 196 and 196;
- tribonacci class: 6 connected components, 4 isolated rules, largest components 4 and 4.

Across all 6,561 laws, the average same-neighbor fraction is about **0.4004** and the average one-mutation `|Δlambda|` is about **0.1154**.

The zero-entropy / `lambda = 1` class is especially mutation-stable: its average same-neighbor fraction is about **0.7098**.

## Interpretation

The golden-ratio class is not merely a collection of isolated coincidences. A connected basin of 106 one-mutation-related laws shares the same asymptotic growth factor.

However, the plastic-constant class is structurally more robust in this specific memory-3 rule space: it occurs in more laws, has a higher probability of surviving a one-action mutation, and contains larger connected plateaus.

Therefore the current evidence does **not** support privileging `phi` as the unique attractor of local admissibility laws. The stronger conclusion is:

> finite local trajectory grammars contain multiple algebraic growth-rate basins with different sizes and mutation robustness.

This is a result about finite-state combinatorics, not a physical-law claim.

## Reproduction

```bash
python experiments/law_robustness_memory3.py
```

The scan uses NumPy for eigenvalue calculation.

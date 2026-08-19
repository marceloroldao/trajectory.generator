# Memory-3 local admissibility scan — 2026-08-19

Status: pre-alpha experimental result

## Objective

Test whether algebraic growth ratios observed in the memory-2 admissibility laws remain present when the local history is expanded from two bits to three bits.

Each 3-bit history state in `000..111` is assigned one of three public actions:

- force next bit to `0`;
- force next bit to `1`;
- leave next bit free in `{0,1}`.

There are therefore exactly

```text
3^8 = 6,561
```

local laws.

No golden ratio, plastic constant, tribonacci constant, Fibonacci recurrence, or other target constant is used to generate these laws.

## Method

For every rule, construct the 8x8 transition matrix over the three-bit history states. The asymptotic number of admissible trajectories grows approximately as

```text
N(n) ~ C * lambda^n
```

when the recurrent component is exponentially growing, where `lambda` is the spectral radius of the transition matrix.

The associated asymptotic information rate is

```text
h = log2(lambda) bits/step.
```

The scan also counts trajectories exactly to determine where a complete law family first exceeds a 63-bit address space.

## Main result

Across all 6,561 laws, the spectral radii clustered into approximately **193 distinct numerical values** at 1e-9 rounding.

Selected algebraic rates reappeared without being inserted into the rules:

| growth factor | approximate value | number of laws |
|---|---:|---:|
| golden ratio | 1.618033989 | **264** |
| plastic constant | 1.324717957 | **524** |
| tribonacci constant | 1.839286755 | **12** |

The most common spectral-radius classes included:

| lambda | laws |
|---:|---:|
| 1.000000000 | 2,181 |
| 1.324717957 | 524 |
| 1.465571232 | 522 |
| 1.380277569 | 370 |
| 1.220744085 | 319 |
| 1.618033989 | 264 |
| 1.167303978 | 120 |
| 1.272019650 | 106 |
| 1.512876397 | 96 |
| 1.403602125 | 88 |

The maximum possible rate remains `lambda = 2`, corresponding to one fully free bit per step.

## 63-bit frontier behavior

The complete-family frontier varies widely across laws.

For laws with `lambda > 1`, the frontier is finite and depends on both the asymptotic growth rate and finite-length transients. Frequently observed frontiers include approximately 89, 103, 111, 112, 125, 126, 131, 132, 149, 150, and 151 steps.

A large subset of laws did not exceed `2^63` trajectories within the first 1,000 steps. These are typically zero-entropy or very low-growth systems, especially those with spectral radius near 1.

This does not mean that such systems encode arbitrary long data. It means their allowed trajectory family grows slowly enough that raw step count can become very large while independent information remains bounded or subexponential.

## Interpretation

The memory-3 scan strengthens the earlier result in three ways.

First, the golden ratio is not a one-off consequence of a single hand-selected rule. It reappears in 264 distinct laws in this finite rule space.

Second, it is **not uniquely privileged**. The plastic constant appears even more frequently, and many other algebraic growth factors occur.

Third, the local-rule space produces a discrete spectral landscape. The natural quantity is therefore not a preferred irrational constant by itself, but the dominant eigenvalue selected by the transition grammar:

```text
local law -> transition graph -> spectral radius lambda -> entropy rate log2(lambda)
```

This is a precise mathematical mechanism by which ratios can emerge from constrained trajectories without being inserted as constants.

## Caution

These are combinatorial / finite-state-system results. They do not by themselves establish a physical law, a universal role for the golden ratio, or a new compression theorem.

The scientifically defensible statement is narrower:

> Small deterministic/local admissibility grammars naturally generate recurring algebraic trajectory-growth rates, including phi, the plastic constant, and the tribonacci constant.

## Reproduction

```bash
python experiments/local_law_memory3_scan.py
```

The experiment uses NumPy for eigenvalue analysis.

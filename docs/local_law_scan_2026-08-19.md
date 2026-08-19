# Local admissibility-law scan — 2026-08-19

Status: pre-alpha experimental result

## Objective

Systematically test small public local laws instead of hand-picking one law that happens to produce a desired ratio.

The scan uses binary trajectories with memory 2. The current state is the last two bits, so there are four history states:

```text
00, 01, 10, 11
```

For each history state, the law chooses exactly one of three actions:

```text
force next bit 0
force next bit 1
leave next bit free (0 or 1)
```

Therefore the complete search space contains

```text
3^4 = 81
```

distinct admissibility laws.

No golden ratio, Fibonacci sequence, plastic constant, tribonacci constant, or other target constant is inserted into the scan.

## Exact counting model

Each law defines a 4x4 adjacency matrix on the history states. If `v_n` counts admissible trajectories ending in each state, then

```text
v_(n+1) = v_n A
N(n) = sum(v_n)
```

The asymptotic number of admissible trajectories is governed by the spectral radius `lambda` of `A`:

```text
N(n) ~ C * lambda^n
```

and the asymptotic information rate is

```text
h = log2(lambda) bits/step.
```

For a fixed 63-bit final address, a law remains globally exactly addressable only while

```text
N(n) <= 2^63.
```

## Result

Across all 81 laws, the scan finds only nine distinct asymptotic growth factors (rounded to 12 decimal places):

| lambda | representative algebraic factor | laws | representative 63-bit frontier |
|---:|---|---:|---:|
| 1.000000000000 | `x - 1` | 42 | unbounded or eventually constant/periodic within scan horizon |
| 1.220744084606 | `x^4 - x - 1` | 2 | 213 |
| 1.324717957245 | `x^3 - x - 1` | 8 | 153 |
| 1.380277569098 | `x^4 - x^3 - 1` | 2 | 133 |
| 1.465571231877 | `x^3 - x^2 - 1` | 10 | 113 |
| 1.618033988750 | `x^2 - x - 1` | 12 | 90 |
| 1.754877666247 | `x^3 - 2x^2 + x - 1` | 2 | 77 |
| 1.839286755214 | `x^3 - x^2 - x - 1` | 2 | 71 |
| 2.000000000000 | `x - 2` | 1 | 63 |

The value

```text
1.324717957245...
```

is the plastic constant, the real root of `x^3 - x - 1 = 0`.

The value

```text
1.618033988750...
```

is the golden ratio, the positive root of `x^2 - x - 1 = 0`.

The value

```text
1.839286755214...
```

is the tribonacci constant, the dominant root of `x^3 - x^2 - x - 1 = 0`.

These constants appear because finite-state local constraints produce integer transition matrices whose dominant eigenvalues are algebraic integers. Their appearance is therefore structural/combinatorial, not evidence that any one constant is a universal physical law.

## Interpretation

The important observation is not merely that `phi` appears. A whole discrete spectrum of growth rates appears naturally from the finite rule space.

This gives the project a stronger experimental language:

```text
local law -> transition graph -> spectral radius -> entropy rate -> address frontier
```

The growth factor `lambda` measures how rapidly the number of physically/admissibly possible trajectories expands. The information rate is `log2(lambda)` rather than one bit per raw step.

A law with `lambda = 2` leaves every next bit free and therefore carries one independent bit per step. A law with `lambda < 2` removes degrees of freedom. A law with `lambda = 1` produces no asymptotic information growth.

## Why this matters for trajectory.generator

The project originally asked whether a long history could be recovered from a much smaller final state. The correct criterion is now explicit:

```text
log2 |A_n| <= state_width
```

where `A_n` is the set of trajectories allowed by the public law.

The next step is to search larger but still finite law spaces (memory 3, time-phased rules, and reversible state-machine constraints) and compare:

- entropy rate;
- 63-bit frontier;
- recurrence order;
- robustness to bit/state perturbations;
- whether the rule remains useful rather than collapsing to a deterministic trivial orbit.

## Reproduction

```bash
python experiments/local_law_scan.py
```

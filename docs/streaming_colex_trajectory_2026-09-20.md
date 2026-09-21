# Streaming colex trajectory — 2026-09-20

## Purpose

The existing hierarchical trajectory codec already reaches the exact
information-theoretic capacity of the family

```text
binary trajectories with at most K changes
```

but it operates in batch form: find all change positions, rank the complete
combination, and later unrank the complete combination.

This experiment keeps the same admissible family and the same exact capacity,
but turns the address into a **step-by-step reversible state machine**.

## Colex address

For `r` change positions

```text
1 <= s_1 < s_2 < ... < s_r <= n
```

define the colex rank

```text
C(S) = sum( binom(s_i - 1, i), i=1..r )
```

Exact-`r` sets occupy a public bucket of size

```text
binom(n,r).
```

The sparse address places these buckets consecutively for

```text
r = 0..K.
```

The initial binary value is a second public block, so the total family size is
exactly

```text
M(steps,K) = 2 * sum(binom(steps-1,r), r=0..K).
```

This is the same count used by `hierarchical_trajectory.py`.

## Online forward law

Suppose the current prefix has `n` possible change positions and already has
`r` changes with within-bucket colex address `c`.

If the next bit does not change:

```text
r' = r
c' = c
```

If the newest position `n+1` is a change:

```text
r' = r + 1
c' = c + binom(n, r+1)
```

This is the key colex property: because the appended change is necessarily the
new largest position, the address update is local.

## Local reverse law

At reverse time, let the current set contain `r` changes among `n` positions.

Exact-`r` combinations that do **not** contain the newest position `n`
occupy:

```text
0 <= c < binom(n-1,r).
```

Combinations that **do** contain `n` occupy the remaining suffix:

```text
binom(n-1,r) <= c < binom(n,r).
```

Therefore:

```text
change_at_n = 1  iff  c >= binom(n-1,r)
```

and, when the change is present:

```text
c_prev = c - binom(n-1,r)
r_prev = r - 1.
```

No list of change positions is reconstructed.

## Binary value recovery

The current bit is also local.

If the initial bit is `b0`, then after `r` changes:

```text
b_current = b0 XOR (r mod 2).
```

So each reverse step recovers both:

- the newest bit value;
- whether the newest transition was a change.

The predecessor address is then reconstructed and the process repeats.

## 63-bit result

For:

```text
width = 63
K = 5
```

the exact frontier is:

```text
14,082 steps
```

At that horizon:

```text
valid states = 9,222,784,404,533,559,556
2^63         = 9,223,372,036,854,775,808
occupancy    ~= 99.9936289%
```

At 14,083 steps the complete admissible family is already larger than
`2^63`.

So this construction does not merely approach the capacity bound: for this
family it uses the exact enumerative address space, and the 14,082-step frontier
is the true 63-bit limit under the stated `K=5` constraint and free initial
bit.

## What is new relative to the earlier hierarchical codec

The admissible family and capacity are **not new**.

The new result is the mechanics:

```text
batch rank/unrank
        ->
online reversible state update + local reverse decision
```

The decoder no longer needs to unrank all change positions before regenerating
the trajectory.

Each step needs only:

- current state/address;
- current public step count;
- public `K`;
- binomial arithmetic over at most `K+1` count buckets.

For fixed `K`, the logical work per step is constant with respect to the total
trajectory length, although the integers themselves grow with state width.

## Relation to the algebraic root trajectory

The algebraic root construction remains useful because its branch test is a
direct field equation:

```text
P(t+1) = 0.
```

The streaming colex construction is denser and reaches exact enumerative
capacity; the root-polynomial construction has a more explicitly algebraic
state geometry.

They should therefore be treated as two reference points for the next stage:

1. **streaming colex:** optimal state occupancy;
2. **root polynomial:** simple algebraic local geometry.

The next useful question is whether an endogenous universe can combine the
algebraic geometry of the second with the near-perfect state occupancy and
streaming reversibility of the first.

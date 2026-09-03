# Information-time coordinate — 2026-09-02

Status: experimental / exact within the selected recurrent macrograph

## Motivation

The previous entropy decomposition suggested introducing an accumulated information time

```text
tau_I = sum_k Delta I_k
```

where only actual branch choices contribute information.

A first path-wise definition used the exact finite-horizon continuation counts. That produced an important correction: under a uniform distribution over all admissible trajectories of a fixed physical length `t`, the chain of conditional branch probabilities telescopes. Every trajectory of that same horizon has exactly

```text
tau_H(t) = log2 |A_t|.
```

Therefore `tau_H` is a family-level entropy coordinate. It does not distinguish trajectories with the same final horizon.

## Intrinsic recurrent-orbit coordinate

For the dominant recurrent core of the topological candidate `(0,2,4,4)`, use the Parry / maximum-entropy probabilities of the variable-length branch macrograph.

The macrograph has two recurrent branch states and four macro-edges with physical lengths

```text
A -> B : 1
A -> A : 12
B -> A : 2
B -> A : 5
```

Its physical-time growth constant is

```text
lambda = 1.2061897001179...
h = log2(lambda) = 0.270456820917216... bit / physical step
```

For an edge `i -> j` of length `L`, the maximum-entropy edge probability is

```text
p(i -> j, L) = lambda^(-L) * r_j / r_i
```

where `r` is the positive right eigenvector of the transfer matrix at the critical lambda.

Define the orbit potential

```text
Phi(i) = log2(r_i).
```

Then the information surprise of one macro-edge is exactly

```text
-log2 p = h*L + Phi(i) - Phi(j).
```

Summing over a complete recurrent macro-path makes all internal potential terms cancel:

```text
tau_orb = h*T + Phi(start) - Phi(end).
```

This is an exact identity for the selected macrograph.

## Numerical values

Using the current branch ordering:

```text
r = [0.8290569882185653, 0.8945582482427992]
Phi = [-0.2704568209172163, -0.1607526699438189] bits
Phi(A)-Phi(B) = -0.1097041509733973 bit
```

The four macro-edge probabilities and information surprises are approximately:

```text
A -> B, L=1  : p=0.8945582482, surprise=0.1607526699 bit
A -> A, L=12 : p=0.1054417518, surprise=3.2454818510 bit
B -> A, L=2  : p=0.6370074750, surprise=0.6506177928 bit
B -> A, L=5  : p=0.3629925250, surprise=1.4619882556 bit
```

Every value satisfies

```text
surprise = h*L + Phi(source)-Phi(target)
```

to numerical precision.

## Interpretation

This gives two distinct coordinates:

```text
t          = physical trajectory time
tau_H(t)   = finite-horizon family entropy
tau_orb    = intrinsic recurrent-orbit information coordinate
```

`tau_orb` is not simply a count of branch events. A long rare deterministic return can carry more information than a short common transition.

More importantly, in this recurrent core the internal event history collapses to a boundary term plus elapsed physical time. Once `(start orbit state, end orbit state, T)` are fixed, the maximum-entropy information coordinate is fixed too.

This resembles an additive potential/action decomposition, but it should not be interpreted as a physical law. It is an exact property of this finite-state symbolic dynamical system.

## Consequence for trajectory equivalence

Two recurrent paths satisfy the same intrinsic information coordinate if

```text
h*T1 + Phi(s1)-Phi(e1)
=
h*T2 + Phi(s2)-Phi(e2).
```

For the same start and end orbit states, equal `tau_orb` implies equal physical duration because `h>0`.

Different boundary orbit states can shift the coordinate by the fixed potential gap, so the natural state space is not `(X,t,tau)` with three independent coordinates. In this core, `tau_orb` is constrained by

```text
tau_orb - h*t = Phi(start)-Phi(end).
```

That suggests the next useful object is the **orbit potential Phi**, or an analogous state function on the full causal graph, rather than another independent clock.

## Reproduction

```bash
python experiments/information_time_coordinate.py
```

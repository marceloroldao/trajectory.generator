# Global information potential — 2026-09-02

Status: experimental / spectral diagnostic

## Question

The recurrent two-branch orbit obeys the exact identity

```text
-log2 p(i->j) = h + Phi(i) - Phi(j)
```

with `h = log2(lambda)` and `Phi(i)=log2 r_i` for the Parry/max-entropy right eigenvector.

This experiment asks whether one finite scalar potential `Phi(X)` extends to the **entire** phase-lifted causal graph of the selected topological universe `params=(0,2,4,4)`.

## Result

The complete graph contains:

```text
192 causal states = history3 * topology3 * phase3
```

Its dominant spectral rate is

```text
lambda_global ~= 1.2061897001179
h_global      ~= 0.270456820917 bit / physical step
```

which is the same dominant rate already measured in the 14-state recurrent orbit core.

However, the dominant non-negative right Perron eigenvector has positive support on only:

```text
121 / 192 states
```

and zero support on:

```text
71 / 192 states.
```

The 121 positive-support states are **exactly the reverse-reachable basin of the dominant 14-state recurrent core**: every one of them can eventually feed that core.  The 71 zero-support states cannot.

Among the eight public initial causal states, five lie in the dominant basin and three do not.

## Exactness on the dominant basin

For every edge whose source and target both have positive Perron support, define

```text
p(i->j) = r_j / (lambda * r_i)
Phi(i)  = log2(r_i)
```

for the unweighted unit-time graph.

Numerically, the identities close to machine precision:

```text
max stochastic-row residual  ~= 4.44e-15
max edge-potential residual   ~= 2.69e-16 bit
```

Therefore inside the dominant basin,

```text
-log2 p(i->j) = h + Phi(i) - Phi(j)
```

is an exact spectral identity up to floating-point error.

There are also 44 graph edges from positive-support states toward zero-support states. Under the global maximal-entropy Parry measure these exits have probability zero: asymptotically they lose against trajectories that remain capable of feeding the maximal-growth recurrent class.

## Other recurrent regimes

The SCC spectrum contains the dominant component

```text
rho ~= 1.2061897001179
nodes = 14
internal edges = 16
```

and several recurrent components with

```text
rho = 1
```

including components of 6 and 3 states. These subdominant recurrent regions remain valid deterministic/low-entropy dynamics, but they do not share the dominant maximal-entropy measure with finite positive potential.

This means the mathematically clean decomposition is **piecewise**:

```text
dominant basin:       h = log2(1.2061897001179), finite Phi_dom
subdominant SCCs:     their own local h_c = log2(rho_c), Phi_c
transient connectors: boundary relations between those regimes
```

For the observed rho=1 recurrent components,

```text
h_c = 0 bit/step,
```

so they behave as asymptotically deterministic or non-expanding orbit classes.

## Interpretation

The attempted single global formula

```text
Delta I = h Delta t + Phi(X_t) - Phi(X_{t+1})
```

is **not finite on every state of the full reducible graph** if `h` is chosen as the global maximal-growth rate.

What survives is stronger and more precise:

```text
Each spectral basin admits its own information rate and potential.
```

The dominant informational universe is therefore not all 192 causal states uniformly. It is a 121-state basin flowing toward a 14-state recurrent orbit that carries the maximal asymptotic information production.

This is a result about the present symbolic automaton, not a claim about physical spacetime.

## Reproduction

```bash
PYTHONPATH=. python experiments/global_information_potential.py
```

The GitHub Actions workflow is:

```text
.github/workflows/global-information-potential.yml
```

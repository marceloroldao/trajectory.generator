# Information clock from recurrent branch events — 2026-09-02

Status: pre-alpha structural analysis

## Objective

Test whether the information growth of the balanced topological trajectory universe can be described by branch events rather than by every physical transition.

The analyzed candidate is the previously selected topological policy:

```text
params = (0, 2, 4, 4)
frontier ~= 221 steps
sampled one-bit survival ~= 14.16%
```

Its dominant phase-lifted recurrent core contains 14 causal states and only two internal branch states.

## Macrograph

Collapsing every deterministic flight between branch states produces only two macro states, A and B, and four macro transitions:

```text
A -> B : 1 physical step
A -> A : 12 physical steps
B -> A : 2 physical steps
B -> A : 5 physical steps
```

No information is discarded by this graph condensation for the recurrent-core path language: the deterministic intermediate states are implied by the selected macro edge.

## Physical-time growth from the macrograph

For a candidate physical-time growth factor `lambda`, give each macro edge of physical length `L` weight

```text
lambda^-L
```

The weighted transfer matrix is

```text
W(lambda) = [ lambda^-12               lambda^-1 ]
            [ lambda^-2 + lambda^-5          0   ]
```

The physical-time growth factor is the positive value for which the spectral radius of `W(lambda)` is one. Equivalently:

```text
1 - lambda^-12 - lambda^-3 - lambda^-6 = 0
```

or

```text
lambda^12 - lambda^9 - lambda^6 - 1 = 0.
```

The positive root is

```text
lambda ~= 1.206189700118
```

which matches the dominant spectral radius of the full 14-state recurrent core.

Therefore the information rate is

```text
log2(lambda) ~= 0.270456820917 bit / physical step.
```

This is an exact structural equivalence of growth rates, not merely a visual analogy.

## Information-clock statistics

Under the maximal-entropy path measure of the macrograph, the branch-state stationary probabilities are approximately:

```text
A : 0.52782753
B : 0.47217247
```

The macro-edge choices are approximately:

```text
from A:
  A -> B, length 1  : 0.89455825
  A -> A, length 12 : 0.10544175

from B:
  B -> A, length 2  : 0.63700748
  B -> A, length 5  : 0.36299252
```

This gives

```text
average physical steps / branch event ~= 2.59856335
entropy / branch event               ~= 0.70279918 bit
```

and the consistency check is

```text
0.70279918 / 2.59856335 ~= 0.27045682 bit / physical step.
```

So physical time and information time are measurably different coordinates of the same path language.

## Interpretation

For this recurrent core, most physical transitions are deterministic. New path entropy enters only at the two branch states. The trajectory can therefore be represented conceptually as

```text
branch event -> deterministic flight -> branch event -> ...
```

rather than treating every transition as an independent information-bearing event.

This does **not** bypass the information bound. The variable physical durations of the macro edges are part of the public dynamics, and the macro-event entropy still reproduces the same total entropy per physical step.

The useful result is narrower:

> The recurrent trajectory language admits an exact information-clock description in which branch events are the entropy-bearing events and deterministic intermediate transitions are consequences of the universe dynamics.

This is currently the strongest formal version in the project of the distinction between physical step count `t` and information-event count `k`.

## Next test

The next experiment should build a rank/unrank representation directly on the variable-length macrograph and verify that a trajectory segment inside the recurrent basin can be regenerated from its macro-event address plus public physical length. If successful, it will provide an operational branch-event codec rather than only a structural analysis.

## Reproduction

```bash
python experiments/information_clock_macrograph.py
```

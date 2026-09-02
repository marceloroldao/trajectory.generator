# Topological transition state — 2026-09-02

Status: pre-alpha / partial Pareto improvement

## Objective

Preserve more of the *shape of the trajectory* than scalar coherence or a single four-state orbit label.

The causal variable `Q_t` is an 8-state relation-history topology containing the last three transition/motion bits. It is updated deterministically from the recovered path and is not side metadata.

The selector remains compact. Rather than storing an arbitrary map from 8 topology classes to 5 policy profiles, the active policy is computed by:

```text
policy(Q,t) = (a*popcount(Q) + b*Q + c*(t mod 3) + d) mod 5
```

with `a,b,c,d in {0,1,2,3,4}`. The complete 5^4 = 625 formula family is scanned.

## Results

The strongest capacity-oriented candidate in the moderate-rate window reached:

```text
params    = (3, 2, 0, 3)
frontier  = 247 steps
rate300   ~= 0.25052 bit/step
```

Its perturbation tolerance is still low, so it is not a balanced reference.

Three representative Pareto points after higher-sample validation are:

```text
params=(1,0,0,2)
frontier=208
N(208)=8,484,982,157,878,442,411
N(209)=10,357,991,777,215,491,665
rate300 ~= 0.2978454
flip64 ~= 14.86%

params=(0,2,4,4)
frontier=221
N(221)=9,131,204,053,820,206,208
N(222)=10,214,739,716,735,776,832
rate300 ~= 0.2808097
flip64 ~= 14.16%

params=(3,2,4,4)
frontier=239
N(239)=8,736,326,121,603,609,111
N(240)=9,803,398,575,756,959,808
rate300 ~= 0.2576497
flip64 ~= 12.66%
```

The perturbation values above use 1,024 sampled admissible 64-step trajectories and test every single-bit flip.

## Comparison

Current balanced memory-3 coherence baseline:

```text
frontier ~= 187
flip64   ~= 32.8%
```

Previous best simple 4-state orbit-class candidate:

```text
frontier = 200
flip64   ~= 9.57%
```

Topological 8-state relation history:

```text
frontier = 221
flip64   ~= 14.16%
```

or, if more capacity is preferred:

```text
frontier = 239
flip64   ~= 12.66%
```

Thus the topological state does not yet dominate the balanced reference, but it improves the capacity/robustness trade-off relative to the simpler structural-class and scalar-coherence experiments.

## Interpretation

This result supports a narrower hypothesis:

> preserving a finite *structure of relations* is more useful than collapsing trajectory history into a scalar score.

However, the remaining robustness gap is large. More state classes alone should not be added blindly, because that risks becoming equivalent to simply increasing raw memory.

A better next step is to ask whether the topology can identify **closed cycles / return classes**. If some relational states return to an equivalent class after a public cycle, that could provide an orbit-like invariant rather than merely a longer relation history.

## Reproduction

```bash
python experiments/topological_transition_state.py
```

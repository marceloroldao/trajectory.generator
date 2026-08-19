# Memory-3 selector policy search — 2026-08-19

Status: pre-alpha exploratory result

## Objective

Search selector policies over all `3^8 = 6,561` memory-3 laws without targeting a named algebraic constant.  The selector sees only public features of the current history, public phase, and candidate rule grammar.

The decoder still receives only `(final_state, steps)` plus the public deterministic policy.

## Search space

Each candidate selector assigns integer weights to nine features:

1. restoring forced move at extreme histories;
2. phase-dependent freedom in balanced histories;
3. number of balanced next-state options;
4. preference for a forced current action;
5. preference for a free current action;
6. global balance between free and forced entries in the grammar;
7. force-0 / force-1 symmetry;
8. number of forced transitions leading to balanced-popcount states;
9. coverage of next history states.

A seeded exploratory sweep (`seed=7`, 300 policies) was used.  This is a model-selection experiment and can overfit the chosen diagnostics; the selected policies are therefore candidates, not universal laws.

## Two informative Pareto points

### Balanced candidate

Weights:

```text
(0, 1, 3, 3, 0, 1, 0, 3, 0)
```

Measured properties:

```text
63-bit exact frontier:       184 steps
finite-length rate @300:     ~0.337 bit/step
active laws across contexts: 5
free context fraction:       0.25
sampled 1-bit survival:      ~0.335
```

This candidate improves substantially on the earlier hand-designed coherence universe (117-step frontier) while retaining much more perturbation tolerance than the longest policy found in the same search.

### Longer but rigid candidate

One longer-frontier policy reached about:

```text
63-bit frontier:       202 steps
rate @300:             ~0.307 bit/step
active laws:           8
1-bit survival:        ~0.024
```

It therefore gains addressable trajectory length mainly by becoming very restrictive.  It is retained as a distinct Pareto point rather than treated as the winner.

## Interpretation

The search supports a trade-off rather than a unique optimum:

```text
longer exact frontier <-> lower entropy / greater rigidity
higher perturbation tolerance <-> larger admissible family
```

The balanced candidate is useful because it exceeds the previous 117-step dynamic-universe result without collapsing to near-deterministic behavior.

No golden ratio, plastic constant, tribonacci constant, or target spectral radius appears in the selector objective.

## Reproduction

```bash
python experiments/policy_search_memory3.py --samples 300 --seed 7
python -m unittest tests.test_policy_universe -v
```

The exact codec is in `trajectory_generator/policy_universe.py`.

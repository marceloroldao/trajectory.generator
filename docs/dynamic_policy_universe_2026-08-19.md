# Second-order dynamic policy universe — 2026-08-19

Status: pre-alpha experimental result

## Objective

Allow the selector policy itself to vary deterministically with the current 3-bit history and public phase, while preserving exact recovery from only `(final_state, steps)` plus the public machine definition.

The policy sequence is not stored externally.

## Construction

The selector still scores all `3^8 = 6,561` memory-3 laws using the same nine structural features as the fixed policy experiment. The difference is that the weight vector is selected from three public profiles according to context:

- extreme histories (`popcount` 0 or 3);
- balanced histories during phase 1;
- other balanced histories.

Thus the causal chain is:

```text
(history, phase)
  -> active policy weights
  -> selected local law
  -> allowed transition(s)
  -> next history
```

Both the active policy and active law are regenerated during decoding.

## Result

The selected moderate-entropy second-order policy has:

```text
184 steps -> 2^63 admissible trajectories
185 steps -> 2^64 admissible trajectories
```

Therefore its exact 63-bit frontier is still:

```text
184 steps
```

Its asymptotic/finite-length information rate at 300 steps is approximately:

```text
0.34 bit/step
```

It uses **12 distinct laws** across the 24 `(history, phase)` contexts, compared with 5 laws for the frozen 184-step policy.

Six of the 24 contexts are free transitions, giving a 25% free-context fraction.

A sampled one-bit perturbation experiment at 64 steps (`1024` trajectories, fixed seed `123`) gave approximately:

```text
32.37% perturbation survival
```

## Interpretation

The second-order policy increases internal law diversity without increasing raw addressable trajectory length. This is an important negative result:

> Making the policy layer more dynamic does not automatically create more information capacity.

In this construction the family lands on exactly one new free degree of freedom per three trajectory steps after the initial memory prefix. Consequently the 63-bit frontier is exactly saturated at 184 steps.

A broader exploratory search did find much longer frontiers, including candidates beyond 400 steps, but those candidates had extremely low information rates (roughly `0.03–0.05 bit/step`) and therefore represent highly constrained families rather than a superior balanced universe.

Under a moderate-rate constraint (`0.25 <= h <= 0.5 bit/step`), no sampled second-order policy exceeded the frozen-policy frontier of 184 steps in this run.

This does not prove that 184 is globally optimal. It shows that added policy dynamics alone did not beat the current balanced baseline under the tested search family.

## Reproduction

```bash
python experiments/dynamic_policy_search_memory3.py
python -m unittest tests.test_dynamic_policy_universe -v
```

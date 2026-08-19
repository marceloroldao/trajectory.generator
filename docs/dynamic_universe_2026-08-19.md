# State-and-phase dynamic universe — 2026-08-19

Status: pre-alpha experimental result

## Question

Can the "universe" participate by changing which local admissibility law is active, while exact recovery still uses only `(final_state, steps)` plus the public machine definition?

## Construction

The experiment keeps memory 3 and a public bank of ordinary local laws. At step `t`, the active law is selected from the current history state and public time phase:

```text
rule_index = (popcount(history) + (t mod period)) mod number_of_rules
```

The selected rule then decides whether the next bit is forced to 0, forced to 1, or free.

No rule schedule is stored. Encoder and decoder independently derive the same active rule from `(history, t)`.

The exact codec ranks/unranks trajectories by dynamic programming over the enlarged state `(history, time phase)`.

## Representative results

Period = 3, width = 63.

| rule bank | effective lambda | entropy rate bits/step | 63-bit frontier |
|---|---:|---:|---:|
| plastic + phi | 1.429803160 | 0.515816546 | **120** |
| phi + tribonacci | 1.680377145 | 0.748785069 | **83** |
| plastic + tribonacci | 1.527725759 | 0.611385588 | **101** |
| plastic + phi + tribonacci | 1.497185456 | 0.582252939 | **106** |

The effective lambda is estimated from exact admissible-family counts over a long interval. Because the selector is periodic in time, single-step count ratios can oscillate; the multi-step geometric growth rate is the relevant quantity.

## Interpretation

The dynamic universe can produce an information-growth rate that is not identical to any rule in its bank.

For example, the plastic+phi bank produces

```text
lambda_eff ~= 1.429803
```

which lies between the static plastic and phi growth rates and gives a 63-bit frontier of 120 steps.

This is a concrete form of co-evolution:

```text
current state + public phase -> active law -> allowed transition -> next state
```

The universe is no longer merely a reversible permutation applied after encoding. It participates in determining which transitions exist.

However, this remains a finite-state constrained-family codec. It is not arbitrary-data compression beyond the information-theoretic limit. The gain in raw trajectory length comes from the dynamic law reducing the number of independent choices.

## Exact recovery

`trajectory_generator/dynamic_law_codec.py` provides exact rank/unrank and encoding/decoding. The decoder receives only:

```text
final_state
steps
public DynamicLawConfig
```

The active-law sequence is reconstructed rather than stored.

## Reproduction

```bash
python experiments/dynamic_universe_scan.py
python -m unittest tests.test_dynamic_law_codec -v
```

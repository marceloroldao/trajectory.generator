# Full information-clock codec — 2026-09-02

Status: experimental / exact equivalence result

## Objective

Extend the branch-aligned recurrent-core information clock to the **complete** topological trajectory universe for candidate:

```text
params = (0, 2, 4, 4)
```

The complete representation must include:

```text
transient entry
+ branch events
+ deterministic flights
+ final partial flight
```

without supplying any of those offsets or events as side metadata.

Decoder contract remains:

```text
(final_state, physical_steps)
```

plus the public machine definition.

## Important correction during validation

The first implementation (`experiments/full_information_clock_codec.py`) misclassified a deterministic flight that returned to its **source branch node** as a branchless deterministic cycle. This caused under-counting beginning at physical length 8.

Independent step-by-step counting exposed the error immediately.

The corrected implementation is:

```text
experiments/full_information_clock_codec_v2.py
```

The rule is simple but critical: after a deterministic transition, test whether the next node is a branch node **before** generic cycle detection.

## Exact equivalence test

Two independent counts are compared.

### Stepwise reference

Propagate every admissible edge one physical transition at a time through the original phase-lifted causal graph.

### Information-clock count

Skip deterministic runs in chunks and sum only when a true branch node is reached. If the requested physical length ends inside a deterministic flight, that partial tail contributes exactly one continuation for the already-selected branch event.

For every tested length:

```text
macro/event count == stepwise original count
```

The corrected implementation was independently checked through the small-length test range and rank/unrank was checked over many paths per length.

## Capacity boundary

The full causal path begins with a 3-bit history. Therefore:

```text
bits represented = physical transitions + 3
```

Near the 63-bit address limit the exact full-family counts are:

```text
physical  total bits  admissible trajectories       fits 63 bits
215       218         5,203,327,975,191,509,899     yes
216       219         5,820,770,252,654,087,216     yes
217       220         6,862,834,056,478,043,753     yes
218       221         9,131,204,053,820,206,208     yes
219       222        10,214,739,716,735,776,832     no
220       223        12,043,434,212,870,513,151     no
221       224        16,024,146,059,990,343,800     no
```

Since:

```text
2^63 = 9,223,372,036,854,775,808
```

the complete information-clock family fits through:

```text
218 physical transitions
= 221 total recovered bits
```

and fails at:

```text
219 physical transitions
= 222 total bits
```

This matches the previously observed frontier of the full topological machine once the 3-bit initial history is accounted for.

## Why this matters

The information clock does **not** enlarge the semantic family and does not evade the information bound. Instead, it proves that the same full trajectory language can be represented structurally as:

```text
initial causal state
-> deterministic time
-> information event
-> deterministic time
-> information event
-> ...
-> partial deterministic tail
```

Only branch events increase the path count. Deterministic physical transitions advance ordinary time without introducing a new independent choice.

Therefore two clocks are operationally meaningful:

```text
t = physical transition count
k = information-event count
```

The full path can be reconstructed exactly even though the internal rank/unrank algorithm reasons primarily in terms of `k` and variable flight lengths.

## Interpretation

This result supports a precise, limited statement:

> For this finite causal universe, information growth is localized at branch events; deterministic transitions carry forward previously selected information but do not create a new branch degree of freedom.

It does **not** establish a physical law about nature. It is a computational property of the tested admissibility grammar.

## Files

```text
experiments/information_clock_macrograph.py
experiments/information_clock_codec.py
experiments/full_information_clock_codec.py      # superseded first draft
experiments/full_information_clock_codec_v2.py   # corrected exact codec
```

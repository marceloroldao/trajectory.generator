# Information entropy decomposition — 2026-09-02

Status: experimental / exact finite-length decomposition

## Question

After proving that the full topological trajectory family can be reconstructed through an information-clock representation, ask where the actual information growth occurs.

For fixed physical length `n`, take the uniform distribution over all admissible causal paths of that exact length and decompose:

```text
log2 |A_n|
```

by the chain rule over public causal choices.

Categories:

```text
initial causal-state choice
transient branch outside dominant recurrent core
branch at core node that exits the core
branch whose alternatives both remain inside the recurrent core
```

## Boundary case

At the exact 63-bit boundary of the complete topological family:

```text
physical transitions = 218
total recovered bits = 221
admissible paths = 9,131,204,053,820,206,208
entropy = 62.985510816588 bits
```

The entropy decomposition is:

```text
initial state          2.019445939804 bits   3.2062%
transient branches     0.731225156439 bits   1.1609%
core exit branches     2.473773731970 bits   3.9275%
core internal branches 57.761065988374 bits 91.7053%
```

The chain-rule sum equals the complete path entropy:

```text
2.019445939804
+ 0.731225156439
+ 2.473773731970
+57.761065988374
=62.985510816588 bits
```

within floating-point precision.

## Interpretation

For this machine at this finite length, about **91.7% of all trajectory information is localized at branch decisions that remain inside the dominant recurrent orbit core**.

The transient region and initialization are not irrelevant, but together they account for only a small fraction of the address entropy near the capacity boundary.

This gives a more precise operational version of the information-clock idea:

```text
physical time advances at every transition
information time advances mainly at recurrent branch events
```

A branch event should not automatically be treated as one full bit. Its information contribution depends on the continuation counts of its alternatives:

```text
H(event | current causal state, remaining physical time)
```

Thus the correct information clock is entropy-weighted rather than merely a branch counter.

## Important limitation

This is a computational result for one finite deterministic/admissibility grammar. It is not evidence that physical information in nature must obey the same decomposition.

## Reproduction

```bash
python experiments/information_entropy_decomposition.py
```

# Operational information-clock codec — 2026-09-02

Status: pre-alpha constrained recurrent-basin codec

## Objective

Turn the recurrent-core information clock into an operational exact codec.

The scope is deliberately narrower than the full topological trajectory family: segments must start and end at one of the two branch states of the dominant recurrent core for the candidate

```text
params = (0, 2, 4, 4)
```

Within that branch-aligned recurrent language, the decoder receives only

```text
(final_state, physical_steps)
```

plus the public machine definition.

It does **not** receive the macro-event sequence, starting branch, intermediate states, or transition bits.

## Macro language

The recurrent core condenses to two branch states, A and B, with four public macro edges:

```text
A -> B : length 1
A -> A : length 12
B -> A : length 2
B -> A : length 5
```

A macro path is valid for physical length `n` only when the sum of its edge lengths is exactly `n`.

The dynamic-programming count is

```text
C(q,0) = 1
C(q,n) = sum(C(q', n-L_e))
```

over outgoing macro edges `e=(q->q', L_e)`.

This permits exact lexicographic rank/unrank without storing the sequence of branch choices.

## Addressing

The macro-path rank is mapped reversibly into the 63-bit final address by a public odd modular affine permutation mixed with a public function of `physical_steps`.

Decoding performs the inverse permutation, un-ranks the variable-length macro path, and expands every macro edge back into its full deterministic causal-state flight.

The bit trajectory is then regenerated from the 3-bit history in the initial causal node plus the appended bit visible in each successor history state.

For a segment of `n` physical transitions, reconstruction yields

```text
n + 1 causal nodes
n + 3 trajectory bits
```

(the first three bits define the initial history state).

## Self-test

`experiments/information_clock_codec.py` exhaustively/partially checks, for small physical lengths:

```text
rank -> unrank -> rank
address -> decode
macro path -> full causal path
causal path -> transition bits
```

No macro-event metadata is supplied to the decoder.

## 63-bit capacity by exact physical length

Because physical length is known externally as part of the contract, each exact length has its own admissible family. Variable-length macro edges make these counts mildly non-monotonic near the capacity boundary.

Representative exact counts are:

```text
230 -> 3,495,391,431,926,239,764   fits
231 -> 7,402,785,320,241,858,195   fits
232 -> 3,907,393,888,315,618,431   fits
233 -> 6,133,984,358,677,405,281   fits
234 -> 12,990,982,626,511,308,208  exceeds 2^63
235 -> 6,856,998,267,833,902,927   fits
236 -> 10,764,392,156,149,521,358  exceeds 2^63
```

For this macro language, 235 is the last exact physical length that fits a 63-bit address; from 236 onward the tested sequence remains above `2^63`.

This must **not** be compared as a direct frontier improvement over the 221-step full topological-family result. The two numbers refer to different admissible families: the information-clock codec is restricted to branch-aligned segments inside the dominant recurrent basin.

## Main result

The structural information clock is operational:

> A variable-length sequence of entropy-bearing branch events can be ranked into one final address and decoded back into every deterministic physical transition using only the final address and exact physical length.

The macro-event description does not create information capacity. It exposes where the entropy is injected and treats deterministic flights as consequences of the trajectory law.

## Interpretation

The experiment supports a precise two-clock description:

```text
t = physical transition count
k = branch / information-event count
```

`k` is variable for a fixed `t`, because different branch choices have different deterministic flight lengths. The address identifies which branch-event trajectory occurred; the public universe determines the intermediate physical path.

This is closer to the project's original trajectory hypothesis than representing every time step as an independent symbol.

## Next test

The next rigorous step is to include transient entry and partial final flights, so the macro codec covers arbitrary segments of the complete topological machine rather than only branch-to-branch recurrent-core segments. That extension must account honestly for entry state, offset and terminal partial flight without adding hidden metadata.

## Reproduction

```bash
python experiments/information_clock_codec.py
```

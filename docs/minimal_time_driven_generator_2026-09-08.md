# Minimal time-driven generator — 2026-09-08

## Result

The validated balanced trajectory universe can be generated exactly without a stored 37-state graph or 49-edge table using:

- a **4-bit private causal state**
  
  `P = (h2, q0, q1, q2)`

- a **public phase clock**
  
  `phase = t mod 3`

- a public binary edge label `z`;
- local phase-dependent admissibility and transition laws.

An exhaustive search over direct projections of the six private raw bits
`h0,h1,h2,q0,q1,q2` found that no 0-, 1-, 2- or 3-bit projection is
generatively sufficient.  Exactly eight 4-bit projections preserve the full
operational language.  Hence four private bits are minimal within this raw
projection family when phase is supplied publicly by time.

All eight minimal projections preserve exactly:

- 37 phase-lifted reachable causal states;
- 49 labeled transitions;
- zero reverse ambiguity;
- identical path counts;
- the 63-bit frontier at 218 transitions.

## Best compact coordinate

The simplest synthesized Boolean law was obtained for

`P = (h2, q0, q1, q2)`.

Writing `P=(r0,r1,r2,r3)`, three forward channels are linear in every phase:

- `r0' = r0 xor r2`
- `r2' = r1`
- `r3' = r2`

Only `r1'` carries the phase-dependent nonlinear interaction:

- phase 0: `r1' = 1 xor r0 xor r3 xor z xor (r1&r2)`
- phase 1: `r1' = r1 xor r3 xor z xor (r0&r1) xor (r1&r2) xor (r0&r1&r2)`
- phase 2: `r1' = r0 xor r3 xor z`

Thus the compact generator has the recurrent pattern

`3 linear channels + 1 interaction channel`,

with phase 2 entirely linear in the state update.

## Reverse law

The exact inverse was synthesized independently on all 49 operational edges.
There were zero mismatches.

For next state `N=(n0,n1,n2,n3)`:

- `prev0 = n0 xor n3`
- `prev1 = n2`
- `prev2 = n3`

and only `prev3` can be nonlinear:

- phase 0: `1 xor n0 xor n1 xor n3 xor z xor (n2&n3)`
- phase 1: `n1 xor n2 xor z xor (n0&n2) xor (n2&n3) xor (n0&n2&n3)`
- phase 2: `n0 xor n1 xor n3 xor z`

So the reverse law also has one interaction channel in phases 0/1 and is fully
linear in phase 2.

## Standalone codec

`experiments/standalone_four_bit_codec.py` contains no reference graph, no
policy-universe lookup, no 37-state list and no 49-edge table.  It contains
only the four-bit local law, public phase clock and the deterministic initial
state construction.

It reproduces exactly:

- `N(218) = 9,131,204,053,820,206,208`
- `N(219) = 10,214,739,716,735,776,832`

therefore

- 218 labeled transitions fit in a 63-bit address space;
- 219 do not.

The first three symbols select one of eight public initial causal states, so
218 transitions correspond to 221 reconstructed path symbols.

Random exact rank/unrank round trips passed at transition lengths 0, 1, 16, 64
and 218, including 100 random addresses at the 218-transition frontier.

## Important distinction

The current exact endpoint contract is

`(enumerative address, transition count) -> unique admissible trajectory`.

The address is a bijective rank in the admissible trajectory family.  It is a
single integer below `2^63`, but it must not be confused with the four-bit
**dynamical endpoint** `P_final` or with a cryptographic hash.

Whether `(P_final, transition count)` alone can identify a unique trajectory is
a separate question.  The next experiment measures endpoint collision
multiplicity and conditional trajectory entropy at the 218-transition
frontier.

# Nonlinear leave-one-out analysis — 2026-09-06

This note records the leave-one-out ablation of the five nonlinear monomials in the balanced universe `(0,2,4,4)`, evaluated on the exact observed 49 `(G,z)` source-label pairs.

Baseline full universe:

- edges: 49
- reverse ambiguity: 0
- frontier: 218 transitions
- rate at 200 steps: 0.2905864402003887 bit/step
- SCC count: 13
- dominant spectral radius: 1.2061897001179003
- dominant recurrent SCC: 14 states

The five nonlinear terms are:

0. `g1&g4`
1. `g1&g5`
2. `g0&g3&g5`
3. `g1&g4&g5`
4. `g2&g4&g5`

## Leave-one-out results

| removed term | reversible | reverse ambiguous | edge agreement | frontier | rate200 | dominant rho | dominant SCC | SCC count |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `g1&g4` | no | 11 | 33/49 | 145 | 0.4286359177 | 1.3308317598 | 26 | 11 |
| `g1&g5` | no | 9 | 34/49 | 229 | 0.2769926944 | 1.1959689031 | 15 | 23 |
| `g0&g3&g5` | yes | 0 | 45/49 | >=300* | 0.1596743815 | 1.0982666799 | 9 | 24 |
| `g1&g4&g5` | no | 6 | 40/49 | 151 | 0.4117060221 | 1.3144960476 | 29 | 7 |
| `g2&g4&g5` | yes | 0 | 43/49 | 171 | 0.3660301392 | 1.2738060483 | 25 | 9 |

`*` No 63-bit crossing was observed within the 300-step scan window.

## Functional interpretation

The terms split into distinct roles.

### Reverse-disambiguation terms

Removing either `g1&g4` or `g1&g4&g5` immediately destroys local reversibility and sharply increases spectral growth. These terms are therefore strong contributors to causal predecessor disambiguation.

`g1&g5` also participates in reverse identity: removing it creates 9 ambiguous reverse keys. Its effect on entropy is milder than the other two, so it occupies an intermediate role between identity and geometry.

### Geometry / entropy-regulation terms

Removing `g0&g3&g5` preserves perfect local reversibility but changes four reference edges, strongly fragments the recurrent structure, lowers the dominant spectral radius from 1.20619 to 1.09827, and reduces information growth enough that the 63-bit limit is not crossed within 300 steps. This term therefore acts primarily as a geometry / entropy-shaping interaction rather than as a reverse-disambiguation requirement.

Removing `g2&g4&g5` also preserves local reversibility but increases spectral radius to 1.27381 and reduces the frontier from 218 to 171. It therefore regulates admissible recurrent expansion in the opposite direction: without it, the universe becomes more expansive.

## Current functional taxonomy

A useful first-order classification is:

- `g1&g4`: strong causal-identity / reverse-disambiguation term;
- `g1&g5`: mixed identity / geometry term;
- `g0&g3&g5`: entropy-suppressing / recurrent-fragmentation regulator;
- `g1&g4&g5`: strong causal-identity / reverse-disambiguation term;
- `g2&g4&g5`: entropy-limiting / recurrent-expansion regulator.

This demonstrates that the nonlinear channel `N` is not monolithic. Different nonlinear interactions perform different structural functions even though all five are necessary to reproduce the exact balanced universe.

## Interpretation

The balanced machine is better described as a constrained reversible geometry than as a generic nonlinear transform. Some nonlinear terms enforce local causal identity, while others determine how much of the reversible state space remains dynamically accessible.

A provisional decomposition is therefore:

`N = N_identity + N_geometry`

with a mixed coupling term between the two roles.

This is an empirical decomposition of the present finite automaton, not a claim of physical universality.

## Next experiment

Test whether the five terms can be regrouped into two or three composite invariants so that the same functional split emerges without referencing individual ANF monomials. The aim is to replace coordinate-specific products by higher-level geometric quantities such as orientation coupling, phase alignment, and recurrent-curvature gates.

# Multilayer endpoint injectivity — first results

Date: 2026-09-14

Objective: test the original requirement directly. Arbitrary bits enter a local state machine. After the run, only `(X_final,T)` remains. No external rank, history, admissible-language restriction or auxiliary decoder state is allowed.

## Exact small-state results

Each candidate uses two layers `(H,V)` with `w` bits each, so the endpoint budget is `W=2w` bits. Exhaustive enumeration was used.

### w=2, W=4
- coupled: first collision at T=3
- feistel_branch: first collision at T=1
- orbit_signed: first collision at T=3

### w=3, W=6
- coupled: first collision at T=4
- feistel_branch: first collision at T=5
- orbit_signed: first collision at T=4

### w=4, W=8
- coupled: first collision at T=5
- feistel_branch: first collision at T=4
- orbit_signed: first collision at T=5

### w=5, W=10
- coupled: first collision at T=7
- feistel_branch: first collision at T=7
- orbit_signed: first collision at T=7

The experiments confirm two separate facts:

1. A multilayer local dynamic can preserve arbitrary-bit history in the natural endpoint for several steps without an external rank.
2. Mere mixing/coupling is not enough: all tested laws merge distinct histories well before the information-theoretic maximum `T=W`.

## Design criterion exposed by the failures

At step t, let `R_t` be the set of endpoints reachable by all length-t inputs. To append one arbitrary input bit without losing reversibility, the two branch images

`F_t(R_t,0)` and `F_t(R_t,1)`

must be disjoint, and each branch map must be injective over `R_t`.

Equivalently:

- no two prior endpoints may merge under the same input bit;
- a `0` successor may never equal a `1` successor from any reachable prior endpoint.

If those conditions hold recursively, `|R_{t+1}|=2|R_t|` until the endpoint state space is exhausted. This is the exact local property the next search should optimize for.

## Next experiment

Search finite local laws directly for **branch-image separation**, rather than for avalanche/mixing. Score a law by:

- longest exact injective prefix;
- branch overlap size at first failure;
- reachable-state occupancy versus theoretical capacity;
- reversibility of predecessor + bit from endpoint and time alone.

The target for a W-bit endpoint is perfect doubling through `T=W`. Passing beyond W for arbitrary fixed-length inputs is impossible by cardinality and is not a research target.

# Reverse observability gate — 2026-09-20

## Why this gate was added

The compact reverse-signature experiments were training the K=2 case at
half-width w=3 (total state width W=6). That regime is already invalid for a
local decoder: the exact e=0 and e=1 branch images collide at t=3.

Once two different predecessor branches produce the same current state, no
function of that current state can recover the branch. Therefore a failed
signature search in that regime says nothing about whether a compact observable
exists in a valid, branch-disjoint regime.

The new experiment
`experiments/reverse_observability_gate.py` makes branch disjointness a hard
precondition before testing observability.

## Corrected result for law A

Public law:

```text
(1, 2, 3, 1, 5)
```

Innovation budget:

```text
K = 2
T = 2 * half_width
```

Exact branch-image results:

```text
W= 6  -> collision at t=3
W= 8  -> collision at t=4
W=10  -> collision at t=8
W=12  -> collision at t=11
W=14  -> branch-disjoint through T=14
W=16  -> branch-disjoint through T=16
W=18  -> branch-disjoint through T=18
W=20  -> branch-disjoint through T=20
W=22  -> branch-disjoint through T=22
W=24  -> branch-disjoint through T=24
```

This means the earlier W=6 K=2 training point was structurally incapable of
supporting an exact local reverse signature.

## Existing 36-observable family

The existing observable family in
`reverse_relation_signature_search.py` still fails after moving into the valid
branch-disjoint regime. The first collision between e=0 and e=1 observable
vectors occurs at:

```text
W=14 -> t=7
W=16 -> t=12
W=18 -> t=7
W=20 -> t=7
W=22 -> t=7
W=24 -> t=7
```

Therefore no subset of those 36 observables can be an exact local decoder on
those tested universes. This is now a valid negative result, unlike the earlier
K=2 search at W=6.

## Raw-coordinate complexity diagnostic

When the full state is branch-disjoint, an exact coordinate signature does
exist. Exhaustive minimum hitting-set search gives:

```text
W=14 -> 11 raw state bits
W=16 -> 11 raw state bits
W=18 -> 12 raw state bits
W=20 -> 12 raw state bits
W=22 -> 12 raw state bits
W=24 -> 13 raw state bits
```

The selected coordinate sets change with width. This is evidence that the
current successful separation is present in the state geometry, but has not yet
been expressed as a stable width-independent local relation.

These raw signatures are diagnostics only. They are not a promoted codec and
must not be interpreted as a constant-size reverse law.

## Interpretation

The project now has three distinct layers of evidence:

1. **Exact state reversibility can fail** when branch images overlap.
2. **Exact state reversibility can hold** while a chosen observable family is
   insufficient.
3. In the branch-disjoint regime, the current state contains enough information
   to identify the branch, but the known compact observables do not expose that
   information structurally.

The next search should therefore target an **equivariant relational basis**:
observables defined relative to the public phase, rotations, horizontal/vertical
halves, and layer relation, with the same decoder frozen across widths and
innovation budgets.

Acceptance must require all of the following:

- branch images are disjoint before any signature search;
- one public feature law is frozen before transfer;
- no width-specific coordinate list;
- no payload-specific retuning;
- exact cross-width transfer;
- exact K-transfer where the branch partition itself remains valid.

This keeps the research focused on the original target: recover the trajectory
from the final state and public universe rules, not from a hidden trajectory
table.

# Endogenous periodic vertical dynamics — 2026-09-20

## Objective

The original reversible fiber lift solved the information-loss problem of the
raw causal graph by adding a vertical coordinate inside each causal fiber.

Its first implementation still transported that vertical coordinate as a rank:

```text
y' = incoming_offset(edge,t) + y
```

That is reversible, but the vertical coordinate has no independent dynamics.

This experiment replaces the identity transport with a public, periodic,
endogenous vertical law.

## Vertical law

For a public causal edge `e: u -> v` at physical time `t`, let:

```text
n = |F(u,t)|
```

be the source-fiber size.

The local vertical coordinate evolves by:

```text
local' = (sigma(e,t) * y + b(e,t)) mod n
```

where:

```text
sigma(e,t) in {+1,-1}
```

and `b(e,t)` is a public integer drive.

The target vertical coordinate is then:

```text
y' = incoming_offset(e,t) + local'
```

so each incoming edge still occupies a disjoint sub-fiber of the target causal
node.

## Why +/-1

The vertical fiber size changes with physical time.

A general multiplier `a` in:

```text
a*y + b mod n
```

would require `gcd(a,n)=1` for every dynamically changing `n`.

Using only:

```text
sigma = +1
sigma = -1
```

avoids that dependency completely. Both orientations are invertible for every
positive integer `n`.

The inverse is:

```text
y = sigma * (local' - b) mod n
```

because `sigma^-1 = sigma`.

## Periodic endogenous drive

The causal graph has public period:

```text
P = 3
```

The vertical drive uses:

```text
P_vertical = 2P = 6
```

This matters because an edge tied to one causal phase is encountered only every
three physical steps. A period of 3 would therefore give that edge the same
vertical drive on every visit.

Using period 6 creates two alternating vertical phases for repeated visits to
the same causal phase.

The drive is generated only from:

- outgoing edge index at the source;
- incoming edge index at the target;
- source in/out degree;
- target in/out degree;
- public causal phase;
- public vertical cycle phase.

There is no:

- trajectory-specific random seed;
- stored vertical-drive history;
- external rank table;
- path-dependent tuning.

The numerical mixing constants are currently a **designed public law**. They are
not claimed to have emerged naturally from the universe search. "Endogenous"
here means that once this fixed law is chosen, every drive value is regenerated
from the current public causal geometry and public phase.

## Horizontal projection

The lifted state is:

```text
X = (causal_node, vertical)
```

and projection is:

```text
pi(X) = causal_node
```

For every lifted transition:

```text
X --e--> X'
```

the gate requires:

```text
pi(X') = target(e)
```

Therefore the lifted dynamics is a reversible refinement of the original causal
dynamics, not a replacement for it.

## Reverse

Given target lifted state:

```text
(v, y')
```

the public incoming sub-fiber intervals identify the unique predecessor edge.

Inside the selected interval:

```text
local' = y' - incoming_offset(e,t)
```

and the previous vertical coordinate is recovered by the inverse periodic law.

The horizontal predecessor is simply the public source of that edge.

## Executed gate

GitHub Actions run:

```text
35553256436
workflow: reversible-pipeline-gate
conclusion: success
```

The complete workflow, including the earlier final-state, scalar-partition,
fiber-lift, minimal-lift, and new periodic vertical gates, passed.

### robust_208

```text
frontier                    208
causal period               3
vertical period             6
frontier lifted states      8,484,982,157,878,442,411

periodic drive              true
drive checks                780
orientation flips           390
nontrivial vertical maps    1,216

early lifted edges checked  1,459
reversible                  true
causal projection           true
frontier partition          true

frontier samples            5
full frontier roundtrip     true
```

### balanced_221

```text
frontier                    221
causal period               3
vertical period             6
frontier lifted states      9,131,204,053,820,206,208

periodic drive              true
drive checks                588
orientation flips           294
nontrivial vertical maps    1,054

early lifted edges checked  1,287
reversible                  true
causal projection           true
frontier partition          true

frontier samples            5
full frontier roundtrip     true
```

### long_239

```text
frontier                    239
causal period               3
vertical period             6
frontier lifted states      8,736,326,121,603,609,111

periodic drive              true
drive checks                528
orientation flips           264
nontrivial vertical maps    1,062

early lifted edges checked  1,241
reversible                  true
causal projection           true
frontier partition          true

frontier samples            5
full frontier roundtrip     true
```

## Full-frontier roundtrip

The frontier gate does not merely test local inverses.

For five final lifted states selected directly from the complete frontier state
space:

```text
0
N/4
N/2
3N/4
N-1
```

the experiment performs:

```text
final lifted state
    -> rewind through every physical transition
    -> reach t=0
    -> replay recovered public edges
    -> recover exact same final lifted state
```

This passed at all three historical frontiers.

## What changed conceptually

Before:

```text
vertical = historical rank
vertical transport = identity inside each edge block
```

Now:

```text
vertical = causal fiber coordinate

vertical transport =
    phase-dependent orientation
    + phase-dependent rotation
    + edge-local causal geometry
```

The historical information is still necessarily present, but it is no longer
transported as a passive rank.

The state now has a genuine horizontal/vertical dynamics:

```text
horizontal:
    causal graph transition

vertical:
    periodic endogenous permutation
    inside the source fiber
    followed by embedding into
    the target edge sub-fiber
```

## Important boundary

This is a **constructed endogenous law**, not yet an emergent law.

The coefficients used to mix local graph invariants were chosen explicitly and
then frozen. The gate proves:

- the law is public;
- the law is periodic;
- the law needs no trajectory-specific metadata;
- the vertical dynamics is nontrivial;
- the lifted dynamics is exactly reversible;
- its projection is exactly the original causal dynamics.

It does not prove that period 6 or this particular drive is uniquely natural.

## Next research gate

The next meaningful experiment is to remove arbitrary mixing constants.

Candidate directions:

1. derive the vertical orientation and rotation directly from the existing
   Floquet modes;
2. derive them from local predecessor multiplicities and branch-event phase;
3. search the smallest finite vertical law family that preserves exact
   reversibility and projection;
4. compare periods `P`, `2P`, `4P`, and recurrent information-clock
   periods for structural simplicity.

The target is a vertical law whose form is forced as much as possible by the
same public universe that generates the horizontal causal dynamics.

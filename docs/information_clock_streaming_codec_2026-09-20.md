# Streaming information-clock codec — 2026-09-20

## Goal

The recurrent information-clock experiment already showed that the dominant
recurrent language has only two branch states and four public macro-edges:

```text
A -> B : 1 physical step
A -> A : 12 physical steps
B -> A : 2 physical steps
B -> A : 5 physical steps
```

All states inside each macro-edge are deterministic consequences of the public
universe.

This experiment makes that observation operational: the final address stores
only the entropy-bearing macro-path. The deterministic physical flights are
regenerated from the public macro-edge definitions.

## Weighted path counts

For endpoint branch state `v` and physical time `t`, define:

```text
D(v,t) = number of macro-paths that
         start at an allowed branch state,
         consume exactly t physical steps,
         and end at v.
```

With positive edge lengths:

```text
D(v,t) = sum D(u, t-L_e)
         over public incoming edges e: u -> v
```

with one zero-length empty path for each allowed initial branch state.

These counts depend only on the public macrograph and time.

## Streaming forward law

At a branch event, the current state identifies the current endpoint, the rank
of the current prefix among paths ending there, and elapsed physical time.

For a selected public macro-edge `e: u -> v` of length `L`, paths ending at
`v` at the new time are partitioned into public blocks by their final incoming
edge. The block for `e` has exactly `D(u,t)` states. The predecessor rank is
inserted unchanged into that block.

## Local reverse law

Given only the current state/address and physical time:

1. recover endpoint bucket `v`;
2. compare the within-bucket rank against public incoming-edge block sizes;
3. the containing block uniquely identifies the last macro-edge;
4. remove that block offset;
5. subtract the edge physical length.

The predecessor state is obtained immediately. No macro-edge history is stored.

## Physical trajectory regeneration

Each public macro-edge already carries its deterministic path through the
phase-lifted recurrent core. After the macro-edge sequence is recovered,
concatenating those public paths reconstructs every physical core state.

Therefore, on this recurrent-basin language:

```text
(final address, physical step count)
    -> macro-edge trajectory
    -> complete deterministic physical trajectory
```

## 63-bit gate

With both branch states allowed as initial states, exact path counts are
periodic/non-monotone because edge lengths are `1,2,5,12`.

The first physical length whose complete exact-length family exceeds `2^63`
is `T=234`. Therefore the conservative streaming frontier, requiring every
complete prefix family from `0..T` to fit, is:

```text
T = 233 physical steps
```

At `T=233`:

```text
paths      = 6,133,984,358,677,405,281
occupancy  ~= 66.5048% of 2^63
```

At `T=234`:

```text
paths = 12,990,982,626,511,308,208
```

which exceeds `2^63`.

The exact-length count at `T=235` falls below `2^63` again. That isolated fit
is preserved as a structural property of the weighted language, but it is
not promoted as the conservative streaming frontier because the immediately
preceding complete prefix family is over capacity.

## Meaning

This closes the loop between the earlier information-clock analysis and an
actual reversible address:

- deterministic flights are not stored;
- only branch-path entropy consumes address space;
- the last branch is recovered locally from public weighted-count blocks;
- the complete physical path is regenerated from public macro-edge paths.

The construction is the weighted-finite-state analogue of the streaming colex
trajectory codec.

The next research step is to remove the special treatment of the already
extracted two-state macrograph and apply the same weighted-address construction
directly to a larger endogenous recurrent core, so branch states and
deterministic flights are derived automatically from the universe.

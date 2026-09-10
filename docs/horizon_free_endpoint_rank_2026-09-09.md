# Horizon-free reversible endpoint address — 2026-09-09

## Result

The balanced trajectory machine now has an exact online address that does not
know the future horizon while evolving.

Private causal state:

    P_t = (h2, q0, q1, q2)

Public clock:

    phase = t mod 3

Public universe population:

    C_t(P) = number of admissible histories that reach P after t transitions

For each endpoint Q at t+1, incoming edge blocks `(P,z)->Q` are ordered
canonically. A history already has a local rank inside the block of histories
ending at P. On transition `(P,z)->Q`, that local rank is translated into the
corresponding incoming block of Q. Endpoint blocks are then concatenated in a
canonical order to obtain a single global integer address A_t.

Crucially, all offsets depend on elapsed time `t` and the public universe rules,
not on a future stopping horizon `T`.

Thus the encoder evolves online as

    (A_t, P_t, z_t, t) -> (A_{t+1}, P_{t+1})

without knowing when the stream will stop.

When it does stop at T, the decoder receives only

    (A_T, T)

plus the public machine rules. It recomputes C_T, locates the endpoint block,
then recursively locates the predecessor edge block at T-1, recovering z and
the predecessor state at every step until the unique 3-bit initial prefix is
reached.

## Exact frontier

The address space is exactly the number of admissible trajectories at each
length:

    N(218) = 9,131,204,053,820,206,208 < 2^63
    N(219) = 10,214,739,716,735,776,832 > 2^63

Therefore:

    218 transitions + 3 initial symbols = 221 reconstructed symbols

fit in one 63-bit reversible address plus the transition count.

The standalone experiment performs exhaustive roundtrips for small horizons and
random roundtrips through T=218. CI validates the complete chain.

## Important interpretation

A_T is an enumerative/reversible address, not a cryptographic hash. A normal
hash is intentionally many-to-one and cannot generally reconstruct its input.

This result also does not compress arbitrary 221-bit strings into 63 bits. It
works because the public universe rules restrict the admissible 221-symbol
trajectories to fewer than 2^63 possibilities at T=218. The information content
of that constrained family is about 62.99 bits.

The useful result is therefore structural:

    constrained trajectory + public laws -> online reversible address

The address is the coordinate of the history inside the space of trajectories
that the universe permits.

## Why this differs from the previous online rank

The previous exact online rank needed the final horizon T because branch weights
were counts of future completions. The endpoint-conditioned construction ranks
histories by the past that has already reached the current state. Its weights
are prefix counts C_t, so it needs only elapsed time.

A naive horizon-free branch-bit accumulator was also tested. It fails the
63-bit target because some 218-transition paths contain up to 147 actual branch
events. Endpoint-conditioned ranking succeeds by exploiting the constraints
between those branch events instead of recording each branch independently.

## Current contract

At the validated frontier:

    (A_218, 218) -> exact 221-symbol trajectory

where `A_218` is a single integer in `[0, N(218))`.

No path history, endpoint state, branch count, future horizon during encoding,
or graph whitelist is stored with the address.

## Next question

The remaining complexity is the public count field C_t(P). It is not private
metadata and can be recomputed from the laws, but the next research target is
to determine whether its evolution admits a closed low-dimensional recurrence
or spectral form. If so, the address update can be expressed as a compact local
law rather than as dynamic-programming counts over the finite state set.

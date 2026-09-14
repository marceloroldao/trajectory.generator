# trajectory.generator — Original Objective Contract

Status: ACTIVE RESEARCH OBJECTIVE

## Objective

Given an arbitrary input bit sequence `b[0:T]`, evolve a deterministic state by local laws

`X[t+1] = F(X[t], b[t], t)`

and, after erasing the input and all intermediate states, recover the complete original sequence from only

`(X[T], T)`.

The endpoint must be the state naturally produced by the dynamics. A separately computed trajectory rank/address is not accepted as satisfying the objective.

## Hard acceptance rules

A candidate only passes when all of the following are true:

1. Input bits may be arbitrary; they are not restricted to an admissible language chosen to make the codec work.
2. After encoding, only the final state `X[T]`, the step count `T`, and fixed public laws/constants remain.
3. No trajectory table, side channel, beam oracle, external rank, checksum carrying missing information, or stored intermediate state may be used.
4. The reverse procedure must recover every bit exactly, not statistically.
5. If the state has multiple layers/components, every component that is required during decode counts as part of the final-state information budget.
6. A component is rejected as "memory in disguise" if its information capacity simply grows with the input and is retained at the endpoint.

## Information-theoretic boundary

For a fixed input length T, there are `2^T` arbitrary binary inputs. If the final state has W bits, it has at most `2^W` distinct values. Exact recovery for every input requires an injective map

`{0,1}^T -> X_T`,

therefore necessarily

`2^T <= 2^W`, hence `T <= W`.

Knowing T does not change this bound when comparing messages of the same length, because T is identical for all `2^T` candidates.

Consequences:

- A fixed 63-bit endpoint cannot losslessly recover every arbitrary 64-bit input from `(X_final, 64)`.
- Deterministic public universe dynamics, time-dependent laws, additional computation, or a 2D/3D interpretation do not change the cardinality unless they add distinguishable endpoint states.
- Multiple layers can help only if their final distinguishable states increase the endpoint information capacity; those layers must then be counted in W.

This does **not** invalidate research into trajectory-based reversible dynamics. It sets the correct target: discover whether a local reversible law can make the *natural endpoint itself* a complete coordinate of history up to its true information capacity, and whether useful structure appears without an externally computed rank.

## Current research question

Instead of silently changing the problem to compression, we now ask:

> Can we construct a local, multilayer state dynamics in which the current endpoint contains exactly the information required for backward inference, with no external trajectory address, and characterize the minimal endpoint dimension required as trajectory length grows?

## Experimental protocol

For each candidate dynamics and `(T,W)`:

1. Exhaustively enumerate all inputs when feasible.
2. Encode every input from one public initial state.
3. Count endpoint collisions.
4. Attempt reverse reconstruction from `(X_final,T)` only.
5. Report injectivity, collision multiplicities and first failing T.
6. Reject any candidate that passes only by restricting input or retaining side information.

The first benchmark is deliberately small (W <= 16) so exhaustive tests can prove or falsify injectivity rather than estimate it.

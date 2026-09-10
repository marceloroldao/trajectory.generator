# O(log t) public-field lookup — 2026-09-09

## Result

The scalar growth law

```text
g[n+3] = 2 g[n+2] - g[n+1] + g[n]
(g0,g1,g2) = (1,0,0)
```

was lifted to the companion-state form

```text
S_n = [g_n, g_{n+1}, g_{n+2}]^T
S_{n+1} = K S_n

K = [[0,1,0],
     [0,0,1],
     [1,-1,2]]
```

so that `S_n = K^n S_0` can be evaluated by binary exponentiation in `O(log n)` matrix squarings.

## Validation

- `g_fast(n) == g_linear(n)` for `n=0..999`.
- Direct exact lookup at `n=10000` succeeded; triplet bit lengths were `(8112, 8113, 8113)`.
- Fast count-field lookup matched the prior scalar implementation state-by-state for all physical times `t=0..220`.
- Exhaustive endpoint-address roundtrip passed for `T=0..9`.
- 200 random endpoint-address roundtrips passed for each of `T=16,64,128,200,218`.
- `N(218)=9131204053820206208` and `N(219)=10214739716735776832`, preserving the 63-bit frontier at 218 transitions.

## Interpretation

The public field no longer needs to be stepped from time zero and does not need retained modal state. At arbitrary time `t`, the count field can be reconstructed exactly from `t` and fixed universe constants in `O(log t)` arithmetic steps (ignoring big-integer operand growth).

The operational contract is therefore:

```text
public_counts(t) = F(t; fixed universe law)
```

with no trajectory history, no future horizon, and no persistent public count-vector state.

This does not make total reverse decoding sublinear in trajectory length: emitting a trajectory of `T` symbols still requires at least `O(T)` output work. The improvement is random access to the public field at any requested time.

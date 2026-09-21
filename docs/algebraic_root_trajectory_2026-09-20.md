# Algebraic root trajectory — 2026-09-20

## Result

This experiment gives an exact endpoint-only decoder for a public family of
binary trajectories containing at most `K` innovation events.

The decoder receives:

```text
(final_state, number_of_steps)
```

plus the fixed public universe parameters `K` and prime field modulus `p`.
It does not receive innovation positions, a trajectory table, branch history,
rank metadata, or a reconstructed reachable manifold.

## State

Let an innovation at physical step `t` have the public non-zero address

```text
x_t = t + 1  in GF(p)
```

with `number_of_steps < p`.

The state is the monic degree-`K` polynomial

```text
P(z) = z^(K-r) * product(z - x_i)
```

where the product contains exactly the `r <= K` innovation positions already
encountered.

Initially:

```text
P_0(z) = z^K
```

Only the `K` non-leading coefficients are stored. The leading coefficient is
always one.

## Forward law

For a normal step:

```text
e_t = 0:
P_(t+1)(z) = P_t(z)
```

For an innovation:

```text
e_t = 1:
P_(t+1)(z) = [P_t(z) / z] * [z - (t+1)]
```

The division by `z` is exact while fewer than `K` innovations have occurred,
because at least one zero root remains.

This replaces one unused zero root with the current public step address.

## Reverse law

At reverse step `t`, evaluate only the current polynomial:

```text
P_(t+1)(t+1)
```

Because all step addresses are distinct and non-zero:

```text
P_(t+1)(t+1) = 0  <=>  e_t = 1
```

Therefore the branch is read directly from the current state.

If the result is non-zero, the predecessor is unchanged.

If it is zero:

```text
P_t(z) = [P_(t+1)(z) / (z-(t+1))] * z
```

Synthetic division and multiplication both cost `O(K)`.

So full trajectory recovery costs:

```text
time   O(K*T)
memory O(K)
```

and each branch decision itself is local.

## Exactness argument

The final polynomial has root multiset:

```text
{0 repeated K-r times} union {t+1 for every innovation step t}
```

Since `T < p`, every physical step maps to a distinct non-zero field element.
A monic polynomial is uniquely determined by its multiset of roots, so two
different innovation-position sets cannot produce the same valid final
polynomial.

This is a constructive injectivity proof for the <=K-sparse trajectory family.

## State width

There are `p^K` possible coefficient tuples, so the complete coefficient state
can be packed into:

```text
ceil(log2(p^K))
```

bits.

For `K=5`, reference public primes close to the packing limit give:

```text
W=63   p=6203                              T_max=6,202
W=128  p=50,858,999                        T_max=50,858,998
W=256  p=2,586,638,741,762,807             T_max=2,586,638,741,762,806
W=512  p=6,690,699,980,388,625,489,511,488,543,441
       T_max=6,690,699,980,388,625,489,511,488,543,440
```

The exact values above are reference primes for the experiment, not a claim that
these widths should become the project's default state sizes.

## Distance from the information bound

The sparse family contains:

```text
A(T,K) = sum(C(T,j), j=0..K)
```

trajectories.

For fixed `K` and large `T`:

```text
log2 A(T,K)
~= K*log2(T) - log2(K!)
```

The polynomial coefficient state costs approximately:

```text
K*log2(T)
```

bits.

Hence the asymptotic redundancy is approximately:

```text
log2(K!)
```

bits, a constant when `K` is fixed.

For `K=5`:

```text
log2(5!) ~= 6.9069 bits
```

This explains why the construction is not numerically optimal at 63 bits but
becomes relatively efficient at larger widths.

For example, with known zero baseline and `W=63, K=5`:

```text
algebraic-root frontier: 6,202 steps
information-theoretic sparse frontier: 16,174 steps
```

The earlier hierarchical construction also accounts for an initial binary value,
so its directly comparable frontier is different.

## What this result means

This is the first construction in the current line of experiments that combines:

- final-state-only trajectory recovery;
- no trajectory log or side table;
- no reachable-manifold reconstruction;
- a branch decision obtained from the current state and public time;
- `O(K)` local reverse work;
- state cost within a constant `log2(K!)` bits of the fixed-K sparse entropy
  asymptotically.

It does **not** defeat the information bound and it does not encode arbitrary
`T > W` binary strings. It succeeds because the admissible family is
`K`-sparse.

## Next gate

The next research question is whether the constant `log2(K!)` redundancy can
be reduced without losing the local reverse law.

The valid coefficient states are precisely the monic degree-`K` polynomials
whose roots consist of distinct public non-zero step addresses plus zero roots.
Only a fraction of all coefficient tuples are valid. A successful next layer
would index or quotient this valid algebraic manifold more densely while still
supporting reversible root insertion/removal without a trajectory table.

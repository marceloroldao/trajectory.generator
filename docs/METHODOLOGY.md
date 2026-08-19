# Experimental Methodology

## 1. Research question

Can an ordered binary trajectory be recovered from only:

- the final machine state; and
- the number of data steps,

when the machine is deterministic, time-dependent and reversible at the primitive-operation level?

The decoder may know the public machine definition and fixed initial state. It may not receive a trajectory log, checksum, plaintext model, branch hints, side database, or any value derived from the original input other than the final state and step count.

## 2. Formal model

For input bit `b_t in {0,1}`:

```text
Y_t     = U_t(X_t)
X_(t+1) = D_(b_t,t)(Y_t)
```

`U_t` is deterministic universe evolution. In the initial experiment it acts every third data step. `D_0` is the identity perturbation and `D_1` is a reversible non-commutative perturbation.

Each primitive operation is bijective over a fixed-width state when the branch bit is known.

## 3. Why non-commutativity matters

The predecessor prototype was dominated by XOR/NOT. At fixed width,

```text
~(x ^ t)
```

is just XOR with a time-dependent constant. Repeated XOR composition is commutative, so different orderings can collapse to the same algebraic result.

The current machine combines modular multiplication by odd values, modular addition, bit rotation, XOR and time-dependent words. The objective is not cryptography; it is to prevent the algebra from trivially erasing event order.

## 4. Exact injectivity experiment

For each trajectory length `n`:

1. enumerate all `2^n` bit sequences;
2. run each sequence from the same public initial state;
3. record its final state;
4. count unique final states and collision multiplicity.

Metrics:

```text
N(n)  = 2^n                         total trajectories
U(n)  = number of unique finals
C(n)  = N(n) - U(n)                 collisions
I(n)  = U(n) / N(n)                 injective fraction
M(n)  = maximum final-state multiplicity
```

A domain is injective only when `C(n)=0`.

## 5. Exact recovery experiment

Given a known valid `(final_state, n)`, the reference decoder enumerates every `n`-bit trajectory and returns all matching candidates up to a configured limit.

Results are classified as:

- **unique**: exactly one trajectory matches;
- **ambiguous**: two or more trajectories match;
- **not found**: no trajectory matches.

The reference decoder never picks the nearest or most language-like candidate.

## 6. Fundamental capacity bound

For a fixed `w`-bit final state and fixed `n`, the codomain contains at most `2^w` distinct final values while arbitrary binary trajectories contain `2^n` possibilities.

Therefore global injectivity for all arbitrary messages requires at least

```text
n <= w
```

when step count is fixed. For `n>w`, collisions are mathematically unavoidable unless the admissible input space is constrained or additional independent information is supplied.

This is a falsification boundary, not an implementation defect.

## 7. Trajectory/orbit measurements

For diagnostics only, a trajectory may be compared with the deterministic zero-input universe baseline using Hamming distance:

```text
r_t = Hamming(X_t, C_t)
```

Possible measurements include recurrence, radius distribution, cycle lengths and ratios between successive non-zero radii.

No preferred irrational constant is used in the machine dynamics.

## 8. Emergence test

The analysis script may compare measured ratios after generation against reference constants such as `sqrt(2)`, `3/2`, `phi`, `sqrt(3)` and `e`.

These constants are analysis references only. A candidate emergent pattern must:

1. arise without appearing in the generator;
2. persist across many input classes and machine widths;
3. outperform alternative reference constants under a predeclared metric;
4. survive parameter perturbations and independent reruns;
5. have uncertainty/error bars reported.

A single numerical proximity to phi is not evidence of emergence.

## 9. Current validated baseline

The initial implementation has been manually checked for exact forward/inverse consistency across both data branches and multiple states/times. Exhaustive scans performed during bootstrap found zero collisions at 8, 12 and 16 input bits with the default 63-bit configuration.

These are preliminary engineering checks, not a publication-level result. Larger scans must be reproduced by committed scripts and recorded before any release-candidate claim.

## 10. Next experiments

1. Extend exhaustive scans until the first collision or computational limit.
2. Record collision pairs and compare their trajectories.
3. Compare against the old XOR/NOT baseline under identical widths.
4. Add a meet-in-the-middle or reverse-frontier decoder without adding side information.
5. Test multiple deterministic universe periods (`2,3,4,5,...`) without selecting results post hoc.
6. Run emergence statistics only after the generator parameters are frozen for an experiment series.
7. Preserve negative results.

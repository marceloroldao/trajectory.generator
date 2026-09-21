# Horizontal/vertical information geometry — 2026-09-21

## Executive result

trajectory.generator now has an exact information-theoretic and geometric
interpretation of the previously heuristic horizontal/vertical picture.

For a finite public causal universe at physical time t:

- the **horizontal state** is the current raw causal node;
- the **vertical fiber** over that node is the set of distinct admissible
  histories that end there;
- exact reversibility requires those histories to remain distinguishable;
- branch structure creates new trajectory entropy;
- almost all long-term history information is forced into the vertical fibers;
- on a recurrent core, the asymptotic vertical-memory rate is exactly the
  topological entropy rate;
- the information-clock event entropy divided by mean physical event length is
  the same rate;
- after normalizing each fiber to the unit interval, predecessor subfibers
  converge to stationary reverse-Parry interval widths.

The current result is therefore not just a two-dimensional drawing.  It is an
operational reversible state geometry.

---

## 1. Exact reversible state

Let D_t(v) be the number of admissible histories of physical length t ending at
causal node v.

The minimal reversible completion at time t is the disjoint union:

```text
X_t = coproduct_v {v} x F_t(v)

|F_t(v)| = D_t(v).
```

A state can therefore be written conceptually as:

```text
(horizontal causal node v, vertical history state y).
```

The scalar `final_state` used by the operational codec is a compact chart of
this disjoint union.

No extra history table is required.

---

## 2. Horizontal/vertical entropy chain rule

Under the uniform distribution over all admissible histories at time t:

```text
H_total(t)      = log2 N_t
N_t             = sum_v D_t(v)

H_horizontal(t) = H(current causal node)

H_vertical(t)   = H(history | current causal node)
                = sum_v p_t(v) log2 D_t(v)
```

The exact chain rule is:

```text
H_total(t)
    = H_horizontal(t)
    + H_vertical(t).
```

GitHub Actions run `35555996837` and subsequent complete runs passed this
identity exactly.

At the 63-bit whole-universe frontiers:

```text
candidate      total bits      horizontal bits      vertical bits
robust_208     62.8796173341       3.5244578269      59.3551595072
balanced_221   62.9855108166       3.2146048331      59.7709059835
long_239       62.9217324201       2.1843232600      60.7374091602
```

So approximately:

```text
robust   94.4% vertical
balanced 94.9% vertical
long     96.5% vertical
```

of the final trajectory information is already in the history fibers at the
63-bit frontier.

---

## 3. Branch-created information budget

The exact total history-count update is:

```text
N_(t+1)
    = sum_u D_t(u) * out_degree(u).
```

Therefore the information created during one physical step is:

```text
Delta H_total
    = log2(N_(t+1) / N_t).
```

The branch-information gate verified telescoping conservation through every
historical frontier.

After the 3-bit bootstrap, the additional trajectory information created was:

```text
robust_208     59.879617334061 bits
balanced_221   59.985510816588 bits
long_239       59.921732420141 bits
```

The same run verified that this equals the exact change in total history entropy.

In the tested full-universe windows every physical row still contained some
populated branching mass, so every row had positive global entropy creation.
This does not imply that every individual causal transition branches.

---

## 4. Asymptotic vertical dominance theorem

Suppose the recurrent causal state space has M finite horizontal states.

Then:

```text
0 <= H_horizontal(t) <= log2 M.
```

But for a positive-entropy recurrent core:

```text
H_total(t) -> infinity.
```

Since:

```text
H_vertical
    = H_total - H_horizontal,
```

we obtain:

```text
H_vertical(t) / H_total(t)
    >= 1 - log2(M) / H_total(t)
```

and therefore:

```text
lim H_vertical(t) / H_total(t) = 1.
```

This is independent of any numeric vertical chart.

GitHub Actions run `35555996837` verified the convergence on all three
recurrent cores.

At 384 recurrent physical steps:

```text
candidate      actual vertical fraction    theorem lower bound
robust_208          0.960465692733             0.960159158096
balanced_221        0.965409699701             0.964599460605
long_239            0.967727776915             0.967344256074
```

The horizontal entropy had already stabilized to an O(1) value while vertical
entropy continued growing.

---

## 5. Correct Perron spectral rate

An earlier recurrent-core helper estimated growth with:

```text
(total_paths_t / total_paths_0)^(1/t).
```

That estimator is useful for rough growth comparison but has an O(1/t)
multiplicative-prefactor bias.

The recurrent module now computes the Perron spectral radius by power iteration
on:

```text
A + I.
```

For an irreducible component this removes periodic oscillation, preserves the
Perron eigenvector, and shifts the Perron eigenvalue from lambda to lambda+1.
Collatz-Wielandt bounds provide the convergence certificate.

The corrected recurrent growth factors are:

```text
candidate      lambda              log2(lambda)
robust_208     1.220744084606      0.287760787084
balanced_221   1.206189700118      0.270456820917
long_239       1.173984996705      0.231413971210
```

For the balanced information clock this restores the previously derived
high-precision value.

---

## 6. Vertical-memory rate equals topological entropy rate

Divide the entropy decomposition by physical time:

```text
H_total(t)/t
    = H_horizontal(t)/t
    + H_vertical(t)/t.
```

Because the horizontal state space is finite:

```text
H_horizontal(t)/t -> 0.
```

For an irreducible recurrent core:

```text
H_total(t)/t -> log2(lambda).
```

Therefore:

```text
lim H_vertical(t)/t
    = log2(lambda).
```

GitHub Actions run `35561947524` passed the corrected spectral gate.

At t=384:

```text
candidate      vertical rate        log2(lambda)        error
robust_208     0.287844485160       0.287760787084      8.37e-5
balanced_221   0.270392049663       0.270456820917      6.48e-5
long_239       0.231517410056       0.231413971210      1.03e-4
```

The finite-time vertical rate is already a better estimator of the asymptotic
entropy rate than the raw total-rate estimate because the bounded horizontal
entropy has been removed.

---

## 7. Information clock = vertical-memory clock

For a recurrent weighted macrograph, let each information-event edge e have
physical length L_e.

Define the weighted transfer matrix:

```text
W_ij(lambda)
    = sum_(e:i->j) lambda^(-L_e).
```

At the physical growth factor:

```text
rho(W(lambda)) = 1.
```

Let r and l be positive right and left eigenvectors at eigenvalue 1.

The maximum-entropy event probability is:

```text
p(e | i)
    = lambda^(-L_e) r_j / r_i.
```

With stationary branch distribution:

```text
pi_i proportional to l_i r_i,
```

define:

```text
<L>      = mean physical steps / information event

H_event  = mean information bits / information event.
```

Stationarity cancels the eigenvector terms and gives the exact identity:

```text
H_event
    = <L> log2(lambda)

H_event / <L>
    = log2(lambda).
```

GitHub Actions run `35561947524` passed this identity for all three automatic
macrographs.

Measured clocks:

```text
robust_208
  branch nodes                  = 6
  macro edges                   = 12
  mean physical steps/event     = 3.450299522098
  bits/event                    = 0.992860906155
  events/physical step          = 0.289829910011
  bits/physical step            = 0.287760787084

balanced_221
  branch nodes                  = 2
  macro edges                   = 4
  mean physical steps/event     = 2.598563354869
  bits/event                    = 0.702799183910
  events/physical step          = 0.384828023579
  bits/physical step            = 0.270456820917

long_239
  branch nodes                  = 1
  macro edges                   = 2
  mean physical steps/event     = 4.145898033750
  bits/event                    = 0.959418728223
  events/physical step          = 0.241202265917
  bits/physical step            = 0.231413971210
```

Clock identity residuals were zero to floating-point precision.

Thus the information clock and vertical-memory growth are two views of the same
entropy production:

```text
event clock:
    when entropy choices occur

vertical fiber:
    where the distinguishable history is retained
```

---

## 8. Variable-cardinality fibered state space

The exact reversible state is not efficiently represented by a fixed Cartesian
product:

```text
horizontal_axis x fixed_vertical_axis.
```

The fiber sizes D_t(v) are strongly nonuniform.

In strict topology this is not a classical fiber bundle with one fixed typical
fiber.  It is better described as a variable-cardinality fibered state space,
or an indexed family of discrete fibers:

```text
X_t
    = coproduct_v {v} x [0, D_t(v)).
```

GitHub Actions run `35562210744` passed the geometry gate.

At the whole-universe frontiers:

```text
robust_208
  populated horizontal states      = 14 / 192
  min nonzero fiber                = 206,440,985,722,566,275
  max fiber                        = 1,143,377,287,880,525,663
  exact optimal integer width      = 63 bits
  active rectangular occupancy     = 53.007%
  active fixed-axis width          = 64 bits
  full 192-state rectangle width   = 68 bits

balanced_221
  populated horizontal states      = 12 / 192
  min nonzero fiber                = 224,126,931,307,187,426
  max fiber                        = 2,754,405,653,601,624,727
  exact optimal integer width      = 63 bits
  active rectangular occupancy     = 27.626%
  active fixed-axis width          = 66 bits
  full 192-state rectangle width   = 70 bits

long_239
  populated horizontal states      = 10 / 192
  min nonzero fiber                = 1
  max fiber                        = 3,627,481,408,934,513,129
  exact optimal integer width      = 63 bits
  active rectangular occupancy     = 24.084%
  active fixed-axis width          = 66 bits
  full 192-state rectangle width   = 70 bits
```

The compact scalar address is therefore not evidence that horizontal/vertical
structure is absent.  It is an efficient chart of a nonuniform fibered state
space.

Forcing the geometry into two fixed-width integer coordinates wastes capacity.

---

## 9. Normalized vertical interval geometry

Normalize every nonempty discrete history fiber to the unit interval.

For a physical edge:

```text
e : u -> v
```

the exact predecessor block has normalized width:

```text
q_t(e)
    = D_t(u) / D_(t+1)(v).
```

Given a chart ordering of incoming edges:

```text
x_(t+1)
    = offset_t(e)
    + q_t(e) x_t.
```

Reverse:

```text
x_t
    = (x_(t+1) - offset_t(e)) / q_t(e).
```

The offset depends on incoming-edge serialization and is therefore gauge/chart
dependent.

The width q_t(e) is not.

---

## 10. Reverse-Parry limit

On a recurrent core, along one phase class:

```text
q_t(e)
    -> q(e | target),
```

where q is the reverse transition probability of the maximum-entropy Parry
process:

```text
q(e:u->v | v)
    = pi(u) p(e|u) / pi(v).
```

GitHub Actions run `35562210744` passed this convergence.

Maximum block-width error:

```text
                 t=24       t=48       t=96       t=192      t=384
robust_208       4.70e-3    1.93e-4    4.41e-8    3.33e-13   3.82e-14
balanced_221     1.79e-3    2.08e-5    2.56e-9    4.57e-14   4.57e-14
long_239         5.65e-5    2.56e-8    2.71e-14   2.71e-14   2.71e-14
```

Every exact target-fiber partition had zero numerical partition residual.

The stationary reverse probabilities normalized to 1 at every target to about
1e-14.

---

## 11. Geometric entropy identity

For the reverse-Parry interval width q(e), define the vertical contraction
information:

```text
I_vertical(e)
    = -log2 q(e).
```

Averaged over stationary causal edge flow:

```text
E[I_vertical]
    = log2(lambda).
```

Measured residuals:

```text
robust_208     ~7.2e-16
balanced_221   ~1.7e-16
long_239       ~5.6e-16
```

So the topological entropy rate has three equivalent operational forms:

```text
log2(lambda)

= asymptotic trajectory bits / physical step

= asymptotic vertical-memory bits / physical step

= information-event entropy / mean event length

= mean reverse vertical interval contraction information.
```

---

## 12. Operational reverse interpretation

One physical forward transition can now be read as:

```text
horizontal:
    u -> v

vertical:
    source history fiber
    -> predecessor-specific subfiber of v
```

Reverse decoding reads the current state as:

```text
1. inspect horizontal destination v;
2. inspect which vertical subfiber contains the state;
3. that subfiber identifies predecessor edge e:u->v;
4. remove the subfiber offset;
5. expand by the inverse vertical scale;
6. recover the predecessor state;
7. repeat.
```

In the exact discrete implementation, block boundaries come from public integer
path counts.  In the recurrent normalized limit, their relative widths converge
to the reverse-Parry geometry above.

This is the strongest current formalization of the original idea:

> relate the current state to the public universe law and determine where it
> came from without carrying an external trajectory map.

The history information is not absent. It is the vertical position inside the
minimal reversible fiber.

---

## 13. What is intrinsic and what remains gauge

Intrinsic / coordinate-independent:

```text
causal graph
admissible history space
fiber cardinalities D_t(v)
which predecessor-edge image a history belongs to
normalized predecessor block widths
entropy rates
information-clock statistics
Parry forward/reverse probabilities
conjugacy classes of gauge-covariant event actions
```

Chart/gauge dependent:

```text
integer labels inside a fiber
ordering of incoming-edge blocks
block offsets in [0,1)
specific numeric vertical permutations
one packed scalar final_state convention
```

The exact trajectory is invariant under valid gauge conversion.

---

## 14. What this does not claim

This result does not violate the fixed-state information bound.

A 63-bit final state cannot injectively encode all arbitrary binary strings
longer than 63 bits.

The long frontiers arise because the public universe restricts the admissible
trajectory language.

The normalized stationary geometry also does not by itself replace the exact
finite-time count field. Exact discrete decoding at finite time still uses the
public recurrence/count geometry so that every integer boundary is exact.

---

## 15. Current strongest model

The project can now be summarized as:

```text
public finite causal universe
    |
    +-- horizontal causal state
    |
    +-- variable vertical history fiber
            |
            +-- exact integer predecessor blocks
            |
            +-- normalized interval geometry
                    |
                    +-- recurrent reverse-Parry limit

branch events
    -> create trajectory entropy

deterministic flights
    -> propagate consequences

information clock
    -> event-time description of entropy creation

vertical fiber
    -> reversible storage of the resulting history distinction

final_state
    -> compact chart coordinate of the complete reversible state
```

The next useful target is an explicit **exact vertical connection** API:
represent forward/reverse evolution directly as horizontal transition plus
vertical subfiber embedding, while retaining integer-exact boundaries generated
from the existing Floquet scalar recurrence.  That would expose the geometry
directly instead of only through the packed scalar address.


---

## 16. Exact local vertical connection

The horizontal/vertical geometry is now exposed as the operational dynamical
state rather than only inferred from the packed integer.

Implementation:

```text
trajectory_generator/exact_vertical_connection.py
```

Local state:

```text
(time, horizontal node, vertical rank, fiber size)
```

For edge `e:u->v` at transition time `t`:

```text
source fiber size = D_t(u)
target fiber size = D_(t+1)(v)

block start = public exact incoming offset

forward:
    (u,r) -> (v, block_start + r)

reverse:
    inspect target rank
    locate unique incoming block
    recover edge e
    r_prev = r_target - block_start
```

The normalized block offset and width are also exposed as exact rational
`Fraction` values.

The packed integer is not used by `forward()` or `reverse()`.

It is only a boundary chart:

```text
unpack:
    final integer -> (node,rank)

pack:
    (node,rank) -> final integer
```

GitHub Actions run `35562749521` passed the complete 43-gate workflow.

The exact connection gate reported:

```text
robust_208
  small local steps checked = 459
  exact partitions checked  = 124
  frontier samples          = 5
  frontier edges reversed   = 1,025

balanced_221
  small local steps checked = 418
  exact partitions checked  = 104
  frontier samples          = 5
  frontier edges reversed   = 1,090

long_239
  small local steps checked = 366
  exact partitions checked  = 92
  frontier samples          = 5
  frontier edges reversed   = 1,180
```

Every local reconstruction repacked to the original final integer.

`packed_state_used_as_dynamics=False` in all three frontier gates.

---

## 17. Final-state-only bit recovery through local fibers

The seeded wrapper:

```text
trajectory_generator/seeded_vertical_connection.py
```

preserves the external contract:

```text
decode(final_state, steps)
    -> exact admissible bit trajectory
```

but changes the internal process.

Decode now performs:

```text
1. one unpack of final_state into the final local fiber coordinate;
2. repeated local vertical reverse steps;
3. recovery of one public edge symbol per reversed transition;
4. recovery of the initial public seed from the singleton time-zero fiber;
5. concatenation of seed bits and recovered edge bits.
```

The packed integer is not updated during reverse dynamics.

Encode performs the dual operation:

```text
seed
    -> singleton initial local fiber
    -> local horizontal/vertical forward dynamics
    -> one final pack
```

Run `35562749521` passed exact comparison against the historical decoder:

```text
candidate      small addresses    frontier samples    bits recovered
robust_208            288                 5                1,040
balanced_221          270                 5                1,105
long_239              234                 5                1,195
```

For every frontier sample:

```text
local decoder bits
    = historical final-state decoder bits

local re-encode
    = original final_state
```

and:

```text
packed chart operations per decode = 1
packed state internal dynamics     = false
```

This establishes the operational target in the horizontal/vertical
representation itself:

```text
(final_state, steps, public law)
    -> unpack once
    -> exact local fiber reverse
    -> original admissible trajectory
```

No external trajectory log or branch map is introduced.

---

## Current next target

The main open implementation problem has shifted.

It is no longer necessary to search for a preferred numerical vertical
permutation in order to recover the trajectory.

The next useful target is to simplify the runtime around the local connection:

1. expose the exact subfiber connection as the primary public codec interface;
2. retain scalar `final_state` only as serialization;
3. reduce repeated scalar-functional evaluations during long reverse walks;
4. investigate whether recurrent reverse-Parry limits can accelerate candidate
   block selection while exact integer boundaries remain the final authority;
5. benchmark direct local decoding against the current packed scalar decoder.

The mathematical information bound remains unchanged.

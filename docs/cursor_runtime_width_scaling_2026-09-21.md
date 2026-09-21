# Cursor runtime and state-width scaling — 2026-09-21

## Status

Validated scientific commit:

```text
5a5f99b765b8bc8aafd3a084167ea6f8e3a62fcf
```

GitHub Actions run:

```text
35564235039
```

Result:

```text
46 / 46 scientific gates passed
```

This phase changes the runtime path, not the admissible trajectory language.

---

## 1. Bidirectional local-fiber cursors

The primary seeded horizontal/vertical machine now has two operational cursors:

```text
VerticalConnectionForwardCursor
VerticalConnectionBackwardCursor
```

Forward state:

```text
(time, horizontal node, vertical rank)
+ current public count vector D_t
```

Backward state:

```text
(time, horizontal node, vertical rank)
+ compact reverse Floquet recurrence window
```

The scalar partition oracle remains available as a reference implementation,
but it is no longer required for the optimized encode/decode path.

---

## 2. Forward cursor

Given current public count vector D_t and physical edge e:u->v:

```text
block_size(e,t) = D_t(u)
```

and the predecessor block offset is the sum of the source-fiber sizes of the
public incoming edges preceding e in the chosen chart ordering.

The next public count row is:

```text
D_(t+1) = A^T D_t.
```

So the local forward step is:

```text
(node=u, rank=r)
    ->
(node=v, rank=offset(e,t)+r).
```

Only one full reachable-state count vector is retained persistently.
A second vector exists transiently while one step is computed.

For the three current universes:

```text
candidate      persistent count integers      peak during step
robust                    46                         92
balanced                  37                         74
long                      34                         68
```

These are integer-slot counts, not Python heap-byte measurements.

---

## 3. Backward cursor

The reverse path uses the previously implemented Floquet backward recurrence.

At time t it regenerates the previous public row D_(t-1), then partitions the
current target fiber by incoming predecessor source counts:

```text
incoming block size
    = D_(t-1)(source).
```

The current vertical rank identifies one unique block, and therefore one unique
predecessor edge.

The reverse recurrence stores:

```text
robust       9 Floquet rows x 16 phase states = 144 count integers
balanced     7 Floquet rows x 13 phase states =  91 count integers
long         5 Floquet rows x 12 phase states =  60 count integers
```

The number of retained count integers is independent of physical decode
horizon.

---

## 4. Scalar-oracle elimination

Run 35564235039 compared the direct scalar local implementation with the cursor
implementation on three frontier final states per universe.

Decode:

```text
candidate      direct scalar_at calls      cursor scalar_at calls
robust                  3,678                       0
balanced                4,413                       0
long                    4,869                       0
```

Encode:

```text
candidate      direct scalar_at calls      cursor scalar_at calls
robust                  3,084                       0
balanced                3,279                       0
long                    3,549                       0
```

The zero-call property is a hard gate, not only instrumentation.

Unit tests also replace `scalar_at()` with a function that raises immediately;
optimized encode/decode still pass.

---

## 5. CI timing measurements

Wall-clock timing is reported but is deliberately not a gate because shared CI
hosts are noisy.

Observed decode speedups in run 35564235039:

```text
robust       ~14.53x
balanced     ~20.66x
long         ~21.86x
```

Observed encode speedups:

```text
robust       ~34.65x
balanced     ~34.42x
long         ~33.47x
```

These measurements compare the same exact trajectory semantics.

---

## 6. Wide-state exact frontiers

The same public universes were tested at final-state widths:

```text
63, 128, 256, 512 bits
```

No universe rule was changed.

Exact trajectory frontiers:

```text
width        robust       balanced       long
  63           208           221          239
 128           434           461          515
 256           879           934        1,064
 512         1,768         1,881        2,166
```

For every width:

- the frontier family fits in 2^W;
- the next exact family exceeds 2^W;
- three representative final states decode exactly;
- re-encode reproduces the exact original final integer;
- scalar_at is forbidden during the cursor roundtrip.

---

## 7. Fixed slot count versus bigint bytes

For each universe, count-integer slot usage remained unchanged from 63 through
512 bits:

```text
candidate      reverse slots       forward persistent slots
robust              144                       46
balanced             91                       37
long                 60                       34
```

This is fixed memory in the sense of number of recurrence/count entries versus
trajectory horizon.

It is NOT constant byte memory with respect to W.

The integer magnitudes grow with the number of admissible trajectories, so
Python big integers require more bytes as W grows.

This distinction is part of the gate output:

```text
storage_measure = integer_slots_not_bigint_bytes
```

---

## 8. Width frontier and topological entropy

For asymptotic public trajectory count

```text
|A_n| ~ C lambda^n,
```

the exact W-bit frontier obeys:

```text
n(W) / W
    -> 1 / log2(lambda).
```

The three independently derived Perron rates are:

```text
candidate      log2(lambda)       asymptotic steps / bit
robust         0.287760787084          3.475108648865
balanced       0.270456820917          3.697447883210
long           0.231413971210          4.321260271238
```

The raw frontier/width ratio approaches those values as W grows.

At W=512:

```text
candidate      observed frontier/W      target          relative error
robust             3.453125000       3.475108649          0.633%
balanced           3.673828125       3.697447883          0.639%
long               4.230468750       4.321260271          2.101%
```

The long candidate has a larger finite transient, so its raw ratio converges
more slowly.

---

## 9. Incremental width slope

Subtracting two frontiers cancels most of the O(1) transient:

```text
Delta n / Delta W
    -> 1 / log2(lambda).
```

For the 256 -> 512 bit interval:

```text
candidate      observed slope       target           relative error
robust          3.472656250      3.475108649           0.0706%
balanced        3.699218750      3.697447883           0.0479%
long            4.304687500      4.321260271           0.3835%
```

Thus the number of additional physical trajectory steps purchased by one
additional state bit is quantitatively controlled by the inverse topological
entropy rate of the public universe.

---

## 10. Current operational picture

The strongest current runtime can be written as:

```text
ENCODE

seed
  -> singleton initial vertical fiber
  -> forward count cursor
  -> horizontal edge + vertical subfiber embedding
  -> ...
  -> one final scalar serialization


DECODE

final_state + steps
  -> initialize backward Floquet cursor
  -> locate final horizontal node + vertical rank
  -> predecessor block identifies previous edge
  -> reverse count cursor
  -> ...
  -> seed node
  -> exact original admissible bits
```

Neither optimized direction requires scalar_at during trajectory evolution.

The public count recurrence is universe state, not trajectory-specific history.

---

## 11. Interpretation

The 63-bit result was not a special numerical coincidence.

Increasing the final-state width extends the exact reversible frontier at an
asymptotic rate determined by the universe's entropy:

```text
additional exact trajectory steps
---------------------------------
additional final-state bits

    -> 1 / log2(lambda).
```

A lower-entropy universe purchases more physical trajectory length per state
bit, but that is precisely because it admits fewer independent trajectory
choices per physical step.

This remains constrained-family addressing, not compression of arbitrary
binary strings.

---

## 12. Next target

The next useful runtime questions are now:

1. benchmark actual Python heap bytes, not only count-integer slots;
2. profile per-step cost as W grows and as physical horizon grows;
3. decide whether the scalar oracle can become a derivation/debug path rather
   than a production decode dependency;
4. expose the cursor-based horizontal/vertical state machine as the primary
   public API;
5. evaluate a C++ implementation of the recurrence and local-fiber cursors;
6. test whether event-clock macrosteps can skip deterministic flights while
   preserving the exact full physical trajectory on demand.

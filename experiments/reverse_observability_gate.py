"""Validate local reverse observability only in branch-disjoint regimes.

Earlier compact-signature experiments trained K=2 at half-width w=3 (total
state width W=6), even though the two branch images already collide there.
No local observable can separate branches after an exact state collision.

This gate separates three questions:

1. Do the full branch images I0(t), I1(t) remain disjoint?
2. If yes, does the existing 36-bit handcrafted observable family remain
   branch-separating?
3. If not, how many raw state coordinates are required by the smallest exact
   coordinate signature on the tested finite universe?

The raw-coordinate search is only a complexity diagnostic. It is not promoted
as a decoder because the selected coordinates may drift with width.
"""

from itertools import combinations

from partition_preserving_universe_search import step
from reverse_relation_signature_search import levels, obs


LAWS = {
    "A": (1, 2, 3, 1, 5),
    "B": (2, 1, 5, 3, 7),
    "C": (3, 2, 9, 1, 11),
    "D": (1, 3, 13, 2, 15),
}


def branch_sets(w, t, kmax, law, level):
    images = [set(), set()]
    for h, v, used in level:
        for e in (0, 1):
            if used + e > kmax:
                continue
            images[e].add(step((h, v), e, t, w, law))
    return images


def first_branch_collision(w, T, kmax, law):
    L = levels(w, T, kmax, law)
    for t in range(T):
        images = branch_sets(w, t, kmax, law, L[t])
        overlap = images[0] & images[1]
        if overlap:
            return t, next(iter(overlap))
    return None


def first_observable_collision(w, T, kmax, law):
    L = levels(w, T, kmax, law)
    for t in range(T):
        signatures = [set(), set()]
        for e in (0, 1):
            for hp, vp in branch_sets(w, t, kmax, law, L[t])[e]:
                signatures[e].add(obs(hp, vp, t, w))
        overlap = signatures[0] & signatures[1]
        if overlap:
            return t, next(iter(overlap))
    return None


def _minimal_difference_masks(w, T, kmax, law):
    """Return irreducible raw-coordinate constraints.

    A selected coordinate set separates the two branch images iff it intersects
    every XOR difference mask between an e=0 state and an e=1 state at the same
    phase. Superset constraints are redundant, so only inclusion-minimal masks
    are retained.
    """
    L = levels(w, T, kmax, law)
    masks = []

    for t in range(T):
        images = branch_sets(w, t, kmax, law, L[t])
        if images[0] & images[1]:
            return None

        left = [h | (v << w) for h, v in images[0]]
        right = [h | (v << w) for h, v in images[1]]
        for a in left:
            for b in right:
                d = a ^ b
                if d == 0:
                    return None
                masks.append(d)

    minimal = []
    for m in sorted(set(masks), key=lambda x: (x.bit_count(), x)):
        if not any((q & m) == q for q in minimal):
            minimal.append(m)
    return minimal


def minimal_raw_coordinate_signature(w, T, kmax, law):
    constraints = _minimal_difference_masks(w, T, kmax, law)
    if constraints is None:
        return None, None

    width = 2 * w
    for size in range(1, width + 1):
        for idx in combinations(range(width), size):
            selected = 0
            for i in idx:
                selected |= 1 << i
            if all(selected & constraint for constraint in constraints):
                return idx, len(constraints)
    return None, len(constraints)


def main():
    law = LAWS["A"]
    kmax = 2

    for w in range(3, 13):
        T = 2 * w
        state_collision = first_branch_collision(w, T, kmax, law)

        if state_collision is not None:
            print(
                "REVERSE_OBSERVABILITY",
                "law", "A",
                "K", kmax,
                "W", 2 * w,
                "T", T,
                "branch_disjoint", False,
                "first_state_collision_t", state_collision[0],
            )
            continue

        observable_collision = first_observable_collision(w, T, kmax, law)
        raw_sig, constraints = minimal_raw_coordinate_signature(
            w, T, kmax, law
        )

        print(
            "REVERSE_OBSERVABILITY",
            "law", "A",
            "K", kmax,
            "W", 2 * w,
            "T", T,
            "branch_disjoint", True,
            "observable36_disjoint", observable_collision is None,
            "first_observable_collision_t",
            None if observable_collision is None else observable_collision[0],
            "raw_signature_bits", None if raw_sig is None else len(raw_sig),
            "raw_signature", raw_sig,
            "minimal_constraints", constraints,
        )


if __name__ == "__main__":
    main()

"""Gate the conditional cyclic-group route to intrinsic vertical reflection."""

from trajectory_generator.gauge_invariant_vertical_law import (
    commutes_with_all_transpositions,
)
from trajectory_generator.structured_fiber_naturality import (
    cyclic_group_automorphisms,
    inversion_is_natural_for_cyclic_group,
    inversion_permutation,
    units_modulo,
)


def main():
    all_group_natural = True
    full_set_noninvariant_witnesses = 0
    checks = 0

    for size in range(1, 33):
        inversion = inversion_permutation(size)
        group_natural = (
            inversion_is_natural_for_cyclic_group(
                size
            )
        )
        all_group_natural = (
            all_group_natural and group_natural
        )

        automorphisms = cyclic_group_automorphisms(
            size
        )
        checks += len(automorphisms)

        set_natural = commutes_with_all_transpositions(
            inversion
        )
        if size >= 3 and not set_natural:
            full_set_noninvariant_witnesses += 1

        print(
            "CYCLIC_FIBER_NATURALITY",
            "size", size,
            "PASS", group_natural,
            "units", len(units_modulo(size)),
            "group_automorphisms",
            len(automorphisms),
            "inversion_group_natural",
            group_natural,
            "inversion_unstructured_set_natural",
            set_natural,
        )

    passed = (
        all_group_natural
        and full_set_noninvariant_witnesses > 0
    )

    print(
        "CYCLIC_FIBER_NATURALITY_FULL_GATE",
        "PASS", passed,
        "group_automorphism_checks", checks,
        "unstructured_noninvariance_witness_sizes",
        full_set_noninvariant_witnesses,
        "conditional_conclusion",
        "if history fibers acquire canonical Z_n structure, inversion becomes "
        "intrinsic under all group-preserving gauge changes",
        "remaining_problem",
        "derive cyclic-group law on history fibers from public universe",
    )

    if not passed:
        raise AssertionError(
            "cyclic fiber naturality gate failed"
        )


if __name__ == "__main__":
    main()

"""Gate that fiber cardinality alone cannot induce a canonical Z_n origin."""

from trajectory_generator.fiber_group_structure_no_go import (
    canonical_origin_exists_from_cardinality,
)


def main():
    exact_small = True

    for size in range(1, 8):
        exists = (
            canonical_origin_exists_from_cardinality(
                size
            )
        )
        expected = size == 1
        passed = exists == expected
        exact_small = exact_small and passed

        print(
            "CARDINALITY_ONLY_ORIGIN_GATE",
            "size", size,
            "PASS", passed,
            "canonical_origin", exists,
            "expected", expected,
        )

    # Project frontier fibers were already measured to have enormous
    # multiplicities.  The theorem is general for every n>1, so it applies to
    # all non-singleton project fibers without enumerating their symmetric
    # groups.
    project_sizes = {
        "robust_208": 1_143_377_287_880_525_663,
        "balanced_221": 2_754_405_653_601_624_727,
        "long_239": 3_627_481_408_934_513_129,
    }

    project_applies = True
    for name, max_fiber in project_sizes.items():
        applies = max_fiber > 1
        project_applies = (
            project_applies and applies
        )
        print(
            "PROJECT_GROUP_STRUCTURE_NO_GO",
            "name", name,
            "PASS", applies,
            "max_fiber", max_fiber,
            "cardinality_only_canonical_origin",
            False,
        )

    passed = exact_small and project_applies

    print(
        "FIBER_GROUP_STRUCTURE_NO_GO_FULL_GATE",
        "PASS", passed,
        "conclusion",
        "Z_n inversion can be intrinsic only after extra public fiber "
        "structure supplies a distinguished origin/group law; cardinality "
        "alone cannot do so",
    )

    if not passed:
        raise AssertionError(
            "fiber group structure no-go gate failed"
        )


if __name__ == "__main__":
    main()

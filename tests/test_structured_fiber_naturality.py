import unittest

from trajectory_generator.structured_fiber_naturality import (
    branch_inversion_is_natural,
    cyclic_group_automorphisms,
    inversion_is_natural_for_cyclic_group,
    inversion_permutation,
    units_modulo,
)
from trajectory_generator.gauge_invariant_vertical_law import (
    commutes_with_all_transpositions,
)


class StructuredFiberNaturalityTests(unittest.TestCase):
    def test_inversion_commutes_with_all_cyclic_group_automorphisms(self):
        for size in range(1, 30):
            self.assertTrue(
                inversion_is_natural_for_cyclic_group(
                    size
                )
            )

    def test_branch_identity_or_inversion_is_group_natural(self):
        for size in range(1, 30):
            self.assertTrue(
                branch_inversion_is_natural(
                    size,
                    is_branch=False,
                )
            )
            self.assertTrue(
                branch_inversion_is_natural(
                    size,
                    is_branch=True,
                )
            )

    def test_extra_structure_really_shrinks_gauge_group(self):
        witness = False
        for size in range(3, 10):
            inversion = inversion_permutation(size)

            self.assertTrue(
                inversion_is_natural_for_cyclic_group(
                    size
                )
            )

            if not commutes_with_all_transpositions(
                inversion
            ):
                witness = True

            for automorphism in cyclic_group_automorphisms(
                size
            ):
                self.assertEqual(
                    automorphism[0],
                    0,
                )

        self.assertTrue(witness)

    def test_units_define_expected_group_automorphism_count(self):
        expected = {
            1: 1,
            2: 1,
            3: 2,
            4: 2,
            5: 4,
            6: 2,
            8: 4,
            10: 4,
        }
        for size, count in expected.items():
            self.assertEqual(
                len(units_modulo(size)),
                count,
            )


if __name__ == "__main__":
    unittest.main()

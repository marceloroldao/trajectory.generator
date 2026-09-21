import unittest

from trajectory_generator.gauge_invariant_vertical_law import (
    certificate,
    center_by_transpositions,
    conjugate,
    identity_permutation,
    phase_reflection_permutation,
    theorem_holds_through,
    transposition,
)


class GaugeInvariantVerticalLawTests(unittest.TestCase):
    def test_center_of_small_symmetric_groups(self):
        expected = {
            1: 1,
            2: 2,
            3: 1,
            4: 1,
            5: 1,
            6: 1,
        }
        for size, center_size in expected.items():
            center = center_by_transpositions(size)
            self.assertEqual(
                len(center),
                center_size,
            )
            if size >= 3:
                self.assertEqual(
                    center,
                    (identity_permutation(size),),
                )

        self.assertTrue(theorem_holds_through(6))

    def test_phase_reflection_is_chart_dependent_for_n_ge_3(self):
        for size in range(3, 8):
            cert = certificate(size)
            self.assertFalse(
                cert.phase_reflection_is_central
            )
            self.assertTrue(
                cert.phase_reflection_witness_exists
            )

    def test_explicit_conjugacy_changes_phase_reflection(self):
        law = phase_reflection_permutation(
            5,
            phase=1,
        )
        gauge = transposition(5, 0, 1)
        changed = conjugate(law, gauge)

        self.assertNotEqual(changed, law)
        self.assertEqual(
            sorted(changed),
            list(range(5)),
        )


if __name__ == "__main__":
    unittest.main()

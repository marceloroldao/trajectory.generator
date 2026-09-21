import unittest

from trajectory_generator.cyclic_fiber_functor import (
    cyclic_injection_homomorphism_exists,
    cyclic_torsor_affine_injection_possible,
    first_divisibility_obstruction,
)


class CyclicFiberFunctorTests(unittest.TestCase):
    def test_cyclic_injection_divisibility_condition(self):
        for n in range(1, 12):
            for m in range(1, 24):
                expected = (m % n) == 0
                self.assertEqual(
                    cyclic_injection_homomorphism_exists(
                        n,
                        m,
                    ),
                    expected,
                )
                self.assertEqual(
                    cyclic_torsor_affine_injection_possible(
                        n,
                        m,
                    ),
                    expected,
                )

    def test_obstruction_certificate(self):
        self.assertIsNone(
            first_divisibility_obstruction(
                ((1, 4), (2, 6), (3, 12))
            )
        )
        self.assertEqual(
            first_divisibility_obstruction(
                ((1, 4), (3, 5), (2, 6))
            ),
            (3, 5),
        )


if __name__ == "__main__":
    unittest.main()

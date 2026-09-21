import unittest

from trajectory_generator.history_naturality_no_go import (
    certificate,
    forced_natural_image,
)
from trajectory_generator.minimal_reversible_completion import (
    MinimalReversibleCompletion,
)


class HistoryNaturalityNoGoTests(unittest.TestCase):
    def test_identity_is_forced_from_singleton_initial_fibers(self):
        completion = MinimalReversibleCompletion(
            {
                0: (1, 2),
                1: (0, 2),
                2: (0,),
            },
            start_nodes=(0,),
        )

        cert = certificate(
            completion,
            horizon=7,
        )
        self.assertTrue(
            cert.singleton_initial_fibers
        )
        self.assertTrue(cert.identity_forced)
        self.assertGreater(
            cert.histories_checked,
            0,
        )
        self.assertEqual(
            cert.histories_checked,
            cert.forced_fixed_histories,
        )

    def test_every_history_is_inductively_fixed(self):
        completion = MinimalReversibleCompletion(
            {
                "a": ("b", "c"),
                "b": ("a",),
                "c": ("a",),
            },
            start_nodes=("a",),
        )

        for time in range(7):
            for node in completion.nodes:
                for history in completion.histories(
                    node,
                    time,
                ):
                    self.assertEqual(
                        forced_natural_image(
                            completion,
                            history,
                        ),
                        history,
                    )

    def test_non_singleton_initial_fiber_is_outside_theorem(self):
        # Duplicate start node creates two distinct initial histories in the
        # implementation, so alpha_0 could permute them and propagate.
        completion = MinimalReversibleCompletion(
            {
                0: (0,),
            },
            start_nodes=(0, 0),
        )
        cert = certificate(
            completion,
            horizon=3,
        )
        self.assertFalse(
            cert.singleton_initial_fibers
        )
        self.assertFalse(
            cert.identity_forced
        )


if __name__ == "__main__":
    unittest.main()

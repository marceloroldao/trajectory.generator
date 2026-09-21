import unittest

from trajectory_generator.symbolic_history_fiber import (
    SymbolicHistoryFibers,
)


class SymbolicHistoryFiberTests(unittest.TestCase):
    def build_pair(self):
        graph_a = {
            "s": ((0, "a"), (1, "b")),
            "a": ((0, "a"), (1, "m")),
            "b": ((0, "m"), (1, "b")),
            "m": ((0, "a"), (1, "b")),
        }
        start_a = {"s": (0, 1)}

        rename = {
            "s": "root",
            "a": "left-renamed",
            "b": "right-renamed",
            "m": "merge-renamed",
        }
        graph_b = {
            rename[source]: tuple(
                (symbol, rename[target])
                for symbol, target in rows
            )
            for source, rows in graph_a.items()
        }
        start_b = {
            rename[node]: word
            for node, word in start_a.items()
        }

        return (
            SymbolicHistoryFibers(
                graph_a,
                start_words=start_a,
                alphabet_order=(0, 1),
            ),
            SymbolicHistoryFibers(
                graph_b,
                start_words=start_b,
                alphabet_order=(0, 1),
            ),
            rename,
        )

    def test_symbol_words_induce_unique_fiber_order(self):
        fibers, _, _ = self.build_pair()

        for time in range(7):
            self.assertTrue(
                fibers.words_are_unique(
                    time=time,
                    within_each_fiber=True,
                )
            )

            for node in fibers.nodes:
                rows = fibers.ordered_histories(
                    node,
                    time,
                )
                for rank, history in enumerate(rows):
                    self.assertEqual(
                        fibers.rank(history, time),
                        rank,
                    )
                    self.assertEqual(
                        fibers.history_by_rank(
                            node,
                            time,
                            rank,
                        ).word,
                        history.word,
                    )

    def test_node_renaming_preserves_symbolic_chart(self):
        first, second, rename = self.build_pair()

        for time in range(7):
            for node in first.nodes:
                self.assertEqual(
                    first.chart_signature(node, time),
                    second.chart_signature(
                        rename[node],
                        time,
                    ),
                )

    def test_ordered_fiber_derives_cyclic_group_coordinate(self):
        fibers, _, _ = self.build_pair()

        witness = False
        for time in range(7):
            for node in fibers.nodes:
                rows = fibers.ordered_histories(
                    node,
                    time,
                )
                size = len(rows)
                if size <= 1:
                    continue

                witness = True
                for rank in range(size):
                    inverse = (
                        fibers.cyclic_inverse_rank(
                            node,
                            time,
                            rank,
                        )
                    )
                    self.assertEqual(
                        fibers.cyclic_add_ranks(
                            node,
                            time,
                            rank,
                            inverse,
                        ),
                        0,
                    )

                self.assertEqual(
                    fibers.rank(
                        fibers.origin(node, time),
                        time,
                    ),
                    0,
                )

        self.assertTrue(witness)


if __name__ == "__main__":
    unittest.main()

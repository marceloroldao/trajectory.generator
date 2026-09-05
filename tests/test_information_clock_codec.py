import unittest

from trajectory_generator.information_clock_codec import (
    count_paths,
    rank_path,
    regenerate_physical_lengths,
    unrank_path,
)


class InformationClockCodecTests(unittest.TestCase):
    def test_rank_unrank_bijection_across_small_lengths(self):
        for start in ("A", "B"):
            for total_length in range(0, 41):
                total = count_paths(start, total_length)
                for rank in range(total):
                    labels = unrank_path(rank, start_state=start, total_length=total_length)
                    self.assertEqual(
                        rank_path(labels, start_state=start, total_length=total_length),
                        rank,
                    )
                    self.assertEqual(sum(regenerate_physical_lengths(labels, start_state=start)), total_length)

    def test_known_macro_path(self):
        labels = ("AB1", "BA2", "AA12")
        total_length = 15
        rank = rank_path(labels, start_state="A", total_length=total_length, end_state="A")
        decoded = unrank_path(rank, start_state="A", total_length=total_length, end_state="A")
        self.assertEqual(decoded, labels)
        self.assertEqual(regenerate_physical_lengths(decoded, start_state="A"), (1, 2, 12))

    def test_invalid_rank_rejected(self):
        total = count_paths("A", 12)
        with self.assertRaises(ValueError):
            unrank_path(total, start_state="A", total_length=12)

    def test_wrong_end_state_rejected(self):
        labels = ("AB1",)
        with self.assertRaises(ValueError):
            rank_path(labels, start_state="A", total_length=1, end_state="A")


if __name__ == "__main__":
    unittest.main()

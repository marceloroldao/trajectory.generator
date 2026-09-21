import unittest

from trajectory_generator.minimal_reversible_completion import (
    MinimalReversibleCompletion,
)


def symmetric_graph():
    return {
        0: (1, 2),
        1: (3,),
        2: (3,),
        3: (0,),
    }


def automorphism(node):
    return {
        0: 0,
        1: 2,
        2: 1,
        3: 3,
    }[node]


def mapped_edge(completion, edge):
    source = automorphism(edge.source)
    target = automorphism(edge.target)
    matches = [
        candidate
        for candidate in completion.outgoing[source]
        if candidate.target == target
    ]
    if len(matches) != 1:
        raise AssertionError(
            "test graph requires unique mapped edge"
        )
    return matches[0]


def incoming_index(completion, edge):
    return completion.incoming[edge.target].index(edge)


def phase_reflection(edge, time, vertical, size):
    sigma = -1 if (time % 3) == 1 else 1
    return (sigma * vertical) % size


def ordered_phase_merge(completion, edge, time, vertical, size):
    sigma = -1 if (time % 3) == 1 else 1
    return (
        sigma * vertical
        + incoming_index(completion, edge)
    ) % size


class VerticalGaugeSymmetryTests(unittest.TestCase):
    def test_phase_reflection_is_automorphism_invariant(self):
        completion = MinimalReversibleCompletion(
            symmetric_graph(),
            start_nodes=(0,),
        )

        checked = 0
        for time in range(10):
            for edge in completion.edges:
                mapped = mapped_edge(completion, edge)
                size = completion.fiber_size(
                    edge.source,
                    time,
                )
                mapped_size = completion.fiber_size(
                    mapped.source,
                    time,
                )
                self.assertEqual(size, mapped_size)
                if size == 0:
                    continue

                for vertical in range(size):
                    checked += 1
                    self.assertEqual(
                        phase_reflection(
                            edge,
                            time,
                            vertical,
                            size,
                        ),
                        phase_reflection(
                            mapped,
                            time,
                            vertical,
                            mapped_size,
                        ),
                    )

        self.assertGreater(checked, 0)

    def test_incoming_index_rotation_breaks_raw_automorphism_invariance(self):
        completion = MinimalReversibleCompletion(
            symmetric_graph(),
            start_nodes=(0,),
        )

        witness = None
        for time in range(12):
            for edge in completion.edges:
                mapped = mapped_edge(completion, edge)
                size = completion.fiber_size(
                    edge.source,
                    time,
                )
                if size <= 1:
                    continue

                for vertical in range(size):
                    left = ordered_phase_merge(
                        completion,
                        edge,
                        time,
                        vertical,
                        size,
                    )
                    right = ordered_phase_merge(
                        completion,
                        mapped,
                        time,
                        vertical,
                        size,
                    )
                    if left != right:
                        witness = (
                            time,
                            edge,
                            mapped,
                            size,
                            vertical,
                            left,
                            right,
                        )
                        break
                if witness is not None:
                    break
            if witness is not None:
                break

        self.assertIsNotNone(witness)


if __name__ == "__main__":
    unittest.main()

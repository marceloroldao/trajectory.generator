from __future__ import annotations

import sys
from pathlib import Path

EXPERIMENTS = Path(__file__).resolve().parents[1] / "experiments"
if str(EXPERIMENTS) not in sys.path:
    sys.path.insert(0, str(EXPERIMENTS))

from information_clock_physical_roundtrip import (  # noqa: E402
    canonical_physical_macrograph,
    expand_labels,
    physical_length,
    roundtrip,
)
from trajectory_generator.information_clock_codec import count_paths, rank_path, unrank_path  # noqa: E402


def _enumerate_labels(start_state: str, total_length: int):
    total = count_paths(start_state, total_length)
    for rank in range(total):
        yield unrank_path(rank, start_state=start_state, total_length=total_length)


def test_derived_macrograph_matches_canonical_public_labels():
    branch_states, edges = canonical_physical_macrograph()
    assert set(branch_states) == {"A", "B"}
    assert {edge.label for edge in edges} == {"AB1", "AA12", "BA2", "BA5"}
    for edge in edges:
        assert len(edge.path) - 1 == edge.physical_length


def test_sample_physical_roundtrip_is_exact():
    samples = (
        ("A", ("AB1", "BA2")),
        ("A", ("AA12",)),
        ("A", ("AB1", "BA5", "AA12")),
        ("B", ("BA2", "AB1", "BA5")),
    )
    for start_state, labels in samples:
        original = expand_labels(labels, start_state=start_state)
        recovered = roundtrip(labels, start_state=start_state)
        assert recovered == original
        assert physical_length(recovered) == sum(len_ for len_ in [
            # rank/unrank already validates the canonical physical accounting;
            # this expression only keeps the assertion explicit for the sample.
            physical_length(original)
        ])


def test_exhaustive_small_lengths_recover_identical_microscopic_path():
    # Exhaust every admissible macro path for a bounded physical-length window.
    # The graph's longest macro edge is 12, so 1..36 exercises multiple long/short
    # combinations while keeping the test lightweight and deterministic.
    for start_state in ("A", "B"):
        for total_length in range(1, 37):
            for labels in _enumerate_labels(start_state, total_length):
                original = expand_labels(labels, start_state=start_state)
                assert physical_length(original) == total_length

                address = rank_path(
                    labels,
                    start_state=start_state,
                    total_length=total_length,
                )
                recovered_labels = unrank_path(
                    address,
                    start_state=start_state,
                    total_length=total_length,
                )
                recovered = expand_labels(recovered_labels, start_state=start_state)

                assert recovered_labels == labels
                assert recovered == original

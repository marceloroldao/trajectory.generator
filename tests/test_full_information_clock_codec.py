import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments"
if str(EXP) not in sys.path:
    sys.path.insert(0, str(EXP))

import full_information_clock_codec_v2 as clock


def test_macro_count_matches_stepwise_small_lengths():
    for n in range(0, 25):
        assert clock.admissible_count(n) == clock.stepwise_reference_count(n)


def test_rank_unrank_small_lengths():
    for n in range(0, 18):
        total = clock.admissible_count(n)
        for rank in range(min(total, 128)):
            path = clock.unrank_path(rank, n)
            assert len(path) == n + 1
            assert clock.rank_path(path) == rank


def test_address_roundtrip():
    for n in range(0, 16):
        total = clock.admissible_count(n)
        for rank in range(min(total, 64)):
            path = clock.unrank_path(rank, n)
            final_state, steps = clock.encode_path(path)
            decoded, bits = clock.decode_path(final_state, steps)
            assert decoded == path
            assert len(bits) == n + 3


def test_full_family_boundary_matches_topological_bit_frontier():
    assert clock.admissible_count(218) == 9_131_204_053_820_206_208
    assert clock.capacity_ok(218)
    assert clock.admissible_count(219) == 10_214_739_716_735_776_832
    assert not clock.capacity_ok(219)
    # Three initial history bits + physical transitions.
    assert 218 + 3 == 221

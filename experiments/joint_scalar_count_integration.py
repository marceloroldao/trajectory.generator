"""Validate scalar public-field counts against the joint dyadic address.

Goal: freeze a v0.1 mathematical baseline only if the compact scalar law
reproduces every whole-slice count used by the joint address through the
63-bit frontier.  This deliberately separates a proved optimization (whole
slice counts from time alone) from future work (interval-conditioned
paths_count used inside dyadic blocks).
"""
from joint_dyadic_address import total_count, block_lengths
from scalar_public_field import scalar_counts_at

EXPECTED218 = 9131204053820206208
EXPECTED219 = 10214739716735776832


def scalar_total(t: int) -> int:
    return sum(scalar_counts_at(t).values())


def main():
    for t in range(220):
        a = total_count(t)
        b = scalar_total(t)
        assert a == b, (t, a, b)
    assert scalar_total(218) == EXPECTED218
    assert scalar_total(219) == EXPECTED219
    assert scalar_total(218).bit_length() == 63
    assert scalar_total(219).bit_length() == 64
    print('joint_scalar_total_equivalence_0_219 ok')
    print('frontier218', scalar_total(218), 'bits', scalar_total(218).bit_length())
    print('frontier219', scalar_total(219), 'bits', scalar_total(219).bit_length())
    print('blocks218', block_lengths(218))
    print('proved: whole-slice public counts are derivable from time via scalar recurrence')
    print('not_yet_proved: replacing interval-conditioned paths_count inside dyadic ranking')


if __name__ == '__main__':
    main()

"""Algebraic sparse trajectory state using a public root polynomial.

For a K-sparse binary trajectory, keep the monic polynomial

    P_t(z) = z^(K-r) * product(z - (i+1))

over GF(p), where the product runs over innovation positions i already seen
and r is their count. p must be prime and greater than the public trajectory
length, so every position maps to a distinct non-zero field element.

Only the K non-leading coefficients are stored; the leading coefficient is
always one. An innovation at step t replaces one zero root with x=t+1.

Reverse decoding is local:

    e_t = 1  iff  P_{t+1}(t+1) == 0 (mod p).

If e_t=1, divide by (z-(t+1)) and multiply by z to restore the predecessor.
No trajectory log, rank table, or reachable-manifold reconstruction is used.

This construction is exact for <=K innovations, but it is not capacity-optimal:
the ambient coefficient state space contains many polynomials that are not valid
trajectory states. For fixed K the asymptotic redundancy is about log2(K!) bits.
"""

from __future__ import annotations

from typing import Iterable, Sequence, Tuple


State = Tuple[int, ...]


def _validate_params(k: int, p: int) -> None:
    if k < 1:
        raise ValueError("k must be >= 1")
    if p <= 2:
        raise ValueError("p must be an odd prime field modulus")


def state_space_size(k: int, p: int) -> int:
    _validate_params(k, p)
    return p ** k


def state_width_bits(k: int, p: int) -> int:
    """Bits required to pack all coefficient states as one base-p integer."""
    return (state_space_size(k, p) - 1).bit_length()


def zero_state(k: int) -> State:
    if k < 1:
        raise ValueError("k must be >= 1")
    return (0,) * k


def pack_state(state: Sequence[int], p: int) -> int:
    """Pack K base-p coefficients into one non-negative integer."""
    k = len(state)
    _validate_params(k, p)
    acc = 0
    mul = 1
    for c in state:
        if not 0 <= c < p:
            raise ValueError("coefficient outside GF(p)")
        acc += c * mul
        mul *= p
    return acc


def unpack_state(value: int, k: int, p: int) -> State:
    """Inverse of pack_state for values in [0, p**K)."""
    _validate_params(k, p)
    if not 0 <= value < p ** k:
        raise ValueError("packed state outside coefficient state space")
    out = []
    x = value
    for _ in range(k):
        x, digit = divmod(x, p)
        out.append(digit)
    return tuple(out)


def _full(state: Sequence[int]) -> list[int]:
    """Return low-to-high coefficients with implicit monic leading 1."""
    return list(state) + [1]


def _eval_full(coeffs: Sequence[int], x: int, p: int) -> int:
    acc = 0
    for c in reversed(coeffs):
        acc = (acc * x + c) % p
    return acc


def _mul_linear(coeffs: Sequence[int], x: int, p: int) -> list[int]:
    """Multiply polynomial by (z-x), low-to-high coefficients."""
    out = [0] * (len(coeffs) + 1)
    for i, c in enumerate(coeffs):
        out[i] = (out[i] - x * c) % p
        out[i + 1] = (out[i + 1] + c) % p
    return out


def _div_linear_monic(coeffs: Sequence[int], x: int, p: int) -> list[int]:
    """Exact synthetic division by (z-x); raise if x is not a root."""
    if len(coeffs) < 2:
        raise ValueError("polynomial degree must be >= 1")
    degree = len(coeffs) - 1
    q = [0] * degree
    q[-1] = coeffs[-1] % p
    for i in range(degree - 2, -1, -1):
        q[i] = (coeffs[i + 1] + x * q[i + 1]) % p
    remainder = (coeffs[0] + x * q[0]) % p
    if remainder:
        raise ValueError("division is not exact")
    return q


def evaluate(state: Sequence[int], x: int, p: int) -> int:
    """Evaluate the implicit monic polynomial represented by state."""
    _validate_params(len(state), p)
    return _eval_full(_full(state), x % p, p)


def forward_step(
    state: Sequence[int],
    innovation: int | bool,
    t: int,
    p: int,
) -> State:
    """Advance one public step.

    innovation=0 leaves the polynomial unchanged.
    innovation=1 replaces one zero root by x=t+1.
    """
    k = len(state)
    _validate_params(k, p)
    if t < 0:
        raise ValueError("t must be >= 0")
    x = t + 1
    if x >= p:
        raise ValueError("trajectory step aliases modulo p; require T < p")

    s = tuple(int(c) % p for c in state)
    if not innovation:
        return s

    full = _full(s)
    if full[0] % p != 0:
        raise ValueError("innovation budget exhausted")

    # P(z) has at least one zero root: divide by z, then insert root x.
    quotient = full[1:]
    updated = _mul_linear(quotient, x, p)
    if updated[-1] % p != 1:
        raise AssertionError("monic invariant violated")
    return tuple(c % p for c in updated[:-1])


def reverse_step(state: Sequence[int], t: int, p: int) -> tuple[State, int]:
    """Recover one branch from current state + public step only.

    Returns (predecessor_state, innovation_bit).
    """
    k = len(state)
    _validate_params(k, p)
    if t < 0:
        raise ValueError("t must be >= 0")
    x = t + 1
    if x >= p:
        raise ValueError("trajectory step aliases modulo p; require T < p")

    s = tuple(int(c) % p for c in state)
    full = _full(s)
    if _eval_full(full, x, p) != 0:
        return s, 0

    quotient = _div_linear_monic(full, x, p)
    predecessor = [0] + quotient
    if predecessor[-1] % p != 1:
        raise AssertionError("monic invariant violated")
    return tuple(c % p for c in predecessor[:-1]), 1


def encode(bits: Iterable[int | bool], k: int, p: int) -> State:
    """Encode a <=K-sparse binary trajectory into the final polynomial state."""
    state = zero_state(k)
    for t, bit in enumerate(bits):
        state = forward_step(state, bit, t, p)
    return state


def decode(state: Sequence[int], steps: int, p: int) -> list[int]:
    """Recover the complete binary trajectory from final state + step count."""
    if steps < 0:
        raise ValueError("steps must be >= 0")
    if steps >= p:
        raise ValueError("require steps < p")
    current = tuple(state)
    bits = [0] * steps
    for t in range(steps - 1, -1, -1):
        current, bit = reverse_step(current, t, p)
        bits[t] = bit
    if current != zero_state(len(state)):
        raise ValueError("state is not a valid trajectory state for this horizon")
    return bits

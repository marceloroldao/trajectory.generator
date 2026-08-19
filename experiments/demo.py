from trajectory_generator import bytes_to_bits, encode_bits, recover_unique


def run(bits: list[int]) -> None:
    final_state, steps = encode_bits(bits)
    recovered = recover_unique(final_state, steps)

    print("bits        :", "".join(map(str, bits)))
    print("final_state :", final_state)
    print("steps       :", steps)
    print("recovered   :", "".join(map(str, recovered)))
    print("exact       :", recovered == bits)
    print()


if __name__ == "__main__":
    # Keep the exact decoder tests deliberately small; it enumerates 2**steps paths.
    run([0, 1, 1, 0, 1, 0, 0, 1])
    run(bytes_to_bits(b"A"))

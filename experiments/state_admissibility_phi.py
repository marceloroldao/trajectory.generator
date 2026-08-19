from trajectory_generator.state_admissibility import admissible_count


if __name__ == "__main__":
    prev = admissible_count(1)
    print("n count ratio")
    for n in range(2, 41):
        current = admissible_count(n)
        print(n, current, current / prev)
        prev = current

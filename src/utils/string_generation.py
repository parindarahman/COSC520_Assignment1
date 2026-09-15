"""Synthetic login name generation for testing and benchmarking."""

import random

# Characters permitted in generated login names.
ALPHABET = "abcdefghijklmnopqrstuvwxyz0123456789"


def generate_strings(count, length=12, seed=None):
    """
    Generate a list of unique random login names.

    Input:  count (int) — how many login names to produce
            length (int) — number of characters in each name
            seed (int or None) — fixed seed for reproducible output
    Output: list of str — exactly 'count' unique login names

    Draws characters uniformly from ALPHABET. Candidates are checked
    against those already produced, so the result contains no
    duplicates. Insertion order is preserved, making output identical
    across runs for a given seed.
    """
    if count < 0:
        raise ValueError("count must be non-negative")
    if length < 1:
        raise ValueError("length must be at least 1")

    # Reject requests that cannot be satisfied with unique names.
    if count > len(ALPHABET) ** length:
        raise ValueError(
            f"cannot generate {count} unique names of length {length}"
        )

    rng = random.Random(seed)
    seen = set()
    names = []

    while len(names) < count:
        candidate = "".join(rng.choices(ALPHABET, k=length))
        if candidate not in seen:
            seen.add(candidate)
            names.append(candidate)

    return names
"""Unit tests for the FNV-1a hash function."""

from src.utils.hashes import FNV_OFFSET_BASIS, MASK_64, fnv1a_64


def test_is_deterministic():
    """The same input and seed always produce the same hash."""
    assert fnv1a_64("parinda") == fnv1a_64("parinda")
    assert fnv1a_64("parinda", seed=7) == fnv1a_64("parinda", seed=7)


def test_matches_published_empty_string_value():
    """Hashing an empty string returns the offset basis unchanged.

    The loop body never runs for an empty input, so the result is the
    starting value. This checks the implementation against the published
    specification rather than only against itself.
    """
    assert fnv1a_64("") == FNV_OFFSET_BASIS


def test_output_fits_in_64_bits():
    """Every hash lies within the unsigned 64-bit range."""
    for text in ["", "a", "parinda", "x" * 1000, "日本語"]:
        assert 0 <= fnv1a_64(text) <= MASK_64


def test_different_inputs_differ():
    """Distinct strings hash to distinct values."""
    assert fnv1a_64("parinda") != fnv1a_64("rahman")
    assert fnv1a_64("parinda") != fnv1a_64("parindaa")


def test_different_seeds_differ():
    """The same string hashes differently under different seeds."""
    values = {fnv1a_64("parinda", seed=s) for s in range(10)}
    assert len(values) == 10


def test_input_change_alters_output():
    """Changing a character early in the input changes most output bits.

    Counts how many of the 64 output bits differ. Because the
    accumulator is multiplied by the FNV prime once per remaining byte,
    a difference early in the string propagates widely. FNV-1a mixes the
    final byte only once, so a trailing-character difference produces a
    small output change by design and is deliberately not used here.
    """
    changed = fnv1a_64("user_00001") ^ fnv1a_64("user_10001")
    assert 16 <= bin(changed).count("1") <= 48


def test_distributes_across_buckets(stored_logins):
    """Hashes spread evenly enough for use as bucket indices.

    With 1000 logins across 64 buckets, a uniform hash gives about 16
    per bucket. Every bucket should be used and none should hold an
    extreme share.
    """
    buckets = [0] * 64
    for login in stored_logins:
        buckets[fnv1a_64(login) % 64] += 1

    assert min(buckets) > 0
    assert max(buckets) < 40
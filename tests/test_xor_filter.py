"""Unit tests for the XorFilter data structure."""

import pytest

from src.utils.string_generation import generate_strings
from src.xor_filter import XorFilter


def test_no_false_negatives(stored_logins):
    """Every login the filter was built over is reported as present.

    This is the filter's defining guarantee and must hold without
    exception.
    """
    checker = XorFilter(stored_logins)
    for login in stored_logins:
        assert checker.check(login) is True


def test_false_positive_rate_near_theory():
    """The observed error rate is close to 2^-f.

    With eight-bit fingerprints the predicted rate is about 0.4 percent.
    The tolerance is wide because the outcome is stochastic.
    """
    stored = generate_strings(10_000, seed=1)
    absent = generate_strings(10_000, seed=2)

    checker = XorFilter(stored, fingerprint_bits=8)
    observed = sum(checker.check(login) for login in absent) / len(absent)

    assert observed < 3 * (2 ** -8)


def test_more_fingerprint_bits_reduce_errors():
    """Wider fingerprints give a lower false positive rate."""
    stored = generate_strings(5_000, seed=1)
    absent = generate_strings(5_000, seed=2)

    narrow = XorFilter(stored, fingerprint_bits=8)
    wide = XorFilter(stored, fingerprint_bits=16)

    narrow_rate = sum(narrow.check(x) for x in absent) / len(absent)
    wide_rate = sum(wide.check(x) for x in absent) / len(absent)

    assert wide_rate <= narrow_rate


def test_array_is_about_one_and_a_quarter_slots_per_login():
    """Space use matches the 1.23n figure the method is built around."""
    checker = XorFilter(generate_strings(10_000, seed=3))
    assert 1.2 <= checker.size / checker.count <= 1.3


def test_single_login():
    """A filter over one login finds it and rejects others."""
    checker = XorFilter(["parinda"])
    assert checker.check("parinda") is True
    assert checker.check("someone_else") is False


def test_duplicate_logins_are_collapsed():
    """Repeated logins in the input do not prevent construction."""
    checker = XorFilter(["a", "b", "a", "c", "b"])
    assert checker.count == 3
    for login in ["a", "b", "c"]:
        assert checker.check(login) is True


def test_rejects_empty_input():
    """Building over no logins raises rather than failing silently."""
    with pytest.raises(ValueError):
        XorFilter([])


def test_handles_unusual_strings():
    """Empty, long, non-ASCII, and symbol-bearing logins are handled."""
    unusual = ["", "x" * 1_000, "user@domain.com", "日本語", "  spaces  "]
    checker = XorFilter(unusual)
    for item in unusual:
        assert checker.check(item) is True
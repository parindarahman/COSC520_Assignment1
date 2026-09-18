"""Unit tests for the BloomFilter data structure."""

import pytest

from src.bloom_filter import BloomFilter
from src.utils.string_generation import generate_strings
from tests.conftest import DUPLICATE_CASES


@pytest.mark.parametrize("logins, expected", DUPLICATE_CASES)
def test_duplicate_detection(logins, expected):
    """Each login is reported as taken only after its first occurrence.

    A false positive would break this, so the filter is sized generously
    relative to the handful of logins involved.
    """
    checker = BloomFilter(expected_items=1000, false_positive_rate=0.001)
    for login, already_taken in zip(logins, expected):
        assert checker.check(login) == already_taken
        if not already_taken:
            checker.add(login)


def test_empty_structure_finds_nothing():
    """An empty filter reports every query as absent."""
    checker = BloomFilter(expected_items=100)
    assert checker.check("parinda") is False
    assert checker.check("") is False


def test_no_false_negatives(stored_logins):
    """Every login that was added is always reported as present.

    This is the filter's defining guarantee and must hold without
    exception.
    """
    checker = BloomFilter(expected_items=len(stored_logins))
    for login in stored_logins:
        checker.add(login)
    for login in stored_logins:
        assert checker.check(login) is True


def test_false_positive_rate_near_target():
    """The observed error rate is close to the configured target.

    Queries 10000 logins that were never stored and counts how many are
    wrongly reported present. The tolerance is wide because the outcome
    is stochastic, but a broken hash or bit index would miss it by far
    more than this.
    """
    target = 0.01
    stored = generate_strings(10_000, seed=1)
    absent = generate_strings(10_000, seed=2)

    checker = BloomFilter(expected_items=10_000, false_positive_rate=target)
    for login in stored:
        checker.add(login)

    false_positives = sum(checker.check(login) for login in absent)
    observed = false_positives / len(absent)

    assert observed < target * 3


def test_sizing_follows_the_formulas():
    """Bit count and hash count match the published expressions."""
    checker = BloomFilter(expected_items=10_000, false_positive_rate=0.01)

    # m = -n ln(p) / (ln 2)^2 is about 9.6 bits per item at p = 0.01,
    # and k = (m/n) ln 2 is then about 7.
    assert 9 * 10_000 <= checker.size <= 11 * 10_000
    assert checker.hash_count == 7


def test_lower_error_rate_costs_more_space():
    """Demanding fewer false positives requires a larger bit array."""
    lenient = BloomFilter(expected_items=1000, false_positive_rate=0.1)
    strict = BloomFilter(expected_items=1000, false_positive_rate=0.001)

    assert strict.size > lenient.size
    assert strict.hash_count > lenient.hash_count


def test_rejects_invalid_parameters():
    """Impossible configurations raise rather than failing silently."""
    with pytest.raises(ValueError):
        BloomFilter(expected_items=0)
    with pytest.raises(ValueError):
        BloomFilter(expected_items=100, false_positive_rate=0)
    with pytest.raises(ValueError):
        BloomFilter(expected_items=100, false_positive_rate=1)


def test_handles_unusual_strings():
    """Empty, long, non-ASCII, and symbol-bearing logins are handled."""
    checker = BloomFilter(expected_items=100, false_positive_rate=0.001)
    unusual = ["", "x" * 1_000, "user@domain.com", "日本語", "  spaces  "]
    for item in unusual:
        checker.add(item)
    for item in unusual:
        assert checker.check(item) is True
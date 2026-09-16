"""Unit tests for the LinearSearch data structure."""

import pytest

from src.linear_search import LinearSearch
from tests.conftest import DUPLICATE_CASES


@pytest.mark.parametrize("logins, expected", DUPLICATE_CASES)
def test_duplicate_detection(logins, expected):
    """Each login is reported as taken only after its first occurrence."""
    checker = LinearSearch()
    for login, already_taken in zip(logins, expected):
        assert checker.check(login) == already_taken
        if not already_taken:
            checker.add(login)


def test_empty_structure_finds_nothing():
    """An empty structure reports every query as absent."""
    checker = LinearSearch()
    assert checker.check("parinda") is False
    assert checker.check("") is False


def test_single_login():
    """A structure holding one login finds it and rejects others."""
    checker = LinearSearch()
    checker.add("parinda")
    assert checker.check("parinda") is True
    assert checker.check("rahman") is False


def test_no_false_negatives(stored_logins):
    """Every login that was added is always reported as present."""
    checker = LinearSearch()
    for login in stored_logins:
        checker.add(login)
    for login in stored_logins:
        assert checker.check(login) is True


def test_no_false_positives(stored_logins, absent_logins):
    """logins never added are reported as absent."""
    checker = LinearSearch()
    for login in stored_logins:
        checker.add(login)
    for login in absent_logins:
        assert checker.check(login) is False


def test_handles_unusual_strings():
    """Empty, long, non-ASCII, and symbol-bearing logins are handled."""
    checker = LinearSearch()
    unusual = ["", "x" * 10_000, "user@domain.com", "日本語", "  spaces  "]
    for item in unusual:
        checker.add(item)
    for item in unusual:
        assert checker.check(item) is True
    assert checker.check("not_added") is False
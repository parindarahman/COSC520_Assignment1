"""Unit tests for the BinarySearch data structure."""

import pytest

from src.binary_search import BinarySearch
from tests.conftest import DUPLICATE_CASES


@pytest.mark.parametrize("logins, expected", DUPLICATE_CASES)
def test_duplicate_detection(logins, expected):
    """Each login is reported as taken only after its first occurrence."""
    checker = BinarySearch()

    # Check each login and add it only when it is not already present.
    for login, already_taken in zip(logins, expected):
        assert checker.check(login) == already_taken
        if not already_taken:
            checker.add(login)


def test_empty_structure_finds_nothing():
    """An empty structure reports every query as absent."""
    checker = BinarySearch()

    # Verify that regular and empty strings are absent initially.
    assert checker.check("parinda") is False
    assert checker.check("") is False


def test_single_login():
    """A structure holding one login finds it and rejects others."""
    checker = BinarySearch()

    # Add one login and verify exact membership.
    checker.add("parinda")
    assert checker.check("parinda") is True
    assert checker.check("rahman") is False


def test_no_false_negatives(stored_logins):
    """Every login that was added is always reported as present."""
    checker = BinarySearch()

    # Add all provided logins to the structure.
    for login in stored_logins:
        checker.add(login)

    # Verify that every added login can be found.
    for login in stored_logins:
        assert checker.check(login) is True


def test_no_false_positives(stored_logins, absent_logins):
    """Exact membership: logins never added are reported as absent."""
    checker = BinarySearch()

    # Populate the structure with the known stored logins.
    for login in stored_logins:
        checker.add(login)

    # Verify that logins not added are never reported as present.
    for login in absent_logins:
        assert checker.check(login) is False


def test_stays_sorted_after_random_inserts(stored_logins):
    """The internal list is in sorted order regardless of insert order."""
    checker = BinarySearch()

    # Insert logins in the order supplied by the fixture.
    for login in stored_logins:
        checker.add(login)

    # Confirm that the internal representation remains sorted.
    items = checker.sorted_items
    assert all(items[i] <= items[i + 1] for i in range(len(items) - 1))


def test_build_matches_incremental_adds(stored_logins):
    """Bulk build produces the same contents as repeated add() calls."""

    # Build one structure by adding each login individually.
    incremental = BinarySearch()
    for login in stored_logins:
        incremental.add(login)

    # Build another structure using the bulk build operation.
    bulk = BinarySearch()
    bulk.build(stored_logins)

    # Verify that both construction methods produce identical contents.
    assert bulk.sorted_items == incremental.sorted_items


def test_handles_unusual_strings():
    """Empty, long, non-ASCII, and symbol-bearing logins are handled."""
    checker = BinarySearch()

    # Create logins containing several unusual string formats.
    unusual = ["", "x" * 1_000, "user@domain.com", "日", "  spaces  "]

    # Add every unusual string to the structure.
    for item in unusual:
        checker.add(item)

    # Verify that every unusual string can be retrieved correctly.
    for item in unusual:
        assert checker.check(item) is True

    # Confirm that an unrelated value is still reported as absent.
    assert checker.check("not_added") is False
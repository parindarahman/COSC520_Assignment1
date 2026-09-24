"""Unit tests for the HashTable data structure."""

import pytest

from src.hash_table import HashTable
from tests.conftest import DUPLICATE_CASES


@pytest.mark.parametrize("logins, expected", DUPLICATE_CASES)
def test_duplicate_detection(logins, expected):
    """Each login is reported as taken only after its first occurrence."""
    checker = HashTable()
    for login, already_taken in zip(logins, expected):
        assert checker.check(login) == already_taken
        if not already_taken:
            checker.add(login)


def test_empty_structure_finds_nothing():
    """An empty table reports every query as absent."""
    checker = HashTable()
    assert checker.check("parinda") is False
    assert checker.check("") is False


def test_single_login():
    """A table holding one login finds it and rejects others."""
    checker = HashTable()
    checker.add("parinda")
    assert checker.check("parinda") is True
    assert checker.check("someone_else") is False


def test_no_false_negatives(stored_logins):
    """Every login that was added is always reported as present."""
    checker = HashTable()
    for login in stored_logins:
        checker.add(login)
    for login in stored_logins:
        assert checker.check(login) is True


def test_no_false_positives(stored_logins, absent_logins):
    """Exact membership: logins never added are reported as absent."""
    checker = HashTable()
    for login in stored_logins:
        checker.add(login)
    for login in absent_logins:
        assert checker.check(login) is False


def test_resizes_as_it_grows(stored_logins):
    """Capacity increases so that the load factor stays within bounds.

    Without resizing, chains would lengthen with n and lookup would
    degrade from constant to linear time.
    """
    checker = HashTable(capacity=16)
    for login in stored_logins:
        checker.add(login)

    assert checker.capacity > 16
    assert checker.count / checker.capacity <= checker.max_load


def test_resize_preserves_every_login(stored_logins):
    """No login is lost when the table is rehashed into more buckets.

    Bucket indices depend on the capacity, so entries must be
    redistributed rather than copied.
    """
    checker = HashTable(capacity=2)
    for login in stored_logins:
        checker.add(login)

    assert checker.count == len(stored_logins)
    for login in stored_logins:
        assert checker.check(login) is True


def test_duplicates_do_not_grow_the_table():
    """Adding the same login repeatedly leaves the stored count at one."""
    checker = HashTable()
    for _ in range(100):
        checker.add("parinda")

    assert checker.count == 1
    assert checker.check("parinda") is True


def test_survives_forced_collisions():
    """Logins sharing a bucket are all still found.

    A single-bucket table forces every login into the same chain, which
    exercises the collision path that a well-distributed hash function
    would otherwise rarely reach.
    """
    checker = HashTable(capacity=1, max_load=1000)
    logins = [f"user_{i}" for i in range(50)]
    for login in logins:
        checker.add(login)

    assert len(checker.buckets) == 1
    for login in logins:
        assert checker.check(login) is True
    assert checker.check("user_999") is False


def test_build_matches_incremental_adds(stored_logins):
    """Bulk loading stores the same logins as repeated add() calls."""
    incremental = HashTable()
    for login in stored_logins:
        incremental.add(login)

    bulk = HashTable()
    bulk.build(stored_logins)

    assert bulk.count == incremental.count
    for login in stored_logins:
        assert bulk.check(login) is True


def test_handles_unusual_strings():
    """Empty, long, non-ASCII, and symbol-bearing logins are handled."""
    checker = HashTable()
    unusual = ["", "x" * 1_000, "user@domain.com", "日本語", "  spaces  "]
    for item in unusual:
        checker.add(item)
    for item in unusual:
        assert checker.check(item) is True
    assert checker.check("not_added") is False
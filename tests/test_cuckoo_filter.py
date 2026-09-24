"""Unit tests for the CuckooFilter data structure."""

import pytest

from src.cuckoo_filter import CuckooFilter
from src.utils.string_generation import generate_strings
from tests.conftest import DUPLICATE_CASES


@pytest.mark.parametrize("logins, expected", DUPLICATE_CASES)
def test_duplicate_detection(logins, expected):
    """Each login is reported as taken only after its first occurrence.

    The filter is sized generously so that a false positive is very
    unlikely to disturb the expected sequence.
    """
    checker = CuckooFilter(expected_items=10_000)
    for login, already_taken in zip(logins, expected):
        assert checker.check(login) == already_taken
        if not already_taken:
            checker.add(login)


def test_empty_structure_finds_nothing():
    """An empty filter reports every query as absent."""
    checker = CuckooFilter(expected_items=100)
    assert checker.check("parinda") is False
    assert checker.check("") is False


def test_no_false_negatives(stored_logins):
    """Every login stored successfully is always reported as present.

    This is the filter's defining guarantee. Only logins whose insertion
    succeeded are checked, since insertion may legitimately fail.
    """
    checker = CuckooFilter(expected_items=len(stored_logins))
    accepted = [login for login in stored_logins if checker.add(login)]

    assert len(accepted) == len(stored_logins)
    for login in accepted:
        assert checker.check(login) is True


def test_alternate_index_is_reversible():
    """Applying the alternate-index step twice returns the original.

    This XOR property is what allows an entry to be relocated knowing
    only its fingerprint, and a break here would silently lose entries.
    """
    checker = CuckooFilter(expected_items=1000)
    fingerprint = checker.fingerprint("parinda")

    for first in range(0, checker.table_size, 17):
        second = checker.alternate_index(first, fingerprint)
        assert checker.alternate_index(second, fingerprint) == first


def test_fingerprints_are_never_zero():
    """No login produces a zero fingerprint.

    Zero is reserved so a stored value is never mistaken for an empty
    slot.
    """
    checker = CuckooFilter(expected_items=1000)
    for login in generate_strings(5000, seed=11):
        assert checker.fingerprint(login) != 0


def test_false_positive_rate_is_low():
    """Absent logins are rarely reported as present.

    With 12-bit fingerprints in buckets of four, theory predicts an
    error rate near 2b/2^f, which is about 0.2 percent.
    """
    stored = generate_strings(5000, seed=1)
    absent = generate_strings(5000, seed=2)

    checker = CuckooFilter(expected_items=5000)
    for login in stored:
        checker.add(login)

    false_positives = sum(checker.check(login) for login in absent)
    assert false_positives / len(absent) < 0.02


def test_delete_removes_a_login():
    """A deleted login is no longer reported as present."""
    checker = CuckooFilter(expected_items=1000)
    checker.add("parinda")

    assert checker.check("parinda") is True
    assert checker.delete("parinda") is True
    assert checker.check("parinda") is False


def test_delete_leaves_other_logins_intact():
    """Removing one login does not disturb the others."""
    logins = generate_strings(500, seed=5)
    checker = CuckooFilter(expected_items=1000)
    for login in logins:
        checker.add(login)

    checker.delete(logins[0])
    for login in logins[1:]:
        assert checker.check(login) is True


def test_delete_of_absent_login_reports_failure():
    """Deleting something never stored returns False."""
    checker = CuckooFilter(expected_items=1000)
    assert checker.delete("never_added") is False


def test_insertion_fails_rather_than_looping():
    """A full table refuses insertions instead of running forever.

    Relocation is capped, so an over-filled filter returns False rather
    than cycling between occupied buckets indefinitely.
    """
    checker = CuckooFilter(expected_items=100, max_kicks=20)
    accepted = sum(checker.add(login) for login in generate_strings(5000, seed=7))

    assert accepted < 5000


def test_handles_unusual_strings():
    """Empty, long, non-ASCII, and symbol-bearing logins are handled."""
    checker = CuckooFilter(expected_items=1000)
    unusual = ["", "x" * 1_000, "user@domain.com", "日本語", "  spaces  "]
    for item in unusual:
        assert checker.add(item) is True
    for item in unusual:
        assert checker.check(item) is True
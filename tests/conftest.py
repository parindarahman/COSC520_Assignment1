"""Shared fixtures and test data for all data structure tests."""

import pytest

from src.utils.string_generation import generate_strings

# Sequences of logins paired with the expected result of check() at the
# moment each login is presented. False means the login is still
# available; True means it appeared earlier in the sequence.
DUPLICATE_CASES = [
    (["a", "a", "b", "b"], [False, True, False, True]),
    (["a", "b", "a", "c", "b", "c"], [False, False, True, False, True, True]),
    ([chr(ord("a") + i) for i in range(26)], [False] * 26),
]


@pytest.fixture
def stored_logins():
    """
    1000 unique login names to insert into a structure.

    Output: list of str — deterministic via fixed seed.
    """
    return generate_strings(1000, seed=42)


@pytest.fixture
def absent_logins():
    """
    1000 login names that do not appear in stored_logins.

    Output: list of str — for absence and false-positive testing.
    """
    return generate_strings(1000, seed=99)
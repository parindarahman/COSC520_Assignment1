"""Probabilistic membership checking using a Cuckoo filter."""

import math
import random

from src.utils.hashes import fnv1a_64


class CuckooFilter:
    """
    Space-efficient membership checking with one-sided error and
    support for deletion.

    Each login is reduced to a short fingerprint stored in one of two
    candidate buckets. The second bucket is derived from the first by
    XOR with a hash of the fingerprint, so an entry can be relocated
    knowing only its fingerprint and current position. That property is
    what makes deletion possible, unlike a Bloom filter.

    Insertion may fail when the table is close to full, since relocation
    is capped to avoid looping indefinitely.
    """

    def __init__(self, expected_items, bucket_size=4, fingerprint_bits=12,
                 max_kicks=500, load_factor=0.95):
        """
        Create an empty filter sized for the expected number of logins.

        Input:  expected_items (int) — logins the filter is sized for
                bucket_size (int) — fingerprints held per bucket
                fingerprint_bits (int) — bits per stored fingerprint
                max_kicks (int) — relocation attempts before giving up
                load_factor (float) — target occupancy, under 1.0
        Output: None

        Buckets of four are the usual choice: larger buckets raise
        achievable load but slow lookups, since every entry in both
        candidate buckets must be scanned.
        """
        if expected_items < 1:
            raise ValueError("expected_items must be at least 1")
        if not 0 < load_factor < 1:
            raise ValueError("load_factor must lie in (0, 1)")

        self.expected_items = expected_items
        self.bucket_size = bucket_size
        self.fingerprint_bits = fingerprint_bits
        self.max_kicks = max_kicks
        self.count = 0

        # Extra room beyond the expected count, since insertion failure
        # becomes likely as occupancy approaches capacity.
        required = math.ceil(expected_items / bucket_size / load_factor)
        self.table_size = 1 << (max(1, required) - 1).bit_length()

        self.fingerprint_mask = (1 << fingerprint_bits) - 1
        self.buckets = [[] for _ in range(self.table_size)]
        self.random = random.Random(0)

    def fingerprint(self, item):
        """
        Reduce a login to a short fingerprint.

        Input:  item (str) — the login name
        Output: int — a value in [1, 2^fingerprint_bits)

        Zero is excluded so that a stored fingerprint is never confused
        with an empty slot. Storing a fingerprint rather than the login
        itself is what makes the filter compact, and is also the source
        of its false positives: two logins sharing both a bucket and a
        fingerprint are indistinguishable.
        """
        value = fnv1a_64(item, seed=2) & self.fingerprint_mask
        return value if value != 0 else 1

    def alternate_index(self, index, fingerprint):
        """
        Find the other bucket a fingerprint may occupy.

        Input:  index (int) — one candidate bucket
                fingerprint (int) — the stored fingerprint
        Output: int — the other candidate bucket

        Uses i2 = i1 XOR hash(fingerprint). Because XOR is its own
        inverse, applying this to either index returns the other, so an
        entry can be relocated without knowing the original login
        (Fan et al., 2014).
        """
        return (index ^ fnv1a_64(str(fingerprint), seed=3)) % self.table_size

    def candidate_indices(self, item):
        """
        Compute the fingerprint and both candidate buckets for a login.

        Input:  item (str) — the login name
        Output: tuple — (fingerprint, first index, second index)
        """
        fingerprint = self.fingerprint(item)
        first = fnv1a_64(item, seed=4) % self.table_size
        second = self.alternate_index(first, fingerprint)
        return fingerprint, first, second

    def add(self, item):
        """
        Store a login name.

        Input:  item (str) — the login name to store
        Output: bool — True if stored, False if the table is too full

        Places the fingerprint in either candidate bucket if one has
        room. Otherwise evicts an existing entry and relocates it to its
        own alternate bucket, repeating until a free slot is found or
        the kick limit is reached. Amortised O(1) at moderate load,
        degrading as the table fills.
        """
        fingerprint, first, second = self.candidate_indices(item)

        for index in (first, second):
            if len(self.buckets[index]) < self.bucket_size:
                self.buckets[index].append(fingerprint)
                self.count += 1
                return True

        # Both candidates are full: evict and relocate.
        index = self.random.choice((first, second))
        for _ in range(self.max_kicks):
            slot = self.random.randrange(self.bucket_size)
            fingerprint, self.buckets[index][slot] = (
                self.buckets[index][slot],
                fingerprint,
            )
            index = self.alternate_index(index, fingerprint)

            if len(self.buckets[index]) < self.bucket_size:
                self.buckets[index].append(fingerprint)
                self.count += 1
                return True

        return False

    def build(self, items):
        """
        Load many login names at once.

        Input:  items (iterable of str) — login names to store
        Output: int — how many were stored successfully
        """
        return sum(self.add(item) for item in items)

    def check(self, item):
        """
        Check whether a login name may already be stored.

        Input:  item (str) — the login name to look for
        Output: bool — False if definitely absent, True if probably
                present

        Scans both candidate buckets. O(1), since bucket size is fixed.
        """
        fingerprint, first, second = self.candidate_indices(item)
        return (
            fingerprint in self.buckets[first]
            or fingerprint in self.buckets[second]
        )

    def delete(self, item):
        """
        Remove a login name from the filter.

        Input:  item (str) — the login name to remove
        Output: bool — True if a matching fingerprint was removed

        Removes one matching fingerprint from either candidate bucket.
        Safe only for logins known to have been added: removing a
        fingerprint reached by a false positive would delete the entry
        belonging to a different login.
        """
        fingerprint, first, second = self.candidate_indices(item)

        for index in (first, second):
            if fingerprint in self.buckets[index]:
                self.buckets[index].remove(fingerprint)
                self.count -= 1
                return True
        return False
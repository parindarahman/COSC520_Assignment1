""" checking whether something exists using a Bloom filter."""

import math

from src.utils.hashes import fnv1a_64


class BloomFilter:
    """
    Space-efficient membership checking with one-sided error.

    Each login sets k bits in an array of m bits. A login whose bits are
    all set is reported as present, which may be wrong; a login with any
    bit clear is definitely absent. So false positives occur at a
    controlled rate and false negatives never do.

    Deletion is not supported: clearing a bit could erase evidence of a
    different login that happens to share it.
    """

    def __init__(self, expected_items, false_positive_rate=0.01):
        """
        Create an empty filter sized for the expected number of logins.

        Input:  expected_items (int) — logins the filter is sized for
                false_positive_rate (float) — target error rate, in (0, 1)
        Output: None
        """
        if expected_items < 1:
            raise ValueError("expected_items must be at least 1")
        if not 0 < false_positive_rate < 1:
            raise ValueError("false_positive_rate must lie in (0, 1)")

        self.expected_items = expected_items
        self.false_positive_rate = false_positive_rate
        self.size = self.optimal_size(expected_items, false_positive_rate)
        self.hash_count = self.optimal_hash_count(self.size, expected_items)
        self.count = 0

        # One bit per slot, eight slots per byte.
        self.bits = bytearray((self.size + 7) // 8)

    @staticmethod
    def optimal_size(n, p):
        """
        Compute the number of bits needed for a target error rate.

        Input:  n (int) — expected number of stored logins
                p (float) — target false positive rate
        Output: int — number of bits, m

        Uses m = -n ln(p) / (ln 2)^2, which minimises space for a given
        p (Bloom, 1970; Broder and Mitzenmacher, 2004).
        """
        return max(1, int(-n * math.log(p) / (math.log(2) ** 2)))

    @staticmethod
    def optimal_hash_count(m, n):
        """
        Compute the number of hash functions that minimises error.

        Input:  m (int) — number of bits in the array
                n (int) — expected number of stored logins
        Output: int — number of hash functions, k

        Uses k = (m/n) ln 2. Too few hashes leave the array sparse and
        collisions likely; too many fill it, which also raises the error
        rate. The value is rounded rather than truncated, since
        truncation biases k downwards and worsens the observed rate.
        """
        return max(1, round((m / n) * math.log(2)))

    def bit_positions(self, item):
        """
        Compute the k bit positions a login maps to.

        Input:  item (str) — the login name
        Output: list of int — k indices into the bit array

        Two base hashes are combined as h1 + i * h2 to derive k
        positions, rather than computing k independent hashes. This
        gives the same asymptotic error rate at a fraction of the cost
        (Kirsch and Mitzenmacher, 2006).
        """
        first = fnv1a_64(item, seed=0)
        second = fnv1a_64(item, seed=1) | 1  # odd, so it never repeats
        return [
            (first + index * second) % self.size
            for index in range(self.hash_count)
        ]

    def set_bit(self, position):
        """
        Set one bit in the array.

        Input:  position (int) — bit index
        Output: None
        """
        self.bits[position // 8] |= 1 << (position % 8)

    def get_bit(self, position):
        """
        Read one bit from the array.

        Input:  position (int) — bit index
        Output: bool — True if the bit is set
        """
        return bool(self.bits[position // 8] & (1 << (position % 8)))

    def add(self, item):
        """
        Store a login name.

        Input:  item (str) — the login name to store
        Output: None

        Sets k bits, so O(k) regardless of how many logins are stored.
        """
        for position in self.bit_positions(item):
            self.set_bit(position)
        self.count += 1

    def build(self, items):
        """
        Load many login names at once.

        Input:  items (iterable of str) — login names to store
        Output: None
        """
        for item in items:
            self.add(item)

    def check(self, item):
        """
        Check whether a login name may already be stored.

        Input:  item (str) — the login name to look for
        Output: bool — False if definitely absent, True if probably
                present

        Returns as soon as a clear bit is found, so a miss is often
        cheaper than a hit. O(k) in the worst case.
        """
        for position in self.bit_positions(item):
            if not self.get_bit(position):
                return False
        return True

    def expected_false_positive_rate(self):
        """
        Predict the error rate for the number of logins actually stored.

        Input:  none
        Output: float — predicted false positive probability

        Uses p = (1 - e^(-kn/m))^k, which is the probability that all k
        bits of an absent login happen to be set by other logins.
        """
        if self.count == 0:
            return 0.0
        exponent = -self.hash_count * self.count / self.size
        return (1 - math.exp(exponent)) ** self.hash_count
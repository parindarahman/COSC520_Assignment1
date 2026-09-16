"""Membership checking using a hash table with separate chaining."""

from src.utils.hashes import fnv1a_64


class HashTable:
    """
    Membership checking by hashing each login to a bucket.

    Collisions are resolved by chaining: each bucket holds a list of the
    logins that hashed to it. The table doubles in size when the load
    factor is exceeded, which keeps chains short and gives amortised
    O(1) insertion and lookup.
    """

    def __init__(self, capacity=16, max_load=0.75):
        """
        Create an empty hash table.

        Input:  capacity (int) — initial number of buckets
                max_load (float) — items per bucket before doubling
        Output: None
        """
        self.capacity = capacity
        self.max_load = max_load
        self.count = 0
        self.buckets = [[] for _ in range(capacity)]

    def bucket_index(self, item):
        """
        Find the bucket a login belongs to.

        Input:  item (str) — the login name
        Output: int — index into self.buckets

        Reducing the 64-bit hash modulo the capacity spreads logins
        across buckets. O(L) for a login of L characters.
        """
        return fnv1a_64(item) % self.capacity

    def resize(self):
        """
        Double the number of buckets and redistribute every login.

        Input:  none
        Output: None

        Costs O(n), but happens only when the table doubles, so the cost
        spread over the insertions since the last resize is O(1) each.
        Logins must be reinserted rather than copied, because bucket
        indices depend on the capacity.
        """
        old_buckets = self.buckets
        self.capacity *= 2
        self.buckets = [[] for _ in range(self.capacity)]

        for bucket in old_buckets:
            for item in bucket:
                self.buckets[self.bucket_index(item)].append(item)

    def add(self, item):
        """
        Store a login name.

        Input:  item (str) — the login name to store
        Output: None

        Already-stored logins are ignored, so duplicates never lengthen
        a chain. Amortised O(1).
        """
        if self.check(item):
            return

        self.buckets[self.bucket_index(item)].append(item)
        self.count += 1

        if self.count / self.capacity > self.max_load:
            self.resize()

    def build(self, items):
        """
        Load many login names at once.

        Input:  items (iterable of str) — login names to store
        Output: None

        O(n) amortised in total.
        """
        for item in items:
            self.add(item)

    def check(self, item):
        """
        Check whether a login name is already stored.

        Input:  item (str) — the login name to look for
        Output: bool — True if present, else False

        Scans only the one bucket the login hashes to. With the load
        factor bounded, chains stay short and this is O(1) on average;
        the worst case is O(n) if every login collided.
        """
        for stored in self.buckets[self.bucket_index(item)]:
            if stored == item:
                return True
        return False
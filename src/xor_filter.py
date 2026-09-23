"""Static probabilistic membership checking using an XOR filter."""

from src.utils.hashes import fnv1a_64

MASK_64 = 0xFFFFFFFFFFFFFFFF


class XorFilter:
    """
    Space-efficient membership checking for a fixed set of logins.

    Each login maps to three slots in an array of fingerprints, and the
    array is constructed so that the XOR of a login's three slots equals
    its own fingerprint. A lookup therefore reads three slots, XORs
    them, and compares against the login's fingerprint.

    The array holds about 1.23 slots per login, against roughly 1.44
    bits per unit of error for a Bloom filter, so it is smaller at the
    same accuracy while performing exactly three memory accesses per
    lookup regardless of the target error rate (Graf and Lemire, 2020).

    The structure is static: the whole array is solved at construction
    and neither insertion nor deletion is supported afterwards.
    """

    def __init__(self, items, fingerprint_bits=8, max_attempts=100):
        """
        Build a filter holding exactly the given logins.

        Input:  items (iterable of str) — every login to store
                fingerprint_bits (int) — bits per stored fingerprint
                max_attempts (int) — construction retries before failing
        Output: None

        Construction may fail for a particular seed, so it is retried
        with a new seed until it succeeds.
        """
        logins = list(dict.fromkeys(items))
        if not logins:
            raise ValueError("an XOR filter must be built over at least one login")

        self.fingerprint_bits = fingerprint_bits
        self.fingerprint_mask = (1 << fingerprint_bits) - 1
        self.count = len(logins)

        # 1.23n slots is the threshold above which peeling succeeds with
        # high probability; the array is split into three equal blocks,
        # one per hash, so the size is rounded up to a multiple of three.
                # 1.23n slots is the asymptotic threshold above which peeling
        # succeeds with high probability; the array is split into three
        # equal blocks, one per hash. At small n that ratio leaves too
        # thin a margin for peeling to start, so a floor is applied.
        self.block_size = max(8, int(1.23 * self.count / 3) + 1)
        self.size = self.block_size * 3

        for seed in range(max_attempts):
            if self.construct(logins, seed):
                self.seed = seed
                return

        raise RuntimeError(
            f"construction failed after {max_attempts} attempts; "
            "increase the array size"
        )

    def fingerprint(self, item):
        """
        Reduce a login to a short fingerprint.

        Input:  item (str) — the login name
        Output: int — a value in [0, 2^fingerprint_bits)
        """
        return fnv1a_64(item, seed=self.seed_base) & self.fingerprint_mask

    def slots(self, item):
        """
        Compute the three array slots a login maps to.

        Input:  item (str) — the login name
        Output: tuple of int — three indices into the array

        Each hash indexes a separate block, which guarantees the three
        slots are distinct and simplifies the peeling construction.
        """
        base = fnv1a_64(item, seed=self.seed_base)
        h0 = base % self.block_size
        h1 = ((base >> 21) % self.block_size) + self.block_size
        h2 = ((base >> 42) % self.block_size) + 2 * self.block_size
        return h0, h1, h2

    def construct(self, logins, seed):
        """
        Attempt to solve the array for one seed.

        Input:  logins (list of str) — the logins to store
                seed (int) — hash seed for this attempt
        Output: bool — True if construction succeeded

        Proceeds in two phases. Peeling repeatedly finds a slot touched
        by exactly one remaining login, records the pair, and removes
        that login, which may leave further slots singly occupied.
        Assignment then walks the recorded pairs in reverse, giving each
        slot the value that makes its login's three slots XOR to its
        fingerprint. Working backwards guarantees that the other two
        slots are already fixed at the point each value is chosen.
        """
        self.seed_base = seed

        # Track, for each slot, how many logins touch it and the XOR of
        # their indices. When the count falls to one, that XOR is the
        # index of the single remaining login.
        counts = [0] * self.size
        xor_sums = [0] * self.size

        for index, login in enumerate(logins):
            for slot in self.slots(login):
                counts[slot] += 1
                xor_sums[slot] ^= index

        queue = [slot for slot in range(self.size) if counts[slot] == 1]
        stack = []

        while queue:
            slot = queue.pop()
            if counts[slot] != 1:
                continue

            index = xor_sums[slot]
            stack.append((slot, index))

            for other in self.slots(logins[index]):
                counts[other] -= 1
                xor_sums[other] ^= index
                if counts[other] == 1:
                    queue.append(other)

        if len(stack) != len(logins):
            return False

        self.fingerprints = [0] * self.size
        for slot, index in reversed(stack):
            login = logins[index]
            value = self.fingerprint(login)
            for other in self.slots(login):
                if other != slot:
                    value ^= self.fingerprints[other]
            self.fingerprints[slot] = value

        return True

    def check(self, item):
        """
        Check whether a login may be stored in the filter.

        Input:  item (str) — the login name to look for
        Output: bool — False if definitely absent, True if probably
                present

        Three array reads and two XOR operations, so O(1) with a fixed
        constant independent of the error rate.
        """
        h0, h1, h2 = self.slots(item)
        combined = (
            self.fingerprints[h0]
            ^ self.fingerprints[h1]
            ^ self.fingerprints[h2]
        )
        return combined == self.fingerprint(item)
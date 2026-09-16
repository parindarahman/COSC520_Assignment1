"""Non-cryptographic hash functions for the hash table and filters."""

# 64-bit FNV-1a parameters, as published in the FNV specification.
# The offset basis seeds the accumulator; the prime is chosen so that
# repeated multiplication disperses changes across all output bits.
FNV_OFFSET_BASIS = 14695981039346656037
FNV_PRIME = 1099511628211
MASK_64 = 0xFFFFFFFFFFFFFFFF


def fnv1a_64(text, seed=0):
    """
    Compute the 64-bit FNV-1a hash of a string.

    Input:  text (str) — the string to hash
            seed (int) — value mixed into the initial state, so that
                         several independent hashes of the same string
                         can be produced
    Output: int — a hash value in the range [0, 2^64)

    For each byte of the UTF-8 encoding, the accumulator is XORed with
    the byte and then multiplied by the FNV prime. The XOR mixes the
    byte in; the multiplication propagates that change through the
    higher bits, so a one-bit change in the input alters roughly half
    the output bits. Cost is O(L) for a string of L bytes.

    Python integers do not overflow, so the accumulator is masked to 64
    bits after each multiplication to reproduce the wraparound the
    algorithm assumes.
    """
    accumulator = (FNV_OFFSET_BASIS ^ seed) & MASK_64

    for byte in text.encode("utf-8"):
        accumulator ^= byte
        accumulator = (accumulator * FNV_PRIME) & MASK_64

    return accumulator
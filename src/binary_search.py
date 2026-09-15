"""Membership checking over a sorted array using binary search."""


class BinarySearch:
    """
    Membership checking on a list kept in sorted order.

    Insertion places each item at its correct position, so the list is
    sorted at all times. Lookup is O(log n) comparisons; insertion is
    O(n) because elements after the insertion point must shift.
    """

    def __init__(self):
        """Create an empty sorted collection of login names."""
        self.sorted_items = []

    def find_index(self, item):
        """
        Locate the position where an item belongs in sorted order.

        Input:  item (str) — the login name to locate
        Output: int — index of the item if present, otherwise the index
                at which it would be inserted to preserve order

        Narrows a left/right window by halving it each step, giving
        O(log n) comparisons. Used by both add() and check().
        """
        left = 0
        right = len(self.sorted_items)
        while left < right:
            # Safe in Python (unbounded ints); in a fixed-width language
            # this would be written left + (right - left) // 2 to avoid
            # overflow on large arrays.
            mid = (left + right) // 2
            mid_value = self.sorted_items[mid]
            if item == mid_value:
                return mid
            if item < mid_value:
                right = mid
            else:
                left = mid + 1
        return left

    def add(self, item):
        """
        Store a login name, keeping the collection sorted.

        Input:  item (str) — the login name to store
        Output: None

        O(log n) to locate the position, O(n) to shift the remaining
        elements, so O(n) overall.
        """
        self.sorted_items.insert(self.find_index(item), item)

    def build(self, items):
        """
        Load many login names at once by appending then sorting.

        Input:  items (iterable of str) — login names to store
        Output: None

        Costs O(n log n) in total, against O(n^2) for repeated add()
        calls. Provided so both construction strategies can be measured.
        """
        self.sorted_items.extend(items)
        self.sorted_items.sort()

    def check(self, item):
        """
        Check whether a login name is already stored.

        Input:  item (str) — the login name to look for
        Output: bool — True if present, else False

        Finds the item's would-be position and tests what is actually
        there. O(log n) comparisons.
        """
        index = self.find_index(item)
        return (
            index < len(self.sorted_items)
            and self.sorted_items[index] == item
        )
"""Sequential search for login names that are stored in a collection."""


class LinearSearch:
    """
    Scanning a list from start to end to see if it exists.

    Lookup should be — O(n).
    """

    def __init__(self):
        """Create an empty collection of login names."""
        self.items = []

    def add(self, item):
        """
        Storing a login name.

        Input:  item (str) add the login name to store
        and Output: Nothing

        Appends to the end of the list in O(1).
        """
        self.items.append(item)

    def check(self, item):
        """
        Check whether a login name is already stored.

        Input:  item (str) — the login name to look for
        Output: bool — True if present, else False

        Scans sequentially, stopping at the first match.
        Worst case O(n) when the item is absent.
        """
        for stored in self.items:
            if stored == item:
                return True
        return False
    def build(self, items):
        """
        Load many login names at once.

        Input:  items (iterable of str) — login names to store
        Output: None

        O(n) in total, since each name is appended without searching.
        """
        self.items.extend(items)
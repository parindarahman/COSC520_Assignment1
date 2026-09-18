"""Measure how insertion and lookup costs grow with the number of logins."""

import csv
import time
from pathlib import Path

from src.binary_search import BinarySearch
from src.bloom_filter import BloomFilter
from src.hash_table import HashTable
from src.linear_search import LinearSearch
from src.utils.plot_generation import make_all_plots
from src.utils.string_generation import generate_strings
from src.cuckoo_filter import CuckooFilter

# Structure sizes to measure.
SIZES = [10, 100, 1_000, 10_000, 100_000, 1_000_000]

# How many operations to time at each size.
SAMPLE = 2000

# Target error rate for the Bloom filter.
FALSE_POSITIVE_RATE = 0.01

RESULTS_DIR = Path("results")


def measure_add(structure, new_logins):
    """
    Time inserting new logins into an already populated structure.

    Input:  structure — an instance with an add() method
            new_logins (list of str) — names not yet stored
    Output: float — average seconds per insertion
    """
    start = time.perf_counter()
    for login in new_logins:
        structure.add(login)
    elapsed = time.perf_counter() - start
    return elapsed / len(new_logins)


def measure_check(structure, queries):
    """
    Time membership checks against a populated structure.

    Input:  structure — an instance with a check() method
            queries (list of str) — names to look up
    Output: float — average seconds per lookup
    """
    start = time.perf_counter()
    for login in queries:
        structure.check(login)
    elapsed = time.perf_counter() - start
    return elapsed / len(queries)


def run_one_size(make_structure, n):
    """
    Measure add and check costs for one structure at one size.

    Input:  make_structure (callable) — takes n, returns a new instance
            n (int) — number of logins already stored
    Output: tuple of float — (seconds per add, seconds per check)

    A factory is used rather than a class, because the Bloom filter must
    be sized for the number of logins it will hold.

    Lookups are timed before insertions, since inserting would change
    the size the measurement is meant to describe.
    """
    stored = generate_strings(n, seed=n)
    extra = generate_strings(SAMPLE, seed=n + 1)

    structure = make_structure(n)
    structure.build(stored)

    # Half the queries are present and half are absent. Misses are the
    # worst case for linear search, so they must be included.
    half = SAMPLE // 2
    queries = stored[:half] + extra[:half]

    check_time = measure_check(structure, queries)
    add_time = measure_add(structure, extra)
    return add_time, check_time


def save_csv(path, time_column, rows):
    """
    Write timing rows to a CSV file.

    Input:  path (Path) — output file
            time_column (str) — header for the timing column
            rows (list of list) — [structure, n, seconds] per row
    Output: None
    """
    with open(path, "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["structure", "n", time_column])
        writer.writerows(rows)
    print(f"Saved {path}")


def run_benchmark():
    """
    Measure every structure at every size and save two CSV files.

    Input:  none
    Output: None — writes insert_timings.csv and lookup_timings.csv
    """
    structures = [
    (lambda n: LinearSearch(), "Linear Search"),
    (lambda n: BinarySearch(), "Binary Search"),
    (lambda n: HashTable(), "Hash Table"),
    (lambda n: BloomFilter(n, FALSE_POSITIVE_RATE), "Bloom Filter"),
    (lambda n: CuckooFilter(n), "Cuckoo Filter"),
]

    RESULTS_DIR.mkdir(exist_ok=True)
    insert_rows = []
    lookup_rows = []

    for make_structure, name in structures:
        for n in SIZES:
            add_time, check_time = run_one_size(make_structure, n)
            insert_rows.append([name, n, add_time])
            lookup_rows.append([name, n, check_time])
            print(f"{name:16} n={n:<9} "
                  f"add={add_time * 1e6:8.2f}us "
                  f"check={check_time * 1e6:8.2f}us")

    save_csv(RESULTS_DIR / "insert_timings.csv", "seconds_per_insert", insert_rows)
    save_csv(RESULTS_DIR / "lookup_timings.csv", "seconds_per_lookup", lookup_rows)


if __name__ == "__main__":
    run_benchmark()
    make_all_plots()
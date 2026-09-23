"""Benchmark the XOR filter against the Bloom and Cuckoo filters.

The XOR filter has no incremental insertion: its array is solved as a
single linear system, so adding one login would require rebuilding the
whole structure. Construction cost is therefore reported as a total
rather than per insertion, and is measured the same way for all three
filters so that the comparison is fair.
"""

import csv
import time
from pathlib import Path

import matplotlib.pyplot as plt

from src.bloom_filter import BloomFilter
from src.cuckoo_filter import CuckooFilter
from src.utils.string_generation import generate_strings
from src.xor_filter import XorFilter

SIZES = [1_000, 10_000, 100_000]
SAMPLE = 2000
RESULTS_DIR = Path("results")
CSV_PATH = RESULTS_DIR / "filter_comparison.csv"


def build_bloom(logins):
    """
    Construct a Bloom filter over the given logins.

    Input:  logins (list of str) — names to store
    Output: an instance holding every login
    """
    structure = BloomFilter(len(logins), 0.01)
    structure.build(logins)
    return structure


def build_cuckoo(logins):
    """
    Construct a Cuckoo filter over the given logins.

    Input:  logins (list of str) — names to store
    Output: an instance holding every login
    """
    structure = CuckooFilter(len(logins))
    structure.build(logins)
    return structure


def build_xor(logins):
    """
    Construct an XOR filter over the given logins.

    Input:  logins (list of str) — names to store
    Output: an instance holding every login
    """
    return XorFilter(logins, fingerprint_bits=8)


def measure(build_function, n):
    """
    Measure construction time, lookup time, and error rate at one size.

    Input:  build_function (callable) — takes logins, returns a filter
            n (int) — number of logins to store
    Output: tuple — (build seconds, mean lookup seconds, error rate)
    """
    stored = generate_strings(n, seed=n)
    absent = generate_strings(SAMPLE, seed=n + 1)

    start = time.perf_counter()
    structure = build_function(stored)
    build_seconds = time.perf_counter() - start

    half = SAMPLE // 2
    queries = stored[:half] + absent[:half]

    start = time.perf_counter()
    for login in queries:
        structure.check(login)
    lookup_seconds = (time.perf_counter() - start) / len(queries)

    errors = sum(structure.check(login) for login in absent)
    return build_seconds, lookup_seconds, errors / len(absent)


def run_benchmark():
    """
    Benchmark all three filters and save the results to CSV.

    Input:  none
    Output: None — writes results/filter_comparison.csv
    """
    filters = [
        (build_bloom, "Bloom Filter"),
        (build_cuckoo, "Cuckoo Filter"),
        (build_xor, "XOR Filter"),
    ]

    RESULTS_DIR.mkdir(exist_ok=True)
    rows = []

    for build_function, name in filters:
        for n in SIZES:
            build_s, lookup_s, error = measure(build_function, n)
            rows.append([name, n, build_s, lookup_s, error])
            print(f"{name:16} n={n:<8} build={build_s:7.3f}s "
                  f"lookup={lookup_s * 1e6:7.2f}us fpr={error:.4f}")

    with open(CSV_PATH, "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["filter", "n", "build_seconds",
                         "lookup_seconds", "false_positive_rate"])
        writer.writerows(rows)
    print(f"\nSaved {CSV_PATH}")


def draw_plot(column, ylabel, title, filename):
    """
    Draw one log-log figure comparing the three filters.

    Input:  column (str) — the CSV column to plot
            ylabel, title, filename (str) — labels and output name
    Output: None — writes a PNG to results/
    """
    grouped = {}
    with open(CSV_PATH, newline="") as handle:
        for row in csv.DictReader(handle):
            name = row["filter"]
            if name not in grouped:
                grouped[name] = {"n": [], "value": []}
            grouped[name]["n"].append(int(row["n"]))
            grouped[name]["value"].append(float(row[column]))

    plt.figure(figsize=(9, 6))
    for name, data in grouped.items():
        plt.plot(data["n"], data["value"], marker="o", label=name)

    plt.xscale("log")
    plt.yscale("log")
    plt.xlabel("Number of stored logins (log scale)")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend()
    plt.grid(True, which="both", linestyle="--", linewidth=0.5)
    plt.tight_layout()
    plt.savefig(RESULTS_DIR / filename, dpi=150)
    plt.close()
    print(f"Saved {RESULTS_DIR / filename}")


if __name__ == "__main__":
    run_benchmark()
    draw_plot("build_seconds", "Total construction time (seconds)",
              "Filter construction cost", "filter_build_plot.png")
    draw_plot("lookup_seconds", "Mean seconds per lookup",
              "Filter lookup cost", "filter_lookup_plot.png")
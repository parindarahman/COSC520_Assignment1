"""Figure generation for benchmark results."""

import csv
from pathlib import Path

import matplotlib.pyplot as plt

RESULTS_DIR = Path("results")

def load_timings(path, time_column):
    """
    Read a timing CSV and group the rows by structure.

    Input:  path (Path) — CSV written by benchmark.py
            time_column (str) — name of the timing column to read
    Output: dict — structure name -> {'n': [...], 'time': [...]}
    """
    grouped = {}
    with open(path, newline="") as handle:
        for row in csv.DictReader(handle):
            name = row["structure"]
            if name not in grouped:
                grouped[name] = {"n": [], "time": []}
            grouped[name]["n"].append(int(row["n"]))
            grouped[name]["time"].append(float(row[time_column]))
    return grouped

def draw_comparison(grouped, ylabel, title, filename):
    """
    Draw one log-log figure comparing every structure on one metric.

    Input:  grouped (dict) — output of load_timings
            ylabel (str) — label for the vertical axis
            title (str) — figure title
            filename (str) — output PNG name, written to results/
    Output: None — saves a figure to disk

    Log-log axes are used because a cost of the form t = c * n^k appears
    as a straight line of slope k, so the measured growth rate can be
    read against the theoretical complexity.
    """
    plt.figure(figsize=(9, 6))

    for name, data in grouped.items():
        plt.plot(data["n"], data["time"], marker="o", label=name)

    plt.xscale("log")
    plt.yscale("log")
    plt.xlabel("Number of stored logins (log scale)")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend()
    plt.grid(True, which="both", linestyle="--", linewidth=0.5)
    plt.tight_layout()

    output = RESULTS_DIR / filename
    plt.savefig(output, dpi=150)
    plt.close()
    print(f"Saved {output}")

def make_all_plots():
    """
    Generate the insertion and lookup figures from the saved CSVs.

    Input:  none
    Output: None — writes two PNG files to results/
    """
    draw_comparison(
        load_timings(RESULTS_DIR / "insert_timings.csv", "seconds_per_insert"),
        ylabel="Seconds per insertion",
        title="Insertion cost vs number of logins",
        filename="insert_plot.png",
    )
    draw_comparison(
        load_timings(RESULTS_DIR / "lookup_timings.csv", "seconds_per_lookup"),
        ylabel="Seconds per lookup",
        title="Lookup cost vs number of logins",
        filename="lookup_plot.png",
    )

if __name__ == "__main__":
    make_all_plots()


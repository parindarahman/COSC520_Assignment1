# COSC 520 Assignment 1 — The Login Checker Problem

Comparing data structures for checking whether a login name has already
been taken: linear search, binary search, a hash table, a Bloom filter,
and a Cuckoo filter, plus an XOR filter implemented for the bonus.

All structures are implemented from scratch, along with the FNV-1a hash
function they depend on. No external library implementing any of these
algorithms is used.

## Requirements

- Python 3.10 or later
- matplotlib
- pytest

## Setup

Clone the repository and move into it:

```bash
git clone https://github.com/parindarahman/COSC520_Assignment1.git
cd COSC520_Assignment1
```

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Then activate it. The command differs by shell:

```bash
.venv\Scripts\activate            # Windows (PowerShell or CMD)
source .venv/Scripts/activate     # Windows (Git Bash)
source .venv/bin/activate         # macOS or Linux
```

Git Bash treats backslashes as escape characters, so the PowerShell form
fails there with `command not found`. Use the forward-slash form instead.

On Windows, if PowerShell refuses to run the activation script, allow
local scripts once and try again:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Do not place the project inside a OneDrive-synced folder. Creating a
virtual environment writes several hundred small files in quick
succession, and OneDrive may lock one of them mid-write, causing
`python -m venv` to fail partway through with a traceback ending in
`_setup_pip`. If this happens, delete the partial environment and
recreate it outside OneDrive:

```powershell
Remove-Item -Recurse -Force .venv
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

## Running the tests

```bash
python -m pytest tests/ -v
```

Covers every structure. For a single one:

```bash
python -m pytest tests/test_bloom_filter.py -v
```

## Running the main benchmark

Measures insertion and lookup cost for the five required structures at
n = 10 through n = 10^6:

```bash
python -m benchmarks.benchmark
```

Writes to `results/`:

- `insert_timings.csv`, `lookup_timings.csv`
- `insert_plot.png`, `lookup_plot.png`

Takes several minutes. To redraw the figures from existing data without
re-measuring:

```bash
python -m src.utils.plot_generation
```

## Running the bonus benchmark

Compares the XOR filter against the Bloom and Cuckoo filters on
construction time, lookup time, and false positive rate:

```bash
python -m benchmarks.bonus_benchmark
```

Writes to `results/`:

- `filter_comparison.csv`
- `filter_build_plot.png`, `filter_lookup_plot.png`

`results/filter_accuracy_plot.png` was produced by an earlier revision of
this script and is retained because the false positive comparison it
shows is referenced in the report. The rates behind it are recorded in
`filter_comparison.csv`.

## Notes on running

Run every command from the project root. The `python -m` prefix matters:
it places the project root on the import path so that `from src...`
resolves. Running `pytest` directly instead of `python -m pytest` will
fail with `ModuleNotFoundError: No module named 'src'`.

The virtual environment must be active in each new terminal session.
Your prompt shows `(.venv)` when it is. In Git Bash, confirm the right
interpreter is being used with `which python`, which should return a path
inside `.venv`.

To measure a different range of sizes, edit the `SIZES` list at the top
of `benchmarks/benchmark.py`. Start with a short list such as
`[10, 100, 1_000]` to confirm the pipeline runs before committing to a
full measurement.

## Repository structure

```
src/
  linear_search.py       sequential scan
  binary_search.py       sorted array with binary search
  hash_table.py          separate chaining with resizing
  bloom_filter.py        bit array with k hash functions
  cuckoo_filter.py       fingerprint buckets with eviction
  xor_filter.py          static filter built by peeling (bonus)
  utils/
    hashes.py            64-bit FNV-1a
    string_generation.py synthetic login generation
    plot_generation.py   figure generation
tests/
  conftest.py            shared fixtures and test cases
  test_linear_search.py
  test_binary_search.py
  test_hashes.py
  test_bloom_filter.py
  test_cuckoo_filter.py
  test_xor_filter.py
benchmarks/
  benchmark.py           main timing harness
  bonus_benchmark.py     filter comparison for the bonus
results/                 timing data and figures
```

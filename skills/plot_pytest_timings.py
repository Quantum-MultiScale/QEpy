#!/usr/bin/env python3
"""Plot serial vs parallel QEpy pytest timings from Amarel TSV output.

Usage:
  python plot_pytest_timings.py pytest-timing-pertest.tsv -o timings.png

TSV columns: mode, test_id, pytest_sec, wall_sec, rc, notes
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def load_tsv(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with path.open(newline="") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            if row.get("test_id") or row.get("workload"):
                rows.append(row)
    return rows


def parse_float(value: str | None) -> float | None:
    if not value or value.strip().upper() in {"NA", "N/A", ""}:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tsv", type=Path, help="per-test timing TSV from pytest_pertest_timing.sh")
    parser.add_argument("-o", "--output", type=Path, default=Path("pytest_timings.png"))
    parser.add_argument("--title", default="QEpy pytest: serial vs parallel (Amarel HPC)")
    args = parser.parse_args()

    if not args.tsv.is_file():
        print(f"TSV not found: {args.tsv}", file=sys.stderr)
        return 1

    rows = load_tsv(args.tsv)
    strict = rows and "exec_sec_median" in rows[0]
    test_key = "test_id" if rows and "test_id" in rows[0] else "workload"

    if strict:
        rows = [r for r in rows if r.get("scope") == "per-test"]

    tests: list[str] = []
    skip_ids = {"both", "n=1", "n=2", "all_4_tests"}
    for row in rows:
        tid = row.get(test_key, "")
        mode_col = row.get("mode", "")
        if tid in skip_ids or mode_col == "pw.x":
            continue
        if tid and tid not in tests:
            tests.append(tid)

    serial_py: list[float] = []
    parallel_py: list[float | None] = []
    serial_wall: list[float] = []
    parallel_wall: list[float | None] = []

    for tid in tests:
        s_row = next((r for r in rows if r.get("mode") == "serial" and r.get(test_key) == tid), None)
        p_row = next((r for r in rows if r.get("mode") == "parallel" and r.get(test_key) == tid), None)
        if strict:
            serial_py.append(parse_float(s_row.get("pytest_sec_median") if s_row else None) or 0.0)
            parallel_py.append(parse_float(p_row.get("pytest_sec_median") if p_row else None))
            serial_wall.append(parse_float(s_row.get("exec_sec_median") if s_row else None) or 0.0)
            parallel_wall.append(parse_float(p_row.get("exec_sec_median") if p_row else None))
        else:
            serial_py.append(parse_float(s_row.get("pytest_sec") if s_row else None) or 0.0)
            parallel_py.append(parse_float(p_row.get("pytest_sec") if p_row else None))
            serial_wall.append(parse_float(s_row.get("wall_sec") if s_row else None) or 0.0)
            parallel_wall.append(parse_float(p_row.get("wall_sec") if p_row else None))

    x = np.arange(len(tests))
    width = 0.35

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle(args.title, fontsize=12)

    exec_label = "/usr/bin/time exec (s, median)" if strict else "wall clock (s)"
    pytest_label = "pytest reported (s, median)" if strict else "pytest reported time (s)"

    for ax, serial_vals, par_vals, ylabel in (
        (axes[0], serial_py, parallel_py, pytest_label),
        (axes[1], serial_wall, parallel_wall, exec_label),
    ):
        serial_lbl = "serial (srun -n 1)" + (" [median×3]" if strict else "")
        par_lbl = "parallel (srun --mpi=pmi2 -n 2)" + (" [median×3]" if strict else "")
        ax.bar(x - width / 2, serial_vals, width, label=serial_lbl, color="#2e7d32")
        par_plot = [v if v is not None else 0.0 for v in par_vals]
        bars = ax.bar(x + width / 2, par_plot, width, label=par_lbl, color="#c62828")
        for i, (bar, raw) in enumerate(zip(bars, par_vals)):
            if raw is None:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    0.05,
                    "FAIL",
                    ha="center",
                    va="bottom",
                    fontsize=8,
                    color="#b71c1c",
                    rotation=90,
                )
            elif raw >= 60:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.1,
                    f"{raw:.0f}s",
                    ha="center",
                    va="bottom",
                    fontsize=7,
                )
        ax.set_ylabel(ylabel)
        ax.set_xticks(x)
        ax.set_xticklabels(tests, rotation=25, ha="right")
        ax.legend(loc="upper right", fontsize=8)
        ax.grid(axis="y", alpha=0.3)
        all_pos = serial_vals + [v for v in par_vals if v is not None]
        ymax = (max(all_pos) if all_pos else 1.0) * 1.25
        ax.set_ylim(0, ymax)

    fig.tight_layout()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=150, bbox_inches="tight")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

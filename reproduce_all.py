# -*- coding: utf-8 -*-
"""Rebuild every figure and every table from the tables committed here.

Run from anywhere:  python reproduce_all.py

This is the check the repository exists for.  It runs the scripts that need
nothing but the files in `outputs/`, then compares the three table CSVs it
regenerates against the checksums recorded at release, so a silent change in
any derived number shows up as a failure rather than as a slightly different
figure.  Figure PDFs are not checksummed: they carry a timestamp and a font
subset, so their bytes move even when the picture does not.

The scripts that read the operational archive are listed at the end.  They are
shipped so that they can be read, not run: the archive stays with the operator.
"""
from __future__ import annotations

import hashlib
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.join(ROOT, "code")

# order matters only in that make_tables.py rewrites the CSVs the figures read
FIGURE_SCRIPTS = [
    "fig1.py", "fig2.py", "fig3.py", "fig4.py", "fig5.py",
    "fig6.py", "fig7_fig9.py", "fig8.py",
]
TABLE_SCRIPTS = ["make_tables.py"]
# recomputes Omega and Delta_obs from the shipped registry table and rewrites
# outputs/p3a_obs_index*.csv, so the central quantity of the paper is not taken
# on trust even though the underlying archive is not public
RECOMPUTE = ["p3a_obs_index.py"]

NEEDS_ARCHIVE = [
    "prep_figdata.py", "p3a_lock_reclass_rain.py", "p3a_recompute_r6.py",
    "p3a_onset_lag_baserate.py", "audit_J_registry.py",
]

CHECKED = [
    "outputs/tables/table1_instruments.csv",
    "outputs/tables/table2_configurations.csv",
    "outputs/tables/table3_treatments.csv",
    "outputs/tables/table2_roworder.csv",
    "outputs/p3a_obs_index.csv",
    "outputs/p3a_obs_index_bydev.csv",
]


def recorded(path):
    """The sha256 this file had at release, from SHA256SUMS."""
    want = os.path.relpath(path, ROOT).replace(os.sep, "/")
    for line in open(os.path.join(ROOT, "SHA256SUMS"), encoding="utf-8"):
        h, name = line.split(None, 1)
        if name.strip().lstrip("*") == want:
            return h
    return None


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def run(script):
    p = subprocess.run([sys.executable, os.path.join(CODE, script)],
                       cwd=ROOT, capture_output=True, text=True)
    ok = p.returncode == 0
    last = (p.stdout.strip().splitlines() or [""])[-1]
    print("  %-18s %s   %s" % (script, "ok  " if ok else "FAIL", last[:70]))
    if not ok:
        print(p.stderr.strip()[-1500:])
    return ok


def main():
    print("figures")
    ok = all([run(s) for s in FIGURE_SCRIPTS])

    print("tables")
    ok = all([run(s) for s in TABLE_SCRIPTS]) and ok

    print("recomputed quantities")
    ok = all([run(s) for s in RECOMPUTE]) and ok

    print("checksums")
    bad = 0
    for rel in CHECKED:
        p = os.path.join(ROOT, rel)
        want = recorded(p)
        got = sha256(p)
        if want is None:
            print("  %-46s no recorded hash" % rel)
            bad += 1
        elif want != got:
            print("  %-46s CHANGED" % rel)
            bad += 1
        else:
            print("  %-46s identical" % rel)

    print("\nnot run (need the operational archive, which is not public)")
    for s in NEEDS_ARCHIVE:
        print("  " + s)

    if ok and not bad:
        print("\nPASS  every figure redrawn, every table and quantity byte-identical")
        return 0
    print("\nFAIL  see above")
    return 1


if __name__ == "__main__":
    sys.exit(main())

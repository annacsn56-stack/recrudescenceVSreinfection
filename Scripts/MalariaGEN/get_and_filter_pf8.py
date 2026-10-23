#!/usr/bin/env python3
"""
filter_pf8_samples.py

Select MalariaGEN Pf8 samples from the Pf8_samples.txt metadata file according
to criteria (country, region/admin level 1, year range, QC status, population,
study). Outputs the filtered table, the list of Sample IDs, and the list of ENA
accessions (for a download script).

--------------------------------------------------------------------------
Metadata source:
  The Pf8 sample metadata is a single static TSV, downloaded automatically by
  this script (stdlib only, no account required):
      https://pf8-release.cog.sanger.ac.uk/metadata/Pf8_samples.txt
  If the file is already present it is reused; use --refresh to re-download.
This script only reads the metadata and does NOT download any genome data, so
that accessions can be cited rather than redistributing MalariaGEN data.
--------------------------------------------------------------------------

Examples:
  # list available columns (downloads the metadata on first run)
  python3 filter_pf8_samples.py --show-columns

  # Pursat (Cambodia), 2017 to 2020, QC-pass only
  python3 filter_pf8_samples.py \
      --country Cambodia --admin1 Pursat --year-min 2017 --year-max 2020 \
      --qc-pass --out-prefix pf8_pursat

  # Peru + PNG + Kenya + Mali, QC-pass, any year
  python3 filter_pf8_samples.py \
      --country Peru "Papua New Guinea" Kenya Mali --qc-pass \
      --out-prefix pf8_4countries
"""
import argparse
import os
import sys
import urllib.request
import pandas as pd

# official Pf8 sample metadata (static TSV, no account needed)
PF8_URL = "https://pf8-release.cog.sanger.ac.uk/metadata/Pf8_samples.txt"


def ensure_metadata(path, url=PF8_URL, refresh=False):
    """Download the Pf8 metadata to `path` if missing (or if refresh)."""
    if os.path.exists(path) and not refresh:
        return path
    print(f"Downloading Pf8 metadata:\n  {url}\n  -> {path}")
    urllib.request.urlretrieve(url, path)
    size = os.path.getsize(path)
    print(f"  done ({size/1e6:.1f} MB)")
    return path


# logical field -> candidate column names (naming varies between Pf7/Pf8)
COLS = {
    "sample":     ["Sample", "sample"],
    "country":    ["Country", "country"],
    "admin1":     ["Admin level 1", "Admin1", "admin_level_1", "Admin level1"],
    "year":       ["Year", "year", "Collection year"],
    "qc":         ["QC pass", "QC_pass", "qc_pass", "QCpass"],
    "population": ["Population", "population", "Pop"],
    "study":      ["Study", "study"],
    "ena":        ["ENA", "ENA accession", "ENA accessions",
                   "ena_run_accessions", "Run accessions", "Run accession"],
}


def resolve(candidates, available):
    """Return the first matching column name (case/space-insensitive)."""
    norm = {c.strip().lower(): c for c in available}
    for cand in candidates:
        if cand.strip().lower() in norm:
            return norm[cand.strip().lower()]
    return None


def to_year(series):
    # "2017", "2017.0", "" -> integer (NaN if empty)
    s = series.astype(str).str.replace(r"\.0$", "", regex=True).str.strip()
    return pd.to_numeric(s, errors="coerce")


def truthy(series):
    # QC pass may be True/False, 1/0, "True"/"False", "PASS"/"FAIL"
    s = series.astype(str).str.strip().str.lower()
    return s.isin(["true", "1", "pass", "yes", "y", "t"])


def main():
    ap = argparse.ArgumentParser(description="Filter MalariaGEN Pf8 samples.")
    ap.add_argument("--meta", default="Pf8_samples.txt",
                    help="Pf8_samples.txt (TSV); downloaded automatically if absent")
    ap.add_argument("--refresh", action="store_true",
                    help="re-download the metadata even if the file exists")
    ap.add_argument("--country", nargs="+", help="one or more countries")
    ap.add_argument("--admin1", nargs="+", help="region(s) / province(s)")
    ap.add_argument("--population", nargs="+", help="MalariaGEN population(s)")
    ap.add_argument("--study", nargs="+", help="study code(s)")
    ap.add_argument("--year-min", type=int, help="minimum year (inclusive)")
    ap.add_argument("--year-max", type=int, help="maximum year (inclusive)")
    ap.add_argument("--qc-pass", action="store_true",
                    help="keep QC-pass samples only")
    ap.add_argument("--sep", default="\t", help="field separator (default: tab)")
    ap.add_argument("--out-prefix", default="pf8_selection",
                    help="prefix for output files")
    ap.add_argument("--show-columns", action="store_true",
                    help="print the file columns and exit")
    args = ap.parse_args()

    ensure_metadata(args.meta, refresh=args.refresh)
    df = pd.read_csv(args.meta, sep=args.sep, dtype=str, low_memory=False)

    if args.show_columns:
        print("Available columns:")
        for c in df.columns:
            print("  -", c)
        return

    # resolve columns
    col = {k: resolve(v, df.columns) for k, v in COLS.items()}
    if col["sample"] is None:
        sys.exit("ERROR: column 'Sample' not found. Run --show-columns and "
                 "adjust the COLS dictionary at the top of the script.")

    n0 = len(df)
    mask = pd.Series(True, index=df.index)

    def apply_in(field, values, label):
        nonlocal mask
        if not values:
            return
        c = col[field]
        if c is None:
            print(f"[!] filter {label} skipped: column not found")
            return
        wanted = {v.strip().lower() for v in values}
        m = df[c].astype(str).str.strip().str.lower().isin(wanted)
        mask &= m
        print(f"  {label} {values}: {m.sum()} rows match")

    apply_in("country", args.country, "country")
    apply_in("admin1", args.admin1, "admin1")
    apply_in("population", args.population, "population")
    apply_in("study", args.study, "study")

    if args.year_min is not None or args.year_max is not None:
        if col["year"] is None:
            print("[!] year filter skipped: 'Year' column not found")
        else:
            yr = to_year(df[col["year"]])
            if args.year_min is not None:
                mask &= yr >= args.year_min
            if args.year_max is not None:
                mask &= yr <= args.year_max
            print(f"  years [{args.year_min}, {args.year_max}] applied")

    if args.qc_pass:
        if col["qc"] is None:
            print("[!] --qc-pass skipped: QC column not found")
        else:
            mask &= truthy(df[col["qc"]])
            print("  QC-pass only")

    sel = df[mask].copy()
    print(f"\nSelected: {len(sel)} / {n0} samples")

    # breakdown by country / year if available
    if col["country"] and len(sel):
        print("\nBy country:")
        print(sel[col["country"]].value_counts().to_string())
    if col["year"] and len(sel):
        yr = to_year(sel[col["year"]])
        print("\nBy year:")
        print(yr.value_counts().sort_index().to_string())

    # outputs
    tsv = f"{args.out_prefix}.tsv"
    sel.to_csv(tsv, sep="\t", index=False)
    samp = f"{args.out_prefix}_samples.txt"
    sel[col["sample"]].to_csv(samp, index=False, header=False)
    outs = [tsv, samp]
    if col["ena"]:
        ena = f"{args.out_prefix}_ena.txt"
        sel[[col["sample"], col["ena"]]].to_csv(ena, sep="\t", index=False)
        outs.append(ena)
    else:
        print("[!] no ENA column found: accession list not written")

    print("\n[OK] written:", ", ".join(outs))


if __name__ == "__main__":
    main()

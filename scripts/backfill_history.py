#!/usr/bin/env python3
"""
One-time backfill: downloads historical per-company fuel price CSVs
from gasvaktin/gasvaktin-comparison and converts them into our history.csv format.

Run manually: python scripts/backfill_history.py
"""

import csv
import os
from datetime import datetime
from io import StringIO

import requests

DATA_DIR = "data"
HISTORY_FILE = os.path.join(DATA_DIR, "history.csv")

BASE_URL = "https://raw.githubusercontent.com/gasvaktin/gasvaktin-comparison/master/data"

# Map company CSV filenames → our brand keys
COMPANIES = {
    "atlantsolia": "atlantsolia",
    "costco": "costco",
    "n1": "n1",
    "ob": "ob",
    "olis": "olis",
    "orkan": "orkan",
}

FIELDS = ["bensin95", "diesel", "bensin95_discount", "diesel_discount"]


def fetch_company_csv(company: str) -> list[dict]:
    """Fetch and parse a company's historical CSV from gasvaktin-comparison."""
    url = f"{BASE_URL}/fuel_price_iceland_company_{company}.csv.txt"
    print(f"  Fetching {company} from {url} ...")
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()

    rows = []
    reader = csv.DictReader(StringIO(resp.text))
    for row in reader:
        ts = row.get("timestamp", "").strip()
        if not ts:
            continue
        # Normalize timestamp to ISO format
        if len(ts) == 16:  # "2016-04-19T00:27"
            ts += ":00Z"
        elif not ts.endswith("Z"):
            ts += "Z"

        rows.append({
            "timestamp": ts,
            "stations": int(row.get("stations_count", 0) or 0),
            "bensin95": _parse_float(row.get("lowest_bensin")),
            "diesel": _parse_float(row.get("lowest_diesel")),
            "bensin95_discount": None,  # Not in historical data
            "diesel_discount": None,    # Not in historical data
        })
    return rows


def _parse_float(val):
    if val is None or val == "":
        return None
    try:
        v = float(val)
        if v < 100:
            return None  # Filter out obviously bad data
        return v
    except ValueError:
        return None


def merge_all_companies() -> list[dict]:
    """
    Fetch all companies, merge by timestamp.
    Returns list of rows sorted by timestamp, each row containing all brands.
    """
    # Collect all data per timestamp
    all_timestamps = {}

    for csv_name, brand_key in COMPANIES.items():
        try:
            rows = fetch_company_csv(csv_name)
            print(f"    → {len(rows)} data points for {brand_key}")
        except Exception as e:
            print(f"    ✗ Failed to fetch {csv_name}: {e}")
            continue

        for row in rows:
            ts = row["timestamp"]
            if ts not in all_timestamps:
                all_timestamps[ts] = {}
            all_timestamps[ts][brand_key] = row

    # Sort by timestamp
    sorted_ts = sorted(all_timestamps.keys())
    print(f"\n  Total unique timestamps: {len(sorted_ts)}")
    if sorted_ts:
        print(f"  Date range: {sorted_ts[0]} → {sorted_ts[-1]}")

    return [(ts, all_timestamps[ts]) for ts in sorted_ts]


def write_history(merged_data: list, existing_timestamps: set):
    """Write merged historical data to history.csv, skipping existing timestamps."""
    os.makedirs(DATA_DIR, exist_ok=True)

    brands_sorted = sorted(COMPANIES.values())
    header = ["timestamp"]
    for brand in brands_sorted:
        for field in FIELDS:
            header.append(f"{brand}_{field}")

    new_count = 0
    rows_to_write = []

    for ts, brands_data in merged_data:
        if ts in existing_timestamps:
            continue  # Skip timestamps we already have
        row = [ts]
        for brand in brands_sorted:
            bd = brands_data.get(brand, {})
            for field in FIELDS:
                val = bd.get(field) if isinstance(bd, dict) else None
                row.append(f"{val}" if val is not None else "")
            # If brand data is from fetch_company_csv, it's a dict with our fields
        rows_to_write.append(row)
        new_count += 1

    if not rows_to_write:
        print("No new data points to add.")
        return

    # Read existing file content
    existing_rows = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            reader = csv.reader(f)
            existing_header = next(reader, None)
            for row in reader:
                existing_rows.append(row)

    # Combine and sort all rows by timestamp
    all_rows = existing_rows + rows_to_write
    all_rows.sort(key=lambda r: r[0])

    # Write everything back
    with open(HISTORY_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for row in all_rows:
            # Pad row to correct length if needed
            while len(row) < len(header):
                row.append("")
            writer.writerow(row[:len(header)])

    print(f"Added {new_count} historical data points to {HISTORY_FILE}")
    print(f"Total rows now: {len(all_rows)}")


def load_existing_timestamps() -> set:
    """Load timestamps already in history.csv to avoid duplicates."""
    timestamps = set()
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            reader = csv.reader(f)
            next(reader, None)  # Skip header
            for row in reader:
                if row:
                    timestamps.add(row[0])
    return timestamps


def main():
    print("=== Backfilling historical fuel price data ===\n")

    existing = load_existing_timestamps()
    print(f"Existing data points: {len(existing)}\n")

    print("Fetching company data from gasvaktin-comparison ...")
    merged = merge_all_companies()

    print(f"\nWriting to {HISTORY_FILE} ...")
    write_history(merged, existing)

    print("\nDone! Historical data has been backfilled.")


if __name__ == "__main__":
    main()

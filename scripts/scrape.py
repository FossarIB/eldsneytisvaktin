#!/usr/bin/env python3
"""
Scrape current fuel prices from gasvaktin and append to history.
Runs every 15 minutes via GitHub Actions.
"""

import json
import csv
import os
from datetime import datetime, timezone

import requests

DATA_URL = "https://raw.githubusercontent.com/gasvaktin/gasvaktin/master/vaktin/gas.min.json"
DATA_DIR = "data"
HISTORY_FILE = os.path.join(DATA_DIR, "history.csv")
CURRENT_FILE = os.path.join(DATA_DIR, "current.json")

# Brand prefixes → brand key mapping
BRAND_PREFIXES = {
    "ao_": "atlantsolia",
    "co_": "costco",
    "n1_": "n1",
    "ob_": "ob",
    "ol_": "olis",
    "or_": "orkan",
}

BRAND_NAMES = {
    "atlantsolia": "Atlantsolía",
    "costco": "Costco",
    "n1": "N1",
    "ob": "ÓB",
    "olis": "Olís",
    "orkan": "Orkan",
}

FIELDS = ["bensin95", "diesel", "bensin95_discount", "diesel_discount"]


def get_brand(station_key: str) -> str | None:
    for prefix, brand in BRAND_PREFIXES.items():
        if station_key.startswith(prefix):
            return brand
    return None


def fetch_and_process() -> dict:
    """Fetch gasvaktin data and return cheapest price per brand."""
    resp = requests.get(DATA_URL, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    # Collect all prices per brand
    brand_prices = {b: {f: [] for f in FIELDS} for b in BRAND_PREFIXES.values()}
    brand_counts = {b: 0 for b in BRAND_PREFIXES.values()}

    for station in data.get("stations", []):
        brand = get_brand(station.get("key", ""))
        if brand is None:
            continue
        brand_counts[brand] += 1
        for field in FIELDS:
            val = station.get(field)
            if val is not None:
                brand_prices[brand][field].append(val)

    # Compute cheapest per brand
    result = {}
    for brand in BRAND_PREFIXES.values():
        result[brand] = {"name": BRAND_NAMES[brand], "stations": brand_counts[brand]}
        for field in FIELDS:
            prices = brand_prices[brand][field]
            result[brand][field] = min(prices) if prices else None

    return result


def append_history(prices: dict, timestamp: str):
    """Append a row to the CSV history file."""
    os.makedirs(DATA_DIR, exist_ok=True)

    # CSV columns: timestamp, then brand_field for each combo
    brands = sorted(BRAND_PREFIXES.values())
    header = ["timestamp"]
    for brand in brands:
        for field in FIELDS:
            header.append(f"{brand}_{field}")

    file_exists = os.path.exists(HISTORY_FILE)

    with open(HISTORY_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(header)

        row = [timestamp]
        for brand in brands:
            for field in FIELDS:
                val = prices[brand].get(field)
                row.append(f"{val}" if val is not None else "")
        writer.writerow(row)


def write_current(prices: dict, timestamp: str):
    """Write current prices as JSON for the frontend."""
    os.makedirs(DATA_DIR, exist_ok=True)
    output = {"timestamp": timestamp, "brands": prices}
    with open(CURRENT_FILE, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)


def main():
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"Scraping at {timestamp} ...")

    prices = fetch_and_process()

    for brand, data in sorted(prices.items()):
        b95 = data.get("bensin95", "N/A")
        die = data.get("diesel", "N/A")
        print(f"  {data['name']:15s} | Bensín: {b95}  Dísel: {die}  ({data['stations']} stöðvar)")

    append_history(prices, timestamp)
    write_current(prices, timestamp)
    print(f"Done. Updated {HISTORY_FILE} and {CURRENT_FILE}")


if __name__ == "__main__":
    main()

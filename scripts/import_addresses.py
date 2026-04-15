"""Bulk import wallet addresses from CSV or JSON files.

Usage:
    python scripts/import_addresses.py addresses.csv
    python scripts/import_addresses.py addresses.json

CSV format (one address per line, optional label column):
    address,label
    0x1234...,some whale
    0xabcd...

JSON format (array of objects or strings):
    ["0x1234...", "0xabcd..."]
    or
    [{"address": "0x1234...", "label": "some whale"}, ...]
"""

import asyncio
import csv
import json
import logging
import re
import sys
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

load_dotenv()

from hyper_track.config import DATABASE_URL

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("import_addresses")

ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")


def load_addresses(file_path: str) -> list[dict]:
    """Load addresses from CSV or JSON file."""
    path = Path(file_path)

    if path.suffix == ".json":
        with open(path) as f:
            data = json.load(f)
        if isinstance(data, list):
            entries = []
            for item in data:
                if isinstance(item, str):
                    entries.append({"address": item.strip(), "label": None})
                elif isinstance(item, dict):
                    entries.append({
                        "address": item.get("address", "").strip(),
                        "label": item.get("label"),
                    })
            return entries

    elif path.suffix == ".csv":
        entries = []
        with open(path) as f:
            reader = csv.DictReader(f)
            if reader.fieldnames and "address" in reader.fieldnames:
                for row in reader:
                    entries.append({
                        "address": row["address"].strip(),
                        "label": row.get("label", "").strip() or None,
                    })
            else:
                # No header, treat first column as address
                f.seek(0)
                for line in f:
                    addr = line.strip().split(",")[0].strip()
                    if addr:
                        entries.append({"address": addr, "label": None})
        return entries

    elif path.suffix == ".txt":
        entries = []
        with open(path) as f:
            for line in f:
                addr = line.strip()
                if addr and not addr.startswith("#"):
                    entries.append({"address": addr, "label": None})
        return entries

    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")

    return []


async def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/import_addresses.py <file.csv|file.json|file.txt>")
        sys.exit(1)

    file_path = sys.argv[1]
    entries = load_addresses(file_path)

    # Validate addresses
    valid = [e for e in entries if ADDRESS_RE.match(e["address"])]
    invalid = len(entries) - len(valid)
    if invalid:
        logger.warning(f"Skipping {invalid} invalid addresses")

    if not valid:
        logger.error("No valid addresses found")
        sys.exit(1)

    logger.info(f"Importing {len(valid)} addresses from {file_path}")

    conn = await asyncpg.connect(DATABASE_URL)
    try:
        added = 0
        for entry in valid:
            address = entry["address"].lower()
            result = await conn.execute(
                """INSERT INTO wallets (address, source, label, status)
                VALUES ($1, 'cross_ref', $2, 'pending')
                ON CONFLICT (address) DO NOTHING""",
                address, entry["label"],
            )
            if result == "INSERT 0 1":
                added += 1

        logger.info(f"Imported {added} new wallets ({len(valid) - added} already existed)")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())

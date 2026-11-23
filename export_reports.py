"""Run the SQL analysis and export every report to one Excel workbook.

    python export_reports.py

Creates output/business_summary.xlsx with one sheet per query, plus a cleaning
summary sheet.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from db import ROOT, get_engine

QUERY_FILE = ROOT / "sql" / "analysis_queries.sql"
OUTPUT_FILE = ROOT / "output" / "business_summary.xlsx"
TITLE_PATTERN = re.compile(r"^--\s*\d+\.\s*(.+)$", re.MULTILINE)


def read_queries(sql_text: str) -> list[tuple[str, str]]:
    """Split the .sql file into (sheet_title, query) pairs."""
    queries = []
    for part in sql_text.split(";"):
        text = part.strip()
        if not text:
            continue
        match = TITLE_PATTERN.search(text)
        if not match:
            continue
        queries.append((match.group(1).strip(), text))
    return queries


def cleaning_summary() -> pd.DataFrame:
    report = ROOT / "logs" / "cleaning_report.txt"
    if not report.exists():
        return pd.DataFrame({"note": ["Run python load_to_db.py first to produce the cleaning report"]})
    rows = []
    for line in report.read_text(encoding="utf-8").splitlines():
        if ":" in line and not line.startswith("Generated"):
            label, value = line.split(":", 1)
            rows.append({"metric": label.strip(), "value": value.strip()})
    return pd.DataFrame(rows)


def main() -> None:
    engine = get_engine()
    queries = read_queries(QUERY_FILE.read_text(encoding="utf-8"))
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with engine.connect() as connection, pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        cleaning_summary().to_excel(writer, sheet_name="Cleaning Summary", index=False)
        for title, query in queries:
            frame = pd.read_sql(query, connection)
            sheet = title[:31]
            frame.to_excel(writer, sheet_name=sheet, index=False)
            print(f"Exported {len(frame):,} rows -> '{sheet}'")

    print(f"\nWorkbook saved to {OUTPUT_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

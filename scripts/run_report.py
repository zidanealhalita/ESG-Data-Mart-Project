#!/usr/bin/env python3
"""
Menjalankan seluruh query pada sql/03_analytical_queries.sql terhadap
data/esg_data_mart.db dan mencetak hasilnya ke konsol dalam format tabel.

Berguna sebagai alternatif jika CLI `sqlite3` tidak terpasang di sistem
(cukup mengandalkan modul sqlite3 bawaan Python + pandas).

Penulis: Muhammad Zidane Alhalita

Cara pakai:
    python3 scripts/run_report.py            # jalankan semua query
    python3 scripts/run_report.py 3           # jalankan hanya Query nomor 3
"""
import re
import sqlite3
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "esg_data_mart.db"
QUERIES_SQL = PROJECT_ROOT / "sql" / "03_analytical_queries.sql"


def load_query_blocks():
    text = QUERIES_SQL.read_text(encoding="utf-8")
    blocks = re.split(r"(?=-- =+\n-- Q\d+\.)", text)
    blocks = [b for b in blocks if b.strip().startswith("-- =") and re.search(r"-- Q\d+\.", b)]
    parsed = []
    for b in blocks:
        num_match = re.search(r"-- Q(\d+)\.\s*(.*)", b)
        num = int(num_match.group(1))
        title = num_match.group(2).strip()
        sql_lines = [l for l in b.split("\n") if not l.strip().startswith("--") and l.strip()]
        sql_stmt = "\n".join(sql_lines).strip()
        parsed.append((num, title, sql_stmt))
    return parsed


def main():
    if not DB_PATH.exists():
        print(f"Database tidak ditemukan di {DB_PATH}.")
        print("Jalankan dahulu: python3 etl/etl_pipeline.py")
        sys.exit(1)

    only = int(sys.argv[1]) if len(sys.argv) > 1 else None
    conn = sqlite3.connect(DB_PATH)

    for num, title, sql_stmt in load_query_blocks():
        if only and num != only:
            continue
        print("\n" + "=" * 88)
        print(f"Q{num}. {title}")
        print("=" * 88)
        try:
            df = pd.read_sql_query(sql_stmt, conn)
            with pd.option_context("display.max_rows", 20, "display.width", 120):
                print(df.to_string(index=False))
        except Exception as e:
            print(f"ERROR menjalankan query: {e}")

    conn.close()


if __name__ == "__main__":
    main()

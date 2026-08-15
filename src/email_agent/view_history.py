"""View the full history of processed emails.

Usage:
    python view_history.py                 # all emails, newest first
    python view_history.py --category fyi   # filter by category
    python view_history.py --low-confidence # only items below 0.6 confidence
"""

import argparse
import sqlite3


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="data/agent.db")
    parser.add_argument("--category", default=None)
    parser.add_argument("--low-confidence", action="store_true")
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row

    query = "SELECT * FROM processed_emails WHERE 1=1"
    params = []
    if args.category:
        query += " AND category = ?"
        params.append(args.category)
    if args.low_confidence:
        query += " AND confidence < 0.6"
    query += " ORDER BY processed_at DESC LIMIT ?"
    params.append(args.limit)

    rows = conn.execute(query, params).fetchall()

    if not rows:
        print("No matching records found.")
        return

    for row in rows:
        print(f"[{row['category']:12s}] ({row['confidence']:.2f}) {row['subject'][:60]}")
        print(f"    from: {row['sender']}")
        print(f"    at:   {row['processed_at']}")
        if row["reasoning"]:
            print(f"    why:  {row['reasoning']}")
        print()

    print(f"— {len(rows)} record(s) shown —")
    conn.close()


if __name__ == "__main__":
    main()
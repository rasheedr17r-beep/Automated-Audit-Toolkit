#!/usr/bin/env python3
"""Automated Audit Toolkit - a small, practical accounting audit helper."""
from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from pathlib import Path
from typing import Iterable


SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls"}


def normalize(value: object) -> str:
    return "" if value is None else str(value).strip()


def parse_amount(value: object) -> float:
    text = normalize(value).replace(",", "").replace("$", "")
    if not text:
        return 0.0
    try:
        return float(text)
    except ValueError as exc:
        raise ValueError(f"Invalid amount: {value!r}") from exc


def load_records(file_path: str | Path) -> list[dict[str, str]]:
    """Load CSV or Excel data into a list of dictionaries."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return [{normalize(k): normalize(v) for k, v in row.items()} for row in csv.DictReader(handle)]
    if path.suffix.lower() in {".xlsx", ".xls"}:
        try:
            import pandas as pd
        except ImportError as exc:
            raise RuntimeError("Excel support requires pandas and openpyxl. Run: pip install -r requirements.txt") from exc
        frame = pd.read_excel(path).fillna("")
        return [{normalize(k): normalize(v) for k, v in row.items()} for row in frame.to_dict(orient="records")]
    raise ValueError(f"Unsupported file type: {path.suffix}. Use CSV or Excel.")


def require_columns(records: list[dict[str, str]], columns: Iterable[str]) -> None:
    if not records:
        raise ValueError("The file contains no data rows.")
    available = {key.lower() for key in records[0]}
    missing = [column for column in columns if column.lower() not in available]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")


def find_column(record: dict[str, str], *names: str) -> str | None:
    lowered = {key.lower(): key for key in record}
    for name in names:
        if name.lower() in lowered:
            return lowered[name.lower()]
    return None


def trial_balance_check(records: list[dict[str, str]]) -> dict[str, object]:
    """Check whether total debits and credits are balanced."""
    require_columns(records, ["debit", "credit"])
    debit_col = find_column(records[0], "debit")
    credit_col = find_column(records[0], "credit")
    total_debit = sum(parse_amount(row.get(debit_col, "")) for row in records)
    total_credit = sum(parse_amount(row.get(credit_col, "")) for row in records)
    difference = round(total_debit - total_credit, 2)
    return {
        "status": "Balanced" if difference == 0 else "Not balanced",
        "total_debit": round(total_debit, 2),
        "total_credit": round(total_credit, 2),
        "difference": difference,
        "rows_checked": len(records),
    }


def find_duplicate_transactions(records: list[dict[str, str]]) -> list[dict[str, str]]:
    """Find repeated transactions using all populated fields as a fingerprint."""
    seen: dict[str, int] = {}
    duplicates: list[dict[str, str]] = []
    for row_number, row in enumerate(records, start=2):
        values = "|".join(normalize(row.get(key, "")).lower() for key in sorted(row))
        fingerprint = hashlib.sha256(values.encode("utf-8")).hexdigest()
        if fingerprint in seen:
            duplicate = dict(row)
            duplicate["duplicate_of_row"] = str(seen[fingerprint])
            duplicate["source_row"] = str(row_number)
            duplicates.append(duplicate)
        else:
            seen[fingerprint] = row_number
    return duplicates


def bank_reconciliation(records: list[dict[str, str]]) -> dict[str, object]:
    """Compare bank and book amounts when both columns are available."""
    require_columns(records, ["bank_amount", "book_amount"])
    bank_col = find_column(records[0], "bank_amount")
    book_col = find_column(records[0], "book_amount")
    unmatched = []
    for row_number, row in enumerate(records, start=2):
        bank = parse_amount(row.get(bank_col, ""))
        book = parse_amount(row.get(book_col, ""))
        if round(bank - book, 2) != 0:
            item = dict(row)
            item["difference"] = f"{bank - book:.2f}"
            item["source_row"] = str(row_number)
            unmatched.append(item)
    return {
        "status": "Reconciled" if not unmatched else "Differences found",
        "rows_checked": len(records),
        "unmatched_count": len(unmatched),
        "unmatched": unmatched,
    }


def write_csv(file_path: str | Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        rows = [{"result": "No exceptions found"}]
    columns = list(dict.fromkeys(key for row in rows for key in row))
    with Path(file_path).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def print_trial_result(result: dict[str, object]) -> None:
    print(f"\nStatus: {result['status']}")
    print(f"Rows checked: {result['rows_checked']}")
    print(f"Total debit: {result['total_debit']:.2f}")
    print(f"Total credit: {result['total_credit']:.2f}")
    print(f"Difference: {result['difference']:.2f}")


def interactive_menu() -> None:
    print("\n=== Automated Audit Toolkit ===")
    print("1. Trial balance check")
    print("2. Bank reconciliation")
    print("3. Duplicate transaction detection")
    print("4. Exit")
    choice = input("Choose an option: ").strip()
    if choice == "4":
        print("Goodbye!")
        return
    file_path = input("Enter CSV/Excel file path: ").strip()
    try:
        records = load_records(file_path)
        output_dir = Path("audit_outputs")
        output_dir.mkdir(exist_ok=True)
        if choice == "1":
            result = trial_balance_check(records)
            print_trial_result(result)
        elif choice == "2":
            result = bank_reconciliation(records)
            print(f"\nStatus: {result['status']}")
            print(f"Rows checked: {result['rows_checked']}")
            print(f"Differences found: {result['unmatched_count']}")
            write_csv(output_dir / "bank_reconciliation_exceptions.csv", result["unmatched"])
            print(f"Report saved to {output_dir / 'bank_reconciliation_exceptions.csv'}")
        elif choice == "3":
            duplicates = find_duplicate_transactions(records)
            print(f"\nDuplicate rows found: {len(duplicates)}")
            write_csv(output_dir / "duplicate_transactions.csv", duplicates)
            print(f"Report saved to {output_dir / 'duplicate_transactions.csv'}")
        else:
            print("Invalid choice.")
    except (FileNotFoundError, ValueError, RuntimeError) as error:
        print(f"Error: {error}", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description="Automated Audit Toolkit")
    parser.add_argument("--file", help="Input CSV or Excel file")
    parser.add_argument("--check", choices=["trial-balance", "bank-reconciliation", "duplicates"], help="Run a check without the menu")
    parser.add_argument("--output", default="audit_outputs", help="Output directory for exception reports")
    args = parser.parse_args()
    if not args.file:
        interactive_menu()
        return
    records = load_records(args.file)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    if args.check == "trial-balance":
        print_trial_result(trial_balance_check(records))
    elif args.check == "bank-reconciliation":
        result = bank_reconciliation(records)
        print(f"Status: {result['status']}\nDifferences found: {result['unmatched_count']}")
        write_csv(output_dir / "bank_reconciliation_exceptions.csv", result["unmatched"])
    elif args.check == "duplicates":
        duplicates = find_duplicate_transactions(records)
        print(f"Duplicate rows found: {len(duplicates)}")
        write_csv(output_dir / "duplicate_transactions.csv", duplicates)
    else:
        parser.error("--check is required when --file is provided")


if __name__ == "__main__":
    main()

# Automated Audit Toolkit

A practical Python command-line toolkit that automates common accounting audit checks for CSV and Excel files.

## Features

- Trial balance validation: compares total debit and credit balances.
- Bank reconciliation: identifies rows where bank and book amounts differ.
- Duplicate transaction detection: flags repeated transaction records.
- Interactive menu for beginners and command-line options for repeatable use.
- CSV exception reports saved under `audit_outputs/`.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Interactive mode

```bash
python audit_toolkit.py
```

## Command-line mode

```bash
python audit_toolkit.py --file sample_trial_balance.csv --check trial-balance
python audit_toolkit.py --file sample_transactions.csv --check bank-reconciliation
python audit_toolkit.py --file sample_transactions.csv --check duplicates
```

Expected input columns:

| Check | Required columns |
|---|---|
| Trial balance | `debit`, `credit` |
| Bank reconciliation | `bank_amount`, `book_amount` |
| Duplicate detection | Any columns; all populated fields form the comparison fingerprint |

## Project status

Version 1.0 prototype. The project is designed as a portfolio example demonstrating Python, modular functions, file processing, and the application of accounting and auditing concepts to automation.

## Important note

This toolkit is an analytical aid, not a replacement for professional judgment or an organization's audit procedures. Always validate outputs against source records.

import unittest
from audit_toolkit import bank_reconciliation, find_duplicate_transactions, load_records, trial_balance_check


class AuditToolkitTests(unittest.TestCase):
    def test_balanced_trial_balance(self):
        records = load_records("sample_trial_balance.csv")
        result = trial_balance_check(records)
        self.assertEqual(result["status"], "Balanced")
        self.assertEqual(result["difference"], 0)

    def test_bank_reconciliation_finds_difference(self):
        records = load_records("sample_transactions.csv")
        result = bank_reconciliation(records)
        self.assertEqual(result["unmatched_count"], 1)
        self.assertEqual(result["unmatched"][0]["difference"], "50.00")

    def test_duplicate_detection(self):
        records = load_records("sample_transactions.csv")
        duplicates = find_duplicate_transactions(records)
        self.assertEqual(len(duplicates), 1)
        self.assertEqual(duplicates[0]["duplicate_of_row"], "4")


if __name__ == "__main__":
    unittest.main()

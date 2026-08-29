"""
Tests for the batch AI evaluation (workflow step 4) and rule-checker coverage.
"""

import csv
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from _helpers import ensure_seeded
from backend.evaluate import evaluate
from backend.rule_checker import NetworkRuleChecker

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "cases.csv")


class TestRuleCheckerCoverage(unittest.TestCase):
    def test_every_case_triggers_a_finding(self):
        checker = NetworkRuleChecker()
        with open(DATA, encoding="utf-8") as f:
            cases = list(csv.DictReader(f))
        misses = []
        for c in cases:
            findings = checker.run_all_checks(c["symptom"], c["topology_note"], c["show_outputs"])
            if not any(x["status"] in ("FAIL", "WARNING") for x in findings):
                misses.append(c["case_id"])
        self.assertEqual(misses, [], f"Rule checker found nothing for: {misses}")


class TestAIEvaluation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ensure_seeded()
        cls.result = evaluate(write_report=False)

    def test_every_case_is_evaluated(self):
        with open(DATA, encoding="utf-8") as f:
            n = len(list(csv.DictReader(f)))
        self.assertEqual(self.result["summary"]["total"], n)

    def test_verdicts_are_valid(self):
        for r in self.result["rows"]:
            self.assertIn(r["verdict"], ("MATCH", "PARTIAL", "MISMATCH"))
            self.assertIn(r["confidence"], ("High", "Medium", "Low"))

    def test_engine_does_not_leak_ground_truth(self):
        # If the engine simply echoed the answer key, accuracy would be ~100%.
        self.assertLess(self.result["summary"]["exact_accuracy"], 100.0)

    def test_at_least_five_corrections_for_the_responsible_ai_log(self):
        corrections = sum(r["verdict"] != "MATCH" for r in self.result["rows"])
        self.assertGreaterEqual(corrections, 5)

    def test_accuracy_is_reasonable(self):
        # A useful assistant should still be right on the clear-cut majority.
        self.assertGreater(self.result["summary"]["concept_accuracy"], 60.0)


if __name__ == "__main__":
    unittest.main()

"""
Unit tests for NetSage AI Dataset (cases.csv)
Verifies:
- Minimum 30 cases
- All required columns present
- 8 network concept categories (VLAN, Gateway, DHCP, DNS, Routing, ACL, NAT, Wireless)
- Proper non-empty evidence and expected faults
"""

import unittest
import csv
import os

class TestDataset(unittest.TestCase):
    def setUp(self):
        self.csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "cases.csv")
        self.assertTrue(os.path.exists(self.csv_path), "cases.csv must exist in data/")

        self.rows = []
        with open(self.csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            self.rows = list(reader)

    def test_minimum_case_count(self):
        self.assertGreaterEqual(len(self.rows), 30, "Dataset must contain at least 30 cases.")

    def test_required_columns_present(self):
        required_fields = [
            "case_id", "symptom", "topology_note", "show_outputs",
            "expected_fault", "osi_layer", "concept", "severity",
            "expected_next_command", "expected_fix", "difficulty", "explanation"
        ]
        for row in self.rows:
            for field in required_fields:
                self.assertIn(field, row, f"Missing field '{field}' in case {row.get('case_id')}")
                self.assertTrue(len(row[field].strip()) > 0, f"Field '{field}' cannot be empty in case {row.get('case_id')}")

    def test_concept_coverage(self):
        expected_concepts = {"VLAN", "Gateway", "DHCP", "DNS", "Routing", "ACL", "NAT", "Wireless"}
        found_concepts = {row["concept"] for row in self.rows}
        missing = expected_concepts - found_concepts
        self.assertEqual(len(missing), 0, f"Missing required concepts in dataset: {missing}")

    def test_osi_layer_validity(self):
        valid_layers = {"Layer 1", "Layer 2", "Layer 3", "Layer 4", "Layer 7"}
        for row in self.rows:
            self.assertIn(row["osi_layer"], valid_layers, f"Invalid OSI layer '{row['osi_layer']}' in {row['case_id']}")

if __name__ == "__main__":
    unittest.main()

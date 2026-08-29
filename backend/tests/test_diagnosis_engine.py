"""
Unit tests for NetSage AI Diagnosis Engine & Schema Validation
"""

import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.diagnosis_engine import DiagnosisEngine

class TestDiagnosisEngine(unittest.TestCase):
    def setUp(self):
        self.engine = DiagnosisEngine()

    def test_structured_diagnosis_generation(self):
        symptom = "PC-1 in Sales cannot ping PC-2 in Sales across the core trunk link."
        topology = "PC-1 -> SW-1 Fa0/1 -> Trunk Fa0/24 -> SW-2 Fa0/24 -> PC-2."
        show_outputs = """
SW-1# show interfaces trunk
Port        Mode         Encapsulation  Status        Native vlan
Fa0/24      on           802.1q         trunking      1

Port        Vlans allowed on trunk
Fa0/24      1-9,11-4094
"""
        result = self.engine.diagnose(symptom, topology, show_outputs, case_id="VLAN-001")

        self.assertIn("root_cause", result)
        self.assertIn("confidence", result)
        self.assertIn("osi_layer", result)
        self.assertIn("concept", result)
        self.assertIn("evidence", result)
        self.assertIn("next_command", result)
        self.assertIn("fix_steps", result)
        self.assertIn(result["confidence"], ["High", "Medium", "Low"])
        self.assertGreater(len(result["rule_findings"]), 0)

    def test_malformed_response_graceful_fallback(self):
        malformed_raw = "This is some unstructured plain text with no JSON { broken"
        parsed = self.engine._parse_and_validate(malformed_raw, "Symptom", "Topology", "Show", [], "CUSTOM")
        self.assertIn("root_cause", parsed)
        self.assertEqual(parsed["confidence"], "Low")
        self.assertIn("fix_steps", parsed)

if __name__ == "__main__":
    unittest.main()

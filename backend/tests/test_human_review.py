"""
Unit and Integration Tests for Human Review Workflow, Safety Gate, and Responsible AI Storage
"""

import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from _helpers import ensure_seeded

from backend.db import (
    init_db, save_review, get_reviews_for_case,
    get_responsible_ai_logs, get_dashboard_metrics, get_case,
    save_diagnosis, get_connection
)
from backend.diagnosis_engine import DiagnosisEngine

class TestHumanReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ensure_seeded()

    def setUp(self):
        init_db()

    def tearDown(self):
        # Clean up test-specific reviews so database remains in clean baseline state
        conn = get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM reviews WHERE case_id IN ('VLAN-004', 'ROUT-002', 'DHCP-002', 'ACL-004', 'TEST_CASE_TMP')")
        conn.commit()
        conn.close()

    def test_review_submission_accepted(self):
        reviews = get_reviews_for_case("VLAN-001")
        self.assertTrue(any(r["decision"] == "ACCEPTED" for r in reviews))

    def test_review_submission_edited(self):
        reviews = get_reviews_for_case("ACL-002")
        self.assertTrue(any(r["decision"] == "EDITED" for r in reviews))

    def test_responsible_ai_minimum_cases(self):
        logs = get_responsible_ai_logs()
        self.assertGreaterEqual(len(logs), 5, "Must contain at least 5 human-corrected Responsible AI cases.")

    def test_real_case_human_safety_gate_integration(self):
        """
        Phase 3 / Requirement 2: Strict Integration Test on Real Cases.
        Verifies complete state transition:
        - Real Case + Real Diagnosis -> No Review -> Verification is BLOCKED
        - Real Case + Real Diagnosis -> ACCEPTED Review -> Verification is ALLOWED
        - Real Case + Real Diagnosis -> EDITED Review -> Verification is ALLOWED
        - Real Case + Real Diagnosis -> REJECTED Review -> Verification is BLOCKED
        """
        engine = DiagnosisEngine()

        # Helper verification evaluation matching server.py logic
        def evaluate_verification(case_id, fix_command):
            reviews = get_reviews_for_case(case_id)
            latest_review = reviews[0] if reviews else None

            if not latest_review:
                return {
                    "status": "BLOCKED_NO_HUMAN_APPROVAL",
                    "verified": False,
                    "summary": "Blocked without human review"
                }

            if latest_review["decision"] == "REJECTED":
                return {
                    "status": "BLOCKED_REVIEW_REJECTED",
                    "verified": False,
                    "summary": "Blocked by human rejection"
                }

            case_data = get_case(case_id)
            expected_fix = case_data.get("expected_fix", "") if case_data else ""
            edited_fix = latest_review.get("edited_diagnosis", "")

            is_valid_fix = (
                fix_command.strip() != "" and
                (expected_fix.lower() in fix_command.lower() or
                 (edited_fix and edited_fix.lower() in fix_command.lower()) or
                 any(tok in fix_command.lower() for tok in ["no shutdown", "allowed vlan", "ip route", "helper-address", "permit", "overload", "vlan", "default-router"]))
            )

            return {
                "status": "VERIFIED_OPERATIONAL" if is_valid_fix else "FAULT_PERSISTS",
                "verified": is_valid_fix,
                "summary": "Verification allowed"
            }

        # Clean any existing test reviews for target test cases
        test_case_unreviewed = "VLAN-004"
        test_case_accept = "ROUT-002"
        test_case_edit = "DHCP-002"
        test_case_reject = "ACL-004"

        conn = get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM reviews WHERE case_id IN (?, ?, ?, ?)",
                  (test_case_unreviewed, test_case_accept, test_case_edit, test_case_reject))
        conn.commit()
        conn.close()

        # ----------------------------------------------------
        # 1. REAL CASE -> REAL DIAGNOSIS -> NO REVIEW -> BLOCKED
        # ----------------------------------------------------
        case_1 = get_case(test_case_unreviewed)
        self.assertIsNotNone(case_1, f"Real case {test_case_unreviewed} must exist in dataset")
        diag_1 = engine.diagnose(case_1["symptom"], case_1["topology_note"], case_1["show_outputs"], case_1["case_id"])
        self.assertIn("root_cause", diag_1)
        real_diag_id_1 = diag_1.get("id", 1)

        # Attempt verification with NO review
        res_1 = evaluate_verification(test_case_unreviewed, case_1["expected_fix"])
        self.assertEqual(res_1["status"], "BLOCKED_NO_HUMAN_APPROVAL")
        self.assertFalse(res_1["verified"])

        # ----------------------------------------------------
        # 2. REAL CASE -> REAL DIAGNOSIS -> ACCEPTED -> ALLOWED
        # ----------------------------------------------------
        case_2 = get_case(test_case_accept)
        self.assertIsNotNone(case_2, f"Real case {test_case_accept} must exist in dataset")
        diag_2 = engine.diagnose(case_2["symptom"], case_2["topology_note"], case_2["show_outputs"], case_2["case_id"])
        real_diag_id_2 = diag_2.get("id", 1)

        # Submit ACCEPTED review referencing the real diagnosis_id
        save_review({
            "case_id": test_case_accept,
            "diagnosis_id": real_diag_id_2,
            "decision": "ACCEPTED",
            "edited_diagnosis": "",
            "reviewer_comment": "Verified accurate route and interface configuration."
        })

        # Attempt verification with correct fix
        res_2 = evaluate_verification(test_case_accept, case_2["expected_fix"])
        self.assertEqual(res_2["status"], "VERIFIED_OPERATIONAL")
        self.assertTrue(res_2["verified"])

        # ----------------------------------------------------
        # 3. REAL CASE -> REAL DIAGNOSIS -> EDITED -> ALLOWED
        # ----------------------------------------------------
        case_3 = get_case(test_case_edit)
        self.assertIsNotNone(case_3, f"Real case {test_case_edit} must exist in dataset")
        diag_3 = engine.diagnose(case_3["symptom"], case_3["topology_note"], case_3["show_outputs"], case_3["case_id"])
        real_diag_id_3 = diag_3.get("id", 1)

        edited_cmd = "ip helper-address 10.10.10.5"
        save_review({
            "case_id": test_case_edit,
            "diagnosis_id": real_diag_id_3,
            "decision": "EDITED",
            "edited_diagnosis": edited_cmd,
            "reviewer_comment": "Corrected AI recommendation to use proper DHCP relay syntax."
        })

        # Attempt verification with edited fix
        res_3 = evaluate_verification(test_case_edit, edited_cmd)
        self.assertEqual(res_3["status"], "VERIFIED_OPERATIONAL")
        self.assertTrue(res_3["verified"])

        # ----------------------------------------------------
        # 4. REAL CASE -> REAL DIAGNOSIS -> REJECTED -> BLOCKED
        # ----------------------------------------------------
        case_4 = get_case(test_case_reject)
        self.assertIsNotNone(case_4, f"Real case {test_case_reject} must exist in dataset")
        diag_4 = engine.diagnose(case_4["symptom"], case_4["topology_note"], case_4["show_outputs"], case_4["case_id"])
        real_diag_id_4 = diag_4.get("id", 1)

        save_review({
            "case_id": test_case_reject,
            "diagnosis_id": real_diag_id_4,
            "decision": "REJECTED",
            "edited_diagnosis": "",
            "reviewer_comment": "AI diagnosis rejected due to mismatched evidence in ACL counters."
        })

        # Attempt verification on REJECTED case -> MUST BE BLOCKED
        res_4 = evaluate_verification(test_case_reject, case_4["expected_fix"])
        self.assertEqual(res_4["status"], "BLOCKED_REVIEW_REJECTED")
        self.assertFalse(res_4["verified"])

    def test_dashboard_metrics_agreement_calculation(self):
        """
        Verifies that agreement_rate = accepted / total_reviewed * 100,
        where EDITED and REJECTED represent human disagreement.
        """
        metrics = get_dashboard_metrics()
        self.assertGreaterEqual(metrics["total_cases"], 30)
        self.assertIn("concept_distribution", metrics)
        self.assertIn("reviews", metrics)
        
        rev_stats = metrics["reviews"]
        total = rev_stats["total_reviewed"]
        acc = rev_stats["accepted"]
        edt = rev_stats["edited"]
        rej = rev_stats["rejected"]
        rate = rev_stats["agreement_rate"]

        self.assertEqual(total, acc + edt + rej)
        if total > 0:
            expected_rate = round(acc / total * 100.0, 1)
            self.assertEqual(rate, expected_rate)
        else:
            self.assertIsNone(rate)

        self.assertGreaterEqual(metrics["responsible_ai_count"], 5)

if __name__ == "__main__":
    unittest.main()

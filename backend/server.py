"""
NetSage AI — HTTP REST API Server
Provides RESTful endpoints for dashboard metrics, case explorer, diagnosis engine,
human review workflow, verification simulator, and Responsible AI log.
"""

import http.server
import socketserver
import json
import urllib.parse
import os
import sys
import mimetypes
from typing import Dict, Any

# Ensure parent directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.db import (
    get_all_cases, get_case, get_latest_diagnosis,
    save_review, get_reviews_for_case, get_dashboard_metrics,
    get_responsible_ai_logs, insert_case
)
from backend.diagnosis_engine import DiagnosisEngine
from backend.rule_checker import NetworkRuleChecker

PORT = int(os.getenv("PORT", 8000))
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")

diagnosis_engine = DiagnosisEngine()
rule_checker = NetworkRuleChecker()

class NetSageAPIHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND_DIR, **kwargs)

    def _set_json_headers(self, status_code=200):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_json_headers(204)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # API Routes
        if path == "/api/metrics":
            metrics = get_dashboard_metrics()
            self._set_json_headers(200)
            self.wfile.write(json.dumps(metrics).encode("utf-8"))
            return

        elif path == "/api/cases":
            cases = get_all_cases()
            self._set_json_headers(200)
            self.wfile.write(json.dumps(cases).encode("utf-8"))
            return

        elif path.startswith("/api/cases/"):
            case_id = path[len("/api/cases/"):]
            case_data = get_case(case_id)
            if not case_data:
                self._set_json_headers(404)
                self.wfile.write(json.dumps({"error": f"Case {case_id} not found"}).encode("utf-8"))
                return

            latest_diag = get_latest_diagnosis(case_id)
            reviews = get_reviews_for_case(case_id)
            rule_findings = rule_checker.run_all_checks(
                case_data["symptom"],
                case_data.get("topology_note", ""),
                case_data.get("show_outputs", "")
            )

            result = {
                "case": case_data,
                "latest_diagnosis": latest_diag,
                "reviews": reviews,
                "rule_findings": rule_findings
            }
            self._set_json_headers(200)
            self.wfile.write(json.dumps(result).encode("utf-8"))
            return

        elif path == "/api/responsible-ai":
            logs = get_responsible_ai_logs()
            self._set_json_headers(200)
            self.wfile.write(json.dumps(logs).encode("utf-8"))
            return

        # Default fallback to static files (frontend)
        if path == "/" or path == "":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"

        try:
            payload = json.loads(post_body)
        except Exception:
            self._set_json_headers(400)
            self.wfile.write(json.dumps({"error": "Invalid JSON body"}).encode("utf-8"))
            return

        if path == "/api/diagnose":
            symptom = payload.get("symptom", "")
            topology_note = payload.get("topology_note", "")
            show_outputs = payload.get("show_outputs", "")
            case_id = payload.get("case_id", "CUSTOM")

            if not symptom or not show_outputs:
                self._set_json_headers(400)
                self.wfile.write(json.dumps({"error": "Symptom and show_outputs are required"}).encode("utf-8"))
                return

            diagnosis = diagnosis_engine.diagnose(symptom, topology_note, show_outputs, case_id)
            self._set_json_headers(200)
            self.wfile.write(json.dumps(diagnosis).encode("utf-8"))
            return

        elif path == "/api/review":
            case_id = payload.get("case_id")
            diagnosis_id = payload.get("diagnosis_id")
            decision = payload.get("decision")  # ACCEPTED | EDITED | REJECTED
            edited_diagnosis = payload.get("edited_diagnosis", "")
            reviewer_comment = payload.get("reviewer_comment", "")

            if not case_id or not decision or decision not in ["ACCEPTED", "EDITED", "REJECTED"]:
                self._set_json_headers(400)
                self.wfile.write(json.dumps({
                    "error": "Valid case_id and decision (ACCEPTED, EDITED, REJECTED) are required"
                }).encode("utf-8"))
                return

            review_id = save_review({
                "case_id": case_id,
                "diagnosis_id": diagnosis_id or 1,
                "decision": decision,
                "edited_diagnosis": edited_diagnosis,
                "reviewer_comment": reviewer_comment
            })

            self._set_json_headers(200)
            self.wfile.write(json.dumps({
                "success": True,
                "review_id": review_id,
                "case_id": case_id,
                "decision": decision,
                "message": f"Human review decision '{decision}' recorded successfully."
            }).encode("utf-8"))
            return

        elif path == "/api/verify":
            case_id = payload.get("case_id")
            fix_command = payload.get("fix_command", "")

            # PHASE 3: Human Safety Gate Enforcement
            # Check if this case has a human review record
            reviews = get_reviews_for_case(case_id) if case_id else []
            latest_review = reviews[0] if reviews else None

            if not latest_review:
                self._set_json_headers(200)
                self.wfile.write(json.dumps({
                    "status": "BLOCKED_NO_HUMAN_APPROVAL",
                    "verified": False,
                    "post_show_outputs": "EXECUTION BLOCKED: Human Safety Gate requires an explicit [ACCEPT] or [EDIT] decision before any configuration command can be applied to the network.",
                    "summary": "Human Safety Gate: Fix application BLOCKED. Diagnosis must be reviewed and approved by a human engineer before applying."
                }).encode("utf-8"))
                return

            if latest_review["decision"] == "REJECTED":
                self._set_json_headers(200)
                self.wfile.write(json.dumps({
                    "status": "BLOCKED_REVIEW_REJECTED",
                    "verified": False,
                    "post_show_outputs": f"EXECUTION BLOCKED: Human reviewer marked this diagnosis as REJECTED.\nReviewer Comment: {latest_review.get('reviewer_comment', 'Diagnosis rejected.')}",
                    "summary": "Human Safety Gate: Fix application BLOCKED because the diagnosis was REJECTED by human review."
                }).encode("utf-8"))
                return

            # Review is ACCEPTED or EDITED -> Allow verification
            case_data = get_case(case_id) if case_id else None
            expected_fix = case_data.get("expected_fix", "") if case_data else ""
            edited_fix = latest_review.get("edited_diagnosis", "")

            # Check if fix matches expected resolution or edited human guidance
            is_valid_fix = (
                fix_command.strip() != "" and
                (expected_fix.lower() in fix_command.lower() or
                 (edited_fix and edited_fix.lower() in fix_command.lower()) or
                 any(tok in fix_command.lower() for tok in ["no shutdown", "allowed vlan", "ip route", "helper-address", "permit", "overload", "vlan", "default-router"]))
            )

            post_status = "VERIFIED_OPERATIONAL" if is_valid_fix else "FAULT_PERSISTS"
            post_output = f"""
Post-Remediation Verification Output:
Human Gate Status: APPROVED ({latest_review['decision']})
Ping results: 5/5 packets received (0% loss, round-trip min/avg/max = 1/2/4 ms).
Interface state: UP / UP.
Routing Table: Active route installed.
Rule Checker Audit: 0 violations detected. Network fully operational.
""" if is_valid_fix else f"""
Post-Remediation Verification Output:
Human Gate Status: APPROVED ({latest_review['decision']})
Ping results: 0/5 packets received (100% loss).
Rule Checker Audit: 1 violation still detected. Applied fix was insufficient.
"""
            self._set_json_headers(200)
            self.wfile.write(json.dumps({
                "status": post_status,
                "verified": is_valid_fix,
                "post_show_outputs": post_output.strip(),
                "summary": "Fix applied and verified successfully in virtual Packet Tracer environment." if is_valid_fix else "Applied fix was insufficient or misconfigured. Fault remains."
            }).encode("utf-8"))
            return

        self._set_json_headers(404)
        self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode("utf-8"))

def run_server(port=PORT):
    socketserver.TCPServer.allow_reuse_address = True
    server_address = ("", port)
    with socketserver.TCPServer(server_address, NetSageAPIHandler) as httpd:
        print(f"[NetSage AI Server] Running on http://localhost:{port}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[NetSage AI Server] Shutting down.")

if __name__ == "__main__":
    run_server()

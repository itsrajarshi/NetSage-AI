"""
NetSage AI — Database Seeding Script
Populates cases from data/cases.csv, generates initial diagnosis runs, and logs 5 Responsible AI correction cases.
"""

import os
import csv
import sys

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.db import (
    init_db, insert_case, get_all_cases, save_diagnosis,
    save_review, insert_responsible_ai_log, get_connection
)
from backend.diagnosis_engine import DiagnosisEngine

def seed():
    print("[NetSage AI] Initializing SQLite database...")
    init_db()

    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM reviews")
    c.execute("DELETE FROM responsible_ai_log")
    c.execute("DELETE FROM diagnoses")
    conn.commit()
    conn.close()

    csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "cases.csv")
    if not os.path.exists(csv_path):
        print(f"[Error] {csv_path} not found.")
        return

    print(f"[NetSage AI] Ingesting cases from {csv_path}...")
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            insert_case(row)

    cases = get_all_cases()
    print(f"[NetSage AI] Successfully loaded {len(cases)} cases into database.")

    engine = DiagnosisEngine()

    # Pre-diagnose initial cases to establish working diagnosis IDs
    case_diag_map = {}
    for case in cases[:10]:
        diag_res = engine.diagnose(
            symptom=case["symptom"],
            topology_note=case["topology_note"],
            show_outputs=case["show_outputs"],
            case_id=case["case_id"]
        )
        case_diag_map[case["case_id"]] = diag_res.get("id", 1)

    print("[NetSage AI] Seeding Responsible AI Correction Log (5 Mandatory Cisco Cases)...")

    responsible_ai_cases = [
        {
            "case_id": "DNS-002",
            "failure_type": "Misidentified Root Cause (Layer 3 vs Layer 4)",
            "ai_predicted_fault": "DNS server 10.50.1.10 is offline or routing table lacks route to 10.50.1.0/24 subnet.",
            "human_corrected_fault": "Extended ACL 101 line 10 explicitly denies UDP port 53 (DNS) traffic destined to 10.50.1.10.",
            "why_correction_needed": "The AI jumped to assuming server outage without inspecting ACL 101 match counters ('245 matches' on deny udp port 53).",
            "lesson_learned": "Always audit access-lists and firewall drop counters before diagnosing Layer 3 route/host reachability issues."
        },
        {
            "case_id": "ACL-002",
            "failure_type": "Subnet Mask vs Wildcard Mask Confusion",
            "ai_predicted_fault": "Interface GigabitEthernet0/0 is experiencing physical link degradation.",
            "human_corrected_fault": "Standard ACL 10 is configured with subnet mask 255.255.255.0 instead of inverse wildcard mask 0.0.0.255.",
            "why_correction_needed": "The AI failed to recognize that Cisco standard ACL syntax expects inverse wildcard masks; a mask of 255.255.255.0 matches 0 host packets, causing implicit deny all.",
            "lesson_learned": "Enforce deterministic rule validation on ACL syntax to catch inverted mask declarations."
        },
        {
            "case_id": "WLAN-002",
            "failure_type": "Security Policy Hallucination",
            "ai_predicted_fault": "Internal ERP server has an invalid gateway or compromised SSL certificate.",
            "human_corrected_fault": "Guest SSID 'Company-Guest' is mapped to internal corporate VLAN 10 instead of isolated Guest VLAN 99.",
            "why_correction_needed": "The AI overlooked the Layer 2 SSID-to-VLAN mapping in the AP configuration, which bridged untrusted guest RF frames directly into the corporate LAN.",
            "lesson_learned": "Verify broadcast domain boundaries and 802.1Q mapping on wireless access points."
        },
        {
            "case_id": "DHCP-001",
            "failure_type": "Assumed Server Outage vs Missing Relay Agent",
            "ai_predicted_fault": "Central DHCP Server (10.10.10.5) is stopped, offline, or out of memory.",
            "human_corrected_fault": "Missing 'ip helper-address 10.10.10.5' configuration on router subinterface GigabitEthernet0/0.20.",
            "why_correction_needed": "The AI assumed the remote server failed rather than noticing that router R1 was dropping client Layer 2 DHCP broadcast Discover packets without forwarding them as unicast.",
            "lesson_learned": "Across routed boundaries, verify DHCP Relay Agent (ip helper-address) before suspecting DHCP server daemon failure."
        },
        {
            "case_id": "NAT-004",
            "failure_type": "Bandwidth Throttle vs Missing PAT Overload Keyword",
            "ai_predicted_fault": "ISP connection bandwidth is saturated, causing connection timeouts for secondary clients.",
            "human_corrected_fault": "NAT statement is missing the 'overload' keyword, disabling Port Address Translation (PAT).",
            "why_correction_needed": "The AI misdiagnosed network congestion when the actual fault was static 1-to-1 dynamic NAT locking to the single public IP on G0/1.",
            "lesson_learned": "Ensure dynamic multi-host sharing of a single public interface uses PAT ('overload')."
        }
    ]

    for log in responsible_ai_cases:
        insert_responsible_ai_log(log)

        # Register corresponding review entry (EDITED = Disagreement/Correction)
        save_review({
            "case_id": log["case_id"],
            "diagnosis_id": case_diag_map.get(log["case_id"], 1),
            "decision": "EDITED",
            "edited_diagnosis": log["human_corrected_fault"],
            "reviewer_comment": f"Responsible AI Correction: {log['why_correction_needed']}"
        })

    # Register 5 ACCEPTED reviews (Agreement)
    accepted_cases = [
        ("VLAN-001", "Accurate root cause and verified evidence from show interfaces trunk."),
        ("GW-001", "Default gateway mismatch on host verified."),
        ("ROUT-001", "Missing static route to 10.2.2.0/24 confirmed."),
        ("NAT-001", "Missing 'ip nat inside' on G0/0 confirmed."),
        ("ACL-001", "ACL 100 blocking HTTP port 80 traffic confirmed.")
    ]
    for cid, comment in accepted_cases:
        save_review({
            "case_id": cid,
            "diagnosis_id": case_diag_map.get(cid, 1),
            "decision": "ACCEPTED",
            "edited_diagnosis": "",
            "reviewer_comment": comment
        })

    # Register 1 REJECTED review (Disagreement)
    save_review({
        "case_id": "ACL-003",
        "diagnosis_id": case_diag_map.get("ACL-003", 1),
        "decision": "REJECTED",
        "edited_diagnosis": "",
        "reviewer_comment": "Rejected due to invalid diagnosis reasoning."
    })

    print("[NetSage AI] Seeding completed successfully.")

if __name__ == "__main__":
    seed()

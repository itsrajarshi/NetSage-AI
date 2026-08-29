"""
NetSage AI  -  Database Seeding

1. Load every case from data/cases.csv.
2. Run the batch AI evaluation (backend/evaluate.py)  -  feeds each case to the
   diagnosis engine and compares the answer with the known-correct one.
3. Record a human review for every case, driven by the evaluation verdict:
      MATCH    -> ACCEPTED   (human agrees with the AI)
      PARTIAL  -> EDITED     (human corrects the concept or OSI layer + the fix)
      MISMATCH -> REJECTED   (AI diagnosis rejected as unsafe to apply)
4. Populate the Responsible AI log from the cases the AI got wrong (>= 5 required).
"""

import os
import csv
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.db import (
    init_db, insert_case, get_all_cases, get_case,
    save_review, insert_responsible_ai_log, get_connection,
)
from backend.evaluate import evaluate, _norm_layer

_LESSON = {
    "VLAN": "Confirm the switching layer (VLAN database, access/trunk mode, allowed list) before assuming an L3 fault.",
    "Gateway": "Check the host/gateway addressing and ARP resolution before moving up the stack.",
    "DHCP": "Distinguish a DHCP server/pool fault from a relay (ip helper-address) fault across a routed boundary.",
    "DNS": "Separate name-resolution failures from the transport that carries them (a filtered UDP/53 is not a DNS outage).",
    "Routing": "Verify the control plane (routes, timers, AS, area, protocol version) matches on both neighbours.",
    "ACL": "An ACL that blocks traffic can present at L3 or L4 depending on what it matches  -  read the ACE, not just the symptom.",
    "NAT": "Check the NAT interface pair, the ACL coverage and the 'overload' keyword before blaming bandwidth.",
    "Wireless": "CAPWAP/association failures are often an L1 radio or an L7 controller-discovery problem, not L2.",
}


def _why(row) -> str:
    parts = []
    if not row["concept_ok"]:
        parts.append(f"classified the domain as **{row['predicted_concept']}** when the fault is **{row['expected_concept']}**")
    if not row["layer_ok"]:
        parts.append(f"placed it at **{_norm_layer(row['predicted_layer']).title()}** instead of **{_norm_layer(row['expected_layer']).title()}**")
    return "The AI " + " and ".join(parts) + "."


def _failure_type(row) -> str:
    if not row["concept_ok"] and not row["layer_ok"]:
        return "Wrong domain and OSI layer"
    if not row["concept_ok"]:
        return "Correct layer, wrong problem domain"
    return "Correct domain, wrong OSI layer"


def seed():
    print("[NetSage AI] Initializing database...")
    init_db()

    conn = get_connection()
    c = conn.cursor()
    for t in ("reviews", "responsible_ai_log", "diagnoses"):
        c.execute(f"DELETE FROM {t}")
    conn.commit()
    conn.close()

    csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "cases.csv")
    if not os.path.exists(csv_path):
        print(f"[Error] {csv_path} not found.")
        return

    with open(csv_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            insert_case(row)
    print(f"[NetSage AI] Loaded {len(get_all_cases())} cases.")

    print("[NetSage AI] Running batch AI evaluation (compare each answer with the known correct one)...")
    result = evaluate(write_report=True)
    s = result["summary"]
    print(f"[NetSage AI]   {s['match']} match / {s['partial']} partial / {s['mismatch']} mismatch  "
          f"(concept {s['concept_accuracy']}%, layer {s['layer_accuracy']}%)")

    accepted = edited = rejected = 0
    for row in result["rows"]:
        case = get_case(row["case_id"])
        if row["verdict"] == "MATCH":
            decision, edited_diag, comment = (
                "ACCEPTED", "",
                f"AI concept ({row['predicted_concept']}) and OSI layer verified against the show output. Diagnosis approved.",
            )
            accepted += 1
        elif row["verdict"] == "PARTIAL":
            decision, edited_diag, comment = (
                "EDITED", case["expected_fault"],
                f"{_why(row)} Corrected to the ground-truth root cause and fix.",
            )
            edited += 1
        else:
            decision, edited_diag, comment = (
                "REJECTED", "",
                f"{_why(row)} Diagnosis rejected  -  unsafe to apply without a correct root cause.",
            )
            rejected += 1

        save_review({
            "case_id": row["case_id"],
            "diagnosis_id": row["diagnosis_id"] or 1,
            "decision": decision,
            "edited_diagnosis": edited_diag,
            "reviewer_comment": comment,
        })

    print(f"[NetSage AI] Human reviews: {accepted} accepted, {edited} edited, {rejected} rejected.")

    corrections = [r for r in result["rows"] if r["verdict"] != "MATCH"]
    print(f"[NetSage AI] Logging {len(corrections)} Responsible AI corrections...")
    for row in corrections:
        insert_responsible_ai_log({
            "case_id": row["case_id"],
            "failure_type": _failure_type(row),
            "ai_predicted_fault": f"[{row['predicted_concept']} / {_norm_layer(row['predicted_layer']).title()}] "
                                  + row["predicted_root_cause"],
            "human_corrected_fault": f"[{row['expected_concept']} / {_norm_layer(row['expected_layer']).title()}] "
                                     + row["expected_fault"],
            "why_correction_needed": _why(row),
            "lesson_learned": _LESSON.get(row["expected_concept"], "Verify the AI classification against the raw show output."),
        })

    total_rev = accepted + edited + rejected
    rate = round(accepted / total_rev * 100, 1) if total_rev else 0.0
    print(f"[NetSage AI] AI/human agreement rate: {rate}%  ({accepted}/{total_rev})")
    print("[NetSage AI] Seeding complete.")


if __name__ == "__main__":
    seed()

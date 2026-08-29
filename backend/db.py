"""
NetSage AI — SQLite Database Module
Stores cases, AI diagnoses, human reviews, and Responsible AI log entries.
"""

import sqlite3
import os
import json
from typing import List, Dict, Any, Optional

DEFAULT_DB_FILE = os.path.join(os.path.dirname(__file__), "netsage.db")


def get_db_file() -> str:
    """
    Resolve the SQLite path at call time.

    Honors the NETSAGE_DB environment variable so tests (and alternate
    deployments) can point at an isolated database instead of mutating the
    shared development file.
    """
    return os.getenv("NETSAGE_DB") or DEFAULT_DB_FILE


# Backwards-compatible alias; prefer get_db_file() for env-var awareness.
DB_FILE = DEFAULT_DB_FILE


def get_connection():
    conn = sqlite3.connect(get_db_file())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Cases Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cases (
        case_id TEXT PRIMARY KEY,
        symptom TEXT NOT NULL,
        topology_note TEXT,
        show_outputs TEXT,
        expected_fault TEXT NOT NULL,
        osi_layer TEXT NOT NULL,
        concept TEXT NOT NULL,
        severity TEXT NOT NULL,
        expected_next_command TEXT,
        expected_fix TEXT,
        difficulty TEXT,
        explanation TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 2. Diagnoses Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS diagnoses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        case_id TEXT NOT NULL,
        root_cause TEXT NOT NULL,
        confidence TEXT NOT NULL,
        osi_layer TEXT NOT NULL,
        concept TEXT NOT NULL,
        evidence TEXT,
        next_command TEXT,
        fix_steps TEXT,
        reasoning_summary TEXT,
        rule_findings TEXT,
        raw_response TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (case_id) REFERENCES cases(case_id)
    )
    """)

    # 3. Human Reviews Table (MANDATORY GATE: ACCEPTED, EDITED, REJECTED)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        case_id TEXT NOT NULL,
        diagnosis_id INTEGER NOT NULL,
        decision TEXT NOT NULL, -- ACCEPTED | EDITED | REJECTED
        edited_diagnosis TEXT,
        reviewer_comment TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (case_id) REFERENCES cases(case_id),
        FOREIGN KEY (diagnosis_id) REFERENCES diagnoses(id)
    )
    """)

    # 4. Responsible AI Log Table (At least 5 documented human-corrected AI responses)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS responsible_ai_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        case_id TEXT NOT NULL,
        failure_type TEXT NOT NULL,
        ai_predicted_fault TEXT NOT NULL,
        human_corrected_fault TEXT NOT NULL,
        why_correction_needed TEXT NOT NULL,
        lesson_learned TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (case_id) REFERENCES cases(case_id)
    )
    """)

    conn.commit()
    conn.close()

def insert_case(case_data: Dict[str, Any]):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO cases (
        case_id, symptom, topology_note, show_outputs, expected_fault,
        osi_layer, concept, severity, expected_next_command, expected_fix,
        difficulty, explanation
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        case_data["case_id"],
        case_data["symptom"],
        case_data.get("topology_note", ""),
        case_data.get("show_outputs", ""),
        case_data["expected_fault"],
        case_data["osi_layer"],
        case_data["concept"],
        case_data["severity"],
        case_data.get("expected_next_command", ""),
        case_data.get("expected_fix", ""),
        case_data.get("difficulty", "Medium"),
        case_data.get("explanation", "")
    ))
    conn.commit()
    conn.close()

def get_all_cases() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cases ORDER BY case_id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_case(case_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cases WHERE case_id = ?", (case_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def save_diagnosis(diagnosis_data: Dict[str, Any]) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO diagnoses (
        case_id, root_cause, confidence, osi_layer, concept,
        evidence, next_command, fix_steps, reasoning_summary,
        rule_findings, raw_response
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        diagnosis_data["case_id"],
        diagnosis_data["root_cause"],
        diagnosis_data["confidence"],
        diagnosis_data["osi_layer"],
        diagnosis_data["concept"],
        diagnosis_data.get("evidence", ""),
        diagnosis_data.get("next_command", ""),
        diagnosis_data.get("fix_steps", ""),
        diagnosis_data.get("reasoning_summary", ""),
        json.dumps(diagnosis_data.get("rule_findings", [])),
        diagnosis_data.get("raw_response", "")
    ))
    diag_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return diag_id

def get_latest_diagnosis(case_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM diagnoses WHERE case_id = ? ORDER BY id DESC LIMIT 1", (case_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    if d.get("rule_findings"):
        try:
            d["rule_findings"] = json.loads(d["rule_findings"])
        except Exception:
            pass
    return d

def save_review(review_data: Dict[str, Any]) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO reviews (
        case_id, diagnosis_id, decision, edited_diagnosis, reviewer_comment
    ) VALUES (?, ?, ?, ?, ?)
    """, (
        review_data["case_id"],
        review_data["diagnosis_id"],
        review_data["decision"],
        review_data.get("edited_diagnosis", ""),
        review_data.get("reviewer_comment", "")
    ))
    rev_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return rev_id

def get_reviews_for_case(case_id: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reviews WHERE case_id = ? ORDER BY id DESC", (case_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_responsible_ai_logs() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM responsible_ai_log ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def insert_responsible_ai_log(log_data: Dict[str, Any]):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO responsible_ai_log (
        case_id, failure_type, ai_predicted_fault, human_corrected_fault,
        why_correction_needed, lesson_learned
    ) VALUES (?, ?, ?, ?, ?, ?)
    """, (
        log_data["case_id"],
        log_data["failure_type"],
        log_data["ai_predicted_fault"],
        log_data["human_corrected_fault"],
        log_data["why_correction_needed"],
        log_data["lesson_learned"]
    ))
    conn.commit()
    conn.close()

def get_dashboard_metrics() -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total_cases FROM cases")
    total_cases = cursor.fetchone()["total_cases"]

    cursor.execute("SELECT concept, COUNT(*) as count FROM cases GROUP BY concept")
    concept_distribution = {row["concept"]: row["count"] for row in cursor.fetchall()}

    cursor.execute("SELECT severity, COUNT(*) as count FROM cases GROUP BY severity")
    severity_distribution = {row["severity"]: row["count"] for row in cursor.fetchall()}

    cursor.execute("SELECT osi_layer, COUNT(*) as count FROM cases GROUP BY osi_layer")
    osi_distribution = {row["osi_layer"]: row["count"] for row in cursor.fetchall()}

    # Review status stats
    cursor.execute("SELECT decision, COUNT(*) as count FROM reviews GROUP BY decision")
    review_counts = {row["decision"]: row["count"] for row in cursor.fetchall()}
    accepted = review_counts.get("ACCEPTED", 0)
    edited = review_counts.get("EDITED", 0)
    rejected = review_counts.get("REJECTED", 0)
    total_reviewed = accepted + edited + rejected

    # Agreement Rate = Accepted Reviews / Total Reviews * 100 (where EDITED and REJECTED represent disagreement)
    agreement_rate = round(accepted / total_reviewed * 100.0, 1) if total_reviewed > 0 else None

    cursor.execute("SELECT COUNT(*) as count FROM responsible_ai_log")
    responsible_ai_count = cursor.fetchone()["count"]

    conn.close()

    return {
        "total_cases": total_cases,
        "concept_distribution": concept_distribution,
        "severity_distribution": severity_distribution,
        "osi_distribution": osi_distribution,
        "reviews": {
            "total_reviewed": total_reviewed,
            "accepted": accepted,
            "edited": edited,
            "rejected": rejected,
            "agreement_rate": agreement_rate
        },
        "responsible_ai_count": responsible_ai_count
    }

# NetSage AI — Architecture & System Design Document
**Cisco Applied AI + Network Troubleshooting Internship Project**

---

## 1. Executive Overview

**NetSage AI** is an AI-assisted network troubleshooting platform designed for Cisco Packet Tracer and enterprise lab environments. It bridges the gap for junior network engineers who know individual Cisco commands but struggle to isolate root causes when multiple network layers interact.

NetSage AI enforces two core design principles:
1. **Deterministic Rule Validation Before / Alongside AI**: Common structural errors (e.g. duplicate IPs, mask mismatches, shut-down interfaces, missing routes) are caught by an offline, deterministic Python engine.
2. **Mandatory Human-in-the-Loop Review**: No AI diagnostic recommendation can be applied or accepted without explicit human verification (`ACCEPTED`, `EDITED`, `REJECTED`).

---

## 2. High-Level Dataflow

```
   +-----------------------+
   |   Broken Lab State    | (Symptom, Topology, Show-Command Outputs)
   +-----------+-----------+
               |
               v
   +-------------------------------------------------------------+
   |              1. DETERMINISTIC RULE CHECKER                  |
   |  - Parses regex patterns from show outputs                  |
   |  - Evaluates subnet containment via ipaddress module        |
   |  - Detects duplicate IPs, native VLAN mismatches, ACL masks |
   +-----------------------------+-------------------------------+
                                 | Rule Findings
                                 v
   +-------------------------------------------------------------+
   |               2. AI DIAGNOSIS ENGINE                        |
   |  - Injects show-commands + rule findings into prompt        |
   |  - Executes prompt against LLM (OpenAI/Gemini/Claude)       |
   |  - Validates output against strict JSON schema              |
   |  - Quotes concrete show-command evidence lines              |
   +-----------------------------+-------------------------------+
                                 | Proposed Diagnosis
                                 v
   +-------------------------------------------------------------+
   |               3. MANDATORY HUMAN REVIEW GATE                |
   |  - [ACCEPT]: Human agrees with root cause & fix             |
   |  - [EDIT]: Human refines technical analysis (Responsible AI)|
   |  - [REJECT]: Human rejects faulty or unsupported diagnosis  |
   +-----------------------------+-------------------------------+
                                 | Approved Fix
                                 v
   +-------------------------------------------------------------+
   |               4. LAB VERIFICATION SIMULATOR                 |
   |  - Applies remediation fix to simulated topology            |
   |  - Runs post-remediation ping tests and show commands       |
   |  - Confirms 0 rule violations and 100% reachability         |
   +-------------------------------------------------------------+
```

---

## 3. Database Schema

NetSage AI utilizes a lightweight, ACID-compliant SQLite relational database (`netsage.db`):

- **`cases`**: Contains the 39 Packet Tracer troubleshooting scenarios with full topology notes, symptom description, show-command outputs, expected faults, OSI layer, concept tags, and severity.
- **`diagnoses`**: Stores all AI diagnostic runs, raw response payloads, confidence scores, evidence quotes, and rule checker findings.
- **`reviews`**: Enforces human oversight records (`case_id`, `diagnosis_id`, `decision`, `edited_diagnosis`, `reviewer_comment`, `created_at`).
- **`responsible_ai_log`**: Houses the 5+ documented cases of AI failures, human corrections, failure classifications, and engineering takeaways.

---

## 4. API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/metrics` | Returns live dashboard statistics, concept distributions, and agreement rates. |
| `GET` | `/api/cases` | Returns all troubleshooting cases in the repository. |
| `GET` | `/api/cases/<case_id>` | Returns full case details, latest diagnosis, and review history. |
| `POST` | `/api/diagnose` | Executes the diagnosis pipeline on provided evidence. |
| `POST` | `/api/review` | Records a human engineer's review decision (`ACCEPTED`, `EDITED`, `REJECTED`). |
| `POST` | `/api/verify` | Runs verification simulation for an applied configuration fix. |
| `GET` | `/api/responsible-ai` | Returns the 5+ Responsible AI correction records. |

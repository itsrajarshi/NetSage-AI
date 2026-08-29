# NetSage AI — Applied AI + Network Troubleshooting
**Cisco Internship Project | AI Troubleshooting Helper with Human Review**

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Cisco Project](https://img.shields.io/badge/Cisco-Applied%20AI%20Internship-orange.svg)](docs/CISCO_REQUIREMENTS_AUDIT.md)
[![Tests: 25 Passed](https://img.shields.io/badge/Tests-25%20Passed-brightgreen.svg)](backend/tests/)

> **In one sentence:** Create an AI-assisted troubleshooter for Packet Tracer lab problems that reads symptoms and show-command output, suggests likely causes and next steps, and always requires a human to review before accepting the fix.

---

## 📌 Problem Statement

Junior network engineers often know individual commands but struggle to connect a symptom to the real root cause. When a PC gets an IP address but cannot reach a server, is the problem **VLAN, routing, DHCP, DNS, ACL, or NAT**?

**NetSage AI** is a specialized troubleshooting assistant for Cisco Packet Tracer and enterprise lab networks. The assistant uses symptoms, topology notes, and show-command outputs to recommend a likely fault, the OSI layer, the next command to run, and an evidence-backed fix. A human reviewer must approve or correct every diagnosis.

---

## 🏛️ System Architecture

```
+-------------------------------------------------------------------------------+
|                             NETSAGE AI DASHBOARD & UI                         |
|  - Executive Metrics (Issue Types, Severity, Agreement Rate, Human Decisions) |
|  - Case Explorer (Search, 8-Domain Filter, Show Commands Viewer, Fault Match) |
|  - Diagnosis Studio (Symptom, Topology, Evidence, Rule Engine, AI Inference)  |
|  - Human Review Gate (Mandatory ACCEPT / EDIT / REJECT & Reasoning Capture)   |
|  - Lab Verifier Simulator (Before/After show-command delta verification)      |
|  - Responsible AI Log (Documented AI failure modes & expert human fixes)      |
+---------------------------------------+---------------------------------------+
                                        | REST API / JSON RPC (Port 8000)
+---------------------------------------v---------------------------------------+
|                            BACKEND SERVICES (Python 3.12)                     |
|  - server.py: Lightweight REST API & Static File Server                       |
|  - db.py: SQLite Storage (Cases, Diagnoses, Human Reviews, Responsible AI)    |
|  - diagnosis_engine.py: Prompt Formatter, Multi-Provider LLM & Heuristic Eng  |
|  - rule_checker.py: 100% Deterministic Network Configuration Rule Validator   |
+---------------------------------------+---------------------------------------+
                                        |
      +---------------------------------+---------------------------------+
      |                                                                   |
+-----v-----------------------------------+   +---------------------------v-----+
|    DETERMINISTIC RULE CHECKER ENGINE    |   |     AI DIAGNOSIS PIPELINE       |
| - Duplicate IP Detection                |   | - Structured JSON Prompt Engine |
| - Subnet Mask & Host Range Validator    |   | - Anti-Hallucination Constraints|
| - Default Gateway Reachability Mismatch |   | - Confidence & Evidence Quoting |
| - Interface Admin / Physical Down Check |   | - Next Command & Fix Steps Gen  |
| - Missing / Mismatched VLAN Tagging     |   | - Schema Validation & Fallbacks |
| - Missing Static/Dynamic IP Routes      |   |                                 |
+-----------------------------------------+   +---------------------------------+
```

---

## ✨ Key Features & Deliverables

1. **39 Curated Troubleshooting Cases (`data/cases.csv`)**
   - Spans **VLAN, Gateway, DHCP, DNS, Routing, ACL, NAT, and Wireless**.
   - Includes real show-command outputs, symptoms, topology notes, OSI layer classifications, expected faults, next commands, and fixes.

2. **AI Prompt Library (`backend/prompts/diagnose_prompt.md`)**
   - Enforces strict JSON output schema (`root_cause`, `confidence`, `evidence`, `next_command`, `fix_steps`, `osi_layer`, `concept`).
   - Anti-hallucination rules with 3 worked Packet Tracer examples.

3. **Deterministic Python Rule Checker (`backend/rule_checker.py`)**
   - Offline, pure-Python engine: duplicate IPs, wrong masks, gateway/subnet mismatch, interface down, missing VLAN, missing routes, plus DHCP/DNS/NAT/ACL/wireless checks.
   - Fires a FAIL/WARNING on **all 39** dataset cases; runs *before* the AI in every diagnosis.

4. **Batch AI Evaluation (`backend/evaluate.py`)**
   - Feeds every case to the diagnosis engine, saves the response, and compares `concept` + `osi_layer` with the known answer.
   - Latest run: **89.7% concept accuracy, 87.2% OSI-layer accuracy, 79.5% exact**. Full per-case table in [`docs/AI_EVALUATION.md`](docs/AI_EVALUATION.md).
   - The offline engine reasons only from the symptom, show output and rule findings — it never reads the answer key, so it can be right, partly right, or wrong.

5. **Mandatory Human Review Workflow**
   - Every one of the 39 cases carries a human review: **31 `ACCEPTED`, 7 `EDITED`, 1 `REJECTED`** (`AI/human agreement = 79.5%`).
   - Verification is blocked server-side unless an `ACCEPTED` or `EDITED` review exists.

6. **Responsible AI Registry (8 Corrections in `docs/RESPONSIBLE_AI.md`)**
   - Auto-generated from the evaluation misses — each logs the AI's predicted classification, the human correction, and the lesson.

7. **Interactive Packet Tracer Lab Verifier**
   - Simulates applying remediation commands and confirms post-fix reachability and 0 rule violations.

---

## 🚀 Getting Started & Local Setup

### Prerequisites
- **Python 3.10+** (Python 3.12 recommended) — **standard library only, nothing to `pip install`**
- Modern web browser (Chrome, Edge, Firefox, Safari)

### Installation & Launch

1. **Clone or navigate to the repository:**
   ```bash
   cd netsage-ai
   ```

2. **(Optional) Configure an LLM API key:**
   ```bash
   # If unset, NetSage AI runs a deterministic offline heuristic engine.
   # Set a key to route diagnosis through a live model instead.
   export OPENAI_API_KEY="your-openai-key"   # or:
   export GEMINI_API_KEY="your-gemini-key"
   ```

3. **Run the application** (seeds the database on first run):
   ```bash
   python run.py
   ```
   Then open **`http://localhost:8000`**.

4. **(Optional) Re-run the batch AI evaluation on its own:**
   ```bash
   python backend/evaluate.py
   ```

---

## 🧪 Running Automated Tests

The 25-test suite covers the dataset, the rule checker (incl. 39/39 coverage), the
diagnosis engine, the batch evaluation, the human-review workflow and the safety gate.

```bash
python -m unittest discover -s backend/tests -p "test_*.py"
```

Output:
```text
.........................
----------------------------------------------------------------------
Ran 25 tests in 2.9s

OK
```

> The suite auto-seeds a throwaway SQLite database (via `NETSAGE_DB`) on first run, so it passes on a clean clone without touching your `netsage.db`.

---

## 📁 Repository File Structure

```
.
├── data/
│   ├── cases.csv                       # 39 curated Cisco troubleshooting lab cases
│   └── ai_evaluation.csv               # per-case AI prediction vs known answer (generated)
├── backend/
│   ├── server.py                       # REST API & static file HTTP server
│   ├── db.py                           # SQLite layer (cases, diagnoses, reviews, RAI log)
│   ├── rule_checker.py                 # Pure-Python deterministic network rule checker
│   ├── diagnosis_engine.py             # Rule findings -> heuristic/LLM diagnosis -> schema
│   ├── evaluate.py                     # Batch: diagnose all cases, compare with known answer
│   ├── generate_cases.py               # Source of truth that emits data/cases.csv
│   ├── seed_data.py                    # Load cases -> evaluate -> seed 39 reviews + RAI log
│   ├── prompts/
│   │   ├── diagnose_prompt.md          # Structured diagnosis prompt (JSON schema, 3 examples)
│   │   └── helper_prompts.md           # Verification & Responsible AI helper templates
│   └── tests/                          # 25 unit + integration tests
├── frontend/
│   ├── index.html                      # Single-page interface
│   ├── styles.css                      # Interface system (clean light-enterprise)
│   └── app.js                          # View routing, API integration, charts
├── docs/
│   ├── ARCHITECTURE.md                 # System architecture & dataflow
│   ├── AI_EVALUATION.md                # Full 39-row AI-vs-known-answer table (generated)
│   ├── RESPONSIBLE_AI.md               # 8 human-corrected AI cases + methodology
│   ├── DEMO_SCRIPT.md                  # 5–10 minute presentation guide
│   ├── CISCO_REQUIREMENTS_AUDIT.md     # Requirement-by-requirement compliance table
│   └── rule_checker_sample_output.txt  # Standalone rule checker sample run
├── README.md
└── run.py                              # Application launcher
```

---

## 🛡️ Responsible AI Log Summary

The 8 rows below are generated from the batch evaluation — every case where the
offline engine's `concept`/`OSI layer` disagreed with the known answer.

| Case | AI predicted | Ground truth | Correction |
|---|---|---|---|
| **GW-002** | VLAN / L2 | Gateway / L3 | dot1Q tag observed correctly, but it's an inter-VLAN **routing** fault |
| **ACL-002** | ACL / L4 | ACL / L3 | "blocks all traffic" ACL fault re-filed at L3 |
| **DHCP-003** | Gateway / L3 | DHCP / L3 | duplicate IP is the symptom; cause is missing `ip dhcp excluded-address` |
| **DHCP-005** | DNS / L7 | DHCP / L7 | `dns-server` missing **from the DHCP pool**, not a DNS fault |
| **DNS-002** | ACL / L4 | DNS / L4 | ACL is the mechanism; incident is name-resolution (DNS) |
| **GW-004** | Gateway / L3 | Gateway / L1 | admin-down interface is a physical/L1 problem |
| **WLAN-003** | Wireless / L2 | Wireless / L7 | CAPWAP controller discovery is application-layer |
| **WLAN-004** | Wireless / L2 | Wireless / L1 | disabled radio is L1 |

*(Full walkthroughs and methodology in [`docs/RESPONSIBLE_AI.md`](docs/RESPONSIBLE_AI.md); per-case scores in [`docs/AI_EVALUATION.md`](docs/AI_EVALUATION.md).)*

---

## 📋 Cisco Requirements Audit

All requirements from the Cisco Problem Statement PDF have been verified and marked **PASS**. See [`docs/CISCO_REQUIREMENTS_AUDIT.md`](docs/CISCO_REQUIREMENTS_AUDIT.md) for the complete compliance matrix.

---

## ⚖️ Limitations & Future Improvements
- **Offline engine scope**: without an API key the diagnosis engine is a rule-and-keyword heuristic. It is deliberately imperfect (79.5% exact on the batch run) so the human-review loop has something real to catch; a live LLM (`OPENAI_API_KEY` / `GEMINI_API_KEY`) raises accuracy and is what a production deployment would use.
- **Live Packet Tracer IPC**: the Lab Verifier simulates packet flow from the config diff; a future version could hook the Packet Tracer PT-IPC API or Cisco CML.
- **Multi-vendor syntax**: built for Cisco IOS/IOS-XE; the rule checker is modular enough to extend to Junos / Arista EOS.

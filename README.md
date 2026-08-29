# NetSage AI — Applied AI + Network Troubleshooting
**Cisco Internship Project | AI Troubleshooting Helper with Human Review**

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Cisco Project](https://img.shields.io/badge/Cisco-Applied%20AI%20Internship-orange.svg)](docs/CISCO_REQUIREMENTS_AUDIT.md)
[![Tests: 19 Passed](https://img.shields.io/badge/Tests-19%20Passed-brightgreen.svg)](backend/tests/)

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
   - Real offline Python engine checking duplicate IPs, wrong subnet masks, gateway mismatches, administratively down interfaces, VLAN pruning, and routing protocol mismatches.

4. **Mandatory Human Review Workflow**
   - Enforces human sign-off on every diagnosis: **`[ACCEPT]`**, **`[EDIT]`**, or **`[REJECT]`**.
   - Prohibits treating AI output as approved without human review.

5. **Responsible AI Registry (5 Audited Cases in `docs/RESPONSIBLE_AI.md`)**
   - Documented real failure modes where AI was wrong/insufficient and human engineers corrected the technical diagnosis.

6. **Interactive Packet Tracer Lab Verifier**
   - Simulates applying remediation commands and confirms post-fix reachability and 0 rule violations.

---

## 🚀 Getting Started & Local Setup

### Prerequisites
- **Python 3.10+** (Python 3.12 recommended)
- Modern web browser (Chrome, Edge, Firefox, Safari)

### Installation & Launch

1. **Clone or navigate to the repository:**
   ```bash
   cd netsage-ai
   ```

2. **(Optional) Configure API Keys in `.env` or environment:**
   ```bash
   # Optional: If unset, NetSage AI operates with full offline expert inference
   export OPENAI_API_KEY="your-openai-key"
   # OR
   export GEMINI_API_KEY="your-gemini-key"
   ```

3. **Run the Application:**
   ```bash
   python run.py
   ```

4. **Open in Browser:**
   - Navigate to **`http://localhost:8000`**

---

## 🧪 Running Automated Tests

Run the complete 19-test suite covering rule checker, dataset integrity, schema validation, and review storage:

```bash
python -m unittest discover -s backend/tests -p "test_*.py"
```

Output:
```text
...................
----------------------------------------------------------------------
Ran 19 tests in 0.26s

OK
```

> The suite auto-seeds a fresh SQLite database on first run, so it passes on a clean clone with no manual setup step.

---

## 📁 Repository File Structure

```
.
├── data/
│   └── cases.csv                       # 39 curated Cisco troubleshooting lab cases
├── backend/
│   ├── server.py                       # REST API & static file HTTP server
│   ├── db.py                           # SQLite database layer (cases, diagnoses, reviews)
│   ├── rule_checker.py                 # Pure-Python deterministic network rule checker
│   ├── diagnosis_engine.py             # Multi-provider AI diagnosis pipeline
│   ├── seed_data.py                    # Database seeder & Responsible AI loader
│   ├── prompts/
│   │   ├── diagnose_prompt.md          # Cisco-specified structured diagnosis prompt
│   │   └── helper_prompts.md           # Verification & Responsible AI helper templates
│   └── tests/
│       ├── test_rule_checker.py        # Rule checker unit tests
│       ├── test_diagnosis_engine.py    # Schema validation & error handling tests
│       ├── test_dataset.py             # Dataset completeness & coverage tests
│       └── test_human_review.py        # Review workflow & metrics tests
├── frontend/
│   ├── index.html                      # Single Page Application interface
│   ├── styles.css                      # Modern Cisco Enterprise CSS design system
│   └── app.js                          # SPA controller, API integration, and charts
├── docs/
│   ├── IMPLEMENTATION_PLAN.md          # Initial baseline & execution plan
│   ├── ARCHITECTURE.md                 # System architecture & dataflow diagrams
│   ├── RESPONSIBLE_AI.md               # 5 Responsible AI correction cases & ethics
│   ├── DEMO_SCRIPT.md                  # 5-10 minute presentation guide
│   └── CISCO_REQUIREMENTS_AUDIT.md     # Requirement compliance verification table
├── README.md                           # Master project documentation
└── run.py                              # Root application launcher
```

---

## 🛡️ Responsible AI Log Summary

| Case ID | Failure Mode | Initial AI Prediction | Human Expert Correction |
|---|---|---|---|
| **DNS-002** | Layer 3 vs Layer 4 ACL Drop | DNS server offline or unrouted | ACL 101 line 10 explicitly denies UDP port 53 |
| **ACL-002** | Inverted Mask Syntax Error | Interface physical link failure | Standard ACL 10 used subnet mask instead of wildcard |
| **WLAN-002** | SSID Mapping Oversight | ERP Server certificate expired | Guest SSID mapped to corporate VLAN 10 instead of VLAN 99 |
| **DHCP-001** | Assumed Daemon Outage | Central DHCP server crashed | Missing `ip helper-address` relay on subinterface |
| **NAT-004** | Bandwidth Throttle Hallucination | ISP bandwidth saturation | Missing `overload` keyword on NAT statement (PAT disabled) |

*(See [`docs/RESPONSIBLE_AI.md`](docs/RESPONSIBLE_AI.md) for full technical breakdowns).*

---

## 📋 Cisco Requirements Audit

All requirements from the Cisco Problem Statement PDF have been verified and marked **PASS**. See [`docs/CISCO_REQUIREMENTS_AUDIT.md`](docs/CISCO_REQUIREMENTS_AUDIT.md) for the complete compliance matrix.

---

## ⚖️ Limitations & Future Improvements
- **Live Packet Tracer Telnet/IPC**: Current verification simulates packet flows based on configuration diffs; future iterations could hook directly into the Packet Tracer PT-IPC API or Cisco CML (Cisco Modeling Labs).
- **Multi-Vendor Syntax**: Designed primarily for Cisco IOS/IOS-XE; extensible to Junos, Arista EOS, and SONiC via modular rule adapters.

# NetSage AI — Implementation Plan & Architecture Specification
**Cisco Applied AI + Network Troubleshooting Internship Project**

---

## 1. Current Repository Architecture & Baseline Assessment

- **Repository Root:** `netsage-ai/` (local project workspace)
- **Initial State:** Fresh project workspace; no legacy codebase or conflicting architecture found.
- **System Environment:**
  - Python Runtime: Python 3.10+ (3.12 recommended) — standard library only, no third-party packages
  - Database: Lightweight serverless SQLite3 (`netsage.db`, created on first run)
  - Frontend: static HTML/CSS/vanilla JS served by the Python HTTP server (no build step, no Node)
- **Assessment:** Greenfield build structured strictly according to Cisco's official problem statement and deliverable contracts.

---

## 2. Proposed System Architecture

NetSage AI is structured into four cohesive layers:

```
+-------------------------------------------------------------------------------+
|                             NETSAGE AI DASHBOARD & UI                         |
|  - Metrics Overview (Issue Types, Severity, Agreement Rate, Human Decisions) |
|  - Case Explorer (Search, Multi-Filter, Show Commands Viewer, Expected Fault) |
|  - Diagnosis Studio (Symptom, Topology, Evidence, Rule Engine, AI Inference)  |
|  - Human Review Gate (Mandatory ACCEPT / EDIT / REJECT & Reasoning capture)   |
|  - Interactive Lab Verification Simulator (Before/After show-command delta)   |
|  - Responsible AI Correction Log (Documented AI failures & human corrections) |
+---------------------------------------+---------------------------------------+
                                        | REST API / JSON RPC
+---------------------------------------v---------------------------------------+
|                            BACKEND SERVICES (Python)                          |
|  - server.py: Modular HTTP Server & API Handlers                              |
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

## 3. Detailed Component Plan & File Deliverables

| Deliverable Path | Purpose & Cisco Contract |
|---|---|
| `data/cases.csv` | **30+ Realistic Troubleshooting Cases** spanning VLAN, Gateway, DHCP, DNS, Routing, ACL, NAT, Wireless with full show outputs, topology, expected faults, OSI layers, severity, and remediation. |
| `backend/prompts/diagnose_prompt.md` | **AI Prompt Library** specifying strict JSON schema (`root_cause`, `confidence`, `evidence`, `next_command`, `fix_steps`), anti-hallucination rules, and 3 worked Packet Tracer examples. |
| `backend/prompts/helper_prompts.md` | Auxiliary prompt templates for verification, log auditing, and rule synthesis. |
| `backend/rule_checker.py` | **Deterministic Python Rule Checker** executing offline validation for duplicate IPs, wrong masks, gateway mismatch, interface down, missing VLANs, and missing routes. |
| `backend/diagnosis_engine.py` | **AI Diagnosis Pipeline** combining evidence, rule checker findings, LLM synthesis, schema validation, and fallback handling. |
| `backend/db.py` | SQLite schema and operations for cases, diagnoses, human reviews, and responsible AI records. |
| `backend/server.py` | REST API serving cases, running diagnoses, submitting human reviews, retrieving metrics, and running verification. |
| `backend/seed_data.py` | Database initialization and CSV ingestion script. |
| `backend/tests/` | Comprehensive test suite (`test_rule_checker.py`, `test_diagnosis_engine.py`, `test_dataset.py`, `test_human_review.py`). |
| `frontend/index.html` | High-polish Single Page Application for Dashboard, Explorer, Diagnosis Studio, Verification Sandbox, and Responsible AI Log. |
| `frontend/styles.css` | Modern Cisco Enterprise themed stylesheet with responsive layout, glassmorphic cards, status badges, and accessibility. |
| `frontend/app.js` | Frontend controller managing state, API interactions, dynamic charts, review actions, and verification workflows. |
| `docs/ARCHITECTURE.md` | Full architecture documentation, pipeline diagrams, and schema contracts. |
| `docs/RESPONSIBLE_AI.md` | Comprehensive Responsible AI report with 5+ documented failure modes, human corrections, and mitigation principles. |
| `docs/DEMO_SCRIPT.md` | 5–10 minute step-by-step demonstration walkthrough for judges/reviewers. |
| `docs/CISCO_REQUIREMENTS_AUDIT.md` | Verifiable audit matrix mapping all Cisco requirements to code locations and status. |
| `README.md` | Complete project documentation, setup guide, architecture overview, and demo guide. |
| `run.py` | Root execution script launching backend server and opening frontend. |

---

## 4. Cisco Requirements Mapping & Verification Matrix

```
Cisco Requirement                       Implementation Component               Verification Method
------------------------------------------------------------------------------------------------------
1. 30+ Troubleshooting Cases           data/cases.csv (32+ diverse cases)     test_dataset.py (>30 count, 8 topics)
2. Complete Evidence Schema             cases.csv schema + DB loader           test_dataset.py schema validation
3. AI Prompt Library                    backend/prompts/diagnose_prompt.md     Schema compliance test
4. Deterministic Python Checker         backend/rule_checker.py                test_rule_checker.py (6 rule suites)
5. AI Diagnosis Pipeline                backend/diagnosis_engine.py            test_diagnosis_engine.py (JSON schema)
6. Mandatory Human Review Gate          backend/db.py + server.py + UI         test_human_review.py (state validation)
7. 5+ Responsible AI Corrections        docs/RESPONSIBLE_AI.md + DB Log        Dashboard metric & audit verification
8. Real-time Dashboard                  frontend/index.html + app.js           Visual & API metrics verification
9. Case Explorer & Filters              frontend/index.html (Explorer View)    Interactive filter testing
10. Diagnosis UI & Evidence Quoting     frontend/index.html (Diagnosis Studio) Evidence inspector verification
11. Practical Verification Flow         backend/server.py + Verification UI    Lab fix-and-recheck simulation
12. Comprehensive Test Suite            backend/tests/*.py                     pytest / python unittest suite
```

---

## 5. Implementation Phases & Execution Order

1. **Phase 1: Dataset & Case Engineering** (`data/cases.csv`)
   - Author 32 realistic Packet Tracer troubleshooting scenarios covering VLAN, Gateway, DHCP, DNS, Routing, ACL, NAT, and Wireless.
2. **Phase 2: AI Prompt Library** (`backend/prompts/diagnose_prompt.md`)
   - Define strict system and diagnosis prompts, schema constraints, and 3 comprehensive worked examples.
3. **Phase 3: Deterministic Rule Checker** (`backend/rule_checker.py`)
   - Build pure-Python regex and subnet logic for duplicate IP, mask errors, gateway mismatches, admin down interfaces, VLAN pruning/missing, and routing table omissions.
4. **Phase 4: Database & Backend Engine** (`backend/db.py`, `backend/diagnosis_engine.py`, `backend/server.py`)
   - Set up SQLite tables, diagnosis engine with schema validation, fallback provider, and REST API.
5. **Phase 5: Automated Testing Suite** (`backend/tests/`)
   - Write comprehensive unit and integration tests for rule checker, diagnosis parsing, review workflow, and dataset integrity.
6. **Phase 6: Frontend Experience** (`frontend/index.html`, `frontend/styles.css`, `frontend/app.js`)
   - Build responsive, professional Cisco-styled UI with Dashboard, Case Explorer, Diagnosis Studio, Verification Sandbox, and Responsible AI Log.
7. **Phase 7: Responsible AI Log & Documentation** (`docs/`, `README.md`)
   - Document 5+ realistic human-corrected AI cases, architecture, demo script, and final requirements audit.
8. **Phase 8: End-to-End Verification & Polish**
   - Run complete test suite, verify all endpoints, and ensure demo readiness.

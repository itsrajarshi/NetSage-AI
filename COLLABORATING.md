# Collaborating on NetSage AI

Welcome! Thank you for your interest in contributing to **NetSage AI** — an applied AI network troubleshooting platform designed for Cisco Packet Tracer and enterprise lab environments.

NetSage AI bridges the gap for junior network engineers by pairing deterministic rule checking with LLM-assisted reasoning, all governed by a mandatory **Human-in-the-Loop Review Gate**.

Whether you are adding new lab troubleshooting scenarios, refining rule validation heuristics, tuning AI prompts, or polishing the frontend dashboard, this guide provides the standards and workflows you need.

---

## 📜 Table of Contents

- [Code of Conduct & Ethics](#-code-of-conduct--ethics)
- [System Principles](#-system-principles)
- [Development Environment Setup](#-development-environment-setup)
- [Repository Architecture](#-repository-architecture)
- [How to Contribute](#-how-to-contribute)
  - [1. Adding or Enhancing Troubleshooting Cases](#1-adding-or-enhancing-troubleshooting-cases)
  - [2. Extending the Deterministic Rule Checker](#2-extending-the-deterministic-rule-checker)
  - [3. Prompt Engineering & AI Tuning](#3-prompt-engineering--ai-tuning)
  - [4. Frontend & User Experience](#4-frontend--user-experience)
  - [5. Responsible AI & Correction Logging](#5-responsible-ai--correction-logging)
- [Development Workflow & Git Standards](#-development-workflow--git-standards)
- [Testing & Quality Assurance](#-testing--quality-assurance)
- [Submitting a Pull Request](#-submitting-a-pull-request)
- [Questions & Support](#-questions--support)

---

## 🤝 Code of Conduct & Ethics

As a project combining **Artificial Intelligence** and **Critical Infrastructure (Networking)**, we adhere to strict ethical standards:

1. **Human Safety First**: Never implement features that bypass or weaken the human review gate. Autonomous application of unverified configuration commands to production-like topologies is strictly forbidden.
2. **Evidence-Grounded AI**: Never craft prompts or heuristics that encourage the model to hallucinate non-existent evidence or assume facts not present in show-command outputs.
3. **Respectful & Constructive Collaboration**: We maintain an inclusive, friendly, and harassment-free environment for all contributors regardless of experience level.

---

## 📐 System Principles

Before writing code, keep these core architectural tenets in mind:

- **Zero External Dependencies**: The backend runs purely on **Python 3.10+ standard library** (`http.server`, `sqlite3`, `json`, `re`, `ipaddress`, `urllib`). Do not introduce third-party libraries (e.g. `fastapi`, `flask`, `requests`, `numpy`) into the default runtime path.
- **Deterministic Rules Run First**: Before any LLM or heuristic model processes evidence, the deterministic Python rule engine (`backend/rule_checker.py`) analyzes configurations.
- **Fail Gracefully**: If LLM API keys (`OPENAI_API_KEY`, `GEMINI_API_KEY`) are missing, NetSage AI runs seamlessly using its offline heuristic reasoning engine.
- **Auditability**: Every AI inference and every human decision (`ACCEPTED`, `EDITED`, `REJECTED`) must be persisted and verifiable.

---

## 💻 Development Environment Setup

### Prerequisites

- **Python 3.10 or higher** (Python 3.12 recommended)
- **Git**
- A modern web browser (Google Chrome, Mozilla Firefox, Microsoft Edge, or Safari)

### 1. Clone the Repository

```bash
git clone https://github.com/itsrajarshi/NetSage-AI.git
cd NetSage-AI
```

### 2. Verify Standard Library Installation

No `pip install -r requirements.txt` is required! Verify your Python environment:

```bash
python --version
```

### 3. (Optional) Configure LLM Providers

NetSage AI defaults to an offline heuristic engine that requires zero API keys. To test with live frontier LLMs, export your API key:

**Linux / macOS:**
```bash
export OPENAI_API_KEY="sk-..."
# or
export GEMINI_API_KEY="AIza..."
```

**Windows PowerShell:**
```powershell
$env:OPENAI_API_KEY="sk-..."
# or
$env:GEMINI_API_KEY="AIza..."
```

### 4. Run the Application

```bash
python run.py
```

Open your browser at `http://localhost:8000` to interact with the dashboard.

---

## 🏛️ Repository Architecture

```
NetSage-AI/
├── backend/
│   ├── db.py                 # SQLite storage layer (cases, diagnoses, reviews, RAI)
│   ├── diagnosis_engine.py   # Hybrid AI engine (heuristic + OpenAI/Gemini)
│   ├── evaluate.py           # Batch evaluation against ground truth
│   ├── generate_cases.py     # Source generator for data/cases.csv
│   ├── rule_checker.py       # Pure-Python deterministic network rule checker
│   ├── seed_data.py          # Database seeding & initial evaluation run
│   ├── server.py             # HTTP REST API & static file server
│   ├── prompts/
│   │   ├── diagnose_prompt.md# Production prompt template & JSON schema
│   │   └── helper_prompts.md # Verification & Responsible AI prompts
│   └── tests/                # Automated unittest suite (25 tests)
├── data/
│   ├── cases.csv             # 39 curated troubleshooting cases
│   └── ai_evaluation.csv     # Evaluation results cache
├── docs/                     # Architectural, audit, and demo documentation
├── frontend/
│   ├── index.html            # Single-page interface layout
│   ├── styles.css            # Enterprise light/dark theme styles
│   └── app.js                # State management, API calls, and charts
├── run.py                    # Root entrypoint
├── README.md                 # Project README
└── COLLABORATING.md          # Contributor & collaboration guide
```

---

## 🛠️ How to Contribute

### 1. Adding or Enhancing Troubleshooting Cases

Troubleshooting cases reside in `data/cases.csv` and are programmatically generated via `backend/generate_cases.py`.

#### Case Schema

Every case must include the following fields:

| Field | Type | Description |
|---|---|---|
| `case_id` | String | Unique identifier (e.g. `VLAN-006`, `ROUT-006`) |
| `title` | String | Concise title describing the problem scenario |
| `concept` | String | One of: `VLAN`, `Gateway`, `DHCP`, `DNS`, `Routing`, `ACL`, `NAT`, `Wireless` |
| `osi_layer` | String | Primary OSI Layer (`Layer 1` to `Layer 7`) |
| `severity` | String | `CRITICAL`, `HIGH`, `MEDIUM`, or `LOW` |
| `topology_note` | String | Description of devices, interfaces, subnets, and hostnames |
| `symptom` | String | User-facing report (e.g. "Host A cannot ping Server B") |
| `show_outputs` | String | Verbatim Cisco IOS output (`show ip int brief`, `show run`, etc.) |
| `expected_fault`| String | Ground-truth root cause summary |
| `next_command` | String | Recommended Cisco diagnostic command |
| `expected_fix` | String | Exact Cisco configuration command(s) resolving the issue |

#### Workflow for Adding Cases:
1. Open `backend/generate_cases.py`.
2. Add your scenario under the relevant domain list with realistic Cisco IOS outputs.
3. Run `python backend/generate_cases.py` to regenerate `data/cases.csv`.
4. Re-run `python backend/seed_data.py` to update `netsage.db`.
5. Run the test suite: `python -m unittest discover -s backend/tests -p "test_*.py"`.

---

### 2. Extending the Deterministic Rule Checker

The deterministic engine (`backend/rule_checker.py`) performs rule-based parsing on `show_outputs`. It catches issues like:
- Duplicate IP assignments
- Mismatched subnet masks & host range containment
- Subinterfaces with mismatched 802.1Q tags
- Missing default gateways or static routes
- Administratively shut interfaces
- Missing DHCP helper addresses (`ip helper-address`)
- ACLs blocking required protocols (e.g., UDP 53 for DNS)
- NAT pools missing overload keywords

#### How to Add a Rule Check:
1. Define a private check method in `NetworkRuleChecker`:
   ```python
   def _check_custom_pattern(self, symptom: str, topology: str, show_outputs: str) -> List[Dict[str, Any]]:
       findings = []
       # Parse configuration using regex and ipaddress
       ...
       findings.append({
           "rule_id": "RULE-CUSTOM-001",
           "status": "FAIL",  # or "WARNING", "INFO"
           "title": "Clear description of violation",
           "evidence": "Quoted line from show command",
           "recommendation": "Remediation command"
       })
       return findings
   ```
2. Call your method inside `run_all_checks()`.
3. Add a unit test in `backend/tests/test_rule_checker.py`.
4. Ensure 100% of existing test cases pass without regressions.

---

### 3. Prompt Engineering & AI Tuning

The prompt definition lives in `backend/prompts/diagnose_prompt.md`.

#### Rules for Prompt Adjustments:
- **Strict JSON Enforcement**: The AI must return a valid JSON object matching the contract:
  ```json
  {
    "root_cause": "Concise summary",
    "confidence": 0.85,
    "evidence": "Quoted string directly from show output",
    "next_command": "Recommended Cisco show command",
    "fix_steps": "Exact configuration remediation lines",
    "osi_layer": "Layer X",
    "concept": "Domain"
  }
  ```
- **Anti-Hallucination Directives**: Always enforce that the model quotes evidence from the provided command output rather than inventing details.
- **Few-Shot Quality**: When adjusting few-shot examples, use realistic Cisco Packet Tracer scenarios.

---

### 4. Frontend & User Experience

NetSage AI features an enterprise single-page interface built with **HTML5, Vanilla CSS, and Modern Vanilla JavaScript**:
- Located in `frontend/index.html`, `frontend/styles.css`, and `frontend/app.js`.
- **No external JavaScript frameworks** (no React, Vue, or Angular build steps needed).
- Follow clean semantic HTML, accessible contrast ratios, and responsive UI design.
- Test UI changes across desktop and mobile screen viewports.

---

### 5. Responsible AI & Correction Logging

NetSage AI embraces human-in-the-loop validation:
- When AI recommendations deviate from ground truth, they must be reviewed and categorized (`MATCH` -> `ACCEPTED`, `PARTIAL` -> `EDITED`, `MISMATCH` -> `REJECTED`).
- Any newly discovered edge cases or AI failure patterns should be documented in [`docs/RESPONSIBLE_AI.md`](docs/RESPONSIBLE_AI.md).
- Never remove human correction logging for the sake of artificial "100% agreement" metrics. Transparency is a core deliverable.

---

## 🔀 Development Workflow & Git Standards

### Branching Strategy

- `main`: Production-ready, stable codebase.
- Feature branches: `feat/<feature-name>` (e.g. `feat/bgp-domain-support`)
- Bugfix branches: `fix/<bug-description>` (e.g. `fix/dhcp-pool-regex`)
- Documentation: `docs/<topic>` (e.g. `docs/api-guide`)

### Commit Conventions

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

- `feat:` A new feature or capability
- `fix:` A bug fix or regex correction
- `docs:` Documentation additions or edits
- `test:` Adding or updating unit tests
- `refactor:` Code reorganization without behavioral change
- `perf:` Performance optimizations

**Example:**
```bash
git commit -m "feat(rule-checker): add trunk native vlan mismatch detection"
```

---

## 🧪 Testing & Quality Assurance

Before submitting any code, execute the test suite:

```bash
python -m unittest discover -s backend/tests -p "test_*.py"
```

All **25 tests** must pass:
```text
.........................
----------------------------------------------------------------------
Ran 25 tests in 2.9s

OK
```

### Running Batch AI Evaluation

To verify that the offline heuristic and rule checker still achieve expected accuracy benchmarks across all 39 cases:

```bash
python backend/evaluate.py
```

Expected baseline:
- **Concept Accuracy**: ≥ 89.0%
- **OSI-Layer Accuracy**: ≥ 87.0%
- **Exact Agreement Rate**: ≥ 79.0%

---

## 🚀 Submitting a Pull Request

1. **Push your branch** to your fork or origin:
   ```bash
   git push origin feat/your-feature-name
   ```
2. **Open a Pull Request** against `main`.
3. **Fill out the PR description**:
   - What problem does this PR solve?
   - What changes were made?
   - Test output / proof of passing tests.
   - Any updates made to documentation or cases.
4. **Code Review**: At least one maintainer review is required before merging.

---

## 💬 Questions & Support

- Open an issue on GitHub for bugs, feature ideas, or case suggestions.
- Review existing architecture in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).
- Review compliance guidelines in [`docs/CISCO_REQUIREMENTS_AUDIT.md`](docs/CISCO_REQUIREMENTS_AUDIT.md).

Thank you for helping make NetSage AI the gold standard for reliable, responsible AI network troubleshooting!

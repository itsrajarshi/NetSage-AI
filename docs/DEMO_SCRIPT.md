# NetSage AI — 5–10 Minute Demo Script & Presentation Walkthrough
**Cisco Applied AI + Network Troubleshooting Internship Project**

---

## Presentation Overview & Objectives
- **Target Duration**: 5 to 8 minutes
- **Key Message**: NetSage AI empowers network engineers to quickly identify root causes in Cisco Packet Tracer topologies using deterministic rule checks and structured AI diagnosis, while maintaining strict human-in-the-loop oversight.

---

## Step-by-Step Live Demo Flow

### 1. Introduction & Executive Dashboard (1.5 Minutes)
- **Action**: Open `http://localhost:8000`.
- **Narrative**:
  > *"Welcome to NetSage AI. Junior network engineers frequently struggle to connect high-level symptoms to specific root causes across VLANs, Routing, ACLs, and NAT. NetSage AI provides an evidence-backed troubleshooting assistant with mandatory human review."*
- **Key UI Elements to Highlight**:
  - **KPI Metrics**: 39 curated troubleshooting cases across 8 core domains.
  - **Concept Distribution**: Balanced coverage across VLAN, Gateway, DHCP, DNS, Routing, ACL, NAT, Wireless.
  - **AI vs. Human Agreement & Responsible AI Count**: 5 audited corrections logged.

---

### 2. Case Explorer & Evidence Inspection (1.5 Minutes)
- **Action**: Click on **"Case Explorer"** in the sidebar.
- **Narrative**:
  > *"The Case Explorer indexes real Packet Tracer troubleshooting scenarios. Let's filter by Concept 'VLAN' and inspect case `VLAN-001`."*
- **Walkthrough**:
  - Show the **Symptom** (*"PC-1 in Sales cannot ping PC-2 in Sales across the core trunk"*).
  - Show the **Network Topology** notes.
  - Show the actual Cisco IOS `show interfaces trunk` output.
  - Click **"Diagnose in Studio"**.

---

### 3. Diagnosis Studio & Deterministic Rule Checking (2 Minutes)
- **Action**: In **"Diagnosis Studio"**, click **"Execute Diagnosis Pipeline"**.
- **Narrative**:
  > *"Notice the multi-stage pipeline. First, the Deterministic Rule Checker runs pure-Python validation and immediately flags that VLAN 10 is missing from the allowed VLAN list (`1-9,11-4094`). Then, the AI synthesis model generates a strict JSON recommendation with quoted evidence and actionable fix steps."*
- **Key UI Elements to Highlight**:
  - **Probable Root Cause**: Detailed explanation of trunk pruning.
  - **Evidence Quote Box**: Direct citation from `show interfaces trunk`.
  - **OSI Layer & Next Command**: Layer 2 / `show interfaces Fa0/24 switchport`.
  - **Remediation Commands**: `switchport trunk allowed vlan add 10`.

---

### 4. Mandatory Human Review Gate (1.5 Minutes)
- **Action**: Scroll to the **"MANDATORY HUMAN REVIEW GATE"** at the bottom of Diagnosis Studio.
- **Narrative**:
  > *"Crucially, the system will NEVER apply AI changes automatically. A human engineer must review and approve. We have three options: ACCEPT, EDIT, or REJECT. For this case, the analysis is 100% accurate, so we enter our reviewer rationale and click [ACCEPT AI DIAGNOSIS]."*
- **Action**: Type *"Verified trunk allowed list pruning"* and click **[ACCEPT AI DIAGNOSIS]**.
- **Result**: Instant update to review history and dashboard metrics.

---

### 5. Closed-Loop Lab Verification Simulator (1.5 Minutes)
- **Action**: Navigate to **"Lab Verifier"**.
- **Narrative**:
  > *"Once approved, we simulate applying the configuration fix to the Packet Tracer lab. Let's enter the corrective command: `switchport trunk allowed vlan add 10` and click [Apply Fix & Verify]."*
- **Action**: Click **"Apply Fix & Verify"**.
- **Result**:
  - Displays simulated post-remediation show output: `Ping results: 5/5 packets received (0% loss, 1ms RTT). Interface state: UP/UP. 0 rule violations.`

---

### 6. Responsible AI Log & Conclusion (1 Minute)
- **Action**: Click on **"Responsible AI Log"**.
- **Narrative**:
  > *"Finally, we review the Responsible AI Registry. Here we document 5 critical cases where human engineers caught AI errors—such as distinguishing Layer 4 ACL drops from Layer 3 server outages, or catching inverted subnet masks in standard ACLs. This ensures continuous safety and model improvement."*
- **Conclusion**:
  > *"NetSage AI fulfills every Cisco requirement: 30+ cases, prompt library, deterministic rule checker, interactive dashboard, human review gate, and closed-loop verification."*

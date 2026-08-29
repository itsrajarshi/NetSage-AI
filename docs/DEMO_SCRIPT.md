# NetSage AI — 5–10 Minute Demo Script

**Cisco Applied AI + Network Troubleshooting Internship Project**

Target length: **6–8 minutes.** Record at 1280×720 or larger.

> **Before recording:** if you have an OpenAI or Gemini key, run
> `export OPENAI_API_KEY=...` (or `GEMINI_API_KEY`) before `python run.py` so the
> diagnosis goes through a real model. Without a key it runs the offline heuristic
> engine, which is fine to show but weaker for an "Applied AI" demo. Either way,
> re-run `python backend/seed_data.py` once so the dashboard numbers are fresh.

---

## 0. Setup (off-camera)

```bash
python run.py          # seeds the DB, runs the batch evaluation, serves :8000
```
Open `http://localhost:8000`.

---

## 1. Problem + dashboard  (~1.5 min)

> *"Junior network engineers know the commands but struggle to connect a symptom
> to the root cause — is a PC that can't reach a server a VLAN, routing, DHCP, DNS,
> ACL or NAT problem? NetSage AI reads the symptom and the show output, proposes a
> diagnosis, and requires a human to sign off before anything is applied."*

Point at the KPI row:
- **39** lab cases across 8 domains (VLAN, Gateway, DHCP, DNS, Routing, ACL, NAT, Wireless).
- **AI diagnostic accuracy 89.7%** — the engine was run against all 39 known answers.
- **AI / human agreement 79.5%** — 31 of 39 diagnoses were accepted as-is.
- **8 corrections logged** — the cases a human had to edit or reject.

Scroll to the **Domain Coverage** and **Human Oversight Decisions** charts.

---

## 2. Case Explorer — the evidence  (~1 min)

Sidebar → **Case Explorer** → filter Concept = **VLAN** → click **VLAN-001**.

Show, in order: the **symptom**, the **topology note**, the real
`show interfaces trunk` output (VLAN 10 missing from `1-9,11-4094`), and the
**ground-truth fault + fix** at the bottom. Click **Diagnose in Studio**.

---

## 3. Diagnosis Studio — pipeline + rule checker  (~2 min)

The Studio opens in **standby**. Click **Execute Complete Diagnosis Pipeline** and
narrate the six steps as they light up:

> *"Evidence is ingested, then the deterministic Python rule checker runs first —
> no model involved — and flags the pruned trunk allowed-VLAN list. Those findings
> are handed to the AI, which returns a strict-JSON diagnosis that has to quote a
> real line from the show output as its evidence. The last step is the human gate."*

Highlight: **Probable Root Cause**, the **evidence quote** (a verbatim show-output
line), **confidence gauge**, **next command**, and the numbered **fix steps**.

---

## 4. Mandatory human review gate  (~1.5 min)

Scroll to **Mandatory Human Review Required**.

> *"Nothing is applied automatically. The reviewer picks ACCEPT, EDIT or REJECT.
> For VLAN-001 the diagnosis is correct, so I add a note and ACCEPT."*

Type *"Verified trunk allowed-VLAN list; VLAN 10 confirmed missing"* → **ACCEPT & VERIFY**.
The gate flips to **HUMAN APPROVED** and the verifier unlocks.

**Then show a case the AI got wrong.** Switch the case dropdown to **DNS-002**,
run the pipeline:

> *"Here the engine calls it an ACL problem at Layer 4. It's not wrong that an ACL
> is involved — but the incident is a DNS-resolution failure, so a human reviewer
> EDITs it, records the correct classification, and that edit becomes an entry in
> the Responsible AI log."*

Click **EDIT & OVERRIDE**, adjust the text, submit.

---

## 5. Closed-loop lab verifier  (~1 min)

Sidebar → **Lab Verifier** → case **VLAN-001** → the fix
`switchport trunk allowed vlan add 10` is pre-filled → **Apply Fix & Verify Network**.

Show the simulated post-fix output: `5/5 packets received`, interfaces `UP/UP`,
`0 rule violations`. Point out that verification was **blocked** until the human
review existed.

---

## 6. Responsible AI log + close  (~1 min)

Sidebar → **Responsible AI Log**.

> *"These 8 rows aren't written by hand — they're generated from the batch run.
> Every case where the AI's concept or OSI-layer classification disagreed with the
> known answer is logged with what it predicted, what the human corrected it to,
> and the lesson. For example GW-002: the AI saw the dot1Q tag and called it a
> switching problem, when it's actually an inter-VLAN routing fault."*

Close:

> *"NetSage AI covers every deliverable — 39 cases, the prompt library, a
> deterministic checker that fires on all of them, the batch AI evaluation against
> known answers, a full human-review log with accepts, edits and rejects, and the
> closed-loop verifier — with a human in the loop at every step."*

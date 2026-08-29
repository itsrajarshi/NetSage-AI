# NetSage AI — Responsible AI & Human Oversight

**Cisco Applied AI + Network Troubleshooting Internship Project**

---

## 1. Responsible AI principles

Applying an incorrect configuration change on the strength of unverified AI output can
cause outages, security holes, or routing loops. NetSage AI is built around four
guardrails:

1. **Mandatory human-in-the-loop gate.** No AI recommendation can be applied or
   "verified" until a human engineer records `ACCEPTED`, `EDITED`, or `REJECTED`.
   The gate is enforced server-side (`backend/server.py` `/api/verify`) and covered
   by an integration test.
2. **Evidence-grounded output.** The prompt (`backend/prompts/diagnose_prompt.md`)
   forces the model to quote real show-command lines as `evidence` and forbids
   inventing configuration that is not in the capture.
3. **Deterministic pre-flight checks.** `backend/rule_checker.py` runs first and
   catches structural errors (duplicate IP, mask/gateway, interface down, missing
   VLAN, missing route, ACL/NAT, DHCP/DNS, wireless) without any model — it fires on
   all 39 dataset cases.
4. **Transparent audit logging.** Every case the AI got wrong is logged with the
   predicted answer, the corrected answer, and the lesson.

---

## 2. How the correction log is produced

The corrections below are **not hand-authored** — they come from an actual batch
run. `backend/evaluate.py` feeds every one of the 39 cases to the offline diagnosis
engine (`backend/diagnosis_engine.py`, which reasons only from the symptom, the show
output, and the deterministic findings — it never reads the answer key) and compares
the predicted `concept` and `osi_layer` with the ground truth in `cases.csv`:

| Verdict | Meaning | Human review decision |
|---|---|---|
| MATCH | concept **and** OSI layer correct | `ACCEPTED` |
| PARTIAL | one of the two correct | `EDITED` (corrected to ground truth) |
| MISMATCH | neither correct | `REJECTED` |

Latest run (`docs/AI_EVALUATION.md`, regenerated on every seed):

| Metric | Value |
|---|---|
| Cases evaluated | 39 |
| Exact match | 31 (79.5%) |
| Partial | 7 |
| Mismatch | 1 |
| Concept accuracy | 89.7% |
| OSI-layer accuracy | 87.2% |
| **AI / human agreement rate** | **79.5%** (31 ACCEPTED / 39) |

---

## 3. The 8 logged corrections

| Case | AI predicted | Ground truth | What the human fixed |
|---|---|---|---|
| **GW-002** | VLAN / L2 — "dot1Q tag 300 ≠ VLAN 30" | Gateway / L3 | Right observation, wrong classification: an inter-VLAN routing (router-on-a-stick) fault, not a switching fault. |
| **ACL-002** | ACL / L4 | ACL / L3 | Domain correct; the reviewer placed a "blocks *all* traffic" ACL fault at L3, not L4. |
| **DHCP-003** | Gateway / L3 — "duplicate IP on Gi0/0" | DHCP / L3 | The duplicate IP is a *symptom*; root cause is a missing `ip dhcp excluded-address` for the gateway. |
| **DHCP-005** | DNS / L7 — "client has no DNS server" | DHCP / L7 | The `dns-server` option is missing **from the DHCP pool** — a DHCP config fault, not a DNS one. |
| **DNS-002** | ACL / L4 — "ACL denies UDP/53" | DNS / L4 | Layer correct; the reviewer files it under DNS (name-resolution reachability) with the ACL as the mechanism. |
| **GW-004** | Gateway / L3 — "Gi0/0 shut down" | Gateway / L1 | Correct fault, wrong layer: an administratively-down interface is a physical/L1 problem. |
| **WLAN-003** | Wireless / L2 — "AP stuck in CAPWAP discovery" | Wireless / L7 | Correct fault; CAPWAP controller discovery is an application-layer process, not L2. |
| **WLAN-004** | Wireless / L2 — "radio interface shut down" | Wireless / L1 | Correct fault, wrong layer: a disabled radio is L1. |

### Detailed walkthroughs

#### GW-002 — dot1Q tag observed, domain misclassified

- **Show evidence**
  ```text
  R1# show running-config interface g0/0.30
  interface GigabitEthernet0/0.30
   encapsulation dot1Q 300
   ip address 192.168.30.1 255.255.255.0
  ```
- **AI said:** `VLAN / Layer 2` — "the dot1Q tag (300) does not match the VLAN the
  subinterface serves (30)".
- **Human corrected to:** `Gateway / Layer 3` — the subinterface *is* the VLAN 30
  default gateway; a wrong `encapsulation dot1Q` breaks inter-VLAN **routing**, so
  this is triaged as a gateway/L3 fault even though the trigger is an 802.1Q tag.
- **Decision:** `EDITED`.
- **Lesson:** the presence of an L2 keyword (`dot1Q`, `trunk`, `vlan`) does not make
  the fault an L2 problem — classify by what actually fails for the user.

#### DNS-002 — right layer, wrong domain

- **Show evidence**
  ```text
  R1# show access-lists 101
      10 deny udp any host 10.50.1.10 eq domain (245 matches)
      20 permit ip any any (1420 matches)
  ```
- **AI said:** `ACL / Layer 4` — "an access-list entry explicitly denies UDP/53".
- **Human corrected to:** `DNS / Layer 4` — the mechanism is an ACL, but the incident
  is a name-resolution failure; the reviewer classifies it as DNS so it groups with
  the other resolution incidents, and notes the ACE as the cause.
- **Decision:** `EDITED`.
- **Lesson:** a filtered UDP/53 is not a DNS server outage — separate the service
  from the transport carrying it.

#### DHCP-005 — plausible but wrong domain

- **Show evidence**
  ```text
  PC-1> ipconfig /all
     DNS Servers . . . : 0.0.0.0
  R1# show running-config | section ip dhcp pool
  ip dhcp pool CORP_USERS
     network 10.10.100.0 255.255.255.0
     default-router 10.10.100.1
  ```
- **AI said:** `DNS / Layer 7` — "the client has no DNS server (0.0.0.0)".
- **Human corrected to:** `DHCP / Layer 7` — the client is missing DNS *because the
  DHCP pool has no `dns-server` line*. The fix is on the router's DHCP pool, not
  anything DNS.
- **Decision:** `EDITED`.
- **Lesson:** trace a missing client parameter back to whoever should have supplied
  it (here, DHCP) before naming the domain.

---

## 4. Where to see this in the product

- **Dashboard → Responsible AI Log** renders the 8 rows above from the
  `responsible_ai_log` table.
- **Dashboard KPIs** show the agreement rate and AI accuracy from the same run.
- **`docs/AI_EVALUATION.md`** / **`data/ai_evaluation.csv`** — the full 39-row
  per-case comparison, regenerated on every `python backend/seed_data.py`.

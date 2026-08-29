# NetSage AI — Responsible AI & Human Oversight Specification
**Cisco Applied AI + Network Troubleshooting Internship Project**

---

## 1. Responsible AI Principles & Philosophy

In enterprise network engineering, applying incorrect configuration changes based on unverified AI output can cause critical outages, security breaches, or network-wide routing loops.

NetSage AI is engineered around four core Responsible AI pillars:

1. **Mandatory Human-in-the-Loop Gate**: The system strictly prohibits auto-applying AI-suggested commands. Every recommendation must be reviewed by a human engineer ([ACCEPT], [EDIT], [REJECT]).
2. **Evidence-Grounded Recommendations**: The AI is constrained by strict prompting to quote actual show-command text (`evidence`). Hallucinating evidence that does not exist in the output is penalized.
3. **Deterministic Pre-flight Verification**: Pure-Python rule checking runs before/alongside the LLM, eliminating reliance on probabilistic models for mathematical IP/subnet and syntax validation.
4. **Transparent Audit Logging**: All cases where human engineers correct or reject AI output are logged permanently to study failure patterns and refine prompt constraints.

---

## 2. Documented Responsible AI Correction Cases (5 Mandatory Scenarios)

The following 5 cases demonstrate real-world scenarios where the AI proposed an inaccurate or incomplete diagnosis, and human engineers intervened with corrective oversight.

---

### Case 1: DNS-002 — Layer 3 Reachability Assumption vs. Layer 4 Extended ACL Deny

- **Symptom**: Internal server `intranet.corp.local` cannot be resolved by hostname; `nslookup` times out to corporate DNS server `10.50.1.10`.
- **Show Command Evidence**:
  ```text
  R1# show access-lists 101
  Extended IP access list 101
      10 deny udp any host 10.50.1.10 eq domain (245 matches)
      20 permit ip any any (1420 matches)
  ```
- **Initial AI Diagnosis**: *"DNS server 10.50.1.10 is offline or the routing table is missing a route to the 10.50.1.0/24 subnet."*
- **Failure Mode**: The AI jumped to a high-level server outage hypothesis without inspecting the ACL packet drop counters (`245 matches` on `deny udp ... eq domain`).
- **Human Expert Correction**:
  - **Decision**: `EDITED`
  - **Corrected Diagnosis**: *"Extended ACL 101 line 10 explicitly drops UDP port 53 (DNS) traffic destined to 10.50.1.10."*
  - **Corrected Fix**: `R1(config)# no access-list 101 deny udp any host 10.50.1.10 eq domain`
- **Engineering Lesson**: Always inspect Layer 4 access-lists and match counters before assuming Layer 3 routing or hardware outages.

---

### Case 2: ACL-002 — Inverted Subnet Mask vs. Cisco Wildcard Mask

- **Symptom**: All host traffic on VLAN 10 is blocked immediately upon applying standard access-list 10.
- **Show Command Evidence**:
  ```text
  R1# show access-lists 10
  Standard IP access list 10
      10 permit 192.168.10.0 255.255.255.0 (0 matches)
  ```
- **Initial AI Diagnosis**: *"Interface GigabitEthernet0/0 is experiencing physical link degradation or cable fault."*
- **Failure Mode**: The AI failed to recognize that Cisco standard ACL syntax requires inverse wildcard masks (`0.0.0.255`). A mask of `255.255.255.0` matches 0 host packets, causing all traffic to hit the implicit deny all.
- **Human Expert Correction**:
  - **Decision**: `EDITED`
  - **Corrected Diagnosis**: *"Standard ACL 10 is misconfigured with subnet mask 255.255.255.0 instead of wildcard mask 0.0.0.255."*
  - **Corrected Fix**: `R1(config)# no access-list 10` followed by `R1(config)# access-list 10 permit 192.168.10.0 0.0.0.255`
- **Engineering Lesson**: Enforce deterministic rule checking to catch inverted mask syntax before applying firewall filters.

---

### Case 3: WLAN-002 — Security Policy Hallucination vs. SSID-to-VLAN Mapping

- **Symptom**: Guest Wi-Fi users can access internal ERP server `192.168.10.50`, violating guest isolation security policies.
- **Show Command Evidence**:
  ```text
  AP-1# show running-config | section dot11
  dot11 ssid Company-Guest
     vlan 10
     authentication open
  ```
- **Initial AI Diagnosis**: *"Internal ERP server has an invalid gateway or compromised SSL certificate."*
- **Failure Mode**: The AI hallucinated a server certificate failure while ignoring the Layer 2 SSID-to-VLAN mapping on the wireless access point.
- **Human Expert Correction**:
  - **Decision**: `REJECTED`
  - **Corrected Diagnosis**: *"Guest SSID 'Company-Guest' is mapped to internal corporate VLAN 10 instead of isolated Guest VLAN 99."*
  - **Corrected Fix**: `AP-1(config-ssid)# vlan 99`
- **Engineering Lesson**: In multi-SSID wireless deployments, always verify that untrusted SSIDs map to dedicated guest VLANs and subnets.

---

### Case 4: DHCP-001 — Assumed Daemon Failure vs. Missing Relay Agent (IP Helper)

- **Symptom**: New clients in VLAN 20 receive `169.254.x.x` APIPA addresses; static IP assignment works normally.
- **Show Command Evidence**:
  ```text
  R1# show running-config interface g0/0.20
  interface GigabitEthernet0/0.20
   encapsulation dot1Q 20
   ip address 192.168.20.1 255.255.255.0
  ! (Missing ip helper-address)
  ```
- **Initial AI Diagnosis**: *"Central DHCP server 10.10.10.5 is stopped, offline, or out of memory."*
- **Failure Mode**: The AI assumed the remote server failed rather than noticing that router R1 was dropping client Layer 2 DHCP broadcast Discover packets without forwarding them as unicast.
- **Human Expert Correction**:
  - **Decision**: `EDITED`
  - **Corrected Diagnosis**: *"Missing 'ip helper-address 10.10.10.5' configuration on router subinterface GigabitEthernet0/0.20."*
  - **Corrected Fix**: `R1(config-subif)# ip helper-address 10.10.10.5`
- **Engineering Lesson**: Across routed inter-VLAN boundaries, verify DHCP Relay Agent configuration before suspecting remote server failure.

---

### Case 5: NAT-004 — Bandwidth Throttle Hallucination vs. Missing PAT Overload Keyword

- **Symptom**: Only one internal user can browse the internet at a time; subsequent connections from other PCs fail until the first closes.
- **Show Command Evidence**:
  ```text
  R1# show running-config | include ip nat
  ip nat inside source list 1 interface GigabitEthernet0/1
  ```
- **Initial AI Diagnosis**: *"ISP connection bandwidth is saturated, causing connection timeouts for secondary clients."*
- **Failure Mode**: The AI misdiagnosed network congestion when the actual fault was static 1-to-1 dynamic NAT locking to the single public IP on G0/1.
- **Human Expert Correction**:
  - **Decision**: `EDITED`
  - **Corrected Diagnosis**: *"NAT statement is missing the 'overload' keyword, disabling Port Address Translation (PAT)."*
  - **Corrected Fix**: `R1(config)# ip nat inside source list 1 interface GigabitEthernet0/1 overload`
- **Engineering Lesson**: Dynamic multi-host sharing of a single public interface requires PAT (`overload`) to map multiple internal hosts to unique Layer 4 port numbers.

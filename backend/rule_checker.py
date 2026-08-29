"""
NetSage AI - Deterministic Network Rule Checker

Pure-Python, offline, deterministic engine that inspects Cisco IOS show-command
output for common configuration mistakes *before or after* AI diagnosis, exactly
as required by the project brief:

    "Use Python to check duplicate IPs, wrong masks, gateway mismatch,
     interface down, missing VLAN, and missing routes before or after
     AI diagnosis."

Checks are grouped by domain. Each returns a list of RuleFinding objects with a
status of PASS / WARNING / FAIL so the diagnosis engine and the dashboard can
weight the evidence.
"""

import re
import ipaddress
from typing import List, Dict, Any, Optional


class RuleFinding:
    def __init__(self, rule: str, status: str, severity: str, evidence: str, explanation: str):
        self.rule = rule
        self.status = status          # PASS | WARNING | FAIL
        self.severity = severity      # CRITICAL | HIGH | MEDIUM | LOW | INFO
        self.evidence = evidence
        self.explanation = explanation

    def to_dict(self) -> Dict[str, str]:
        return {
            "rule": self.rule,
            "status": self.status,
            "severity": self.severity,
            "evidence": self.evidence,
            "explanation": self.explanation,
        }


def _first_line_matching(text: str, *needles: str) -> str:
    for line in text.splitlines():
        low = line.lower()
        if any(n.lower() in low for n in needles):
            return line.strip()
    return ""


class NetworkRuleChecker:
    def run_all_checks(self, symptom: str, topology_note: str, show_outputs: str) -> List[Dict[str, str]]:
        findings: List[RuleFinding] = []
        combined = f"{symptom}\n{topology_note}\n{show_outputs}"

        findings += self.check_interface_down(show_outputs)
        findings += self.check_duplicate_ips(combined, show_outputs)
        findings += self.check_subnet_and_gateway(combined, show_outputs)
        findings += self.check_vlan_issues(show_outputs, symptom)
        findings += self.check_routing_issues(show_outputs)
        findings += self.check_acl_and_nat(show_outputs, symptom)
        findings += self.check_dhcp_and_dns(show_outputs, symptom)
        findings += self.check_wireless(show_outputs, symptom)

        # De-duplicate on (rule, evidence)
        seen = set()
        unique: List[RuleFinding] = []
        for f in findings:
            key = (f.rule, f.evidence[:80])
            if key in seen:
                continue
            seen.add(key)
            unique.append(f)

        if not unique:
            unique.append(RuleFinding(
                rule="Baseline Health Assessment",
                status="PASS",
                severity="INFO",
                evidence="All deterministic pattern audits completed without a rule violation.",
                explanation="No interface shutdown, duplicate IP, mask/gateway, VLAN, routing, "
                            "ACL/NAT, DHCP/DNS or wireless anomaly matched the supplied show output. "
                            "The fault may require evidence not present in these captures.",
            ))

        # FAIL first, then WARNING, then PASS; CRITICAL/HIGH before others
        sev_rank = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
        status_rank = {"FAIL": 0, "WARNING": 1, "PASS": 2}
        unique.sort(key=lambda f: (status_rank.get(f.status, 3), sev_rank.get(f.severity, 5)))
        return [f.to_dict() for f in unique]

    # ------------------------------------------------------------------ #
    # 1. Interface / physical state
    # ------------------------------------------------------------------ #
    def check_interface_down(self, show_outputs: str) -> List[RuleFinding]:
        findings: List[RuleFinding] = []

        _IFACE = (r'(?:GigabitEthernet|FastEthernet|TenGigabitEthernet|Ethernet|Serial|'
                  r'Dot11Radio|Loopback|Vlan|Tunnel|Port-channel|Gi|Fa|Te|Se|Eth)[0-9][0-9/._-]*')
        for iface in re.findall(rf'({_IFACE})[^\n]*?administratively down', show_outputs, re.IGNORECASE):
            if iface.lower().startswith("dot11radio"):
                continue  # reported by the dedicated wireless-radio check below
            findings.append(RuleFinding(
                "Interface Administrative State", "FAIL", "CRITICAL",
                f"Interface {iface} is reported as 'administratively down'.",
                f"{iface} has been shut down in configuration and cannot pass traffic until "
                f"'no shutdown' is issued.",
            ))

        for iface, vlan in re.findall(
                r'Name:\s*([A-Za-z0-9/._-]+).*?Access Mode VLAN:\s*(\d+)\s*\(inactive\)',
                show_outputs, re.IGNORECASE | re.DOTALL):
            findings.append(RuleFinding(
                "Inactive Access VLAN State", "FAIL", "HIGH",
                f"Port {iface} is assigned to VLAN {vlan} which is '(inactive)'.",
                f"VLAN {vlan} does not exist in the switch VLAN database, so port {iface} stays "
                f"operationally down.",
            ))

        if re.search(r'Dot11Radio\d+\s+is\s+administratively down', show_outputs, re.IGNORECASE):
            findings.append(RuleFinding(
                "Wireless Radio Operational State", "FAIL", "HIGH",
                _first_line_matching(show_outputs, "Dot11Radio") or "Dot11Radio interface administratively down.",
                "A wireless radio interface is shut down, preventing client RF association on that band.",
            ))

        # line protocol down while the interface is 'up' (L1/cabling / speed-duplex)
        for iface in re.findall(r'([A-Za-z][A-Za-z0-9/._-]*) is up, line protocol is down',
                                show_outputs, re.IGNORECASE):
            findings.append(RuleFinding(
                "Interface Line Protocol", "FAIL", "HIGH",
                f"{iface} is up / line protocol is down.",
                f"Layer 1 is present on {iface} but Layer 2 keepalives fail - check cabling, "
                f"encapsulation, or speed/duplex.",
            ))
        return findings

    # ------------------------------------------------------------------ #
    # 2. Duplicate addressing
    # ------------------------------------------------------------------ #
    def check_duplicate_ips(self, combined_text: str, show_outputs: str) -> List[RuleFinding]:
        findings: List[RuleFinding] = []
        search = f"{combined_text}\n{show_outputs}"

        m = re.search(
            r'%(?:IP-4-DUPADDR|SYS-3-IP_DUP):\s*Duplicate (?:address|IP address)\s+'
            r'([0-9.]+)\s+on\s+([A-Za-z0-9/._-]+)',
            search, re.IGNORECASE)
        if m:
            findings.append(RuleFinding(
                "Duplicate IP Address Detection", "FAIL", "CRITICAL",
                m.group(0).strip(),
                f"IOS reports a duplicate IP ({m.group(1)}) on {m.group(2)}. Two devices claim the "
                f"same address, causing ARP instability and intermittent loss.",
            ))

        # show ip arp listing the same IP twice with different MACs
        arp_ips = re.findall(r'Internet\s+([0-9.]+)\s+\S+\s+([0-9a-fA-F.]{14})', show_outputs)
        dupes = {ip for ip, _ in arp_ips if [i for i, _ in arp_ips].count(ip) > 1}
        for ip in dupes:
            findings.append(RuleFinding(
                "ARP Table Duplicate Entry", "FAIL", "CRITICAL",
                f"IP {ip} appears in the ARP table with more than one MAC address.",
                f"Address {ip} is claimed by two MACs - a static host has been given the gateway/"
                f"another host's IP.",
            ))
        return findings

    # ------------------------------------------------------------------ #
    # 3. Subnet mask / default gateway / L3 edge
    # ------------------------------------------------------------------ #
    def check_subnet_and_gateway(self, combined_text: str, show_outputs: str) -> List[RuleFinding]:
        findings: List[RuleFinding] = []
        text = f"{combined_text}\n{show_outputs}"

        host_ip = re.search(
            r'(?:Autoconfiguration IPv4 Address|IPv4 Address|IP Address)[.\s:]*'
            r'([0-9]{1,3}(?:\.[0-9]{1,3}){3})', text, re.IGNORECASE)
        mask = re.search(r'Subnet Mask[.\s:]*([0-9]{1,3}(?:\.[0-9]{1,3}){3})', text, re.IGNORECASE)
        gw = re.search(r'Default Gateway[.\s:]*([0-9]{1,3}(?:\.[0-9]{1,3}){3})', text, re.IGNORECASE)

        # APIPA - DHCP failure
        apipa = re.search(r'\b(169\.254\.\d{1,3}\.\d{1,3})\b', text)
        if apipa:
            findings.append(RuleFinding(
                "APIPA Address Allocation", "FAIL", "HIGH",
                f"Host holds an APIPA link-local address {apipa.group(1)}.",
                "A 169.254.x.x address means the client never received a DHCP reply - the DHCP "
                "server is down or, across a routed boundary, 'ip helper-address' is missing.",
            ))

        if host_ip and gw:
            hip, gip = host_ip.group(1), gw.group(1)
            mstr = mask.group(1) if mask else "255.255.255.0"

            if gip == "0.0.0.0":
                findings.append(RuleFinding(
                    "Default Gateway Assignment", "FAIL", "HIGH",
                    f"Host IPv4 {hip}, Default Gateway 0.0.0.0.",
                    "No usable default gateway - the DHCP lease is missing the 'default-router' "
                    "option, so the host cannot route off-subnet.",
                ))
            elif not apipa:
                try:
                    net = ipaddress.ip_network(f"{hip}/{mstr}", strict=False)
                    if ipaddress.ip_address(gip) not in net:
                        findings.append(RuleFinding(
                            "Host / Gateway Subnet Containment", "FAIL", "HIGH",
                            f"Host {hip}/{mstr} (network {net.network_address}) does not contain "
                            f"gateway {gip}.",
                            f"The configured default gateway {gip} is outside the host's local "
                            f"subnet, so ARP for the gateway never resolves.",
                        ))
                except ValueError:
                    pass

        # Host mask differs from the router mask for the same interface
        router_mask = re.search(r'Mask on \S+:\s*([0-9]{1,3}(?:\.[0-9]{1,3}){3})', text)
        if mask and router_mask and mask.group(1) != router_mask.group(1):
            findings.append(RuleFinding(
                "Subnet Mask Consistency", "FAIL", "HIGH",
                f"Host mask {mask.group(1)} vs gateway mask {router_mask.group(1)}.",
                "Host and gateway disagree on the subnet mask, so each computes a different network "
                "boundary and local hosts appear remote.",
            ))

        # ping to the gateway/DNS fails
        pf = re.search(r'ping\s+([0-9.]+)[\s\S]{0,80}?(Request timed out|Destination host unreachable)',
                       text, re.IGNORECASE)
        if pf:
            findings.append(RuleFinding(
                "Gateway / Next-Hop Reachability", "WARNING", "MEDIUM",
                f"ping {pf.group(1)} -> {pf.group(2)}.",
                f"The host cannot reach {pf.group(1)}. Confirm the target IP is correct and that "
                f"L2 adjacency / the gateway interface is up.",
            ))

        # router-on-a-stick: subinterface number != dot1Q tag
        for subif, tag in re.findall(
                r'interface \S+?\.(\d+)\s+encapsulation dot1Q (\d+)', text, re.IGNORECASE):
            if subif != tag:
                findings.append(RuleFinding(
                    "Subinterface 802.1Q Encapsulation", "FAIL", "HIGH",
                    f"Subinterface .{subif} is tagged 'encapsulation dot1Q {tag}'.",
                    f"The dot1Q tag ({tag}) does not match the VLAN the subinterface serves ({subif}); "
                    f"tagged frames for VLAN {subif} are never de-encapsulated.",
                ))

        # HSRP / standby virtual IP mismatch - take the trailing IP of the
        # 'Standby' / group data row, not the "Virtual IP" header line.
        vip = None
        for line in text.splitlines():
            if re.search(r'\b(Standby|Active|Init|Listen)\b', line) and "Virtual IP" not in line:
                tail = re.search(r'([0-9]{1,3}(?:\.[0-9]{1,3}){3})\s*$', line.strip())
                if tail:
                    vip = tail
                    break
        want_vip = re.search(r'(?:VIP|virtual ip|gateway)\D{0,12}([0-9]{1,3}(?:\.[0-9]{1,3}){3})',
                             combined_text, re.IGNORECASE)
        if vip and want_vip and vip.group(1) != want_vip.group(1):
            findings.append(RuleFinding(
                "HSRP Virtual IP Consistency", "FAIL", "HIGH",
                f"Standby group advertises Virtual IP {vip.group(1)}; expected {want_vip.group(1)}.",
                "The HSRP peers do not share an identical virtual IP, so failover to the standby "
                "does not present the expected default gateway.",
            ))
        return findings

    # ------------------------------------------------------------------ #
    # 4. VLAN / trunk / switching
    # ------------------------------------------------------------------ #
    def check_vlan_issues(self, show_outputs: str, symptom: str = "") -> List[RuleFinding]:
        findings: List[RuleFinding] = []

        m = re.search(
            r'%CDP-4-NATIVE_VLAN_MISMATCH:.*?on\s+([A-Za-z0-9/._-]+)\s*\((\d+)\).*?\((\d+)\)',
            show_outputs, re.IGNORECASE)
        if m:
            findings.append(RuleFinding(
                "Native VLAN Mismatch", "FAIL", "MEDIUM",
                m.group(0).strip(),
                f"Trunk {m.group(1)} native VLAN differs between the two ends "
                f"({m.group(2)} vs {m.group(3)}); untagged frames leak between broadcast domains.",
            ))

        m = re.search(r'Vlans allowed on trunk\s*\n?\s*([A-Za-z0-9/._-]+)?\s*([0-9][0-9,\-]+)',
                      show_outputs, re.IGNORECASE)
        if m:
            allowed = m.group(2)
            if allowed not in ("1-4094", "1-1005") and re.search(r'[,\-]', allowed):
                findings.append(RuleFinding(
                    "Trunk Allowed VLAN List", "FAIL", "HIGH",
                    f"Trunk allowed VLANs: '{allowed}'.",
                    "The trunk carries an explicit (pruned) allowed-VLAN list. Any production VLAN "
                    "not in this range is dropped between switches.",
                ))

        if re.search(r'VLAN id (\d+) not found in current VLAN database', show_outputs, re.IGNORECASE):
            vid = re.search(r'VLAN id (\d+) not found', show_outputs).group(1)
            findings.append(RuleFinding(
                "VLAN Database Existence", "FAIL", "CRITICAL",
                f"'VLAN id {vid} not found in current VLAN database'.",
                f"VLAN {vid} was never created on this switch; every access port in VLAN {vid} "
                f"stays operationally down.",
            ))

        # access port left in the default VLAN while the symptom expects another
        ap = re.search(r'Access Mode VLAN:\s*1\s*\(default\)', show_outputs, re.IGNORECASE)
        if ap and re.search(r'\b(finance|sales|engineering|voice|hr|guest|vlan\s*\d{2,})\b',
                            symptom, re.IGNORECASE):
            findings.append(RuleFinding(
                "Access Port VLAN Assignment", "WARNING", "HIGH",
                "Access port is in 'VLAN 1 (default)'.",
                "The port that should carry a department VLAN is still in the default VLAN 1 - "
                "run 'switchport access vlan <id>'.",
            ))

        # trunk not forming: admin dynamic but operational access, or both access
        if re.search(r'Administrative Mode:\s*dynamic', show_outputs, re.IGNORECASE) and \
           re.search(r'Operational Mode:\s*static access', show_outputs, re.IGNORECASE):
            findings.append(RuleFinding(
                "Trunk Negotiation (DTP)", "FAIL", "HIGH",
                "Administrative Mode: dynamic / Operational Mode: static access.",
                "DTP cannot negotiate a trunk because the peer is hard-set to access mode. Set "
                "'switchport mode trunk' on both ends.",
            ))

        # voice VLAN missing on a VoIP port
        if re.search(r'Voice VLAN:\s*none', show_outputs, re.IGNORECASE) and \
           re.search(r'\b(voip|voice|ip phone|phone)\b', f"{symptom} {show_outputs}", re.IGNORECASE):
            findings.append(RuleFinding(
                "Voice VLAN Configuration", "WARNING", "MEDIUM",
                "'Voice VLAN: none' on a port serving an IP phone.",
                "The IP phone and PC share one port but no voice VLAN is configured, so phone "
                "traffic lands untagged in the data VLAN.",
            ))
        return findings

    # ------------------------------------------------------------------ #
    # 5. Routing
    # ------------------------------------------------------------------ #
    def check_routing_issues(self, show_outputs: str) -> List[RuleFinding]:
        findings: List[RuleFinding] = []

        if "Gateway of last resort is not set" in show_outputs and "S*" not in show_outputs:
            findings.append(RuleFinding(
                "Gateway of Last Resort", "WARNING", "MEDIUM",
                "'Gateway of last resort is not set' with no default route present.",
                "No default route: traffic to any network not explicitly in the routing table is "
                "dropped. Add 'ip route 0.0.0.0 0.0.0.0 <next-hop>' or a routing-protocol default.",
            ))

        # missing route to a specific destination
        m = re.search(r'(Destination host unreachable|Network is unreachable)\D{0,60}from\s+([A-Za-z0-9._-]+)',
                      show_outputs, re.IGNORECASE)
        if m:
            findings.append(RuleFinding(
                "Missing Route to Destination", "FAIL", "HIGH",
                m.group(0).strip(),
                f"{m.group(2)} has no route toward the destination network - add the missing "
                f"static route or fix the routing-protocol 'network' statement.",
            ))

        hd = re.findall(r'Timer intervals(?: configured)?,?\s*Hello\s+(\d+),\s*Dead\s+(\d+)',
                        show_outputs, re.IGNORECASE)
        if len(hd) >= 2 and hd[0] != hd[1]:
            findings.append(RuleFinding(
                "OSPF Timer Interval Agreement", "FAIL", "HIGH",
                f"Hello/Dead {hd[0][0]}s/{hd[0][1]}s vs {hd[1][0]}s/{hd[1][1]}s on the shared link.",
                "OSPF neighbours must use identical Hello and Dead intervals or the adjacency never "
                "leaves INIT/DOWN.",
            ))

        if re.search(r'%OSPF-4-ERRRCV:.*invalid area ID\s+([0-9.]+)', show_outputs, re.IGNORECASE):
            aid = re.search(r'invalid area ID\s+([0-9.]+)', show_outputs).group(1)
            findings.append(RuleFinding(
                "OSPF Area ID Consistency", "FAIL", "HIGH",
                f"'%OSPF-4-ERRRCV ... invalid area ID {aid}'.",
                "Interfaces on the same segment are in different OSPF areas; move one end into the "
                "matching area.",
            ))
        areas = re.findall(r'Gi0/\d+\s+\d+\s+(\d+)\s+\d', show_outputs)
        if len(set(areas)) > 1:
            findings.append(RuleFinding(
                "OSPF Area ID Consistency", "FAIL", "HIGH",
                f"'show ip ospf interface brief' reports Area {' and '.join(sorted(set(areas)))} "
                f"on the same link.",
                "The two routers place the interconnect in different areas, so no adjacency forms.",
            ))

        eig = re.findall(r'(?:eigrp\s+(\d+)|EIGRP-IPv4 Protocol for AS\((\d+)\))', show_outputs, re.IGNORECASE)
        asn = {a or b for a, b in eig if (a or b)}
        if len(asn) >= 2:
            findings.append(RuleFinding(
                "EIGRP Autonomous System Match", "FAIL", "HIGH",
                f"EIGRP AS numbers seen: {', '.join(sorted(asn))}.",
                "EIGRP routers must share one AS number to become neighbours.",
            ))

        rip_v = re.findall(r'send version (\d)', show_outputs, re.IGNORECASE)
        if len(rip_v) >= 2 and len(set(rip_v)) > 1:
            findings.append(RuleFinding(
                "RIP Version Agreement", "FAIL", "MEDIUM",
                f"One router sends RIP v{rip_v[0]}, the other sends v{rip_v[1]}.",
                "RIPv1 broadcasts and RIPv2 multicasts are not interoperable - set 'version 2' on "
                "both routers.",
            ))

        # static default route via a next-hop outside the WAN subnet
        nh = re.search(r'0\.0\.0\.0/0\s+\[[\d/]+\]\s+via\s+([0-9.]+)', show_outputs)
        wan = re.search(r'([0-9]{1,3}(?:\.[0-9]{1,3}){3})\s+YES manual up\s+up', show_outputs)
        if nh and wan:
            try:
                if ipaddress.ip_address(nh.group(1)) not in ipaddress.ip_network(f"{wan.group(1)}/30", strict=False):
                    findings.append(RuleFinding(
                        "Default Route Next-Hop", "WARNING", "HIGH",
                        f"Default route points to {nh.group(1)}; local WAN interface is {wan.group(1)}.",
                        f"The next-hop {nh.group(1)} is not on the directly connected WAN subnet, so "
                        f"the router cannot resolve it.",
                    ))
            except ValueError:
                pass

        # static route bound to an exit interface
        m = re.search(r'S\s+([0-9./]+)\s+is directly connected,\s+([A-Za-z0-9/]+)', show_outputs)
        if m:
            findings.append(RuleFinding(
                "Static Route Exit Interface", "WARNING", "MEDIUM",
                f"Static route for {m.group(1)} egresses {m.group(2)}.",
                f"The static route uses an exit interface rather than a next-hop IP. Confirm "
                f"{m.group(2)} is the correct egress toward {m.group(1)}.",
            ))
        return findings

    # ------------------------------------------------------------------ #
    # 6. ACL / NAT
    # ------------------------------------------------------------------ #
    def check_acl_and_nat(self, show_outputs: str, symptom: str = "") -> List[RuleFinding]:
        findings: List[RuleFinding] = []

        if re.search(r'Standard IP access list.*?\n\s*\d+\s+permit\s+[0-9.]+\s+255\.255\.255\.\d',
                     show_outputs, re.IGNORECASE | re.DOTALL):
            findings.append(RuleFinding(
                "ACL Wildcard Mask Format", "FAIL", "CRITICAL",
                _first_line_matching(show_outputs, "permit ") or "Standard ACL uses a subnet mask.",
                "A standard ACL uses a subnet mask (255.255.255.0) instead of an inverse wildcard "
                "mask (0.0.0.255); the entry matches no host packets and the implicit deny drops "
                "everything.",
            ))

        # explicit DNS deny
        if re.search(r'deny udp .*?eq (?:domain|53)\s*\((\d+) matches\)', show_outputs, re.IGNORECASE):
            findings.append(RuleFinding(
                "ACL Denies DNS (UDP/53)", "FAIL", "CRITICAL",
                _first_line_matching(show_outputs, "deny udp"),
                "An access-list entry explicitly denies UDP/53, so name resolution to that server "
                "fails while IP connectivity still works.",
            ))

        # inbound ACL denies the LAN with no 'established' permit
        if re.search(r'\d+\s+deny ip any (?:host )?[0-9.]+ 0\.0\.0\.\d+\s*\(\d+ matches\)', show_outputs) \
           and "established" not in show_outputs.lower():
            findings.append(RuleFinding(
                "Inbound ACL Blocks Return Traffic", "FAIL", "HIGH",
                _first_line_matching(show_outputs, "deny ip any"),
                "The inbound WAN ACL denies traffic to the LAN and never permits 'established' TCP, "
                "so replies to outbound sessions are dropped.",
            ))

        # extended ACL with no permit for a protocol the symptom needs
        if re.search(r'Extended IP access list', show_outputs, re.IGNORECASE):
            body = show_outputs.lower()
            sym = symptom.lower()
            wants_http = any(k in sym for k in ("http", "port 80", ":80", "browse", "web server", "web browsing"))
            if wants_http and "permit tcp" in body and "eq www" not in body and "eq 80" not in body:
                findings.append(RuleFinding(
                    "ACL Missing Permit (HTTP/80)", "FAIL", "HIGH",
                    _first_line_matching(show_outputs, "permit tcp"),
                    "The extended ACL permits HTTPS/other ports but not TCP/80 (and ICMP); HTTP and "
                    "ping hit the implicit 'deny ip any any'.",
                ))
            if "dns" in sym and "eq domain" not in body and "eq 53" not in body:
                findings.append(RuleFinding(
                    "ACL Missing Permit (DNS/53)", "FAIL", "HIGH",
                    _first_line_matching(show_outputs, "deny ip any any", "deny ip any"),
                    "The outbound ACL permits web ports but not UDP/53, so DNS queries are denied "
                    "and browsing fails.",
                ))

        # standard ACL whose only entries have 0 matches while applied
        acl_zero = re.findall(r'\d+\s+permit\s+[0-9.]+\s*\(0 matches\)', show_outputs)
        if acl_zero and re.search(r'access-class \d+ in|ip access-group', show_outputs):
            findings.append(RuleFinding(
                "ACL Has No Matching Traffic", "WARNING", "HIGH",
                acl_zero[0].strip(),
                "Every permit entry in the applied ACL shows 0 matches - the source address the "
                "user connects from is not listed, so the implicit deny blocks them.",
            ))

        # NAT: no inside interface
        if re.search(r'Inside interfaces:\s*none', show_outputs, re.IGNORECASE):
            findings.append(RuleFinding(
                "NAT Inside Interface Missing", "FAIL", "CRITICAL",
                "'show ip nat statistics' -> Inside interfaces: none.",
                "No interface carries 'ip nat inside', so the router never translates LAN traffic "
                "and 'show ip nat translations' stays empty.",
            ))

        # NAT: dynamic PAT statement without 'overload'
        if re.search(r'ip nat inside source list \S+ interface \S+(?!\s+overload)', show_outputs) \
           and "overload" not in _first_line_matching(show_outputs, "ip nat inside source list").lower():
            findings.append(RuleFinding(
                "NAT Overload (PAT) Disabled", "FAIL", "HIGH",
                _first_line_matching(show_outputs, "ip nat inside source list"),
                "The dynamic NAT statement is missing the 'overload' keyword, so only one inside "
                "host can use the public IP at a time.",
            ))

        # NAT ACL that may not cover a second subnet mentioned in the symptom
        nat_acl = re.search(r'access list (\S+)\s*\n\s*\d+\s+permit\s+([0-9.]+)\s+0\.0\.0\.\d+', show_outputs)
        second = re.search(r'(192\.168\.\d+\.0|10\.\d+\.\d+\.0)/24', symptom)
        if nat_acl and second and second.group(1).rsplit(".", 1)[0] not in show_outputs:
            findings.append(RuleFinding(
                "NAT ACL Subnet Coverage", "WARNING", "HIGH",
                f"NAT ACL {nat_acl.group(1)} permits {nat_acl.group(2)} only.",
                f"The subnet {second.group(1)}/24 from the symptom is not permitted by the NAT ACL, "
                f"so that LAN is never translated.",
            ))

        # static PAT / port-forward present (verify target)
        m = re.search(r'ip nat inside source static tcp ([0-9.]+) (\d+) ([0-9.]+) (\d+)', show_outputs)
        if m:
            findings.append(RuleFinding(
                "Static NAT Port Forward", "WARNING", "MEDIUM",
                m.group(0).strip(),
                f"A static port-forward maps public {m.group(3)}:{m.group(4)} to internal "
                f"{m.group(1)}:{m.group(2)} - verify the internal IP is the real server.",
            ))
        return findings

    # ------------------------------------------------------------------ #
    # 7. DHCP / DNS service layer
    # ------------------------------------------------------------------ #
    def check_dhcp_and_dns(self, show_outputs: str, symptom: str = "") -> List[RuleFinding]:
        findings: List[RuleFinding] = []
        low = show_outputs.lower()

        # DHCP relay missing on a routed subinterface
        if re.search(r'169\.254\.\d', show_outputs) and re.search(
                r'interface \S+\.\d+\s+encapsulation dot1Q \d+\s+ip address', show_outputs, re.IGNORECASE) \
                and "ip helper-address" not in low:
            findings.append(RuleFinding(
                "DHCP Relay (ip helper-address)", "FAIL", "HIGH",
                _first_line_matching(show_outputs, "interface", "encapsulation dot1Q") or "routed subinterface without ip helper-address",
                "The client subnet is on a routed subinterface with no 'ip helper-address', so "
                "broadcast DHCP Discover packets are never forwarded to the server.",
            ))

        # DHCP pool block: missing default-router / dns-server
        pool = re.search(r'(ip dhcp pool[\s\S]{0,300})', show_outputs, re.IGNORECASE)
        if pool:
            block = pool.group(1).lower()
            if "network " in block and "default-router" not in block:
                findings.append(RuleFinding(
                    "DHCP Pool Missing default-router", "FAIL", "HIGH",
                    _first_line_matching(show_outputs, "ip dhcp pool"),
                    "The DHCP pool defines a network but no 'default-router', so clients lease an "
                    "address with gateway 0.0.0.0 and cannot leave the subnet.",
                ))
            if "network " in block and "dns-server" not in block:
                findings.append(RuleFinding(
                    "DHCP Pool Missing dns-server", "WARNING", "MEDIUM",
                    _first_line_matching(show_outputs, "ip dhcp pool"),
                    "The DHCP pool has no 'dns-server' option, so clients receive DNS 0.0.0.0 and "
                    "cannot resolve names.",
                ))

        # DHCP pool exhaustion
        if re.search(r'Leased/Pending/Free[\s\S]{0,120}?/\s*0\s*$', show_outputs, re.MULTILINE) or \
           re.search(r'\b\d+\s*/\s*0\s*/\s*0\b', show_outputs) or "Utilization mark (high/low)    : 100" in show_outputs:
            findings.append(RuleFinding(
                "DHCP Pool Exhaustion", "FAIL", "HIGH",
                _first_line_matching(show_outputs, "Leased", "Utilization mark") or "DHCP pool has 0 free addresses.",
                "Every address in the DHCP scope is leased; new clients get nothing. Enlarge the "
                "subnet/scope or shorten the lease time.",
            ))

        # DHCP hands out the router's own IP (no excluded-address)
        if re.search(r'%(?:IP-4-DUPADDR|SYS-3-IP_DUP)', show_outputs) and \
           re.search(r'default-router\s+([0-9.]+)', show_outputs) and "excluded-address" not in low:
            findings.append(RuleFinding(
                "DHCP Excluded-Address Missing", "FAIL", "CRITICAL",
                _first_line_matching(show_outputs, "default-router"),
                "The gateway address is inside the DHCP pool and not excluded, so DHCP handed the "
                "router's IP to a client - add 'ip dhcp excluded-address'.",
            ))

        # DNS server set to an unreachable / null address
        dns = re.search(r'DNS Servers?[.\s:]*([0-9]{1,3}(?:\.[0-9]{1,3}){3})', show_outputs, re.IGNORECASE)
        if dns and dns.group(1) == "0.0.0.0":
            findings.append(RuleFinding(
                "DNS Server Not Assigned", "FAIL", "HIGH",
                "DNS Servers . . . : 0.0.0.0",
                "The client has no DNS server (0.0.0.0) - the DHCP pool 'dns-server' option is "
                "missing or misspelt.",
            ))
        elif dns and re.search(rf'ping {re.escape(dns.group(1))}[\s\S]{{0,60}}unreachable', show_outputs, re.IGNORECASE):
            findings.append(RuleFinding(
                "DNS Server Unreachable", "FAIL", "HIGH",
                f"Configured DNS server {dns.group(1)} is unreachable.",
                f"Name resolution points at {dns.group(1)}, which does not answer - correct the "
                f"host/DHCP dns-server value.",
            ))

        # CAPWAP / lightweight AP discovery failing
        if re.search(r'CAPWAP (?:State|Discovery)', show_outputs, re.IGNORECASE) and \
           re.search(r'(timed out|Discovery Request Sent Count)', show_outputs, re.IGNORECASE):
            opt43 = "option 43" in low
            findings.append(RuleFinding(
                "CAPWAP / WLC Discovery", "FAIL" if not opt43 else "WARNING", "HIGH",
                _first_line_matching(show_outputs, "CAPWAP", "Discovery response"),
                "The lightweight AP is stuck in CAPWAP discovery. Without DHCP option 43 (or a DNS "
                "CISCO-CAPWAP-CONTROLLER record) it never learns the WLC address.",
            ))
        return findings

    # ------------------------------------------------------------------ #
    # 8. Wireless (SSID / PSK)
    # ------------------------------------------------------------------ #
    def check_wireless(self, show_outputs: str, symptom: str = "") -> List[RuleFinding]:
        findings: List[RuleFinding] = []

        clear = re.search(r'Clear text key:\s*([^\s)]+)', show_outputs)
        client = re.search(r'<KeyMaterial>\s*([^<\s]+)\s*</KeyMaterial>', show_outputs)
        if clear and client and clear.group(1).strip() != client.group(1).strip():
            findings.append(RuleFinding(
                "WPA2 Pre-Shared Key Mismatch", "FAIL", "HIGH",
                f"AP key '{clear.group(1)}' vs client key '{client.group(1)}'.",
                "The client and access point WPA2 pre-shared keys differ, so the 4-way handshake "
                "fails with an authentication error.",
            ))

        m = re.search(r'dot11 ssid (\S+)\s+vlan (\d+)', show_outputs, re.IGNORECASE)
        if m and re.search(r'guest', m.group(1), re.IGNORECASE):
            ssid_vlan = m.group(2)
            guest_vlan = re.search(r'(\d+)\s+Guest[-\w]*\s+active', show_outputs)
            if guest_vlan and guest_vlan.group(1) != ssid_vlan:
                findings.append(RuleFinding(
                    "Guest SSID VLAN Mapping", "FAIL", "CRITICAL",
                    f"SSID {m.group(1)} is mapped to VLAN {ssid_vlan}; guest VLAN is {guest_vlan.group(1)}.",
                    "The guest SSID bridges wireless guests straight into a corporate VLAN instead of "
                    "the isolated guest VLAN, defeating guest isolation.",
                ))
        return findings


# Standalone runner / sample output
if __name__ == "__main__":
    checker = NetworkRuleChecker()
    scenarios = [
        ("Layer 2 VLAN pruning on a trunk",
         "PC in Sales cannot ping across trunk Fa0/24 to SW-2",
         "SW-1 -> Trunk Fa0/24 -> SW-2",
         "SW-1# show interfaces trunk\nPort        Vlans allowed on trunk\nFa0/24      1-9,11-4094\n"),
        ("Layer 3 duplicate IP conflict",
         "Workstation has intermittent connectivity; gateway unreachable.",
         "Host -> SW -> R1",
         "%IP-4-DUPADDR: Duplicate address 192.168.10.1 on GigabitEthernet0/0, sourced by 0050.7966.6800\n"),
        ("Default gateway outside host subnet",
         "Host reaches local hosts but not the internet.",
         "Host-A -> R1",
         "Host-A> ipconfig\n IPv4 Address. . : 10.0.1.50\n Subnet Mask . . : 255.255.255.0\n Default Gateway : 10.0.2.1\nRouter-1# show ip interface brief\nGigabitEthernet0/0 10.0.1.1 YES manual up up\n"),
        ("DHCP relay missing (APIPA)",
         "New clients in VLAN 20 receive 169.254.x.x addresses.",
         "Client -> SW -> R1 (router-on-a-stick)",
         "Client> ipconfig\n Autoconfiguration IPv4 Address. : 169.254.120.44\nR1# show running-config interface g0/0.20\ninterface GigabitEthernet0/0.20\n encapsulation dot1Q 20\n ip address 192.168.20.1 255.255.255.0\n"),
        ("Missing default route",
         "HQ PC cannot reach the branch network.",
         "HQ-Rtr -- Serial -- Branch",
         "HQ-Rtr# show ip route\nGateway of last resort is not set\nC  10.1.1.0 is directly connected, GigabitEthernet0/0\n"),
        ("ACL denies DNS",
         "nslookup to the corporate DNS server times out.",
         "Client -> R1 -> DNS 10.50.1.10",
         "R1# show access-lists 101\nExtended IP access list 101\n 10 deny udp any host 10.50.1.10 eq domain (245 matches)\n 20 permit ip any any (1420 matches)\n"),
    ]
    out = ["=" * 78, "NetSage AI - Deterministic Rule Checker - Sample Execution", "=" * 78]
    for name, sym, topo, show in scenarios:
        out.append(f"\n--- {name} ---")
        for r in checker.run_all_checks(sym, topo, show):
            out.append(f"[{r['status']}] {r['rule']} ({r['severity']})")
            out.append(f"    evidence : {r['evidence']}")
            out.append(f"    detail   : {r['explanation']}")
    print("\n".join(out))

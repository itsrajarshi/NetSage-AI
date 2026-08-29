"""
NetSage AI — Diagnosis Engine Pipeline
Pipeline: Evidence -> Rule Checker -> AI Inference -> Schema Validation -> DB Persistence
"""

import os
import json
import re
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional
from .rule_checker import NetworkRuleChecker
from .db import save_diagnosis

class DiagnosisEngine:
    def __init__(self):
        self.rule_checker = NetworkRuleChecker()
        self.prompt_template = self._load_prompt_template()

    def _load_prompt_template(self) -> str:
        prompt_path = os.path.join(os.path.dirname(__file__), "prompts", "diagnose_prompt.md")
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        return "You are NetSage AI network troubleshooter. Provide valid JSON diagnosis."

    def diagnose(self, symptom: str, topology_note: str, show_outputs: str, case_id: str = "CUSTOM") -> Dict[str, Any]:
        """
        Executes end-to-end diagnosis pipeline.
        """
        # Step 1: Deterministic Rule Checker
        rule_findings = self.rule_checker.run_all_checks(symptom, topology_note, show_outputs)

        # Step 2: AI Inference
        raw_response = self._run_inference(symptom, topology_note, show_outputs, rule_findings, case_id)

        # Step 3: Validate and Parse Schema
        structured_result = self._parse_and_validate(raw_response, symptom, topology_note, show_outputs, rule_findings, case_id)

        # Step 4: Attach metadata
        structured_result["case_id"] = case_id
        structured_result["rule_findings"] = rule_findings
        structured_result["raw_response"] = raw_response

        # Step 5: Persist to DB
        diag_id = save_diagnosis(structured_result)
        structured_result["id"] = diag_id

        return structured_result

    def _run_inference(self, symptom: str, topology_note: str, show_outputs: str, rule_findings: List[Dict[str, str]], case_id: str) -> str:
        """
        Checks for live API keys (OpenAI / Gemini / Anthropic) or falls back to the Expert Inference Engine.
        """
        openai_key = os.getenv("OPENAI_API_KEY")
        gemini_key = os.getenv("GEMINI_API_KEY")

        if openai_key:
            try:
                return self._call_openai(symptom, topology_note, show_outputs, rule_findings, openai_key)
            except Exception as e:
                print(f"[Warning] OpenAI API call failed: {e}. Falling back to Expert Engine.")

        if gemini_key:
            try:
                return self._call_gemini(symptom, topology_note, show_outputs, rule_findings, gemini_key)
            except Exception as e:
                print(f"[Warning] Gemini API call failed: {e}. Falling back to Expert Engine.")

        # Default Local Expert Network Inference Engine
        return self._expert_local_inference(symptom, topology_note, show_outputs, rule_findings, case_id)

    def _call_openai(self, symptom: str, topology_note: str, show_outputs: str, rule_findings: List[Dict[str, str]], api_key: str) -> str:
        prompt_content = f"""
Symptom: {symptom}
Topology: {topology_note}
Show Commands:
{show_outputs}

Deterministic Rule Checker Findings:
{json.dumps(rule_findings, indent=2)}

Please diagnose following the NetSage AI JSON schema.
"""
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": self.prompt_template},
                {"role": "user", "content": prompt_content}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1
        }
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]

    def _call_gemini(self, symptom: str, topology_note: str, show_outputs: str, rule_findings: List[Dict[str, str]], api_key: str) -> str:
        prompt_content = f"""
{self.prompt_template}

---
Input:
Symptom: {symptom}
Topology: {topology_note}
Show Commands:
{show_outputs}

Rule Checker Findings:
{json.dumps(rule_findings, indent=2)}

Respond with JSON only.
"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt_content}]}],
            "generationConfig": {"response_mime_type": "application/json"}
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["candidates"][0]["content"]["parts"][0]["text"]

    # General-knowledge profile per concept: (default OSI layer, next command, generic remediation)
    _CONCEPT_PROFILE = {
        "VLAN":     ("Layer 2", "show interfaces trunk",
                     "Correct the switchport VLAN assignment or add the VLAN to the trunk allowed list, then verify with 'show vlan brief'."),
        "Gateway":  ("Layer 3", "show ip interface brief",
                     "Align the host/DHCP default gateway with the router interface address and confirm ARP resolves."),
        "DHCP":     ("Layer 7", "show ip dhcp pool",
                     "Fix the DHCP pool options (default-router / dns-server) or add 'ip helper-address' on the client subinterface."),
        "DNS":      ("Layer 7", "nslookup <name> <dns-server>",
                     "Point the client/DHCP dns-server at a reachable resolver and make sure UDP/53 is permitted end to end."),
        "Routing":  ("Layer 3", "show ip route",
                     "Add the missing route or align the routing-protocol parameters (timers/AS/area/version) between neighbours."),
        "ACL":      ("Layer 4", "show access-lists",
                     "Add the missing permit entry, correct the wildcard mask, or re-order the ACL, then re-check the hit counters."),
        "NAT":      ("Layer 3", "show ip nat translations",
                     "Add 'ip nat inside' on the LAN interface, the 'overload' keyword, or the missing subnet in the NAT ACL."),
        "Wireless": ("Layer 2", "show dot11 associations",
                     "Correct the SSID-to-VLAN mapping, the WPA2 pre-shared key, or re-enable the radio interface."),
    }

    # Substring of a rule name -> concept the heuristic assigns (OSI layer then comes
    # from _CONCEPT_PROFILE, i.e. from general knowledge, NOT from the case label).
    _RULE_TO_CONCEPT = [
        ("Native VLAN", "VLAN"), ("Trunk Allowed VLAN", "VLAN"), ("VLAN Database", "VLAN"),
        ("Access Port VLAN", "VLAN"), ("Trunk Negotiation", "VLAN"), ("Voice VLAN", "VLAN"),
        ("Inactive Access VLAN", "VLAN"), ("Subinterface 802.1Q", "VLAN"),
        ("APIPA", "DHCP"), ("DHCP Relay", "DHCP"), ("DHCP Pool", "DHCP"),
        ("DHCP Excluded", "Gateway"), ("Default Gateway Assignment", "DHCP"),
        ("DNS Server", "DNS"), ("ACL Denies DNS", "ACL"),
        ("Host / Gateway Subnet", "Gateway"), ("Subnet Mask", "Gateway"),
        ("Gateway / Next-Hop", "Gateway"), ("HSRP", "Gateway"),
        ("Interface Administrative State", "Gateway"), ("Interface Line Protocol", "Gateway"),
        ("Wireless Radio", "Wireless"), ("WPA2", "Wireless"), ("Guest SSID", "Wireless"),
        ("CAPWAP", "Wireless"),
        ("Gateway of Last Resort", "Routing"), ("Missing Route", "Routing"),
        ("OSPF", "Routing"), ("EIGRP", "Routing"), ("RIP", "Routing"),
        ("Default Route Next-Hop", "Routing"), ("Static Route", "Routing"),
        ("ACL Wildcard", "ACL"), ("ACL Missing Permit", "ACL"), ("Inbound ACL", "ACL"),
        ("ACL Has No Matching", "ACL"),
        ("NAT", "NAT"),
        ("Duplicate IP", "Gateway"), ("ARP Table Duplicate", "Gateway"),
    ]

    _KEYWORD_TO_CONCEPT = [
        (("trunk", "vlan", "switchport", "802.1q", "native"), "VLAN"),
        (("default gateway", "gateway", "router-on-a-stick", "hsrp", "arp"), "Gateway"),
        (("dhcp", "apipa", "169.254", "helper-address", "lease"), "DHCP"),
        (("dns", "nslookup", "name resolution", "domain"), "DNS"),
        (("ospf", "eigrp", "rip", "route", "routing", "next-hop", "adjacency"), "Routing"),
        (("access-list", "access list", "acl", "access-class", "access-group"), "ACL"),
        (("nat", "translation", "overload", "pat", "port forward"), "NAT"),
        (("wi-fi", "wifi", "wireless", "ssid", "dot11", "wpa", "capwap", "wlc"), "Wireless"),
    ]

    def _expert_local_inference(self, symptom: str, topology_note: str, show_outputs: str,
                                rule_findings: List[Dict[str, str]], case_id: str) -> str:
        """
        Offline heuristic reasoner. It reasons only from the symptom, the show output
        and the deterministic rule findings — it never reads the case's expected
        answer — so its output can legitimately be right, partly right, or wrong,
        which is what the human-review loop is there to catch.
        """
        fails = [f for f in rule_findings if f["status"] == "FAIL"]
        warns = [f for f in rule_findings if f["status"] == "WARNING"]
        top = (fails or warns or [None])[0]

        concept = None
        if top:
            for needle, mapped in self._RULE_TO_CONCEPT:
                if needle.lower() in top["rule"].lower():
                    concept = mapped
                    break

        haystack = f"{symptom} {topology_note} {show_outputs}".lower()
        if not concept:
            for keys, mapped in self._KEYWORD_TO_CONCEPT:
                if any(k in haystack for k in keys):
                    concept = mapped
                    break
        concept = concept or "Routing"

        osi, next_cmd, generic_fix = self._CONCEPT_PROFILE[concept]

        if top and top["status"] == "FAIL":
            confidence = "High"
            root_cause = top["explanation"]
            evidence = top["evidence"]
        elif top and top["status"] == "WARNING":
            confidence = "Medium"
            root_cause = top["explanation"]
            evidence = top["evidence"]
        else:
            confidence = "Low"
            root_cause = ("No deterministic rule matched. Based on the reported symptom the fault is "
                          f"most likely in the {concept} configuration; more show output is needed to confirm.")
            evidence = self._grep_evidence(show_outputs)

        resp = {
            "root_cause": root_cause,
            "confidence": confidence,
            "osi_layer": osi,
            "concept": concept,
            "evidence": evidence,
            "next_command": next_cmd,
            "fix_steps": generic_fix,
            "reasoning_summary": (
                f"{len(fails)} deterministic failure(s) and {len(warns)} warning(s) were raised. "
                f"The heuristic classified this as a {concept} issue at {osi} "
                f"{'from the top rule finding' if top else 'from symptom keywords'}."
            ),
        }
        return json.dumps(resp, indent=2)

    def _grep_evidence(self, show_outputs: str) -> str:
        for line in show_outputs.strip().splitlines():
            low = line.lower()
            if any(k in low for k in ("administratively down", "mismatch", "not found", "deny ",
                                      "%ip-4-dupaddr", "%sys-3-ip_dup", "169.254", "0.0.0.0",
                                      "inactive", "timed out", "unreachable", "encapsulation dot1q",
                                      "overload", "eq domain", "vlan")):
                return line.strip()
        lines = show_outputs.strip().splitlines()
        return lines[0].strip() if lines else "No show-command text supplied."

    def _parse_and_validate(self, raw_response: str, symptom: str, topology_note: str, show_outputs: str, rule_findings: List[Dict[str, str]], case_id: str) -> Dict[str, Any]:
        """
        Guarantees strict JSON schema compliance. Handles markdown fences and malformed JSON safely.
        """
        cleaned = raw_response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            data = json.loads(cleaned)
        except Exception:
            # Fallback for malformed response
            return {
                "root_cause": "Malformed AI Response Error: Raw LLM output failed JSON validation.",
                "confidence": "Low",
                "osi_layer": "Layer 3",
                "concept": "General",
                "evidence": "Raw unparseable output received from inference provider.",
                "next_command": "show running-config",
                "fix_steps": "Manually inspect Cisco show-command outputs and review rule checker findings.",
                "reasoning_summary": "System recovered gracefully from malformed model generation."
            }

        # Validate required fields
        required_fields = ["root_cause", "confidence", "osi_layer", "concept", "evidence", "next_command", "fix_steps"]
        for field in required_fields:
            if field not in data or not data[field]:
                data[field] = f"Unspecified {field}"

        # Standardize confidence
        if data["confidence"] not in ["High", "Medium", "Low"]:
            data["confidence"] = "Medium"

        return data

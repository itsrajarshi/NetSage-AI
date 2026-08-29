"""
Unit tests for NetSage AI Deterministic Rule Checker
"""

import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.rule_checker import NetworkRuleChecker

class TestRuleChecker(unittest.TestCase):
    def setUp(self):
        self.checker = NetworkRuleChecker()

    def test_interface_administratively_down(self):
        show = "GigabitEthernet0/0 is administratively down, line protocol is down"
        findings = self.checker.check_interface_down(show)
        self.assertTrue(any(f.status == "FAIL" and "administratively down" in f.evidence for f in findings))

    def test_inactive_vlan_detection(self):
        show = "Name: Fa0/10\nAccess Mode VLAN: 50 (inactive)"
        findings = self.checker.check_interface_down(show)
        self.assertTrue(any(f.status == "FAIL" and "inactive" in f.evidence for f in findings))

    def test_duplicate_ip_detection(self):
        show = "%IP-4-DUPADDR: Duplicate address 192.168.10.1 on GigabitEthernet0/0, sourced by 0050.7966.6800"
        findings = self.checker.check_duplicate_ips(show, show)
        self.assertTrue(any(f.status == "FAIL" and "192.168.10.1" in f.evidence for f in findings))

    def test_gateway_subnet_mismatch(self):
        text = "IPv4 Address: 10.0.1.50\nSubnet Mask: 255.255.255.0\nDefault Gateway: 10.0.2.1"
        findings = self.checker.check_subnet_and_gateway(text, text)
        self.assertTrue(any(f.status == "FAIL" and "10.0.2.1" in f.evidence for f in findings))

    def test_native_vlan_mismatch(self):
        show = "%CDP-4-NATIVE_VLAN_MISMATCH: Native VLAN mismatch discovered on GigabitEthernet0/1 (1), with SW-2 GigabitEthernet0/1 (99)."
        findings = self.checker.check_vlan_issues(show)
        self.assertTrue(any(f.status == "FAIL" and "Native VLAN Mismatch".lower() in f.rule.lower() for f in findings))

    def test_vlan_pruning_on_trunk(self):
        show = "Vlans allowed on trunk\nFa0/24      1-9,11-4094"
        findings = self.checker.check_vlan_issues(show)
        self.assertTrue(any(f.status == "FAIL" and "1-9,11-4094" in f.evidence for f in findings))

    def test_ospf_timer_mismatch(self):
        show = """
R1: Timer intervals configured, Hello 10, Dead 40
R2: Timer intervals configured, Hello 30, Dead 120
"""
        findings = self.checker.check_routing_issues(show)
        self.assertTrue(any(f.status == "FAIL" and "OSPF" in f.rule for f in findings))

    def test_acl_subnet_mask_mistake(self):
        show = "Standard IP access list 10\n    10 permit 192.168.10.0 255.255.255.0"
        findings = self.checker.check_acl_and_nat(show)
        self.assertTrue(any(f.status == "FAIL" and "Wildcard Mask" in f.rule for f in findings))

if __name__ == "__main__":
    unittest.main()

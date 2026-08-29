"""
NetSage AI — Case Dataset Generator

Source of truth for `data/cases.csv`. Edit the `cases` list below and run
`python backend/generate_cases.py` to regenerate the CSV. This keeps the 39
troubleshooting cases version-controlled as structured Python rather than
hand-edited CSV rows.
"""

import csv
import os

cases = [
    # ---------------- VLAN CASES ----------------
    {
        "case_id": "VLAN-001",
        "symptom": "PC-1 in Sales cannot communicate with PC-2 in Sales across Switch-1 and Switch-2; ping fails with Request Timed Out.",
        "topology_note": "PC-1 (192.168.10.10/24) -> SW-1 (Fa0/1 access VLAN 10) -> Trunk Fa0/24 -> SW-2 (Fa0/24) -> PC-2 (Fa0/2 access VLAN 10, 192.168.10.20/24).",
        "show_outputs": "SW-1# show interfaces trunk\nPort        Mode         Encapsulation  Status        Native vlan\nFa0/24      on           802.1q         trunking      1\n\nPort        Vlans allowed on trunk\nFa0/24      1-9,11-4094\n\nSW-2# show vlan brief\nVLAN Name                             Status    Ports\n---- -------------------------------- --------- -------------------------------\n10   Sales                            active    Fa0/2\n",
        "expected_fault": "VLAN 10 is missing from the allowed VLAN list on trunk link Fa0/24 of SW-1.",
        "osi_layer": "Layer 2",
        "concept": "VLAN",
        "severity": "High",
        "expected_next_command": "show interfaces Fa0/24 switchport",
        "expected_fix": "SW-1(config-if)# switchport trunk allowed vlan add 10",
        "difficulty": "Medium",
        "explanation": "Trunk port Fa0/24 on SW-1 has an explicit allowed list (1-9,11-4094) that prunes VLAN 10, preventing inter-switch broadcast and unicast frames for Sales."
    },
    {
        "case_id": "VLAN-002",
        "symptom": "CDP native VLAN mismatch warnings logged continuously; untagged traffic is leaking between VLAN 1 and VLAN 99.",
        "topology_note": "SW-1 (Gig0/1 Native VLAN 1) <---> (Gig0/1 Native VLAN 99) SW-2.",
        "show_outputs": "%CDP-4-NATIVE_VLAN_MISMATCH: Native VLAN mismatch discovered on GigabitEthernet0/1 (1), with SW-2 GigabitEthernet0/1 (99).\nSW-1# show interfaces gig0/1 switchport\nName: Gi0/1\nAdministrative Mode: trunk\nTrunking Native Mode VLAN: 1 (default)\nTrunking VLANs Enabled: ALL\nSW-2# show interfaces gig0/1 switchport\nName: Gi0/1\nAdministrative Mode: trunk\nTrunking Native Mode VLAN: 99 (Management)\n",
        "expected_fault": "Native VLAN mismatch between SW-1 (VLAN 1) and SW-2 (VLAN 99) on trunk Gi0/1.",
        "osi_layer": "Layer 2",
        "concept": "VLAN",
        "severity": "Medium",
        "expected_next_command": "show interfaces trunk",
        "expected_fix": "SW-1(config-if)# switchport trunk native vlan 99",
        "difficulty": "Easy",
        "explanation": "Both ends of an 802.1Q trunk must agree on the native VLAN. A mismatch causes untagged frames sent by SW-1 on VLAN 1 to be received by SW-2 into VLAN 99."
    },
    {
        "case_id": "VLAN-003",
        "symptom": "Finance PC (192.168.20.15) connected to Fa0/5 cannot reach its default gateway (192.168.20.1) or any other Finance hosts.",
        "topology_note": "PC-Finance (192.168.20.15/24) -> SW-1 Fa0/5 -> Gateway on Router subinterface G0/0.20.",
        "show_outputs": "SW-1# show vlan brief\nVLAN Name                             Status    Ports\n---- -------------------------------- --------- -------------------------------\n1    default                          active    Fa0/1, Fa0/3, Fa0/4, Fa0/5\n10   Sales                            active    Fa0/2\n20   Finance                          active    \n\nSW-1# show interfaces Fa0/5 switchport\nName: Fa0/5\nAdministrative Mode: static access\nAccess Mode VLAN: 1 (default)\n",
        "expected_fault": "Access port Fa0/5 is assigned to default VLAN 1 instead of Finance VLAN 20.",
        "osi_layer": "Layer 2",
        "concept": "VLAN",
        "severity": "High",
        "expected_next_command": "show running-config interface Fa0/5",
        "expected_fix": "SW-1(config)# interface Fa0/5\nSW-1(config-if)# switchport access vlan 20",
        "difficulty": "Easy",
        "explanation": "Port Fa0/5 is in VLAN 1 by default, isolating the PC from Finance broadcast domain VLAN 20 where its gateway and peers reside."
    },
    {
        "case_id": "VLAN-004",
        "symptom": "All host ports in VLAN 50 (Engineering) are down/down or inactive after reboot; switch reports VLAN does not exist.",
        "topology_note": "SW-Core connecting engineering lab workstations on Fa0/10 - Fa0/20.",
        "show_outputs": "SW-Core# show vlan id 50\nVLAN id 50 not found in current VLAN database\n\nSW-Core# show interfaces Fa0/10 switchport\nName: Fa0/10\nAccess Mode VLAN: 50 (inactive)\nOperational Mode: down\n",
        "expected_fault": "VLAN 50 is not created in the local switch VLAN database.",
        "osi_layer": "Layer 2",
        "concept": "VLAN",
        "severity": "Critical",
        "expected_next_command": "show vlan brief",
        "expected_fix": "SW-Core(config)# vlan 50\nSW-Core(config-vlan)# name Engineering",
        "difficulty": "Easy",
        "explanation": "Ports assigned to non-existent VLANs show 'inactive' state. Defining 'vlan 50' activates the ports immediately."
    },

    # ---------------- GATEWAY CASES ----------------
    {
        "case_id": "GW-001",
        "symptom": "Workstation can ping other workstations on the same local subnet (10.0.1.0/24) but cannot ping 8.8.8.8 or corporate servers.",
        "topology_note": "Host-A (10.0.1.50/24) -> SW-1 -> Router-1 (G0/0 IP 10.0.1.1/24) -> WAN.",
        "show_outputs": "Host-A> ipconfig\n   IPv4 Address. . . . . . . . . . . : 10.0.1.50\n   Subnet Mask . . . . . . . . . . . : 255.255.255.0\n   Default Gateway . . . . . . . . . : 10.0.1.254\n\nHost-A> ping 10.0.1.254\nRequest timed out.\n\nRouter-1# show ip interface brief\nInterface              IP-Address      OK? Method Status                Protocol\nGigabitEthernet0/0     10.0.1.1        YES manual up                    up\n",
        "expected_fault": "Host default gateway is configured as 10.0.1.254, but router interface is 10.0.1.1.",
        "osi_layer": "Layer 3",
        "concept": "Gateway",
        "severity": "High",
        "expected_next_command": "show arp",
        "expected_fix": "Change Host-A Default Gateway to 10.0.1.1 (or update DHCP scope option 3).",
        "difficulty": "Easy",
        "explanation": "Host-A sends ARP requests for non-existent IP 10.0.1.254 when trying to route packets off-subnet. The actual gateway on R1 is 10.0.1.1."
    },
    {
        "case_id": "GW-002",
        "symptom": "Router-on-a-stick subinterface for VLAN 30 fails to route traffic; hosts in VLAN 30 cannot reach their gateway 192.168.30.1.",
        "topology_note": "SW-1 (Trunk Gi0/1) <---> R1 (G0/0.30 subinterface).",
        "show_outputs": "R1# show ip interface brief\nInterface              IP-Address      OK? Method Status                Protocol\nGigabitEthernet0/0.30  192.168.30.1    YES manual up                    up\n\nR1# show running-config interface g0/0.30\ninterface GigabitEthernet0/0.30\n encapsulation dot1Q 300\n ip address 192.168.30.1 255.255.255.0\n",
        "expected_fault": "Subinterface dot1Q encapsulation tag is misconfigured as 300 instead of VLAN 30.",
        "osi_layer": "Layer 3",
        "concept": "Gateway",
        "severity": "High",
        "expected_next_command": "show interfaces trunk on SW-1",
        "expected_fix": "R1(config)# interface g0/0.30\nR1(config-subif)# encapsulation dot1Q 30",
        "difficulty": "Medium",
        "explanation": "Router expects frames tagged with 802.1Q tag 300, while switch frames arrive tagged as VLAN 30. The router ignores incoming frames."
    },
    {
        "case_id": "GW-003",
        "symptom": "HSRP standby router is not responding to default gateway VIP 172.16.1.1 when primary router goes offline.",
        "topology_note": "R1 (Active 172.16.1.2) and R2 (Standby 172.16.1.3), VIP: 172.16.1.1.",
        "show_outputs": "R2# show standby brief\n                     P Indicates configured to preempt.\n                     |\nInterface   Grp  Pri P State   Active          Standby         Virtual IP\nGi0/0       10   90    Standby 172.16.1.2      local           172.16.1.254\n",
        "expected_fault": "HSRP Virtual IP mismatch on R2 (configured 172.16.1.254 instead of 172.16.1.1).",
        "osi_layer": "Layer 3",
        "concept": "Gateway",
        "severity": "Critical",
        "expected_next_command": "show standby on R1 and R2",
        "expected_fix": "R2(config-if)# standby 10 ip 172.16.1.1",
        "difficulty": "Medium",
        "explanation": "R2 has virtual IP set to 172.16.1.254 while R1 and clients use 172.16.1.1. Failover causes gateway blackhole."
    },
    {
        "case_id": "GW-004",
        "symptom": "Entire branch office lost internet connectivity suddenly; router interface connecting LAN switch is administratively shut down.",
        "topology_note": "Branch LAN -> Switch -> R-Branch G0/0 -> ISP.",
        "show_outputs": "R-Branch# show ip interface brief\nInterface              IP-Address      OK? Method Status                Protocol\nGigabitEthernet0/0     192.168.1.1     YES manual administratively down down\nGigabitEthernet0/1     203.0.113.2     YES manual up                    up\n",
        "expected_fault": "LAN gateway interface GigabitEthernet0/0 is administratively down.",
        "osi_layer": "Layer 1",
        "concept": "Gateway",
        "severity": "Critical",
        "expected_next_command": "show running-config interface g0/0",
        "expected_fix": "R-Branch(config)# interface GigabitEthernet0/0\nR-Branch(config-if)# no shutdown",
        "difficulty": "Easy",
        "explanation": "Interface G0/0 is in 'administratively down' state due to a shutdown command, cutting off LAN hosts from their default gateway."
    },

    # ---------------- DHCP CASES ----------------
    {
        "case_id": "DHCP-001",
        "symptom": "New clients in VLAN 20 receive 169.254.x.x APIPA addresses; static IP assignment works normally.",
        "topology_note": "Client (VLAN 20) -> SW-Access -> R1 (Router G0/0.20) -> Central DHCP Server (10.10.10.5 on G0/1).",
        "show_outputs": "Client> ipconfig\n   Autoconfiguration IPv4 Address. : 169.254.120.44\n   Subnet Mask . . . . . . . . . . . : 255.255.0.0\n\nR1# show running-config interface g0/0.20\ninterface GigabitEthernet0/0.20\n encapsulation dot1Q 20\n ip address 192.168.20.1 255.255.255.0\n!\n",
        "expected_fault": "Missing 'ip helper-address 10.10.10.5' on router subinterface G0/0.20.",
        "osi_layer": "Layer 7",
        "concept": "DHCP",
        "severity": "High",
        "expected_next_command": "show ip dhcp server statistics",
        "expected_fix": "R1(config-subif)# ip helper-address 10.10.10.5",
        "difficulty": "Medium",
        "explanation": "DHCP Discover broadcasts from clients in VLAN 20 are dropped by R1 because DHCP Relay (ip helper-address) is not configured on G0/0.20."
    },
    {
        "case_id": "DHCP-002",
        "symptom": "Clients receive IP addresses from DHCP but cannot browse websites by domain or IP; default gateway option is missing from lease.",
        "topology_note": "Cisco IOS Router acting as local DHCP server for 192.168.1.0/24 subnet.",
        "show_outputs": "Client> ipconfig\n   IPv4 Address. . . . . . . . . . . : 192.168.1.102\n   Subnet Mask . . . . . . . . . . . : 255.255.255.0\n   Default Gateway . . . . . . . . . : 0.0.0.0\n\nR1# show running-config | section dhcp\nip dhcp pool LAN_POOL\n network 192.168.1.0 255.255.255.0\n dns-server 8.8.8.8\n",
        "expected_fault": "DHCP pool LAN_POOL is missing the 'default-router 192.168.1.1' configuration option.",
        "osi_layer": "Layer 7",
        "concept": "DHCP",
        "severity": "High",
        "expected_next_command": "show ip dhcp pool",
        "expected_fix": "R1(config)# ip dhcp pool LAN_POOL\nR1(config-dhcp)# default-router 192.168.1.1",
        "difficulty": "Easy",
        "explanation": "DHCP option 3 (Default Router) is omitted in pool configuration, so clients are assigned 0.0.0.0 as gateway and cannot route traffic outside the subnet."
    },
    {
        "case_id": "DHCP-003",
        "symptom": "Duplicate IP address conflict detected on 192.168.10.1; router gateway address was assigned to a client by DHCP.",
        "topology_note": "Router R1 (192.168.10.1) provides DHCP for LAN 192.168.10.0/24.",
        "show_outputs": "%IP-4-DUPADDR: Duplicate address 192.168.10.1 on GigabitEthernet0/0, sourced by 0050.7966.6800\nR1# show running-config | section dhcp\nip dhcp pool POOL10\n network 192.168.10.0 255.255.255.0\n default-router 192.168.10.1\n dns-server 1.1.1.1\n",
        "expected_fault": "Static router IP 192.168.10.1 is not excluded from DHCP distribution pool.",
        "osi_layer": "Layer 3",
        "concept": "DHCP",
        "severity": "Critical",
        "expected_next_command": "show ip dhcp binding",
        "expected_fix": "R1(config)# ip dhcp excluded-address 192.168.10.1 192.168.10.10",
        "difficulty": "Easy",
        "explanation": "Without `ip dhcp excluded-address`, the DHCP server leases out 192.168.10.1 to the first requesting host, conflicting with its own gateway interface."
    },
    {
        "case_id": "DHCP-004",
        "symptom": "New visitors cannot connect to office network; router DHCP pool has 0 available free addresses.",
        "topology_note": "Guest VLAN 192.168.50.0/28 (14 usable addresses).",
        "show_outputs": "R1# show ip dhcp pool GUEST\nPool GUEST :\n Utilization mark (high/low)    : 100 / 0\n Subnet size (total/usable)       : 16/14\n Leased addresses                : 14\n Pending event                   : none\n 1 subnet is currently in the pool :\n Current index        IP address range                    Leased/Pending/Free\n 192.168.50.14        192.168.50.1     - 192.168.50.14     14    / 0     / 0\n",
        "expected_fault": "DHCP address pool exhaustion (all 14 available host addresses are leased).",
        "osi_layer": "Layer 7",
        "concept": "DHCP",
        "severity": "Medium",
        "expected_next_command": "show ip dhcp binding",
        "expected_fix": "Expand subnet mask to /24 (192.168.50.0 255.255.255.0) or reduce DHCP lease time.",
        "difficulty": "Medium",
        "explanation": "The configured /28 subnet only provides 14 usable IP addresses. High host turnover exhausted all leases."
    },

    # ---------------- DNS CASES ----------------
    {
        "case_id": "DNS-001",
        "symptom": "Hosts can ping public IP 8.8.8.8 and 1.1.1.1 but cannot browse 'cisco.com' or 'google.com'; browser reports DNS_PROBE_FINISHED_NXDOMAIN.",
        "topology_note": "Host-PC (192.168.1.15) -> R1 Gateway -> ISP.",
        "show_outputs": "Host-PC> ipconfig /all\n   IPv4 Address. . . . . . . . . . . : 192.168.1.15\n   Subnet Mask . . . . . . . . . . . : 255.255.255.0\n   Default Gateway . . . . . . . . . : 192.168.1.1\n   DNS Servers . . . . . . . . . . . : 192.168.1.250\n\nHost-PC> ping 192.168.1.250\nDestination host unreachable.\n",
        "expected_fault": "Client DNS server is set to unreachable IP 192.168.1.250.",
        "osi_layer": "Layer 7",
        "concept": "DNS",
        "severity": "High",
        "expected_next_command": "nslookup cisco.com 8.8.8.8",
        "expected_fix": "Update host DNS server (or DHCP pool dns-server) to valid IP e.g. 8.8.8.8 or 1.1.1.1.",
        "difficulty": "Easy",
        "explanation": "Host cannot resolve domain names because its configured DNS server (192.168.1.250) does not exist on the local network."
    },
    {
        "case_id": "DNS-002",
        "symptom": "Internal server intranet.corp.local cannot be reached by hostname; nslookup times out to corporate DNS server 10.50.1.10.",
        "topology_note": "Client (10.10.1.5) -> Core-Switch -> Firewall/Router -> Corp DNS (10.50.1.10).",
        "show_outputs": "Client> nslookup intranet.corp.local 10.50.1.10\nDNS request timed out.\n    timeout was 2 seconds.\n*** Can't find server name for address 10.50.1.10: Timed out\n\nR1# show access-lists 101\nExtended IP access list 101\n    10 deny udp any host 10.50.1.10 eq domain (245 matches)\n    20 permit ip any any (1420 matches)\n",
        "expected_fault": "ACL 101 explicitly denies UDP port 53 (DNS) traffic to DNS server 10.50.1.10.",
        "osi_layer": "Layer 4",
        "concept": "DNS",
        "severity": "Critical",
        "expected_next_command": "show ip access-lists",
        "expected_fix": "R1(config)# no access-list 101 deny udp any host 10.50.1.10 eq domain\n(or re-order ACL to permit DNS)",
        "difficulty": "Medium",
        "explanation": "Line 10 of ACL 101 drops UDP port 53 packets destined for corporate DNS server 10.50.1.10, preventing domain resolution."
    },

    # ---------------- ROUTING CASES ----------------
    {
        "case_id": "ROUT-001",
        "symptom": "Headquarters PC (10.1.1.10) cannot ping Branch PC (10.2.2.20); ping returns 'Destination host unreachable' from HQ-Router.",
        "topology_note": "HQ-PC (10.1.1.10) -> HQ-Rtr (192.168.12.1) <--- Serial WAN ---> Branch-Rtr (192.168.12.2) -> Branch-PC (10.2.2.20).",
        "show_outputs": "HQ-Rtr# show ip route\nGateway of last resort is not set\n\n      10.0.0.0/24 is subnetted, 1 subnets\nC        10.1.1.0 is directly connected, GigabitEthernet0/0\n      192.168.12.0/30 is subnetted, 1 subnets\nC        192.168.12.0 is directly connected, Serial0/0/0\n",
        "expected_fault": "HQ-Rtr is missing a route to destination network 10.2.2.0/24.",
        "osi_layer": "Layer 3",
        "concept": "Routing",
        "severity": "High",
        "expected_next_command": "show ip protocols",
        "expected_fix": "HQ-Rtr(config)# ip route 10.2.2.0 255.255.255.0 192.168.12.2",
        "difficulty": "Easy",
        "explanation": "HQ-Rtr has no route in its routing table for 10.2.2.0/24 and no default gateway set, so it discards the packet immediately."
    },
    {
        "case_id": "ROUT-002",
        "symptom": "OSPF neighbor adjacency between R1 and R2 remains stuck in INIT or DOWN state over GigabitEthernet0/0.",
        "topology_note": "R1 (10.0.0.1/24) <---> (10.0.0.2/24) R2 on OSPF Area 0.",
        "show_outputs": "R1# show ip ospf interface g0/0\nGigabitEthernet0/0 is up, line protocol is up\n  Internet Address 10.0.0.1/24, Area 0\n  Timer intervals configured, Hello 10, Dead 40, Wait 40, Retransmit 5\n\nR2# show ip ospf interface g0/0\nGigabitEthernet0/0 is up, line protocol is up\n  Internet Address 10.0.0.2/24, Area 0\n  Timer intervals configured, Hello 30, Dead 120, Wait 120, Retransmit 5\n",
        "expected_fault": "OSPF Hello/Dead timer mismatch (R1 Hello 10s/Dead 40s vs R2 Hello 30s/Dead 120s).",
        "osi_layer": "Layer 3",
        "concept": "Routing",
        "severity": "High",
        "expected_next_command": "show ip ospf neighbor",
        "expected_fix": "R2(config-if)# ip ospf hello-interval 10\nR2(config-if)# ip ospf dead-interval 40",
        "difficulty": "Medium",
        "explanation": "OSPF routers will not form an adjacency unless their Hello and Dead timer intervals match exactly on the common segment."
    },
    {
        "case_id": "ROUT-003",
        "symptom": "OSPF adjacency fails to form on link between R1 and R3; R1 logs area mismatch error.",
        "topology_note": "R1 (G0/1) <---> R3 (G0/1) subnet 172.16.13.0/24.",
        "show_outputs": "%OSPF-4-ERRRCV: Received packet with valid checksum but invalid area ID 0.0.0.1 from 172.16.13.3 on GigabitEthernet0/1\nR1# show ip ospf interface brief\nInterface    PID   Area            IP Address/Mask    Cost  State Nbrs(F/C)\nGi0/1        1     0               172.16.13.1/24     1     BDR   0/0\n\nR3# show ip ospf interface brief\nInterface    PID   Area            IP Address/Mask    Cost  State Nbrs(F/C)\nGi0/1        1     1               172.16.13.3/24     1     DR    0/0\n",
        "expected_fault": "OSPF Area mismatch on interconnecting link (R1 in Area 0 vs R3 in Area 1).",
        "osi_layer": "Layer 3",
        "concept": "Routing",
        "severity": "High",
        "expected_next_command": "show running-config | section router ospf",
        "expected_fix": "R3(config-router)# network 172.16.13.0 0.0.0.255 area 0",
        "difficulty": "Easy",
        "explanation": "Connecting interfaces on a point-to-point or broadcast link must be in the same OSPF Area for neighbors to exchange link-state advertisements."
    },
    {
        "case_id": "ROUT-004",
        "symptom": "Branch router cannot route any internet traffic; static default route points to non-existent IP next-hop.",
        "topology_note": "Branch-Rtr connected to ISP via G0/1 (ISP IP is 203.0.113.1/30).",
        "show_outputs": "Branch-Rtr# show ip route static\nS*    0.0.0.0/0 [1/0] via 203.0.113.5\n\nBranch-Rtr# show ip interface brief\nInterface              IP-Address      OK? Method Status                Protocol\nGigabitEthernet0/1     203.0.113.2     YES manual up                    up\n",
        "expected_fault": "Static default route next-hop 203.0.113.5 is not in the local WAN subnet 203.0.113.0/30.",
        "osi_layer": "Layer 3",
        "concept": "Routing",
        "severity": "Critical",
        "expected_next_command": "show cdp neighbors",
        "expected_fix": "Branch-Rtr(config)# no ip route 0.0.0.0 0.0.0.0 203.0.113.5\nBranch-Rtr(config)# ip route 0.0.0.0 0.0.0.0 203.0.113.1",
        "difficulty": "Medium",
        "explanation": "The /30 subnet 203.0.113.0/30 only includes 203.0.113.1 and 203.0.113.2. Next-hop 203.0.113.5 is unreachable."
    },
    {
        "case_id": "ROUT-005",
        "symptom": "EIGRP neighbors R1 and R2 fail to exchange routes across Serial 0/1/0; neighbor table is empty.",
        "topology_note": "R1 (10.10.12.1/30) <--- Serial ---> (10.10.12.2/30) R2.",
        "show_outputs": "R1# show ip protocols\nRouting Protocol is \"eigrp 100\"\n  Outgoing update filter list for all interfaces is not set\n  Incoming update filter list for all interfaces is not set\n  Default networks flagged in outgoing updates\n  Default networks accepted from incoming updates\n  EIGRP-IPv4 Protocol for AS(100)\n\nR2# show ip protocols\nRouting Protocol is \"eigrp 200\"\n  EIGRP-IPv4 Protocol for AS(200)\n",
        "expected_fault": "EIGRP Autonomous System (AS) number mismatch (R1 AS 100 vs R2 AS 200).",
        "osi_layer": "Layer 3",
        "concept": "Routing",
        "severity": "High",
        "expected_next_command": "show ip eigrp neighbors",
        "expected_fix": "R2(config)# no router eigrp 200\nR2(config)# router eigrp 100\nR2(config-router)# network 10.10.12.0 0.0.0.3",
        "difficulty": "Easy",
        "explanation": "EIGRP requires routers to be configured with the same Autonomous System number to accept and process hello packets and route updates."
    },

    # ---------------- ACL CASES ----------------
    {
        "case_id": "ACL-001",
        "symptom": "Marketing PC (192.168.10.50) cannot browse Web Server (192.168.20.100:80); ping to server also fails.",
        "topology_note": "Host (192.168.10.50) -> R1 Gateway G0/0 -> Web Server (192.168.20.100) on G0/1.",
        "show_outputs": "R1# show ip access-lists FILTER_WEB\nExtended IP access list FILTER_WEB\n    10 permit tcp 192.168.10.0 0.0.0.255 host 192.168.20.100 eq 443 (12 matches)\n\nR1# show ip interface g0/1 | include Inbound|Outbound\n  Inbound  access list is not set\n  Outbound access list is FILTER_WEB\n",
        "expected_fault": "ACL FILTER_WEB permits port 443 (HTTPS) but drops HTTP port 80 and ICMP via implicit deny.",
        "osi_layer": "Layer 4",
        "concept": "ACL",
        "severity": "High",
        "expected_next_command": "show access-lists FILTER_WEB",
        "expected_fix": "R1(config)# ip access-list extended FILTER_WEB\nR1(config-ext-nacl)# 15 permit tcp 192.168.10.0 0.0.0.255 host 192.168.20.100 eq 80",
        "difficulty": "Medium",
        "explanation": "The ACL only permits port 443. Port 80 HTTP requests hit the default 'deny ip any any' at the end of the access-list."
    },
    {
        "case_id": "ACL-002",
        "symptom": "All host traffic on VLAN 10 is blocked immediately upon applying standard access list 10 to G0/0.",
        "topology_note": "LAN Subnet 192.168.10.0/24 connected to Router interface G0/0.",
        "show_outputs": "R1# show access-lists 10\nStandard IP access list 10\n    10 permit 192.168.10.0 255.255.255.0 (0 matches)\n\nR1# show running-config interface g0/0\ninterface GigabitEthernet0/0\n ip address 192.168.10.1 255.255.255.0\n ip access-group 10 in\n",
        "expected_fault": "Standard ACL 10 uses a subnet mask (255.255.255.0) instead of a wildcard mask (0.0.0.255).",
        "osi_layer": "Layer 3",
        "concept": "ACL",
        "severity": "Critical",
        "expected_next_command": "show access-lists 10",
        "expected_fix": "R1(config)# no access-list 10\nR1(config)# access-list 10 permit 192.168.10.0 0.0.0.255",
        "difficulty": "Medium",
        "explanation": "Cisco ACLs require wildcard (inverse) masks. 'permit 192.168.10.0 255.255.255.0' matches no valid packets and triggers implicit deny."
    },
    {
        "case_id": "ACL-003",
        "symptom": "IT Administrator PC (10.0.0.50) cannot SSH to Core Router management interface 10.0.0.1; connection refused/timeout.",
        "topology_note": "Admin PC 10.0.0.50 connecting via VTY lines to R1 (10.0.0.1).",
        "show_outputs": "R1# show running-config | section line vty\nline vty 0 4\n access-class 23 in\n login local\n transport input ssh\n\nR1# show access-lists 23\nStandard IP access list 23\n    10 permit 10.0.0.10 (0 matches)\n    20 permit 10.0.0.20 (0 matches)\n",
        "expected_fault": "VTY access-class 23 does not permit Admin PC IP address 10.0.0.50.",
        "osi_layer": "Layer 4",
        "concept": "ACL",
        "severity": "High",
        "expected_next_command": "show running-config | section vty",
        "expected_fix": "R1(config)# access-list 23 permit 10.0.0.50",
        "difficulty": "Easy",
        "explanation": "The access-class applied to VTY lines restricts management access to 10.0.0.10 and 10.0.0.20. Admin PC 10.0.0.50 is dropped by implicit deny."
    },
    {
        "case_id": "ACL-004",
        "symptom": "Outbound web browsing works, but return HTTP responses from internet servers are dropped by edge router ACL.",
        "topology_note": "LAN (192.168.1.0/24) -> Edge-Rtr G0/1 -> Internet.",
        "show_outputs": "Edge-Rtr# show ip access-lists INBOUND_WAN\nExtended IP access list INBOUND_WAN\n    10 deny ip any 192.168.1.0 0.0.0.255 (450 matches)\n\nEdge-Rtr# show running-config interface g0/1\ninterface GigabitEthernet0/1\n ip address 203.0.113.2 255.255.255.252\n ip access-group INBOUND_WAN in\n",
        "expected_fault": "Inbound WAN ACL blocks all traffic without permitting established TCP sessions (missing 'permit tcp any 192.168.1.0 0.0.0.255 established').",
        "osi_layer": "Layer 4",
        "concept": "ACL",
        "severity": "Critical",
        "expected_next_command": "show access-lists INBOUND_WAN",
        "expected_fix": "Edge-Rtr(config-ext-nacl)# 5 permit tcp any 192.168.1.0 0.0.0.255 established",
        "difficulty": "Medium",
        "explanation": "Stateless ACL on WAN interface drops return packets from external web servers because no rule permits established connections."
    },

    # ---------------- NAT CASES ----------------
    {
        "case_id": "NAT-001",
        "symptom": "LAN hosts cannot access the internet; router has valid default route but `show ip nat translations` is completely empty.",
        "topology_note": "LAN Hosts (192.168.1.0/24) -> Gateway R1 (G0/0 Inside, G0/1 Outside) -> Internet (203.0.113.2).",
        "show_outputs": "R1# show ip nat translations\n\nR1# show running-config interface g0/0\ninterface GigabitEthernet0/0\n ip address 192.168.1.1 255.255.255.0\n\nR1# show running-config interface g0/1\ninterface GigabitEthernet0/1\n ip address 203.0.113.2 255.255.255.252\n ip nat outside\n\nR1# show ip nat statistics\nTotal active translations: 0 (0 static, 0 dynamic, 0 extended)\nOutside interfaces: GigabitEthernet0/1\nInside interfaces: none\n",
        "expected_fault": "Missing 'ip nat inside' configuration on LAN interface GigabitEthernet0/0.",
        "osi_layer": "Layer 3",
        "concept": "NAT",
        "severity": "Critical",
        "expected_next_command": "show running-config | include ip nat",
        "expected_fix": "R1(config)# interface GigabitEthernet0/0\nR1(config-if)# ip nat inside",
        "difficulty": "Easy",
        "explanation": "Cisco IOS NAT requires both an inside and an outside interface designated. Without 'ip nat inside' on G0/0, the router routes packets un-translated."
    },
    {
        "case_id": "NAT-002",
        "symptom": "Second LAN subnet 192.168.20.0/24 has no internet access, while 192.168.10.0/24 works perfectly.",
        "topology_note": "R1 handles NAT overload for VLAN 10 (192.168.10.0/24) and VLAN 20 (192.168.20.0/24).",
        "show_outputs": "R1# show ip access-lists NAT_ACL\nStandard IP access list NAT_ACL\n    10 permit 192.168.10.0 0.0.0.255 (3420 matches)\n\nR1# show running-config | include ip nat inside source\nip nat inside source list NAT_ACL interface GigabitEthernet0/1 overload\n",
        "expected_fault": "NAT access list NAT_ACL does not include the 192.168.20.0/24 subnet.",
        "osi_layer": "Layer 3",
        "concept": "NAT",
        "severity": "High",
        "expected_next_command": "show access-lists NAT_ACL",
        "expected_fix": "R1(config)# ip access-list standard NAT_ACL\nR1(config-std-nacl)# 20 permit 192.168.20.0 0.0.0.255",
        "difficulty": "Easy",
        "explanation": "The NAT ACL only matches 192.168.10.0/24. Packets from 192.168.20.0/24 bypass NAT and are dropped upstream on the public internet."
    },
    {
        "case_id": "NAT-003",
        "symptom": "External clients cannot access internal web server at public IP 203.0.113.10; internal hosts can access server directly.",
        "topology_note": "Public IP 203.0.113.10 -> R1 -> Internal Server (192.168.1.50:80).",
        "show_outputs": "R1# show running-config | include ip nat inside source static\nip nat inside source static tcp 192.168.1.55 80 203.0.113.10 80\n\nR1# show ip interface brief\nInterface              IP-Address      OK? Method Status                Protocol\nGigabitEthernet0/0     192.168.1.1     YES manual up                    up\nGigabitEthernet0/1     203.0.113.2     YES manual up                    up\n",
        "expected_fault": "Static NAT port forwarding statement maps to incorrect internal IP 192.168.1.55 instead of 192.168.1.50.",
        "osi_layer": "Layer 3",
        "concept": "NAT",
        "severity": "High",
        "expected_next_command": "show ip nat translations",
        "expected_fix": "R1(config)# no ip nat inside source static tcp 192.168.1.55 80 203.0.113.10 80\nR1(config)# ip nat inside source static tcp 192.168.1.50 80 203.0.113.10 80",
        "difficulty": "Easy",
        "explanation": "Static NAT forward rule forwards incoming port 80 traffic to 192.168.1.55 (an unused address), rather than the actual web server at 192.168.1.50."
    },
    {
        "case_id": "NAT-004",
        "symptom": "Only one internal user can browse the internet at a time; subsequent connections from other PCs fail until the first closes.",
        "topology_note": "Branch Router NAT configuration for 192.168.1.0/24 subnet.",
        "show_outputs": "R1# show running-config | include ip nat\nip nat inside source list 1 interface GigabitEthernet0/1\n\nR1# show ip nat translations\nPro Inside global      Inside local       Outside local      Outside global\n--- 203.0.113.2        192.168.1.10       ---                ---\n",
        "expected_fault": "NAT configuration is missing the 'overload' keyword (Port Address Translation / PAT disabled).",
        "osi_layer": "Layer 3",
        "concept": "NAT",
        "severity": "Critical",
        "expected_next_command": "show ip nat statistics",
        "expected_fix": "R1(config)# no ip nat inside source list 1 interface GigabitEthernet0/1\nR1(config)# ip nat inside source list 1 interface GigabitEthernet0/1 overload",
        "difficulty": "Medium",
        "explanation": "Without 'overload' (PAT), dynamic NAT allocates 1-to-1 IP mapping. Because there is only one public IP (G0/1), only a single host can translate at once."
    },

    # ---------------- WIRELESS CASES ----------------
    {
        "case_id": "WLAN-001",
        "symptom": "Laptops fail to associate with SSID 'Corp-Secure'; client displays 'Authentication error' or 'Cannot connect to this network'.",
        "topology_note": "Laptop-1 -> Wireless Access Point AP-1 -> Switch -> Corporate Network.",
        "show_outputs": "AP-1# show running-config | section dot11\ndot11 ssid Corp-Secure\n   vlan 10\n   authentication open\n   authentication key-management wpa_psk\n   wpa-psk ascii 7 0822455D1A16\n   (Clear text key: Cisco12345!)\n\nLaptop-1 Profile XML:\n   <SSID>Corp-Secure</SSID>\n   <KeyMaterial>Cisco12345</KeyMaterial>\n",
        "expected_fault": "WPA2 Pre-Shared Key (PSK) password mismatch between Laptop and Access Point.",
        "osi_layer": "Layer 2",
        "concept": "Wireless",
        "severity": "Medium",
        "expected_next_command": "show dot11 associations",
        "expected_fix": "Update Laptop client Wi-Fi profile key to 'Cisco12345!' to match the AP configuration.",
        "difficulty": "Easy",
        "explanation": "The 4-way WPA2 handshake fails because the client entered 'Cisco12345' instead of the AP configured PSK 'Cisco12345!'."
    },
    {
        "case_id": "WLAN-002",
        "symptom": "Guest Wi-Fi users can access internal ERP server at 192.168.10.50, violating security guest isolation policy.",
        "topology_note": "Guest SSID 'Company-Guest' on AP-1 -> Trunk -> SW-1 -> Router -> Internal LAN.",
        "show_outputs": "AP-1# show running-config | section dot11\ndot11 ssid Company-Guest\n   vlan 10\n   authentication open\n\nSW-1# show vlan brief\nVLAN Name                             Status    Ports\n---- -------------------------------- --------- -------------------------------\n10   Corporate-Internal               active    Fa0/1, Fa0/2, Fa0/10\n99   Guest-Network                    active    Fa0/20\n",
        "expected_fault": "Guest SSID 'Company-Guest' is mapped to internal corporate VLAN 10 instead of Guest VLAN 99.",
        "osi_layer": "Layer 2",
        "concept": "Wireless",
        "severity": "Critical",
        "expected_next_command": "show dot11 ssid",
        "expected_fix": "AP-1(config)# dot11 ssid Company-Guest\nAP-1(config-ssid)# vlan 99",
        "difficulty": "Medium",
        "explanation": "Mapping Guest SSID to VLAN 10 dumps untrusted guest Wi-Fi clients directly into the internal corporate broadcast domain."
    },
    {
        "case_id": "WLAN-003",
        "symptom": "Lightweight Access Point AP-Branch LED blinks green continuously; AP is not showing up on Wireless LAN Controller (WLC).",
        "topology_note": "LAP-Branch (192.168.100.15/24) -> Switch -> Router -> WLC (10.0.50.10).",
        "show_outputs": "LAP-Branch# show capwap client status\nCAPWAP State: Discovery\nCAPWAP Discovery Request Sent Count: 28\nLast Error: Discovery response from WLC timed out\n\nR-Branch# show running-config | section dhcp\nip dhcp pool AP_POOL\n network 192.168.100.0 255.255.255.0\n default-router 192.168.100.1\n",
        "expected_fault": "DHCP pool AP_POOL is missing Option 43 (WLC IP address 10.0.50.10) for CAPWAP discovery.",
        "osi_layer": "Layer 7",
        "concept": "Wireless",
        "severity": "High",
        "expected_next_command": "show capwap client detail",
        "expected_fix": "R-Branch(config-dhcp)# option 43 ip 10.0.50.10",
        "difficulty": "Medium",
        "explanation": "Lightweight APs in remote subnets rely on DHCP Option 43 to learn the IP address of the WLC to establish a CAPWAP tunnel."
    },
    {
        "case_id": "WLAN-004",
        "symptom": "Smartphones connecting to 5GHz Wi-Fi experience intermittent drops; 2.4GHz radio interface is shut down.",
        "topology_note": "Autonomous Cisco AP-2802 servicing warehouse barcode scanners.",
        "show_outputs": "AP-Warehouse# show interfaces Dot11Radio 0\nDot11Radio0 is administratively down, line protocol is down\n  Hardware is BCM4366, address is 00a3.d144.1200\n\nAP-Warehouse# show interfaces Dot11Radio 1\nDot11Radio1 is up, line protocol is up\n",
        "expected_fault": "2.4GHz radio interface (Dot11Radio0) is administratively disabled.",
        "osi_layer": "Layer 1",
        "concept": "Wireless",
        "severity": "Medium",
        "expected_next_command": "show interfaces dot11radio 0 brief",
        "expected_fix": "AP-Warehouse(config)# interface Dot11Radio0\nAP-Warehouse(config-if)# no shutdown",
        "difficulty": "Easy",
        "explanation": "The 2.4GHz radio (Dot11Radio0) is shut down, preventing 2.4GHz legacy devices and long-range clients from connecting."
    },

    # ---------------- COMPREHENSIVE MULTI-LAYER CASES ----------------
    {
        "case_id": "VLAN-005",
        "symptom": "Switch trunk link Gi0/1 is negotiating dynamic desirable mode but peer port is set to access mode.",
        "topology_note": "SW-A (Gi0/1) <---> (Gi0/1) SW-B.",
        "show_outputs": "SW-A# show interfaces Gi0/1 switchport\nAdministrative Mode: dynamic desirable\nOperational Mode: static access\nAccess Mode VLAN: 1 (default)\n\nSW-B# show interfaces Gi0/1 switchport\nAdministrative Mode: static access\nOperational Mode: static access\nAccess Mode VLAN: 1\n",
        "expected_fault": "SW-B is statically configured in access mode, preventing DTP dynamic trunk negotiation.",
        "osi_layer": "Layer 2",
        "concept": "VLAN",
        "severity": "High",
        "expected_next_command": "show dtp interface Gi0/1",
        "expected_fix": "SW-B(config-if)# switchport mode trunk\nSW-A(config-if)# switchport mode trunk",
        "difficulty": "Medium",
        "explanation": "Dynamic Desirable on SW-A cannot form a trunk with a port forced into static access mode on SW-B."
    },
    {
        "case_id": "GW-005",
        "symptom": "Host-B cannot communicate with other hosts in 172.16.5.0/24; IP address was configured with wrong subnet mask /16 instead of /24.",
        "topology_note": "Host-B (172.16.5.50) -> Switch -> Router Gateway (172.16.5.1/24).",
        "show_outputs": "Host-B> ipconfig\n   IPv4 Address. . . . . . . . . . . : 172.16.5.50\n   Subnet Mask . . . . . . . . . . . : 255.255.0.0\n   Default Gateway . . . . . . . . . : 172.16.5.1\n\nR1# show ip interface brief g0/0\nInterface              IP-Address      OK? Method Status                Protocol\nGigabitEthernet0/0     172.16.5.1      YES manual up                    up\n(Mask on R1: 255.255.255.0)\n",
        "expected_fault": "Subnet mask mismatch: Host-B has 255.255.0.0 (/16) while gateway router uses 255.255.255.0 (/24).",
        "osi_layer": "Layer 3",
        "concept": "Gateway",
        "severity": "Medium",
        "expected_next_command": "ping 172.16.6.1",
        "expected_fix": "Change Host-B subnet mask to 255.255.255.0 (/24).",
        "difficulty": "Easy",
        "explanation": "Host-B misinterprets 172.16.6.x as local broadcast domain instead of routing through 172.16.5.1, resulting in silent packet drop."
    },
    {
        "case_id": "ROUT-006",
        "symptom": "Static route configured with incorrect exit interface; packets for 192.168.50.0/24 egress out LAN interface instead of WAN.",
        "topology_note": "R1 has LAN on G0/0 (192.168.1.1/24) and WAN on G0/1 (10.0.0.1/30).",
        "show_outputs": "R1# show ip route static\nS    192.168.50.0/24 is directly connected, GigabitEthernet0/0\n\nR1# show ip interface brief\nInterface              IP-Address      OK? Method Status                Protocol\nGigabitEthernet0/0     192.168.1.1     YES manual up                    up\nGigabitEthernet0/1     10.0.0.1        YES manual up                    up\n",
        "expected_fault": "Static route specifies exit interface GigabitEthernet0/0 (LAN) instead of GigabitEthernet0/1 (WAN).",
        "osi_layer": "Layer 3",
        "concept": "Routing",
        "severity": "High",
        "expected_next_command": "show ip route 192.168.50.1",
        "expected_fix": "R1(config)# no ip route 192.168.50.0 255.255.255.0 GigabitEthernet0/0\nR1(config)# ip route 192.168.50.0 255.255.255.0 GigabitEthernet0/1",
        "difficulty": "Easy",
        "explanation": "Packets destined for remote network 192.168.50.0 are broadcasted out the LAN interface G0/0 instead of sent towards the next-hop router via G0/1."
    },
    {
        "case_id": "DHCP-005",
        "symptom": "PC receives IP address but cannot resolve corporate intranet names; DHCP pool dns-server parameter is misspelled as dnsserver or omitted.",
        "topology_note": "Router R1 serves DHCP for 10.10.100.0/24 subnet.",
        "show_outputs": "PC-1> ipconfig /all\n   IPv4 Address. . . . . . . . . . . : 10.10.100.25\n   Default Gateway . . . . . . . . . : 10.10.100.1\n   DNS Servers . . . . . . . . . . . : 0.0.0.0\n\nR1# show running-config | section ip dhcp pool\nip dhcp pool CORP_USERS\n   network 10.10.100.0 255.255.255.0\n   default-router 10.10.100.1\n",
        "expected_fault": "Missing 'dns-server' configuration in DHCP pool CORP_USERS.",
        "osi_layer": "Layer 7",
        "concept": "DHCP",
        "severity": "High",
        "expected_next_command": "show ip dhcp pool CORP_USERS",
        "expected_fix": "R1(config-dhcp)# dns-server 10.10.1.10 8.8.8.8",
        "difficulty": "Easy",
        "explanation": "The DHCP pool supplies an IP and gateway, but omits DNS server option (option 6), leaving client DNS server configured as 0.0.0.0."
    },
    {
        "case_id": "ACL-005",
        "symptom": "DNS queries from LAN clients to public DNS 8.8.8.8 are denied; web browsing fails across the network.",
        "topology_note": "LAN -> R1 -> WAN (ACL on G0/1 outbound).",
        "show_outputs": "R1# show ip access-lists OUTBOUND_WAN\nExtended IP access list OUTBOUND_WAN\n    10 permit tcp 192.168.1.0 0.0.0.255 any eq www (450 matches)\n    20 permit tcp 192.168.1.0 0.0.0.255 any eq 443 (890 matches)\n    30 deny ip any any (120 matches)\n",
        "expected_fault": "ACL OUTBOUND_WAN does not permit UDP port 53 (DNS) outbound traffic.",
        "osi_layer": "Layer 4",
        "concept": "ACL",
        "severity": "High",
        "expected_next_command": "show access-lists OUTBOUND_WAN",
        "expected_fix": "R1(config-ext-nacl)# 25 permit udp 192.168.1.0 0.0.0.255 any eq domain",
        "difficulty": "Easy",
        "explanation": "Browsers require DNS (UDP 53) to resolve hostnames before establishing TCP HTTP/HTTPS connections. Denying UDP 53 breaks all domain browsing."
    },
    {
        "case_id": "VLAN-006",
        "symptom": "VoIP IP Phones and Workstations on the same physical port cannot communicate; voice VLAN not configured on switchport.",
        "topology_note": "Cisco IP Phone connected to Switch Fa0/10, PC daisy-chained behind IP Phone.",
        "show_outputs": "SW-1# show running-config interface fa0/10\ninterface FastEthernet0/10\n switchport mode access\n switchport access vlan 10\n\nSW-1# show interfaces fa0/10 switchport\nName: Fa0/10\nOperational Mode: static access\nAccess Mode VLAN: 10 (Data)\nVoice VLAN: none\n",
        "expected_fault": "Missing Voice VLAN configuration on switchport Fa0/10 (Voice VLAN is 'none').",
        "osi_layer": "Layer 2",
        "concept": "VLAN",
        "severity": "Medium",
        "expected_next_command": "show interfaces fa0/10 switchport",
        "expected_fix": "SW-1(config-if)# switchport voice vlan 150",
        "difficulty": "Medium",
        "explanation": "Cisco IP Phones require `switchport voice vlan <id>` to tag voice frames with 802.1Q and assign appropriate CoS QoS values."
    },
    {
        "case_id": "ROUT-007",
        "symptom": "RIP routing updates are not received by neighbor router R2; R1 is sending RIP version 1 broadcasts while R2 listens for version 2 multicasts.",
        "topology_note": "R1 (10.0.0.1/24) <---> (10.0.0.2/24) R2 running RIP.",
        "show_outputs": "R1# show ip protocols\nRouting Protocol is \"rip\"\n  Sending updates every 30 seconds\n  Default version-control: send version 1, receive any version\n\nR2# show ip protocols\nRouting Protocol is \"rip\"\n  Default version-control: send version 2, receive version 2\n",
        "expected_fault": "RIP version mismatch between R1 (sending v1 broadcasts) and R2 (listening for v2 multicasts).",
        "osi_layer": "Layer 3",
        "concept": "Routing",
        "severity": "Medium",
        "expected_next_command": "show ip rip database",
        "expected_fix": "R1(config)# router rip\nR1(config-router)# version 2",
        "difficulty": "Easy",
        "explanation": "RIPv2 ignores RIPv1 classful broadcast updates by default. Setting 'version 2' on R1 enables classless RIPv2 multicast updates."
    },
    {
        "case_id": "GW-006",
        "symptom": "Duplicate IP address configured on Router subinterface G0/0.10 and another static workstation on VLAN 10.",
        "topology_note": "Host-1 (192.168.10.1) and Router G0/0.10 (192.168.10.1).",
        "show_outputs": "%SYS-3-IP_DUP: Duplicate IP address 192.168.10.1 on GigabitEthernet0/0.10, sourced by mac 0001.64d2.a112\nR1# show ip arp | include 192.168.10.1\nInternet  192.168.10.1            0   0001.64d2.a112  ARPA   GigabitEthernet0/0.10\nInternet  192.168.10.1            -   0009.7c55.bb01  ARPA   GigabitEthernet0/0.10\n",
        "expected_fault": "Duplicate IP address conflict: Host workstation is assigned identical IP (192.168.10.1) as Router gateway.",
        "osi_layer": "Layer 3",
        "concept": "Gateway",
        "severity": "Critical",
        "expected_next_command": "show mac address-table on SW-1",
        "expected_fix": "Reconfigure conflicting workstation to use 192.168.10.50 instead of gateway IP.",
        "difficulty": "Easy",
        "explanation": "A workstation statically misconfigured with the gateway IP creates ARP table thrashing, breaking routing for the entire subnet."
    }
]

os.makedirs('data', exist_ok=True)
csv_path = os.path.join('data', 'cases.csv')

fields = [
    "case_id", "symptom", "topology_note", "show_outputs",
    "expected_fault", "osi_layer", "concept", "severity",
    "expected_next_command", "expected_fix", "difficulty", "explanation"
]

with open(csv_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fields, quoting=csv.QUOTE_ALL)
    writer.writeheader()
    for case in cases:
        writer.writerow(case)

print(f"Successfully generated {len(cases)} cases in {csv_path}")

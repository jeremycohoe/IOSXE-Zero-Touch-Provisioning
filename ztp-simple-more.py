print "\n\n *** Sample ZTP Day0 Python Script *** \n\n"
# Importing cli module
import cli

print "Configure hostname, vlans, and others\n\n"

cli.configurep(["hostname C93-Services"])

cli.configurep(["license boot level network-advantage addon dna-advantage"])

cli.configurep(["ip routing"])
cli.configurep(["ip domain name cisco.com"])

cli.configurep(["interface loopback 0", "ip address 10.0.114.5 255.255.255.255", "end"])

cli.configurep(["interface TenGigabitEthernet1/1/1", "description L2-to-C9404-SVL-Te1/2/0/4 ", "switchport access vlan 100", "switchport mode access", "end"])
cli.configurep(["interface TenGigabitEthernet1/1/2", "description L2-to-C9404-SVL-Te2/2/0/4 ", "switchport access vlan 100", "switchport mode access", "end"])

cli.configurep(["username admin privilege 15 secret Cisco123"])
cli.configurep(["username admin2 privilege 15 secret Cisco456"])

cli.configurep(["snmp-server community Public RO "])
cli.configurep(["snmp-server community Private RW "])

cli.configurep(["ip ssh source-interface Loopback0"])
cli.configurep(["ip ssh version 2"])
cli.configurep(["ip scp server enable "])

cli.configurep(["crypto key generate rsa"])

cli.configurep(["vlan 1", "end" ])
cli.configurep(["interface vlan 1", "shut", "no ip address", "end"])

cli.configurep(["vlan 100", "end"])
cli.configurep(["interface vlan 100", "description Services", "ip address 10.0.100.3 255.255.255.0", "shut", "no shut", "end"])

cli.configurep(["ip route 0.0.0.0 0.0.0.0 10.0.100.1", "end"])

cli.configurep(["line con 0" , "privilege level 15" , "stopbits 1", "end"])
cli.configurep(["line vty 0 15" , "privilege level 15" , "login local", "transport input all", "end"])

cli.configurep(["netconf-yang", "end"])

print "\n\n *** Executing show ip interface brief  *** \n\n"
cli_command = "sh ip int brief"
cli.executep(cli_command)

print "\n\n *** ZTP Day0 Python Script Execution Complete *** \n\n"

from cli import configure, cli
import cli
import re
import json
import time

eem_commands = ['no event manager applet catchall',
                'event manager applet catchall',
                'event  cli pattern ".*" sync no skip no',
                'action 1 syslog msg "$_cli_msg"'
                ]
results = configure(eem_commands)
print ("*** Successfully configured catchall EEM script on device! ***")

print("\n\n *** Sample ZTP Day0 Python Script *** \n\n")
print("Configure vlan interface, gateway, aaa, and enable netconf-yang, etc... \n\n")

cli.configurep(["int gi1/0/24","no switchport", "ip address 10.1.1.5 255.255.255.0", "no shut", "end"])
cli.configurep(["ip route 0.0.0.0 0.0.0.0 10.1.1.3", "end"])
cli.configurep(["int vlan 1", "no ip address", "end"])
cli.configurep(["username admin privilege 15 secret 0 Cisco123"])
cli.configurep(["ip tftp blocksize 8192", "end"])
cli.configurep(["ip tcp window-size 65535", "end"])
cli.configurep(["ip http client source-interface GigabitEthernet1/0/24", "end"])
cli.configurep(["interface Loopback0", "ip address 192.168.12.1 255.255.255.0", "end"])
cli.configurep(["aaa new-model", "aaa authentication login default local", "end"])
cli.configurep(["aaa authorization exec default local", "aaa session-id common", "end"])
cli.configurep(["netconf-yang", "end"])
cli.configurep(["gnxi", "gnxi secure-init", "gnxi secure-server", "end"])
cli.configurep(["line vty 0 32", "transport input all", "exec-timeout 0 0", "no ip domain lookup", "end"])
cli.configurep(["ip scp server enable", "end"])
cli.configurep(["hostname C9300", "ntp server 10.1.1.3", "clock timezone Pacific -7", "end"])
cli.configurep(["telemetry ietf subscription 101","encoding encode-kvgpb","filter xpath /process-cpu-ios-xe-oper:cpu-usage/cpu-utilization/five-seconds","stream yang-push","update-policy periodic 30000","receiver ip address 10.1.1.3 57500 protocol grpc-tcp","end"])
cli.configurep(["logging buffered 32000", "logging host 10.1.1.3 transport udp port 5144", "line con 0", "logging synchronous limit 1000", "end"])

print("\n\n *** Executing show ip interface brief  *** \n\n")
cli_command = "sh ip int brief | exclude unassigned"

cli.executep(cli_command)
print("\n\n *** ZTP Day0 Python Script Execution Complete *** \n\n")

cli.configurep(["int gi1/0/24","no switchport", "ip address 10.1.1.5 255.255.255.0", "no shut", "end"])
cli.configurep(["ip route 0.0.0.0 0.0.0.0 10.1.1.3", "end"])
cli.configurep(["int vlan 1", "no ip address", "end"])

print("\n\n *** Executing show ip interface brief  *** \n\n")
cli_command = "sh ip int brief | exclude unassigned"

cli.executep(cli_command)
print("\n\n *** ZTP Day0 Python Script Execution Complete *** \n\n")

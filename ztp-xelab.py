auto@pod29-xelab:~$ cat /tftpboot/ztp-simple.py
from cli import configure, cli
import cli
import re
import json
import time

print("\n\n *** Sample ZTP Day0 Python Script *** \n\n")

print("\n\n *** Determine hostname based on serial number  *** \n\n")
hostnames = {
    'FCW2129G042': 'c9300-pod01', 
    'FCW2129G01K': 'c9300-pod02', 
    'FCW2129G02M': 'c9300-pod03', 
    'FCW2129L05L': 'c9300-pod04', 
    'FCW2129L03E': 'c9300-pod05', 
    'FCW2241DH93': 'c9300-pod06', 
    'FCW2126G05V': 'c9300-pod07', 
    'FCW2241AHB1': 'c9300-pod08', 
    'FCW2129L0DU': 'c9300-pod09', 
    'FCW2241AHAT': 'c9300-pod10', 
    'FCW2129G02U': 'c9300-pod11', 
    'FCW2129L05A': 'c9300-pod12', 
    'FCW2241CHAT': 'c9300-pod13', 
    'FCW2129L049': 'c9300-pod14', 
    'FCW2241CH9K': 'c9300-pod15', 
    'FCW2241D0KM': 'c9300-pod16', 
    'FCW2129G0EF': 'c9300-pod17', 
    'FCW2129L09E': 'c9300-pod18', 
    'FCW2241BH95': 'c9300-pod19', 
    'FCW2241BH96': 'c9300-pod20', 
    'FCW2129L04A': 'c9300-pod21', 
    'FCW2241DHBH': 'c9300-pod22', 
    'FCW2146G095': 'c9300-pod23', 
    'FCW2241DHBN': 'c9300-pod24', 
    'FCW2129L02R': 'c9300-pod25', 
    'FCW2129L03Z': 'c9300-pod26', 
    'FCW2129G03A': 'c9300-pod27', 
    'FCW2129G03G': 'c9300-pod28', 
    'FCW2129G0PZ': 'c9300-pod29', 
    'FCW2129L05N': 'c9300-pod30'
}

## set hostname 
serial = cli.execute('show version | i System Serial Number')
serial = serial[serial.find(': ')+2:].strip() # we just care about the part after the ': ' and remove any newline chars throughout (one is at the end of the string)
if(serial in hostnames):
    hostname = hostnames[serial]
else: 
    hostname = 'c9300' # create a default hostname incase a mapping isn't found
cli.configurep(['hostname {}'.format(hostname)])

# Configure interface
print("Configure vlan interface, gateway, aaa, and enable netconf-yang, etc... \n\n")
cli.configurep(["int gi1/0/24","no switchport", "ip address 10.1.1.5 255.255.255.0", "no shut", "end"])
cli.configurep(["ip route 0.0.0.0 0.0.0.0 10.1.1.3", "end"])
cli.configurep(["int vlan 1", "no ip address", "end"])
# AAA
cli.configurep(["username admin privilege 15 secret 0 Cisco123"])
cli.configurep(["aaa new-model", "aaa authentication login default local", "end"])
cli.configurep(["aaa authorization exec default local", "aaa session-id common", "end"])
# TCP settings
cli.configurep(["ip tftp blocksize 8192", "end"])
cli.configurep(["ip tcp window-size 65535", "end"])
cli.configurep(["ip http client source-interface GigabitEthernet1/0/24", "end"])
# Create loopback0
cli.configurep(["interface Loopback0", "ip address 192.168.12.1 255.255.255.192", "end"])
# Enable NETCONF-YANG API
cli.configurep(["netconf-yang", "end"])
# NETCONF from Guestshell
#cli.configurep(["netconf-yang ssh local-vrf guestshell enable", "end"])
# Enable gNMI secure API
#cli.configurep(["gnxi", "gnxi secure-init", "gnxi secure-server", "end"])
# Enable gNMI non-secured API
cli.configurep(["gnxi", "gnxi server", "end"])
# Line settings + syslog
cli.configurep(["line vty 0 32", "transport input all", "exec-timeout 0 0", "end"])
cli.configurep(["logging buffered 32000", "logging host 10.1.1.3 transport udp port 5144", "line con 0", "logging synchronous limit 1000", "end"])
# Secure SCP
cli.configurep(["ip scp server enable", "end"])
# NTP time
cli.configurep(["ntp server 10.1.1.3", "clock timezone Pacific -7", "end"])
# DNS settings
cli.configurep(["ip name-server 10.1.1.3", "ip domain lookup", "end"])
# Dial-Out MDT
cli.configurep(["telemetry ietf subscription 1011","encoding encode-kvgpb","filter xpath /process-cpu-ios-xe-oper:cpu-usage/cpu-utilization/five-seconds","stream yang-push","update-policy periodic 30000","receiver ip address 10.1.1.3 57500 protocol grpc-tcp","end"])
#
# Show ip int brief
print("\n\n *** Executing show ip interface brief  *** \n\n")
cli_command = "sh ip int brief | exclude unassigned"
#
# Configure interface 2nd time
cli.configurep(["int gi1/0/24","no switchport", "ip address 10.1.1.5 255.255.255.0", "no shut", "end"])
cli.configurep(["ip route 0.0.0.0 0.0.0.0 10.1.1.3", "end"])
cli.configurep(["int vlan 1", "no ip address", "end"])
cli.configurep(["int gi1/0/13", "shut", "end"])
cli.configurep(["int gi1/0/1", "desc flag: 8a53f11c1afb6c714c91eab145b0580cce61c69d94820e5fd342f3874f2d9a57", "end"])

#
# Show interface
print("\n\n *** Executing show ip interface brief  *** \n\n")
cli_command = "sh ip int brief | exclude unassigned"
cli.executep(cli_command)
#
# Enable RESTCONF API
cli.configurep(["restconf", "end"])
cli.executep(cli_command)
#
# Configure Guest Shell via EEM applet
print ("*** Configure eem_gs_config ... ***")
eem_gs_commands = ['no event manager applet eem_gs_config',
                'event manager applet eem_gs_config',
                'event none maxrun 900',
                'action 1003 wait 250',
                'action 1004 cli command "enable"',
                'action 1005 cli command "conf t"',
                'action 1006 cli command "iox"',
                'action 1007 cli command "ip nat inside source list NAT_ACL interface vlan 1 overload"',
                'action 1008 cli command "ip access-list standard NAT_ACL"',
                'action 1009 cli command "permit 192.168.0.0 0.0.255.255"',
                'action 1010 cli command "exit"',
                'action 1011 cli command "vlan 4094"',
                'action 1012 cli command "exit"',
                'action 1013 cli command "int vlan 4094"',
                'action 1014 cli command "ip address 192.168.2.1 255.255.255.0"',
                'action 1015 cli command "ip nat inside"',
                'action 1016 cli command "ip routing"',
                'action 1017 cli command "ip route 0.0.0.0 0.0.0.0 10.1.1.3"',
                'action 1101 cli command "app-hosting appid guestshell"',
                'action 1102 cli command "app-vnic AppGigabitEthernet trunk"',
                'action 1103 cli command "vlan 4094 guest-interface 0"',
                'action 1104 cli command "guest-ipaddress 192.168.2.2 netmask 255.255.255.0"',
                'action 1105 cli command "exit"',
                'action 1106 cli command "exit"',
                'action 1107 cli command "app-default-gateway 192.168.2.1 guest-interface 0"',
                'action 1108 cli command "name-server0 128.107.212.175"',
                'action 1109 cli command "name-server1 64.102.6.247"',
                'action 1110 cli command "exit"',
                'action 1111 cli command "interface AppGigabitEthernet1/0/1"',
                'action 1112 cli command "switchport mode trunk"',
                'action 1113 cli command "exit"',
                'action 1114 cli command "end"'
                ]
results = configure(eem_gs_commands)

# Enable Guest Shell via EEM applet
print ("*** Configure cli2yang examples on device... ***")
eem_enable_gs_commands = ['no event manager applet enable_gs',
                'event manager applet enable_gs',
                'event none maxrun 900',
                'action 0001 cli command "enable"',
                'action 0002 wait 300',
                'action 0003 cli command "guestshell enable"',
                'action 0004 wait 120',
                'action 0005 cli command "guestshell run /usr/bin/bash /bootflash/guest-share/cli2yang.sh"'
                ]
results = configure(eem_enable_gs_commands)
print ("*** Successfully configured cli2yang on device! ***")

# Run the cli2yang Guest Shell custom integration for CTF:
# Copy the files for the cli2yang
cli_command = "copy tftp://10.1.1.3/cli2yang.tgz flash:guest-share/"
cli.executep(cli_command)
cli_command = "copy tftp://10.1.1.3/cli2yang.sh  flash:guest-share/"
cli.executep(cli_command)
cli_command = "event manager run eem_gs_config"
cli.executep(cli_command)
cli_command = "event manager run enable_gs"
cli.executep(cli_command)

# Enable catchall EEM applet
print ("*** Configure catchall EEM script on device... ***")
eem_commands = ['no event manager applet catchall',
                'event manager applet catchall',
                'event  cli pattern ".*" sync no skip no',
                'action 1 syslog msg "$_cli_msg"'
                ]
results = configure(eem_commands)
print ("*** Successfully configured catchall EEM script on device! ***")

# Save config
cli_command = "write memory"
cli.executep(cli_command)

# The End.
print("\n\n *** Finished device day 0 configuration... *** \n\n")
print("\n\n *** *** *** \n\n")
print("\n\n *** *** \n\n")
print("\n\n *** \n\n")
print("\n\n FLAG TO FOLLOW :) \n\n")
print("\n\n *** \n\n")
print("\n\n *** \n\n")
print("\n\n *** \n\n")
print("\n\n flag: 5a92266d5b83d55a21ec262961c3d226e7e0310b  \n\n")
print("\n\n *** \n\n")
print("\n\n \n\n")#
print("\n\n \n\n")

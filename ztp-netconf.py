from cli import configure, cli
import cli
import re
import json
import time

print("\n\n *** Sample ZTP Day0 Python Script *** \n\n")

# Enable EEM applet
print ("*** Configure catchall EEM script on device... ***")
eem_commands = ['no event manager applet catchall',
                'event manager applet catchall',
                'event  cli pattern ".*" sync no skip no',
                'action 1 syslog msg "$_cli_msg"'
                ]
results = configure(eem_commands)
print ("*** Successfully configured catchall EEM script on device! ***")

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
cli.configurep(["interface Loopback0", "ip address 192.168.12.1 255.255.255.0", "end"])
# NETCONF-YANG
cli.configurep(["netconf-yang", "end"])
# NETCONF from Guestshell
cli.configurep(["netconf-yang ssh local-vrf guestshell enable", "end"])
# gNMI secure
#cli.configurep(["gnxi", "gnxi secure-init", "gnxi secure-server", "end"])
# gNMI non-secured
cli.configurep(["gnxi", "gnxi server", "end"])
# Line settings
cli.configurep(["line vty 0 32", "transport input all", "exec-timeout 0 0", "end"])
# Line logging
cli.configurep(["logging buffered 32000", "logging host 10.1.1.3 transport udp port 5144", "line con 0", "logging synchronous limit 1000", "end"])
# Secure SCP
cli.configurep(["ip scp server enable", "end"])
# Hostname and NTP time
cli.configurep(["hostname C9300", "ntp server 10.1.1.3", "clock timezone Pacific -7", "end"])
# DNS settings
cli.configurep(["ip name-server 10.1.1.3", "ip domain lookup", "end"])
# Dial-Out MDT
#cli.configurep(["telemetry ietf subscription 101","encoding encode-kvgpb","filter xpath /process-cpu-ios-xe-oper:cpu-usage/cpu-utilization/five-seconds","stream yang-push","update-policy periodic 30000","receiver ip address 10.1.1.3 57500 protocol grpc-tcp","end"])
#
#
#
# Show ip int brief
print("\n\n *** Executing show ip interface brief  *** \n\n")
cli_command = "sh ip int brief | exclude unassigned"
#
# Configure interface
cli.configurep(["int gi1/0/24","no switchport", "ip address 10.1.1.5 255.255.255.0", "no shut", "end"])
cli.configurep(["ip route 0.0.0.0 0.0.0.0 10.1.1.3", "end"])
cli.configurep(["int vlan 1", "no ip address", "end"])
#
# Show interface
print("\n\n *** Executing show ip interface brief  *** \n\n")
cli_command = "sh ip int brief | exclude unassigned"
cli.executep(cli_command)
#
# Enable RESTCONF
cli.configurep(["restconf", "end"])
cli.executep(cli_command)
#
# Time to go !
print("\n\n *** Finished device day 0 configuration... *** \n\n")
print("\n\n *** *** *** \n\n")
print("\n\n *** *** \n\n")
print("\n\n *** \n\n")
#
#
# Now for the fun part... lets send a GET request for the device hostname to the NETCONF interface connected through Guesthshell's localhost port 830
print("\n\n *** Starting NETCONF usecase, delay some seconds while NETCONF starts... *** \n\n")
print("\n\n *** \n\n")
time.sleep(90)
print("\n\n *** \n\n")
print("\n\n *** Lest go... *** \n\n")
from ncclient import manager
import sys
import xml.dom.minidom

HOST = '127.0.0.1'
# use the NETCONF port for your device
PORT = 830
# use the user credentials for your  device
USER = 'admin'
PASS = 'Cisco123'

FILTER = '''
                <filter xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
                  <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
                    <hostname></hostname>
                  </native>
                </filter>
            '''

def main():
    """
    Main method that prints netconf capabilities of remote device.
    """
    # Create a NETCONF session to the router with ncclient
    with manager.connect(host=HOST, port=PORT, username=USER,
                         password=PASS, hostkey_verify=False,
                         device_params={'name': 'default'},
                         allow_agent=False, look_for_keys=False) as m:

        # Retrieve the configuraiton
        results = m.get_config('running', FILTER)
        # Print the output in a readable format
        print(xml.dom.minidom.parseString(results.xml).toprettyxml())


if __name__ == '__main__':
    sys.exit(main())

print("\n\n *** Finished NETCONF example... *** \n\n")
print("\n\n *** *** *** \n\n")
print("\n\n *** *** \n\n")
print("\n\n *** \n\n")

print("\n\n *** ZTP Day0 Python Script Execution Complete *** \n\n")

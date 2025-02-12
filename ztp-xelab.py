# Updated 12FEB2025
from cli import configure, cli
import cli
import re
import json
import time

print("\n\n *** Sample ZTP Day0 Python Script *** \n\n")

# 2024 for 30x C9300 and 30x C9300 with IP .5 and .55
hostnames = {
    'FOC2727Y739': ('cat9300x-pod01a', 21, 5),
    'FCW2129G042': ('cat9300-pod01b', 21, 55),
    'FOC2727Y6MX': ('cat9300x-pod02a', 22, 5),
    'FCW2129G01K': ('cat9300-pod02b', 22, 55),
    'FOC2727Y75Q': ('cat9300x-pod03a', 23, 5),
    'FCW2129G02M': ('cat9300-pod03b', 23, 55),
    'FOC2727Y767': ('cat9300x-pod04a', 24, 5),
    'FCW2129L05L': ('cat9300-pod04b', 24, 55),
    'FOC2727Y72E': ('cat9300x-pod05a', 25, 5),
    'FCW2129L03E': ('cat9300-pod05b', 25, 55),
    'FOC2727Y72J': ('cat9300x-pod06a', 26, 5),
    'FCW2241DH93': ('cat9300-pod06b', 26, 55),
    'FOC2727Y6TE': ('cat9300x-pod07a', 27, 5),
    'FCW2126G05V': ('cat9300-pod07b', 27, 55),
    'FOC2727Y70N': ('cat9300x-pod08a', 28, 5),
    'FCW2241AHB1': ('cat9300-pod08b', 28, 55),
    'FOC2727Y72F': ('cat9300x-pod09a', 29, 5),
    'FCW2129L0DU': ('cat9300-pod09b', 29, 55),
    'FOC2727Y72G': ('cat9300x-pod10a', 30, 5),
    'FCW2241AHAT': ('cat9300-pod10b', 30, 55),
    'FOC2727Y6ML': ('cat9300x-pod11a', 31, 5),
    'FCW2129G02U': ('cat9300-pod11b', 31, 55),
    'FOC2727Y6TW': ('cat9300x-pod12a', 32, 5),
    'FCW2129L05A': ('cat9300-pod12b', 32, 55),
    'FOC2727Y73C': ('cat9300x-pod13a', 33, 5),
    'FCW2241CHAT': ('cat9300-pod13b', 33, 55),
    'FOC2727Y6Z9': ('cat9300x-pod14a', 34, 5),
    'FCW2129L049': ('cat9300-pod14b', 34, 55),
    'FOC2727Y6EJ': ('cat9300x-pod15a', 35, 5),
    'FCW2241CH9K': ('cat9300-pod15b', 35, 55),
    'FOC2727Y71E': ('cat9300x-pod16a', 36, 5),
    'FCW2241D0KM': ('cat9300-pod16b', 36, 55),
    'FOC2727Y6MU': ('cat9300x-pod17a', 37, 5),
    'FCW2129G0EF': ('cat9300-pod17b', 37, 55),
    'FOC2727Y6X1': ('cat9300x-pod18a', 38, 5),
    'FCW2129L09E': ('cat9300-pod18b', 38, 55),
    'FOC2724YB76': ('cat9300x-pod19a', 39, 5),
    'FCW2241BH95': ('cat9300-pod19b', 39, 55),
    'FOC2727Y73Z': ('cat9300x-pod20a', 40, 5),
    'FCW2241BH96': ('cat9300-pod20b', 40, 55),
    'FOC2724YBQ4': ('cat9300x-pod21a', 41, 5),
    'FCW2129L04A': ('cat9300-pod21b', 41, 55),
    'FOC2724YBQ9': ('cat9300x-pod22a', 42, 5),
    'FCW2241DHBH': ('cat9300-pod22b', 42, 55),
    'FOC2724YBQH': ('cat9300x-pod23a', 43, 5),
    'FCW2146G095': ('cat9300-pod23b', 43, 55),
    'FOC2724YBSA': ('cat9300x-pod24a', 44, 5),
    'FCW2241DHBN': ('cat9300-pod24b', 44, 55),
    'FOC2724YBPN': ('cat9300x-pod25a', 45, 5),
    'FCW2129L02R': ('cat9300-pod25b', 45, 55),
    'FOC2724YBPZ': ('cat9300x-pod26a', 46, 5),
    'FCW2129L03Z': ('cat9300-pod26b', 46, 55),
    'FOC2724YBP8': ('cat9300x-pod27a', 47, 5),
    'FCW2129G03A': ('cat9300-pod27b', 47, 55),
    'FOC2724YBS5': ('cat9300x-pod28a', 48, 5),
    'FCW2129G03G': ('cat9300-pod28b', 48, 55),
    'FOC2724YBMS': ('cat9300x-pod29a', 49, 5),
    'FCW2129G0PZ': ('cat9300-pod29b', 49, 55),
    'FOC2724YBPM': ('cat9300x-pod30a', 50, 5),
    'FCW2129L05N': ('cat9300-pod30b', 50, 55),
}

#Old pod 30  nonX SN = FVH2812L1A3


## set hostname
serial = cli.execute('show version | i System Serial Number')
serial = serial[serial.find(': ')+2:].strip() # we just care about the part after the ': ' and remove any newline chars throughout (one is at the end of the string)
if(serial in hostnames):
    values = hostnames[serial]
    hostname = values[0]
    vlan = str(values[1])
    ipaddr = str(values[2])
else:
    hostname = 'c9300'  # create a default hostname incase a mapping isn't found
cli.configurep(['hostname {}'.format(hostname)])

# Configure interface
print("Configure vlan interface, gateway, aaa, and enable netconf-yang, etc... \n\n")
ID = hostname[-2:]
print("ID is ...." + ID)

cli.configurep(["vlan " + vlan, "end"])
cli.configurep(["int vlan 1", "no ip address", "end"])
cli.configurep(["int vlan " + vlan, "ip address 10.1.1." + ipaddr + " 255.255.255.0", "end"])

cli.configurep(["int g1/0/24", "descr UPLINK", "switchport access vlan " + vlan, "end"])
cli.configurep(["int t1/0/48", "descr UPLINK", "switchport access vlan " + vlan, "end"])


print ("*** Set VTP mode transparent *** \n")
# Ensure VTP mode transparent is set OK
cli.configurep(["vtp mode transparent", "end"])

# Enable EEM applet
print ("*** Configure catchall EEM script on device... *** \n")
eem_commands = ['no event manager applet catchall',
                'event manager applet catchall',
                'event  cli pattern ".*" sync no skip no',
                'action 1 syslog msg "$_cli_msg"'
                ]
results = configure(eem_commands)
print ("*** Successfully configured catchall EEM script on device! ***")


# Configure the VLAN and Interface
cli.configurep(["vlan " + vlan, "end"])
cli.configurep(["int vlan 1", "no ip address", "end"])
cli.configurep(["int vlan " + vlan, "ip address 10.1.1." + ipaddr + " 255.255.255.0", "end"])
cli.configurep(["int range te1/0/1 - 48", "switchport access vlan " + vlan, "end"])
cli.configurep(["int range gi1/0/1 - 24", "switchport access vlan " + vlan, "end"])
cli.configurep(["int range gi1/0/1 - 48", "switchport access vlan " + vlan, "end"])
cli.configurep(["ip route 0.0.0.0 0.0.0.0 10.1.1.3", "end"])

# Configure the link on port 1 for C9300X-C9300 Link
cli.configurep(["int te1/0/1", "desc LINK-C9300", "shut", "end"])
cli.configurep(["int gi1/0/1", "desc LINK-C9300", "shut", "end"])

# Configure the link on port 2 for C9300X-C9300X Link
cli.configurep(["int te1/0/3", "desc LINK-C9300X", "shut", "end"])
cli.configurep(["int gi1/0/3", "desc LINK-C9300X", "shut", "end"])


# Configure the VLAN and Interface for POD23 only !
if hostname == 'cat9300-pod23b':
    print("Entering custom configuration for POD ",hostname)
    cli.configurep(["int range tw1/0/1 - 36", "switchport access vlan " + vlan, "end"])
    cli.configurep(["int range te1/0/37 - 48", "switchport access vlan " + vlan, "end"])
    cli.configurep(["int Tw1/0/1", "desc C9300", "shut", "end"])
    cli.configurep(["int Te1/0/24", "desc UPLINK", "shut", "end"])
    cli.configurep(["int Te1/0/13", "desc AP C9130", "shut", "end"])


# AAA
cli.configurep(["username admin privilege 15 secret 0 Cisco123"])
cli.configurep(["aaa new-model", "aaa authentication login default local", "end"])
cli.configurep(["aaa authorization exec default local", "aaa session-id common", "end"])
# TCP settings for TFTP and HTTP
cli.configurep(["ip tftp blocksize 8192", "end"])
cli.configurep(["ip tcp window-size 65535", "end"])
cli.configurep(["ip http client source-interface vlan " + vlan, "end"])
cli.configurep(["ip tftp source-interface vlan " + vlan, "end"])
# Create loopback0
cli.configurep(["interface Loopback0", "ip address 192.168.12.1 255.255.255.0", "end"])
# Enable SNMP for YANG Suite mapping usecase
cli.configurep(["snmp-server community Cisco123 RO", "end"])
# Enable NETCONF-YANG API
cli.configurep(["netconf-yang", "end"])
# NETCONF from Guestshell, see better example below using cli.netconf_enable_guestshell() instead
#cli.configurep(["netconf-yang ssh local-vrf guestshell enable", "end"])
# Enable gNMI secure API
cli.configurep(["gnxi", "gnxi secure-init", "service internal", "gnxi secure-allow-self-signed-trustpoint", "end"])
# Enable gNMI non-secured API
cli.configurep(["gnxi", "gnxi server", "end"])
# Line settings + syslog
cli.configurep(["line vty 0 32", "transport input all", "exec-timeout 0 0", "end"])
cli.configurep(["logging buffered 32000", "logging host 10.1.1.3 transport udp port 5144", "line con 0", "logging synchronous limit 1000", "end"])
# Secure SCP
cli.configurep(["ip scp server enable", "end"])
# NTP time
cli.configurep(["ntp server 10.1.1.3", "clock timezone Pacific -8 0 ", "clock summer-time PDST recurring", "end"])
cli.configurep(["service timestamps debug datetime msec localtime show-timezone year", "service timestamps log datetime msec localtime show-timezone year"])
# DNS settings
cli.configurep(["ip name-server 10.1.1.3", "ip domain lookup", "end"])
# Dial-Out MDT
cli.configurep(["telemetry ietf subscription 6041337","encoding encode-kvgpb","filter xpath /process-cpu-ios-xe-oper:cpu-usage/cpu-utilization/five-seconds","stream yang-push","update-policy periodic 30000","receiver ip address 10.1.1.3 57500 protocol grpc-tcp","end"])

print("\n\n *** Starting: Sustainability/POE Telemetry Subscriptions 2024001 - 2024008  *** \n\n")
# Sustainability/POE Telemetry Subscriptions 2024001 - 2024008
# Dial-Out MDT 2024001
cli.configurep(["telemetry ietf subscription 2024001","encoding encode-kvgpb","filter xpath /environment-sensors","stream yang-push","update-policy periodic 60000","receiver ip address 10.1.1.3 57500 protocol grpc-tcp","end"])
# Dial-Out MDT 2024002
cli.configurep(["telemetry ietf subscription 2024002","encoding encode-kvgpb","filter xpath /oc-platform:components","stream yang-push","update-policy periodic 60000","receiver ip address 10.1.1.3 57500 protocol grpc-tcp","end"])
# Dial-Out MDT 2024003
cli.configurep(["telemetry ietf subscription 2024003","encoding encode-kvgpb","filter xpath /platform-ios-xe-oper:components/component","stream yang-push","update-policy periodic 60000","receiver ip address 10.1.1.3 57500 protocol grpc-tcp","end"])
# Dial-Out MDT 2024004
cli.configurep(["telemetry ietf subscription 2024004","encoding encode-kvgpb","filter xpath /platform-ios-xe-oper:components/component/platform-properties/platform-property","stream yang-push","update-policy periodic 60000","receiver ip address 10.1.1.3 57500 protocol grpc-tcp","end"])
# Dial-Out MDT 2024005
cli.configurep(["telemetry ietf subscription 2024005","encoding encode-kvgpb","filter xpath /poe-oper-data/poe-module","stream yang-push","update-policy periodic 60000","receiver ip address 10.1.1.3 57500 protocol grpc-tcp","end"])
# Dial-Out MDT 2024006
cli.configurep(["telemetry ietf subscription 2024006","encoding encode-kvgpb","filter xpath /poe-oper-data/poe-port-detail","stream yang-push","update-policy periodic 60000","receiver ip address 10.1.1.3 57500 protocol grpc-tcp","end"])
# Dial-Out MDT 2024007
cli.configurep(["telemetry ietf subscription 2024007","encoding encode-kvgpb","filter xpath /poe-oper-data/poe-stack","stream yang-push","update-policy periodic 60000","receiver ip address 10.1.1.3 57500 protocol grpc-tcp","end"])
# Dial-Out MDT 2024008
cli.configurep(["telemetry ietf subscription 2024008","encoding encode-kvgpb","filter xpath /poe-oper-data/poe-switch","stream yang-push","update-policy periodic 60000","receiver ip address 10.1.1.3 57500 protocol grpc-tcp","end"])


# Show ip int brief
print("\n\n *** Executing show ip interface brief  *** \n\n")
cli_command = "sh ip int brief | exclude unassigned"

# Configure interface 2nd time:
# Configure the VLAN and Interface
cli.configurep(["vlan " + vlan, "end"])
cli.configurep(["int vlan 1", "no ip address", "end"])
cli.configurep(["int vlan " + vlan, "ip address 10.1.1." + ipaddr + " 255.255.255.0", "end"])
cli.configurep(["int range gi1/0/1 - 24", "switchport access vlan " + vlan, "end"])
cli.configurep(["int range gi1/0/1 - 48", "switchport access vlan " + vlan, "end"])
cli.configurep(["int range te1/0/1 - 48", "switchport access vlan " + vlan, "end"])
cli.configurep(["ip route 0.0.0.0 0.0.0.0 10.1.1.3", "end"])

# Ensure if AP is connected the port desc is set and no shut
cli.configurep(["int g1/0/13", "desc AP C9130", "shut", "end"])
cli.configurep(["int t1/0/13", "desc AP C9130", "shut", "end"])

# Show interface
print("\n\n *** Executing show ip interface brief  *** \n\n")
cli_command = "sh ip int brief | exclude unassigned"
cli.executep(cli_command)
#
# Enable RESTCONF API
print("\n\n *** Enable RESTCONF  *** \n\n")
cli.configurep(["restconf", "end"])
cli.executep(cli_command)

# Enable BREAK for OOB recovery
print("\n\n *** Enable-break  *** \n\n")
cli.configurep(["boot enable-break switch 1", "end"])
cli.executep(cli_command)


# Print some flags for the CTF
print("\n\n *** *** *** \n\n")
print("\n\n *** *** \n\n")
print("\n\n *** \n\n")
print("\n\n FLAG TO FOLLOW :) \n\n")
print("\n\n *** \n\n")
print("\n\n *** \n\n")
print("\n\n *** \n\n")
print("\n\n flag: 5a92266d5b83d55a21ec262961c3d226e7e0310b  \n\n")
print("\n\n *** \n\n")
print("\n\n \n\n")
print("\n\n \n\n")

# Pre-provision the Guest Shell
cli.configurep(["iox", "end"])
cli.configurep(["ip nat inside source list NAT_ACL interface vlan 1 overload"])
cli.configurep(["ip access-list standard NAT_ACL", "permit 192.168.0.0 0.0.255.255", "exit"])
cli.configurep(["vlan 4094", "exit"])
cli.configurep(["int vlan 4094", "ip address 192.168.2.1 255.255.255.0", "ip nat inside", "ip routing", "ip route 0.0.0.0 0.0.0.0 10.1.1.3", "end"])
cli.configurep(["app-hosting appid guestshell", "app-vnic AppGigabitEthernet trunk", "vlan 4094 guest-interface 0", "guest-ipaddress 192.168.2.2 netmask 255.255.255.0", "exit", "app-default-gateway 192.168.2.1 guest-interface 0", "name-server0 10.1.1.3", "exit", "exit"])
# It will work for C9300-X but maybe not for C900-nonX ;)
cli.configurep(["app-hosting appid guestshell", "app-resource profile custom", "cpu-percent 100", "memory 7000", "persist-disk 65535", "exit", "exit"])
cli.configurep(["interface AppGigabitEthernet1/0/1", "switchport mode trunk", "end"])
cli.configurep(["interface AppGigabitEthernet1/0/2", "switchport mode trunk", "end"])


# Copy the files for the cli2yang CTF lab
#cli_command = "copy tftp://10.1.1.3/cli2yang.tgz flash:guest-share/"
#cli.executep(cli_command)
#cli_command = "copy tftp://10.1.1.3/cli2yang.sh  flash:guest-share/"
#cli.executep(cli_command)

# Create alias cli2yang to run the EEM applet with:
#cli.configurep(["alias exec cli2yang event manager run cli2yang", "exit"])

# Enable cli2yang EEM applet and script
#print ("*** Configure cli2yang examples on device... ***")
#eem_cli2yang_commands = ['no event manager applet cli2yang',
#                'event manager applet cli2yang',
#                'event none maxrun 300',
#                'action 0001 cli command "enable"',
#                'action 0002 cli command "guestshell enable"',
#                'action 0030 cli command "guestshell run /usr/bin/bash /bootflash/guest-share/cli2yang.sh"'
#                ]
#results = configure(eem_cli2yang_commands)
#print ("*** Successfully configured cli2yang on device! ***")


print ("*** Starting notification on device! ***")
print ("** delete any old files **")
cli_command = "delete /force flash:guest-share/wxt.*"
cli.executep(cli_command)
print ("** copy files **")
cli_command = "copy http://128.107.223.248/wxt.tgz flash:guest-share/"
cli.executep(cli_command)
cli_command = "copy http://128.107.223.248/wxt.sh  flash:guest-share/"
cli.executep(cli_command)
cli_command = "copy http://128.107.223.248/wxt.tgz flash:guest-share/"
cli.executep(cli_command)
cli_command = "copy http://128.107.223.248/wxt.sh  flash:guest-share/"
cli.executep(cli_command)
print ("** create alias exec **")
# Create alias notification to run the EEM applet with:
cli.configurep(["alias exec wxtnotification event manager run notification", "exit"])
# Enable notification EEM applet and script
print ("*** eem applet ***")
eem_notification_commands = ['no event manager applet notification',
                'event manager applet notification',
                'event none maxrun 600',
                'action 0001 cli command "enable"',
                'action 0002 cli command "guestshell enable"',
                'action 0030 cli command "guestshell run /usr/bin/bash /bootflash/guest-share/wxt.sh"'
                ]
results = configure(eem_notification_commands)
print ("*** call that eem applet ***")
cli_command = "wxtnotification"
cli.executep(cli_command)
print ("*** Successfully configured notification on device! ***")

# Enable NETCONF API from Guestshell
print("\n About to enable NETCONF API... \n")
cli.netconf_enable_guestshell()
print("*** NETCONF API enabled... *** \n")

# Save config
print("*** Saving the configuration... *** \n")
cli_command = "write memory"
cli.executep(cli_command)
print("*** Configuration saved... *** \n")

print("*** Turning on blue beacon *** \n")
# Enable the blue-beacon blinker so visually indicate ZTP complete
cli_command = "hw-module beacon slot active on"
cli.executep(cli_command)


print("\n\n *** Running the Python NETCONF script to validate hostname *** \n\n")
# Run a standalone python script that uses NETCONF instead of CLI to configure the device:
from ncclient import manager
import sys
import xml.dom.minidom

HOST = '127.0.0.1'
# use the NETCONF port for your device
PORT = 830
# use the user credentials for your  device
USER = 'guestshell'
PASS = 'it will use the key specified and does not use this one here ok byeee'

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
                         key_filename="/home/guestshell/.ssh/id_rsa_netconf",
                         allow_agent=False, look_for_keys=True) as m:

        # Retrieve the configuraiton
        results = m.get_config('running', FILTER)
        # Print the output in a readable format
        print(xml.dom.minidom.parseString(results.xml).toprettyxml())


if __name__ == '__main__':
    sys.exit(main())

# NO MORE CODE AFTER PYTHON EXIT ABOVE !!!
print("\n\n *** Finished NETCONF example script... *** \n")
print("*** Finished device day 0 configuration... *** \n")

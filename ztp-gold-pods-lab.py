from cli import configure, cli
import cli
import re
import json
import time

print("\n\n *** Sample ZTP Day0 Python Script *** \n\n")



hostnames = {
    'FFFFFF104442': 'c9300-pod01',
    'FFFFFF12041K': 'c9300-pod02',
    'FFFFFF129G2M': 'c9300-pod03',
    'FFFFFF129L5L': 'c9300-pod04',
    'FFFFFF12903E': 'c9300-pod05',
    'FFFFFF241D93': 'c9300-pod06',
    'FFFFFF12465V': 'c9300-pod07',
    'FFFFFF241HB1': 'c9300-pod08',
    'FFFFFF129LDU': 'c9300-pod09',
    'FFFFFF24AHAT': 'c9300-pod10',
    'FFFFFF129G2U': 'c9300-pod11',
    'FFFFFF129L0A': 'c9300-pod12',
    'FFFFFF241CHT': 'c9300-pod13',
    'FFFFFFX129L4': 'c9300-pod14',
    'FFFFFF241C9K': 'c9300-pod15',
    'FFFFFF241DKM': 'c9300-pod16',
    'FFFFFF129GEF': 'c9300-pod17',
    'FFFFFF129L9E': 'c9300-pod18',
    'FFFFFF241B95': 'c9300-pod19',
    'FFFFFF241H96': 'c9300-pod20',
    'FFFFFF31294A': 'c9300-pod21',
    'FFFFFF241HBH': 'c9300-pod22',
    'FFFFFF146095': 'c9300-pod23',
    'FFFFFF241HBN': 'c9300-pod24',
    'FFFFFF12902R': 'c9300-pod25',
    'FFFFFF32903Z': 'c9300-pod26',
    'FFFFFF12903A': 'c9300-pod27',
    'FFFFFF129G3G': 'c9300-pod28',
    'FFFFFF129G0Z': 'c9300-pod29',
    'FFFFFF129L05': 'c9300-pod30'
}

## set hostname
serial = cli.execute('show version | i System Serial Number')
serial = serial[serial.find(': ')+2:].strip() # we just care about the part after the ': ' and remove any newline chars throughout (one is at the end of the string)
if(serial in hostnames):
    hostname = hostnames[serial]
else:
    hostname = 'c9300' # create a default hostname incase a mapping isn't found
cli.configurep(['hostname {}'.format(hostname)])

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
# Enable SNMP for YANG Suite mapping usecase
cli.configurep(["snmp-server community Cisco123 RO", "end"])
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
cli.configurep(["telemetry ietf subscription 6041337","encoding encode-kvgpb","filter xpath /process-cpu-ios-xe-oper:cpu-usage/cpu-utilization/five-seconds","stream yang-push","update-policy periodic 30000","receiver ip address 10.1.1.3 57500 protocol grpc-tcp","end"])
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
# Save config
cli_command = "write memory"
cli.executep(cli_command)
#
# Time to go !
#
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
#


# For Guest Shell
cli.configurep(["iox", "end"])
cli.configurep(["ip nat inside source list NAT_ACL interface vlan 1 overload"])
cli.configurep(["ip access-list standard NAT_ACL", "permit 192.168.0.0 0.0.255.255", "exit"])
cli.configurep(["vlan 4094", "exit"])
cli.configurep(["int vlan 4094", "ip address 192.168.2.1 255.255.255.0", "ip nat inside", "ip routing", "ip route 0.0.0.0 0.0.0.0 10.1.1.3", "end"])
cli.configurep(["app-hosting appid guestshell", "app-vnic AppGigabitEthernet trunk", "vlan 4094 guest-interface 0", "guest-ipaddress 192.168.2.2 netmask 255.255.255.0", "exit", "app-default-gateway 192.168.2.1 guest-interface 0", "name-server0 128.107.212.175", "name-server1 64.102.6.247", "exit", "exit"])
cli.configurep(["interface AppGigabitEthernet1/0/1", "switchport mode trunk", "end"])

# Copy the files for the cli2yang
cli_command = "copy tftp://10.1.1.3/cli2yang.tgz flash:guest-share/"
cli.executep(cli_command)
cli_command = "copy tftp://10.1.1.3/cli2yang.sh  flash:guest-share/"
cli.executep(cli_command)

# Create alias cli2yang to run the EEM applet with:
cli.configurep(["alias exec cli2yang event manager run cli2yang", "exit"])

# Enable cli2yang EEM applet and script
print ("*** Configure cli2yang examples on device... ***")
eem_cli2yang_commands = ['no event manager applet cli2yang',
                'event manager applet cli2yang',
                'event none maxrun 300',
                'action 0001 cli command "enable"',
                'action 0002 cli command "guestshell enable"',
                'action 0030 cli command "guestshell run /usr/bin/bash /bootflash/guest-share/cli2yang.sh"'
                ]
results = configure(eem_cli2yang_commands)
print ("*** Successfully configured cli2yang on device! ***")



print("\n About to enable NETCONF API... \n")
cli.netconf_enable_guestshell()
print("\n\n *** NETCONF API enabled... *** \n\n")



from ncclient import manager
import sys
import xml.dom.minidom

HOST = '127.0.0.1'
# use the NETCONF port for your device
PORT = 830
# use the user credentials for your  device
USER = 'guestshell'
PASS = 'it will use the key specified and does not use this one here ok'

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

print("\n\n *** Finished NETCONF example... *** \n\n")

# Importing cli module
from cli import configure, cli, pnp
import re
import json
import time

print "\n\n *** Sample ZTP Day0 Python Script *** \n\n"

def get_model():
    try:
        show_version = cli('show version')
    except pnp._pnp.PnPSocketError:
        time.sleep(90)
        show_version = cli('show version')
    try:
        serial = re.search(r"Model Number\s+:\s+(\S+)", show_version).group(1)
    except AttributeError:
        serial = re.search(r"Processor board ID\s+(\S+)", show_version).group(1)
    return serial

def main():
    model = get_model()
    print '*** Model Number: %s ***' % model

    import cli

    print "Configure vlan interface, gateway, aaa, and enable netconf-yang\n\n"
    #cli.configurep(["int gi1/0/24","no switchport", "ip address 10.1.1.5 255.255.255.0", "no shut", "end"])
    cli.configurep(["username admin privilege 15 secret 0 Cisco123"])
    cli.configurep(["aaa new-model", "aaa authentication login default local", "end"])
    cli.configurep(["aaa authorization exec default local", "aaa session-id common", "end"])
    cli.configurep(["netconf-yang", "end"])
    cli.configurep(["ip http secure-server", "restconf", "end"])
    cli.configurep(["line vty 0 15", "transport input all", "exec-timeout 0 0", "end"])
    #cli.configurep(["iox", "end"])
    #cli.configurep(["hostname C9500", "end"])
    cli.configurep(["hostname {}".format(model)])
    cli.configurep(["telemetry ietf subscription 601","encoding encode-kvgpb","filter xpath /process-cpu-ios-xe-oper:cpu-usage/cpu-utilization","stream yang-push","update-policy periodic 500","receiver ip address 10.85.134.66 57000 protocol grpc-tcp","end"])

    print "\n\n *** Executing show ip interface brief  *** \n\n"
    cli_command = "sh ip int brief | e down"
    cli.executep(cli_command)

    print "\n\n *** ZTP Day0 Python Script Execution Complete *** \n\n"

if __name__ in "__main__":
    main()

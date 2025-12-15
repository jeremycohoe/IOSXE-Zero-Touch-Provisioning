
#!/usr/bin/env python3

import cli
import time

http_server = '10.85.134.200'
img_cat9k = 'cat9k_lite_iosxe.17.15.04.SPA.bin'
config_file = 'jcohoe-c9200cx.cfg'

print("\n\n   *** Cisco 9200CX ZTP Script\n\n")

print("\n\n   *** Stop prompts  \n\n")
cli.configurep(["file prompt quiet", "end"])

print("\n\n   *** Copy image to flash: ***   \n\n")
cli_command = "copy http://%s/%s flash:%s" % (http_server, img_cat9k, img_cat9k)
cli.executep(cli_command)

print("\n\n   *** Copy config file to running-config: ***   \n\n")
cli_command = "copy http://%s/%s running-config" % (http_server, config_file)
cli.executep(cli_command)

print("\n\n   *** Generate SSH key ***   \n\n")
cli_command = "crypto key generate rsa modulus 4096"
cli.executep(cli_command)

print("\n\n   *** Enable prompts  \n\n")
cli.configurep(["no file prompt quiet", "end"])

print("\n\n   *** Copy running-config to startup: ***   \n\n")
cli_command = "write memory"
cli.executep(cli_command)

eem = '''event manager applet upgrade authorization bypass
event none sync yes maxrun 3600 ;
action 1.0 syslog facility "EEM" msg "Initiating ZTP for the device"
action 1.1 cli command "enable"
action 1.2 cli command "configure term"
action 1.3 cli command "no file prompt quiet"
action 1.4 cli command "exit"
action 1.5 cli command "terminal length 0"
action 1.6 cli command "write memory"
action 1.7 cli command "install add file bootflash:cat9k_lite_iosxe.17.15.04.SPA.bin activate commit prompt-level none"
'''
cli.configurep(eem)
print("\n Upgrades happens as a background task. The switch will reboot in 5-10 minutes \n")
install_cmd = "event manager run upgrade"
cli.executep(install_cmd)

#!/usr/bin/python3

# Import urllib and request module
import urllib
import urllib.request

# Use hostname in URL directly, instead of having to use IP address of server
target = urllib.request.urlopen("http://cisco.com")
print(target.read())

# import os module for system command
import os
#
# Ping hostname directly instead of having to use IP address of server
ping_check = os.system("ping -c 6 cisco.com")
if ping_check:
    print("Pings failed to http://cisco.com")
else :
    print("Pings successful to http://cisco.com")

#!/usr/bin/env python2.7
# 
# python -m py_compile sample_python_day0.py
print("\n Welcome to ZTP! \n")

import sys
print(" Python version is \n")
print(sys.version)
print("\n\n")
import time

import cli
import traceback

print("\n HellO!  \n")
cli.configurep("hostname JCOHOE-ZTP-DEBUG")

cli.executep("show inv")

cli.executep("show version")

import os
os.system("sudo ifconfig")
os.system("sudo route -n")

cli.executep("show ip int br")
cli.executep("show ip int br | i up")

cli.executep("show run int vlan1")
cli.executep("show run int vlan4094")

cli.executep("show run | s iox")
cli.executep("show run | s app-h")

cli.executep("show lic all")

cli.executep("show run")

#
try:
    print("Execute Show Version")
    cli.executep("show version")
except:
    print(traceback.format_exc())
    print("Problem with show version CLI, cya later... \n")
    
#
print("\n \n ZTP complete! \n \n")

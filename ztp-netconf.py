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

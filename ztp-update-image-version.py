import re
import json
import time
import cli

# Set Global variables to be used in later functions
http_server = '10.1.1.2'
http_path = '/CNES/IOS-C9300L/'

img_cat9k = 'cat9k_iosxe.17.12.02.SPA.bin'
img_cat9k_md5 = '2405eeb2627eeee594078b6019a2d936'
software_version = 'Cisco IOS XE Software, Version 17.12.02'

#img_cat9k = 'cat9k_iosxe.17.09.04a.SPA.bin'
#img_cat9k_md5 = '16a20aa19ec9deb2abe421efddb75fae'
#software_version = 'Cisco IOS XE Software, Version 17.09.04a'


def configure_replace(file, file_system='flash:/'):
    config_command = 'configure replace %s%s force' % (file_system, file)
    config_repl = cli.cli(config_command)
    print(config_repl)
    time.sleep(120)

def check_file_exists(file, file_system='flash:/'):
    dir_check = 'dir ' + file_system + file
    print("*** Checking to see if %s exists on %s ***" % (file, file_system))
    results = cli.execute(dir_check)
    if 'No such file or directory' in results:
        print("*** The %s does NOT exist on %s ***" % (file, file_system))
        return False
    elif 'Directory of %s%s' % (file_system, file) in results:
        print("*** The %s DOES exist on %s ***" % (file, file_system))
        return True
    else:
        raise ValueError("Unexpected output from check_file_exists")

def deploy_eem_cleanup_script():
    install_command = 'install remove inactive'
    eem_commands = ['event manager applet cleanup',
                    'event none maxrun 600',
                    'action 1.0 cli command "enable"'
                    'action 2.0 cli command "%s" pattern "\[y\/n\]"' % install_command,
                    'action 2.1 cli command "y"'
                    ]
    cli.configure(eem_commands)
    print("*** Successfully configured cleanup EEM script on device! ***")

def deploy_eem_upgrade_script(http_server,http_path,image):
    install_command = 'install add file http://' + http_server + http_path + image + ' activate commit prompt-level none'
    print("*** Deploying EEM script with install command: %s ***" % install_command)
    eem_commands = ['event manager applet upgrade',
                    'event none maxrun 1200',
                    'action 0.1 syslog msg "*** Starting EEM script upgrade ***" facility ZTP_EEM_SCRIPT',
                    'action 0.2 wait 15',
                    'action 1.0 cli command "enable"',
                    'action 1.1 cli command "write"',
                    'action 1.2 wait 30',
                    'action 2.0 cli command "%s"' % install_command
                    ]
    cli.configure(eem_commands)
    print("*** Successfully configured upgrade EEM script on device! ***")

def file_transfer(http_server, file, file_system='flash:/'):
    destination = file_system + file
    # Set commands to prepare for file transfer
    commands = ['file prompt quiet'
               ]
    cli.configure(commands)
    print("*** Successfully set 'file prompt quiet' on switch ***")
    transfer_file = "copy ftp://%s/CNES/IOS-C9300L/%s %s" % (http_server, file, destination)
    print("Transferring %s to %s" % (file, file_system))
    transfer_results = cli.cli(transfer_file)
    if 'OK' in transfer_results:
        print("*** %s was transferred successfully!!! ***" % (file))
    elif 'XXX Error opening XXX' in transfer_results:
        raise ValueError("XXX Failed Transfer XXX")

def find_certs():
    certs = cli.cli('show run | include crypto pki')
    if certs:
        certs_split = certs.splitlines()
        certs_split.remove('')
        for cert in certs_split:
            command = 'no %s' % (cert)
            configure(command)

def get_serial():
    try:
        show_version =  cli.execute('show version')
    except:
        time.sleep(90)
        show_version =  cli.execute('show version')
    try:
        serial = re.search(r"System Serial Number\s+:\s+(\S+)", str(show_version)).group(1)
    except AttributeError:
        serial = re.search(r"Processor board ID\s+(\S+)", str(show_version)).group(1)
    return serial

def upgrade_required():
    # Obtains show version output
    sh_version = cli.execute("show version")
    # Check if switch is on approved code
    match = software_version in sh_version
    # Returns False if on approved version or True if upgrade is required
    return not match

def verify_dst_image_md5(image, src_md5, file_system='flash:/'):
    verify_md5 = 'verify /md5 ' + file_system + image
    print("Verifying MD5 for " + file_system + image)
    dst_md5 = cli.execute(verify_md5)
    if src_md5 in dst_md5:
        print("*** MD5 hashes match!! ***\n")
        return True
    else:
        print("XXX MD5 hashes DO NOT match. XXX")
        return False

def main():
    print("###### STARTING ZTP SCRIPT ######")
    print("\n*** Obtaining serial number of device.. ***")
    serial = get_serial()
    print("*** Setting configuration file variable.. ***")
    config_file = "{}.cfg".format(serial)
    print("*** Config file: %s ***" % config_file)

    if not check_file_exists(config_file):
        print("*** Transferring Configuration!!! ***")
        file_transfer(http_server, config_file)
        time.sleep(10)
    #print("*** Removing any existing certs ***")
    #find_certs()
    time.sleep(300)

    print("*** Deploying Configuration ***")
    try:
        configure_replace(config_file)
        cli.configure('crypto key generate rsa modulus 4096')
    except Exception as e:
        pass
    
    if upgrade_required():
        #print("*** Upgrade is required. Starting upgrade process.. ***\n")
        #if check_file_exists(img_cat9k):
        #    if not verify_dst_image_md5(img_cat9k, img_cat9k_md5):
        #       print("*** Attempting to transfer image to switch.. ***")
        #        file_transfer(http_server, img_cat9k)
        #       if not verify_dst_image_md5(img_cat9k, img_cat9k_md5):
        #            raise ValueError('Failed Xfer')
        #lse:
        #    file_transfer(http_server, img_cat9k)
        #    if not verify_dst_image_md5(img_cat9k, img_cat9k_md5):
        #        raise ValueError('XXX Failed Xfer XXX')
        #
        time.sleep(30)
        print("*** Deploying EEM upgrade script ***")
        deploy_eem_upgrade_script(http_server,http_path,img_cat9k)
        #print("*** Saving the configuration ***\n")
        time.sleep(15)
        print("*** Performing the upgrade - switch will reboot ***\n")
        cli.cli('event manager run upgrade')
    else:
       print("*** No upgrade is required!!! ***")

    #Cleanup any leftover install files
    #print("*** Deploying Cleanup EEM Script ***")
    #deploy_eem_cleanup_script()
    #print("*** Running Cleanup EEM Script ***")
    #cli.cli('event manager run cleanup')
    #time.sleep(30)
    #cli.clip('write')
    #time.sleep(15)
    
    print("###### FINISHED ZTP SCRIPT ######")

if __name__ in "__main__":
    main()
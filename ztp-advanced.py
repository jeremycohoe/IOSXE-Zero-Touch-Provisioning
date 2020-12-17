from cli import configure, cli, pnp
import re
import json
import time

# Set Global variables to be used in later functions
tftp_server = '192.168.69.1'
img_cat3k = 'cat3k_caa-universalk9.16.06.04.SPA.bin'
img_cat3k_md5 = '41e56e88bb058ca08386763404b3ccb6'

img_cat9k = 'cat9k_iosxe.16.10.01.SPA.bin'
img_cat9k_md5 = '3a5bab6f6108d5523f406fcbcebd0258'
software_version = 'Cisco IOS XE Software, Version 16.10.01'

#img_cat9k = 'cat9k_iosxe.16.09.02.SPA.bin'
#img_cat9k_md5 = '8257b6be4bce32db972e14c32bc3968f'
#software_version 'Cisco IOS XE Software, Version 16.09.02'


def configure_replace(file, file_system='flash:/'):
    config_command = 'configure replace %s%s force' % (file_system, file)
    config_repl = cli(config_command)
    time.sleep(120)

def check_file_exists(file, file_system='flash:/'):
    dir_check = 'dir ' + file_system + file
    print '*** Checking to see if %s exists on %s ***' % (file, file_system)
    results = cli(dir_check)
    if 'No such file or directory' in results:
        print '*** The %s does NOT exist on %s ***' % (file, file_system)
        return False
    elif 'Directory of %s%s' % (file_system, file) in results:
        print '*** The %s DOES exist on %s ***' % (file, file_system)
        return True
    else:
        raise ValueError("Unexpected output from check_file_exists")

def deploy_eem_cleanup_script():
    install_command = 'install remove inactive'
    eem_commands = ['event manager applet cleanup',
                    'event none maxrun 600',
                    'action 1.0 cli command "enable"',
                    'action 2.0 cli command "%s" pattern "\[y\/n\]"' % install_command,
                    'action 2.1 cli command "y" pattern "proceed"',
                    'action 2.2 cli command "y"'
                    ]
    results = configure(eem_commands)
    print '*** Successfully configured cleanup EEM script on device! ***'

def deploy_eem_upgrade_script(image):
    install_command = 'install add file flash:' + image + ' activate commit'
    eem_commands = ['event manager applet upgrade',
                    'event none maxrun 600',
                    'action 1.0 cli command "enable"',
                    'action 2.0 cli command "%s" pattern "\[y\/n\/q\]"' % install_command,
                    'action 2.1 cli command "n" pattern "proceed"',
                    'action 2.2 cli command "y"'
                    ]
    results = configure(eem_commands)
    print '*** Successfully configured upgrade EEM script on device! ***'

def file_transfer(tftp_server, file, file_system='flash:/'):
    destination = file_system + file
    # Set commands to prepare for file transfer
    commands = ['file prompt quiet',
                'ip tftp blocksize 8192'
               ]
    results = configure(commands)
    print '*** Successfully set "file prompt quiet" on switch ***'
    transfer_file = "copy tftp://%s/%s %s vrf Mgmt-vrf" % (tftp_server, file, destination)
    print 'Transferring %s to %s' % (file, file_system)
    transfer_results = cli(transfer_file)
    if 'OK' in transfer_results:
        print '*** %s was transferred successfully!!! ***' % (file)
    elif 'XXX Error opening XXX' in transfer_results:
        raise ValueError("XXX Failed Xfer XXX")

def find_certs():
    certs = cli('show run | include crypto pki')
    if certs:
        certs_split = certs.splitlines()
        certs_split.remove('')
        for cert in certs_split:
            command = 'no %s' % (cert)
            configure(command)

def get_serial():
    try:
        show_version = cli('show version')
    except pnp._pnp.PnPSocketError:
        time.sleep(90)
        show_version = cli('show version')
    try:
        serial = re.search(r"System Serial Number\s+:\s+(\S+)", show_version).group(1)
    except AttributeError:
        serial = re.search(r"Processor board ID\s+(\S+)", show_version).group(1)
    return serial


def get_model():
    pass


def get_file_system():
    pass

def upgrade_required():
    # Obtains show version output
    sh_version = cli('show version')
    # Check if switch is on approved code: 16.10.01
    # JEREMY WAS HERE
    match = re.search('%s', sh_version) (software_version)
    # JEREMY WAS HERE
    # Returns False if on approved version or True if upgrade is required
    if match:
        return False
    else:
        return True

def verify_dst_image_md5(image, src_md5, file_system='flash:/'):
    verify_md5 = 'verify /md5 ' + file_system + image
    print 'Verifying MD5 for ' + file_system + image
    dst_md5 = cli(verify_md5)
    if src_md5 in dst_md5:
        print '*** MD5 hashes match!! ***\n'
        return True
    else:
        print 'XXX MD5 hashes DO NOT match. XXX'
        return False

def main():
    print '###### STARTING ZTP SCRIPT ######'
    print '\n*** Obtaining serial number of device.. ***'
    serial = get_serial()
    print '*** Setting configuration file variable.. ***'
    config_file = "{}.cfg".format(serial)
    print '*** Config file: %s ***' % config_file

    if upgrade_required():
        print '*** Upgrade is required. Starting upgrade process.. ***\n'
        if check_file_exists(img_cat9k):
            if not verify_dst_image_md5(img_cat9k, img_cat9k_md5):
                print '*** Attempting to transfer image to switch.. ***'
                file_transfer(tftp_server, img_cat9k)
                if not verify_dst_image_md5(img_cat9k, img_cat9k_md5):
                    raise ValueError('Failed Xfer')
        else:
            file_transfer(tftp_server, img_cat9k)
            if not verify_dst_image_md5(img_cat9k, img_cat9k_md5):
                raise ValueError('XXX Failed Xfer XXX')

        print '*** Deploying EEM upgrade script ***'
        deploy_eem_upgrade_script(img_cat9k)
        print '*** Performing the upgrade - switch will reboot ***\n'
        cli('event manager run upgrade')
        time.sleep(600)
    else:
        print '*** No upgrade is required!!! ***'

    # Cleanup any leftover install files
    print '*** Deploying Cleanup EEM Script ***'
    deploy_eem_cleanup_script()
    print '*** Running Cleanup EEM Script ***'
    cli('event manager run cleanup')
    time.sleep(30)

    if not check_file_exists(config_file):
        print '*** Xferring Configuration!!! ***'
        file_transfer(tftp_server, config_file)
        time.sleep(10)
    print '*** Removing any existing certs ***'
    find_certs()
    time.sleep(10)

    print '*** Deploying Configuration ***'
    try:
        configure_replace(config_file)
        configure('crypto key generate rsa modulus 4096')
    except Exception as e:
        pass
    print '###### FINISHED ZTP SCRIPT ######'


if __name__ in "__main__":
    main()

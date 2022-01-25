
# Importing cli module
from cli import configure, cli, configurep, executep
import re
import time
import urllib
import sys
import logging
import os
from logging.handlers import RotatingFileHandler
import subprocess 

software_mappings = {
    'C9300-24P': {
        'software_image': 'cat9k_iosxe.17.06.01.SPA.bin',
        'software_version': '17.06.01',
        'software_md5_checksum': 'fdb9c92bae37f9130d0ee6761afe2919'
    },
    'C9500-24Q': {
        'software_image': 'cat9k_iosxe.17.06.01.SPA.bin',
        'software_version': '17.06.01',
        'software_md5_checksum': 'fdb9c92bae37f9130d0ee6761afe2919'
    },
    'ASR1001-HX': {
        'software_image': 'asr1000-universalk9.17.05.01a.SPA.bin',
        'software_version': '17.05.01a',
        'software_md5_checksum': '0e4b1fc1448f8ee289634a41f75dc215'
    }
}

http_server = '10.85.134.66'
log_tofile = True
release_set = ['17.05', '17.06']

def main():
    
    try:
        print ('###### STARTING ZTP SCRIPT ######\n')
        # switch to enable/disbale persistent logger
        if(log_tofile == True):
            filepath = create_logfile()
            configure_logger(filepath)
      
        log_info('###### STARTING ZTP SCRIPT ######\n')
        print ('**** Determining Device Model ****\n')
        log_info('**** Determining Device Model ****\n')
        model = get_model()
        
        software_image = software_mappings[model]['software_image']
        software_version = software_mappings[model]['software_version']
        software_md5_checksum = software_mappings[model]['software_md5_checksum']
        
        print ('**** Checking if upgrade is required or not ***** \n')
        log_info('**** Checking if upgrade is required or not ***** \n')
        update_status, current_version = upgrade_required(software_version)
        if update_status:
            #check if image transfer needed
            if check_file_exists(software_image):
              print(current_version)
              if current_version[0:5] not in release_set:
                if not verify_dst_image_md5(software_image, software_md5_checksum):
                    print ('*** Attempting to transfer image to switch.. ***')
                    log_info('*** Attempting to transfer image to switch.. ***')
                    file_transfer(http_server, software_image)
                    if not verify_dst_image_md5(software_image, software_md5_checksum):
                        log_critical('*** Failed Xfer mds hash mismatch ***')
                        raise ValueError('Failed Xfer')
            else:
              file_transfer(http_server, software_image)
              if current_version[0:5] not in release_set:
                if not verify_dst_image_md5(software_image, software_md5_checksum):
                    log_critical('XXX Failed Xfer XXX')
                    raise ValueError('XXX Failed Xfer XXX')
            
            print ('*** Deploying EEM upgrade script ***')
            log_info('*** Deploying EEM upgrade script ***')
            deploy_eem_upgrade_script(software_image)
            print ('*** Performing the upgrade - switch will reboot ***\n')
            log_info('*** Performing the upgrade - switch will reboot ***\n')
            cli('event manager run upgrade')
            time.sleep(600)
            print('*** EEM upgrade took more than 600 seconds to complete..Increase the sleep time by few minutes before retrying  ***\n')
            log_info('*** EEM upgrade took more than 600 seconds to reload the device..Increase the sleep time by few minutes before retrying  ***\n')
        else:
          print ('*** No upgrade is required!!! *** \n')
          log_info('*** No upgrade is required!!! *** \n')

    # Cleanup any leftover install files
        print ('*** Deploying Cleanup EEM Script ***')
        log_info('*** Deploying Cleanup EEM Script ***')
        deploy_eem_cleanup_script()
        print ('*** Running Cleanup EEM Script ***')
        log_info('*** Running Cleanup EEM Script ***')
        cli('event manager run cleanup')
        time.sleep(30)

    #print config file name to download
        config_file = '%s.cfg' % model
        print('**** Downloading config file ****\n')
        log_info('**** Downloading config file ****\n')
        file_transfer(http_server, config_file)
        print ('*** Trying to perform  Day 0 configuration push  **** \n')
        log_info('*** Trying to perform  Day 0 configuration push  **** \n')
        #configure_replace(config_file)
        configure_merge(config_file)
        configure('crypto key generate rsa modulus 4096')
        print ('######  END OF ZTP SCRIPT ######\n')
        log_info('######  END OF ZTP SCRIPT ######\n')
    
    except Exception as e:
        print('*** Failure encountered during day 0 provisioning . Aborting ZTP script execution. Error details below   ***\n')
        log_critical('*** Failure encountered during day 0 provisioning . Aborting ZTP script execution. Error details below   ***\n' + e)
        print(e)
        sys.exit(e)
       

def configure_replace(file,file_system='flash:/' ):
        config_command = 'configure replace %s%s force' % (file_system, file)
        print("************************Replacing configuration************************\n")
        log_info('************************Replacing configuration************************\n')
        config_repl = executep(config_command)
        time.sleep(120)
    
def configure_merge(file,file_system='flash:/'):
     print("************************Merging running config with given config file************************\n")
     log_info('************************Merging running config with given config file************************\n')
     config_command = 'copy %s%s running-config' %(file_system,file)
     config_repl = executep(config_command)
     time.sleep(120)

def check_file_exists(file, file_system='flash:/'):
    dir_check = 'dir ' + file_system + file
    print ('*** Checking to see if %s exists on %s ***' % (file, file_system))
    log_info('*** Checking to see if %s exists on %s ***' % (file, file_system))
    results = cli(dir_check)
    if 'No such file or directory' in results:
        print ('*** The %s does NOT exist on %s ***' % (file, file_system))
        log_info('*** The %s does NOT exist on %s ***' % (file, file_system))
        return False
    elif 'Directory of %s%s' % (file_system, file) in results:
        print ('*** The %s DOES exist on %s ***' % (file, file_system))
        log_info('*** The %s DOES exist on %s ***' % (file, file_system))
        return True
    elif 'Directory of %s%s' % ('bootflash:/', file) in results:
        print ('*** The %s DOES exist on %s ***' % (file, 'bootflash:/'))
        log_info('*** The %s DOES exist on %s ***' % (file, 'bootflash:/'))
        return True
    else:
        log_critical('************************Unexpected output from check_file_exists************************\n')
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
    results = configurep(eem_commands)
    print ('*** Successfully configured cleanup EEM script on device! ***')
    log_info('*** Successfully configured cleanup EEM script on device! ***')

def deploy_eem_upgrade_script(image):
    install_command = 'install add file flash://' + image + ' activate commit'
    eem_commands = ['event manager applet upgrade',
                    'event none maxrun 600',
                    'action 1.0 cli command "enable"',
                    'action 2.0 cli command "%s" pattern "\[y\/n\/q\]"' % install_command,
                    'action 2.1 cli command "n" pattern "proceed"',
                    'action 2.2 cli command "y"'
                    ]
    results = configurep(eem_commands)
    print ('*** Successfully configured upgrade EEM script on device! ***')
    log_info('*** Successfully configured upgrade EEM script on device! ***')

def file_transfer(http_server, file):
  print('**** Start transferring  file *******\n')
  log_info('**** Start transferring  file *******\n')
  res = cli('copy http://%s/%s flash:%s' % (http_server,file,file))
  print(res)
  log_info(res)
  print("\n")
  print('**** Finished transferring device configuration file *******\n')
  log_info('**** Finished transferring device configuration file *******\n')

def find_certs():
    certs = cli('show run | include crypto pki')
    if certs:
        certs_split = certs.splitlines()
        certs_split.remove('')
        for cert in certs_split:
            command = 'no %s' % (cert)
            configure(command)

def get_serial():
    print ("******** Trying to  get Serial# *********** ")
    log_info("******** Trying to  get Serial# *********** ")
    try:
        show_version = cli('show version')
    except Exception as e:
        time.sleep(90)
        show_version = cli('show version')
    try:
        serial = re.search(r"System Serial Number\s+:\s+(\S+)", show_version).group(1)
    except AttributeError:
        serial = re.search(r"Processor board ID\s+(\S+)", show_version).group(1)
    return serial

def get_model():
    print ("******** Trying to  get Model *********** ")
    log_info("******** Trying to  get Model *********** ")
    try:
        show_version = cli('show version')
    except Exception as e:
        time.sleep(90)
        show_version = cli('show version')
    model = re.search(r"Model Number\s+:\s+(\S+)", show_version)
    if model != None:
        model = model.group(1)
    else:     
        model = re.search(r"cisco\s(\w+-.*?)\s", show_version)
        if model != None:
          model = model.group(1)
    return model

def get_file_system():
    pass

def update_config(file,file_system='flash:/'):
    update_running_config = 'copy %s%s running-config' % (file_system, file)
    save_to_startup = 'write memory'
    print("************************Copying to startup-config************************\n")
    running_config = executep(update_running_config)
    startup_config = executep(save_to_startup)

def upgrade_required(target_version):
    # Obtains show version output
    sh_version = cli('show version')
    current_version = re.search(r"Cisco IOS XE Software, Version\s+(\S+)", sh_version).group(1)
    print('**** Current Code Version is %s ****** \n' % current_version)
    print('**** Target Code Version is %s ****** \n' % target_version)
    log_info('**** Current Code Version is %s ****** \n' % current_version)
    log_info('**** Target Code Version is %s ****** \n' % target_version)
    # Returns False if on approved version or True if upgrade is required

    if (target_version == current_version):
        return False, current_version
    else:
        return True, current_version

def verify_dst_image_md5(image, src_md5, file_system='flash:/'):
    verify_md5 = 'verify /md5 ' + file_system + image
    print ('Verifying MD5 for ' + file_system + image)
    #
    try:
        dst_md5 = cli(verify_md5)
        if src_md5 in dst_md5:
           print ('*** MD5 hashes match!! ***\n')
           log_info('*** MD5 hashes match!! ***\n')
           return True
        else:
          print ('**** Failed transfer due to MD5 checksum mismatch *****')
          log_info('**** Failed transfer due to MD5 checksum mismatch *****')
          return False
    except Exception as e:
       print ('****  MD5 checksum failed due to an exception  *****')
       print(e)
       log_info('****  MD5 checksum failed due to an exception  *****')
       log_info(e)
       return True
        #output = subprocess.Popen(['md5sum', '/flash/'+image],stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        #stdout_data, stderr_data = output.communicate()
        #output.wait() 
        #outputdata = (stdout_data.decode('utf-8')).split()
        #md5_returned = outputdata[0]
        #if src_md5 == md5_returned:
         #   return True
        #else:
         #   return False
    
def create_logfile():
    try:
        print ("******** Creating  a persistent log file *********** ")
        path = '/flash/guest-share/ztp.log'
        #file_exists = os.path.isfile(path)
        #if(file_exists == False):
          #print ("******** ztp.log file dont exist .  *********** ")
        with open(path, 'a+') as fp:
             pass
        return path
    except IOError:
      print("Couldnt create a log file at guset-share .Trying to use  /flash/ztp.log as an alternate log path")
      path = '/flash/ztp.log'
      #file_exists = os.path.isfile(path)
      #if(file_exists == False):
      #    print ("******** ztp.log file dont exist .  *********** ")
      with open(path, 'a+') as fp:
             pass
      return path
    except Exception as e:
         print("Couldnt create a log file to proceed")


def configure_logger(path):
    log_formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')
    logFile = path
    #create a new file > 5 mb size
    log_handler = RotatingFileHandler(logFile, mode='a', maxBytes=5*1024*1024, backupCount=10, encoding=None, delay=0)
    log_handler.setFormatter(log_formatter)
    log_handler.setLevel(logging.INFO)
    ztp_log = logging.getLogger('root')
    ztp_log.setLevel(logging.INFO)
    ztp_log.addHandler(log_handler)
    
def log_info(message ):
    if(log_tofile == True):
        ztp_log = logging.getLogger('root')
        ztp_log.info(message)

def log_critical(message ):
    if(log_tofile == True):
        ztp_log = logging.getLogger('root')
        ztp_log.critical(message)


if __name__ == "__main__":
    main()

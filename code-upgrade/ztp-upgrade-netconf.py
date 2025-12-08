#!/usr/bin/env python3
"""
ZTP NETCONF Software Upgrade Script for Cisco Catalyst 9000 Series
===================================================================

Description:
    This script performs automated software upgrades using NETCONF RPCs
    during Zero-Touch Provisioning (ZTP) on Cisco Catalyst 9000 switches.

    The script will:
    - Verify current IOS XE version supports NETCONF (17.6+)
    - Download target image from HTTP server if not present
    - Verify MD5 checksum of the image
    - Execute NETCONF install RPC to trigger upgrade
    - Device will automatically reload and apply new image

Target Version: 17.15.01
Expected Runtime: ~2 minutes (script) + 5-7 minutes (upgrade)

Requirements:
    - IOS XE 17.6 or newer (for NETCONF install RPC support)
    - Guestshell enabled
    - NETCONF service available
    - HTTP server hosting the target image

Author: Cisco ZTP Automation
Date: December 2025
Reference: https://github.com/YangModels/yang/tree/main/vendor/cisco/xe

NETCONF YANG Models Used:
    - Cisco-IOS-XE-install-rpc (install operations)
    - Cisco-IOS-XE-install-oper (status queries)
    - Cisco-IOS-XE-native (hostname retrieval)
"""

# ============================================================================
# IMPORTS
# ============================================================================

from cli import cli, configurep
import cli as cli_module
import re
import sys
import time
import uuid
import xml.dom.minidom
from datetime import datetime

# NETCONF imports - only needed for IOS XE 17.6+
# These will be imported later after version check
# from ncclient import manager
# from lxml import etree


# ============================================================================
# CONFIGURATION - MODIFY THESE VALUES FOR YOUR ENVIRONMENT
# ============================================================================

# Target software version and image details
TARGET_VERSION = '17.18.01'
TARGET_IMAGE = 'usbflash1:/cat9k_iosxe.17.18.01.SPA.bin'
TARGET_IMAGE_MD5 = '3d95fc4dffa160507e927612ce38a7ee'

# HTTP server for image downloads
HTTP_SERVER = '10.1.1.3'  # Your HTTP server IP
HTTP_PATH = '/'           # Path to image file on server

# NETCONF connection parameters (localhost via guestshell - No need to change these defaults)
NETCONF_HOST = '127.0.0.1'
NETCONF_PORT = 830
NETCONF_USER = 'guestshell'
NETCONF_PASS = ''  # SSH key authentication used
NETCONF_KEY = '/home/guestshell/.ssh/id_rsa_netconf'


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def log(message, level='INFO'):
    """Print timestamped log message"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print('[{}] {}: {}'.format(timestamp, level, message))


def print_banner():
    """Display script information banner"""
    banner = """
    ========================================================================
    Cisco Catalyst 9000 ZTP NETCONF Software Upgrade
    ========================================================================
    Method:          NETCONF RPC (Cisco-IOS-XE-install-rpc)
    Target Version:  {}
    Expected Time:   ~2 minutes (script) + 5-7 minutes (upgrade)
    ========================================================================
    """.format(TARGET_VERSION)
    print(banner)


# ============================================================================
# VERSION DETECTION AND COMPATIBILITY CHECKS
# ============================================================================


def get_current_version():
    """
    Get current IOS-XE version from 'show version' output

    Returns:
        str: Version string (e.g., '17.15.01') or None if parse fails
    """
    log('Checking current software version...')
    try:
        output = cli('show version')
        match = re.search(r'Cisco IOS XE Software, Version\s+(\S+)', output)
        if match:
            version = match.group(1)
            log('Current version: {}'.format(version))
            return version
        else:
            log('Could not parse version from show version', 'ERROR')
            return None
    except Exception as e:
        log('Error getting version: {}'.format(str(e)), 'ERROR')
        return None


def check_netconf_api_support(version):
    """
    Verify IOS XE version supports NETCONF install RPC (17.6+)

    Args:
        version (str): IOS XE version string

    Returns:
        bool: True if version >= 17.6, False otherwise
    """
    log('Checking NETCONF API compatibility...')
    try:
        # Parse version (e.g., '17.15.01' -> major=17, minor=15)
        version_clean = version.rstrip('abcdefghijklmnopqrstuvwxyz')
        parts = version_clean.split('.')

        if len(parts) >= 2:
            major = int(parts[0])
            minor = int(parts[1])

            # NETCONF install RPC requires IOS XE 17.6 or newer
            if major > 17 or (major == 17 and minor >= 6):
                log('Version {} supports NETCONF install RPC'.format(version))

                # Import ncclient and lxml now that we've confirmed support
                log('Importing NETCONF libraries...')
                try:
                    global manager, etree
                    from ncclient import manager
                    from lxml import etree
                    log('NETCONF libraries imported successfully')
                except ImportError as ie:
                    log('Failed to import NETCONF libraries: {}'.format(
                        str(ie)), 'ERROR')
                    log('ncclient and lxml must be available', 'ERROR')
                    return False

                return True
            else:
                log('Version {} does NOT support NETCONF'.format(
                    version), 'ERROR')
                log('Requires IOS XE 17.6 or newer', 'ERROR')
                return False
        else:
            log('Could not parse version format: {}'.format(version), 'ERROR')
            return False

    except Exception as e:
        log('Error checking version: {}'.format(str(e)), 'ERROR')
        return False
# ============================================================================
# IMAGE VERIFICATION AND DOWNLOAD FUNCTIONS
# ============================================================================
def calculate_md5(image_path):
    """
    Calculate MD5 checksum of image file using CLI command

    Args:
        image_path (str): Full path to image file

    Returns:
        str: MD5 hash (lowercase hex) or None if calculation fails
    """
    log('Calculating MD5 checksum for: {}'.format(image_path))
    try:
        output = cli('verify /md5 {}'.format(image_path))
        # Parse: "verify /md5 (path) = e5496cd..."
        match = re.search(r'=\s*([0-9a-fA-F]{32})', output)
        if match:
            md5_hash = match.group(1).lower()
            log('Calculated MD5: {}'.format(md5_hash))
            return md5_hash
        else:
            log('Could not parse MD5 from output', 'ERROR')
            return None
    except Exception as e:
        log('Error calculating MD5: {}'.format(str(e)), 'ERROR')
        return None


def verify_image_checksum(image_path, expected_md5):
    """
    Verify image MD5 checksum matches expected value

    Args:
        image_path (str): Full path to image file
        expected_md5 (str): Expected MD5 hash value

    Returns:
        bool: True if checksums match, False otherwise
    """
    log('Verifying image checksum...')
    actual_md5 = calculate_md5(image_path)

    if not actual_md5:
        log('Failed to calculate MD5 checksum', 'ERROR')
        return False

    # Normalize both hashes: lowercase and strip whitespace
    actual_normalized = actual_md5.lower().strip()
    expected_normalized = expected_md5.lower().strip()

    log('Expected MD5: {}'.format(expected_normalized))
    log('Actual MD5:   {}'.format(actual_normalized))

    if actual_normalized == expected_normalized:
        log('MD5 checksum verified successfully', 'SUCCESS')
        return True
    else:
        log('MD5 mismatch detected!', 'ERROR')
        log('Expected: {}'.format(expected_normalized), 'ERROR')
        log('Got:      {}'.format(actual_normalized), 'ERROR')

        # Show character-by-character comparison if lengths match
        if len(actual_normalized) == len(expected_normalized):
            differences = []
            for i, (a, e) in enumerate(zip(actual_normalized, expected_normalized)):
                if a != e:
                    differences.append('Position {}: expected "{}" got "{}"'.format(
                        i, e, a))
            if differences:
                log('Differences found:', 'ERROR')
                for diff in differences:
                    log('  {}'.format(diff), 'ERROR')
        else:
            log('Length mismatch: expected {} chars, got {} chars'.format(
                len(expected_normalized), len(actual_normalized)), 'ERROR')

        return False
def verify_image_exists(image_path):
    """
    Check if image file exists on device storage

    Args:
        image_path (str): Full path to image file

    Returns:
        bool: True if file exists, False otherwise
    """
    log('Verifying image file: {}'.format(image_path))
    try:
        output = cli('dir {}'.format(image_path))
        if 'Error' in output or 'No such file' in output:
            log('Image file not found: {}'.format(image_path), 'ERROR')
            return False
        log('Image file verified: {}'.format(image_path))
        return True
    except Exception as e:
        log('Error verifying image: {}'.format(str(e)), 'ERROR')
        return False


def download_image(image_path, image_filename):
    """
    Download image from HTTP server to device storage

    Args:
        image_path (str): Destination path on device
        image_filename (str): Filename of image to download

    Returns:
        bool: True if download successful, False otherwise
    """
    log('Image not found, attempting to download...')

    # Build HTTP URL
    http_url = 'http://{}{}{}'.format(HTTP_SERVER, HTTP_PATH, image_filename)
    log('Download URL: {}'.format(http_url))
    log('Destination: {}'.format(image_path))

    # Check available space on usbflash1
    try:
        log('Checking available space on usbflash1:...')
        output = cli('dir usbflash1:')
        match = re.search(r'(\d+) bytes free', output)

        if match:
            free_bytes = int(match.group(1))
            free_gb = free_bytes / (1024**3)
            log('Free space: {:.2f} GB'.format(free_gb))

            if free_gb < 2.0:
                log('Insufficient space (need ~2GB minimum)', 'ERROR')
                return False
        else:
            log('Could not determine free space, continuing anyway', 'WARNING')

    except Exception as e:
        log('Error checking space: {}'.format(str(e)), 'WARNING')

    # Download the image via HTTP
    try:
        log('Starting download (this may take 10-15 minutes)...')
        copy_cmd = 'copy {} {}'.format(http_url, image_path)
        log('Executing: {}'.format(copy_cmd))

        start_time = time.time()
        output = cli('configure terminal\nexit\n' + copy_cmd)
        elapsed = time.time() - start_time

        log('Download completed in {} seconds'.format(int(elapsed)))

        # Check for errors in output
        if output:
            if 'Error' in output or 'failed' in output.lower():
                log('Download failed: {}'.format(output), 'ERROR')
                return False

        # Verify file exists after download
        if verify_image_exists(image_path):
            log('Image successfully downloaded and verified')
            return True
        else:
            log('Download appeared to succeed but file not found', 'ERROR')
            return False

    except Exception as e:
        log('Error downloading image: {}'.format(str(e)), 'ERROR')
        return False


# ============================================================================
# NETCONF SETUP FUNCTIONS
# ============================================================================
def enable_netconf_guestshell():
    """
    Enable NETCONF service and guestshell access

    This function:
    1. Enables global netconf-yang service if not already enabled
    2. Enables NETCONF API access from guestshell
    3. Generates SSH keys for authentication (~100 seconds)

    Returns:
        bool: True on success, continues anyway on error
    """
    log('Ensuring NETCONF is enabled from guestshell...')
    try:
        # Check if netconf-yang is globally enabled
        output = cli('show run | include netconf-yang')
        if 'netconf-yang' in output:
            log('NETCONF already enabled globally')
        else:
            log('Enabling NETCONF service...')
            configurep(['netconf-yang'])

        # Enable NETCONF API from guestshell (generates SSH keys)
        log('Enabling NETCONF from guestshell (takes ~100 seconds)...')
        start_time = time.time()
        cli_module.netconf_enable_guestshell()
        elapsed = time.time() - start_time
        log('NETCONF enabled in {} seconds'.format(int(elapsed)))

        return True

    except Exception as e:
        log('Error enabling NETCONF: {}'.format(str(e)), 'WARNING')
        return True  # Continue anyway


# ============================================================================
# NETCONF CONNECTION AND RPC FUNCTIONS
# ============================================================================
def create_netconf_connection(max_retries=5, retry_delay=10):
    """
    Create NETCONF connection with retry logic

    Connects to localhost:830 via SSH using guestshell credentials
    and SSH key authentication.

    Args:
        max_retries (int): Number of connection attempts
        retry_delay (int): Seconds to wait between retries

    Returns:
        ncclient.manager.Manager: NETCONF connection or None on failure
    """
    log('Creating NETCONF connection...')

    for attempt in range(1, max_retries + 1):
        try:
            log('Connection attempt {} of {}...'.format(attempt, max_retries))
            conn = manager.connect(
                host=NETCONF_HOST,
                port=NETCONF_PORT,
                username=NETCONF_USER,
                password=NETCONF_PASS,
                hostkey_verify=False,
                device_params={'name': 'default'},
                key_filename=NETCONF_KEY,
                allow_agent=False,
                look_for_keys=True
            )
            log('NETCONF connection established on attempt {}'.format(attempt))
            return conn

        except Exception as e:
            log('Attempt {} failed: {}'.format(attempt, str(e)), 'WARNING')
            if attempt < max_retries:
                log('Retrying in {} seconds...'.format(retry_delay))
                time.sleep(retry_delay)
            else:
                msg = 'Failed to create NETCONF connection after {} attempts'
                log(msg.format(max_retries), 'ERROR')
                return None


def get_hostname_netconf(conn):
    """
    Retrieve hostname via NETCONF (connection test)

    Args:
        conn: NETCONF connection object

    Returns:
        str: Device hostname or None on failure
    """
    log('Testing NETCONF connection by getting hostname...')

    filter_xml = '''
        <filter xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
          <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
            <hostname></hostname>
          </native>
        </filter>
    '''

    try:
        response = conn.get_config(source='running', filter=filter_xml)
        xml_doc = xml.dom.minidom.parseString(response.xml)
        hostname_elem = xml_doc.getElementsByTagName('hostname')

        if hostname_elem:
            hostname = hostname_elem[0].firstChild.nodeValue
            log('Retrieved hostname via NETCONF: {}'.format(hostname))
            return hostname
        else:
            log('No hostname found in NETCONF response', 'WARNING')
            return None

    except Exception as e:
        log('Error getting hostname: {}'.format(str(e)), 'ERROR')
        return None


def send_activate_rpc(conn, image_path):
    """
    Send NETCONF install RPC to trigger software upgrade

    Uses Cisco-IOS-XE-install-rpc YANG model to send install operation
    with one-shot mode (automatic reload after install).

    Args:
        conn: NETCONF connection object
        image_path (str): Full path to target image file

    Returns:
        bool: True if RPC accepted, False on error
    """
    log('Preparing NETCONF install RPC...')

    # Generate unique UUID for this operation
    operation_uuid = str(uuid.uuid4())
    log('Operation UUID: {}'.format(operation_uuid))

    # Build the RPC XML string - use <install> with <one-shot>true</one-shot>
    xmlns = 'http://cisco.com/ns/yang/Cisco-IOS-XE-install-rpc'
    rpc_xml_str = '''<install xmlns="{}">'''.format(xmlns) + '''
  <uuid>{}</uuid>
  <one-shot>true</one-shot>
  <path>{}</path>
</install>'''.format(operation_uuid, image_path)

    log('Sending install RPC for image: {}'.format(image_path))
    log('RPC XML:\n{}'.format(rpc_xml_str))

    try:
        # Convert string to XML element for dispatch
        rpc_xml = etree.fromstring(rpc_xml_str)

        # Send the RPC
        response = conn.dispatch(rpc_xml)

        log('RPC Response received:')
        xml_pretty = xml.dom.minidom.parseString(response.xml).toprettyxml()
        log('\n{}'.format(xml_pretty))

        # Check response for success or errors
        if '<ok/>' in response.xml:
            log('Activate RPC accepted - upgrade initiated!', 'SUCCESS')
            return True
        elif 'rpc-error' in response.xml:
            log('RPC Error in response', 'ERROR')
            log(xml_pretty)
            return False
        else:
            log('Unexpected response format', 'WARNING')
            return True  # Proceed anyway

    except Exception as e:
        log('Error sending activate RPC: {}'.format(str(e)), 'ERROR')
        log('Exception details: {}'.format(repr(e)), 'DEBUG')
        return False


def query_install_status_netconf(conn):
    """
    Query installation status via NETCONF operational data

    Uses Cisco-IOS-XE-install-oper YANG model to retrieve current
    install operation status.

    Args:
        conn: NETCONF connection object

    Returns:
        bool: True on successful query, False on error
    """
    log('Querying install status via NETCONF...')

    xmlns_oper = 'http://cisco.com/ns/yang/Cisco-IOS-XE-install-oper'
    filter_xml = '''
        <filter xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
          <install-oper-data xmlns="{}">'''.format(xmlns_oper) + '''
            <install-oper/>
          </install-oper-data>
        </filter>
    '''

    try:
        response = conn.get(filter=filter_xml)
        xml_pretty = xml.dom.minidom.parseString(response.xml).toprettyxml()
        log('Install operational data:')
        log('\n{}'.format(xml_pretty))
        return True

    except Exception as e:
        log('Error querying install status: {}'.format(str(e)), 'WARNING')
        return False


# ============================================================================
# MAIN UPGRADE WORKFLOW
# ============================================================================

def main():
    """Main upgrade workflow"""
    print_banner()
    log('=== ZTP NETCONF Software Upgrade Started ===')

    # Step 1: Get current version
    current_version = get_current_version()
    if not current_version:
        log('Cannot proceed without version information', 'ERROR')
        sys.exit(1)

    # Step 2: Check NETCONF API compatibility
    if not check_netconf_api_support(current_version):
        log('Current version does not support NETCONF install RPC', 'ERROR')
        log('This script requires IOS XE 17.6 or newer', 'ERROR')
        sys.exit(1)

    # Step 3: Check if already on target version
    current_clean = current_version.rstrip('abcdefghijklmnopqrstuvwxyz')
    if current_clean == TARGET_VERSION:
        msg = 'Already running target version {}!'
        log(msg.format(TARGET_VERSION), 'SUCCESS')
        log('No upgrade needed - exiting')
        sys.exit(0)

    log('Current version: {}'.format(current_version))
    log('Target version: {}'.format(TARGET_VERSION))
    log('Target image: {}'.format(TARGET_IMAGE))

    # Step 4: Verify image exists, download if needed
    if not verify_image_exists(TARGET_IMAGE):
        log('Image not found on device, attempting download...', 'WARNING')

        # Extract filename from path
        image_filename = TARGET_IMAGE.split('/')[-1]

        if not download_image(TARGET_IMAGE, image_filename):
            log('Cannot proceed - image not available', 'ERROR')
            sys.exit(1)
    else:
        log('Image already present on device')

    # Step 5: Verify MD5 checksum
    if not verify_image_checksum(TARGET_IMAGE, TARGET_IMAGE_MD5):
        log('Image checksum verification failed!', 'ERROR')
        log('Image may be corrupted - aborting upgrade', 'ERROR')
        sys.exit(1)

    # Step 6: Enable NETCONF if needed
    enable_netconf_guestshell()

        # Step 6: Enable NETCONF if needed
    enable_netconf_guestshell()

    # Step 7: Create NETCONF connection with retry logic
    log('Waiting 10 seconds for NETCONF service to be ready...')
    time.sleep(10)

    conn = create_netconf_connection(max_retries=5, retry_delay=5)
    if not conn:
        log('Cannot proceed without NETCONF connection', 'ERROR')
        sys.exit(1)

    # Step 8: Test NETCONF connection
    hostname = get_hostname_netconf(conn)
    if hostname:
        log('NETCONF connection validated successfully')
    else:
        log('Could not validate NETCONF connection', 'WARNING')

    # Step 9: Query current install status (optional)
    log('Checking current install status...')
    query_install_status_netconf(conn)

    # Step 10: Send activate RPC
    log('=== Initiating Software Upgrade ===')
    log('Current: {} -> Target: {}'.format(current_version, TARGET_VERSION))
    log('Image: {}'.format(TARGET_IMAGE))
    log('')
    log('Sending NETCONF activate RPC...')

    success = send_activate_rpc(conn, TARGET_IMAGE)

    if success:
        log('=== Upgrade RPC Successfully Sent ===', 'SUCCESS')
        log('Device will now install and reload automatically')
        log('Expected timeline:')
        log('  - Install process: ~1-2 minutes')
        log('  - Microcode update: ~1-2 minutes')
        log('  - Device reload: ~2-3 minutes')
        log('  - Total downtime: ~5-7 minutes')
        log('')
        log('Auto-abort timer: 2 hours (7200 seconds)')
        log('Post-reload actions required:')
        log('  1. Verify: show version')
        log('  2. Check status: show install summary')
        log('  3. COMMIT within 2 hours: install commit')
        log('     (or device will auto-rollback)')

        # Close NETCONF connection
        conn.close_session()
        log('NETCONF session closed')

        log('=== ZTP NETCONF Upgrade Script Complete ===')
        log('Device will reload shortly...')
        sys.exit(0)

    else:
        log('Failed to send upgrade RPC', 'ERROR')
        conn.close_session()
        sys.exit(1)


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        log('Script interrupted by user', 'WARNING')
        sys.exit(1)
    except Exception as e:
        log('Unexpected error: {}'.format(str(e)), 'ERROR')
        log('Exception details: {}'.format(repr(e)), 'DEBUG')
        sys.exit(1)

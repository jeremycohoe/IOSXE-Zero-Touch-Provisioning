#!/usr/bin/env python3
"""
Unified Day0 Onboarding Script for Cisco Nexus (POAP) and Catalyst XE (ZTP)
This script auto-detects the device type and applies the appropriate
configuration.

Based on Cisco official POAP and ZTP examples with enhancements.
"""

import sys
import os
import json
import re
import time
import syslog

# Try to import device-specific modules
try:
    import cli  # Available on IOS-XE ZTP
    DEVICE_TYPE = "IOS-XE"
except ImportError:
    try:
        from cisco import system  # Available on NX-OS POAP
        DEVICE_TYPE = "NX-OS"
    except ImportError:
        # Fallback detection method
        DEVICE_TYPE = None


def detect_device_type():
    """
    Detect whether this is a Nexus (NX-OS) or Catalyst (IOS-XE) device
    Returns: 'NX-OS' or 'IOS-XE'
    """
    global DEVICE_TYPE

    if DEVICE_TYPE:
        return DEVICE_TYPE

    # Alternative detection methods
    if os.path.exists('/bootflash/'):
        # Check for NX-OS specific paths
        if os.path.exists('/isan/'):
            DEVICE_TYPE = "NX-OS"
            return "NX-OS"

    # Check for IOS-XE specific paths
    if os.path.exists('/flash/'):
        DEVICE_TYPE = "IOS-XE"
        return "IOS-XE"

    # Try checking environment or process info
    try:
        with open('/proc/version', 'r') as f:
            version_info = f.read()
            if 'NX-OS' in version_info or 'nexus' in version_info.lower():
                DEVICE_TYPE = "NX-OS"
                return "NX-OS"
    except:
        pass

    return "UNKNOWN"


def log_message(message):
    """
    Log messages to console, syslog, and optionally to file
    Enhanced logging similar to official POAP script
    """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    sys.stdout.flush()

    # Also log to syslog (priority 9 = info)
    try:
        syslog.syslog(9, log_msg)
    except Exception:
        pass  # Syslog may not be available in all environments


def configure_nxos_device():
    """
    Configure Cisco Nexus (NX-OS) device via POAP
    Enhanced with features from official Cisco POAP script
    """
    log_message("Starting NX-OS POAP Configuration")

    try:
        # Import NX-OS specific modules
        from cli import cli, clid

        # Get device information
        try:
            serial_num = os.environ.get('POAP_SERIAL', 'UNKNOWN')
            log_message(f"Device Serial Number: {serial_num}")
        except Exception as e:
            log_message(f"Could not retrieve serial number: {str(e)}")
            serial_num = "UNKNOWN"

        # Create configuration file in bootflash
        config_file_path = "/bootflash/poap_config.cfg"
        log_message(f"Creating configuration file: {config_file_path}")

        # Build NX-OS configuration
        nxos_config = """
! NX-OS Configuration via POAP
hostname NXOS-SWITCH-POAP
!
feature interface-vlan
feature ssh
feature nxapi
feature lldp
!
username admin password Cisco123 role network-admin
enable secret Cisco123
!
vlan 10
  name DATA_VLAN
vlan 20
  name VOICE_VLAN
!
interface Ethernet1/1
  description UPLINK
  no switchport
  ip address 10.0.0.1/24
  no shutdown
!
interface mgmt0
  description MANAGEMENT
  ip address dhcp
  no shutdown
!
line vty
  exec-timeout 30
  session-limit 10
!
boot nxos bootflash:nxos.bin
"""

        # Write configuration to file
        try:
            with open(config_file_path, 'w') as f:
                f.write(nxos_config.strip())
            log_message("Configuration file created successfully")
        except Exception as e:
            log_message(f"Error creating config file: {str(e)}")
            # Fall back to direct CLI commands
            return apply_nxos_config_via_cli(nxos_config)

        # Apply configuration using copy scheduled-config method
        log_message("Applying configuration via scheduled-config...")
        try:
            # Copy config to scheduled-config for reload
            cli("terminal dont-ask")
            cli("copy bootflash:poap_config.cfg scheduled-config")
            log_message("Configuration scheduled successfully")

            # Also apply to running config immediately
            cli("copy bootflash:poap_config.cfg running-config")
            log_message("Configuration applied to running-config")

            # Save to startup config
            cli("copy running-config startup-config")
            log_message("Configuration saved to startup-config")

        except Exception as e:
            log_message(f"Error applying configuration: {str(e)}")
            # Try alternative method
            return apply_nxos_config_via_cli(nxos_config)

        log_message("NX-OS configuration completed successfully")
        return True

    except Exception as e:
        log_message(f"Error during NX-OS configuration: {str(e)}")
        return False


def apply_nxos_config_via_cli(config_text):
    """
    Fallback method to apply NX-OS configuration line by line
    """
    from cli import cli

    log_message("Using fallback CLI method for configuration")

    # Split config into lines and filter
    config_lines = [line.strip() for line in config_text.split('\n')
                    if line.strip() and not line.strip().startswith('!')]

    try:
        cli("terminal dont-ask")
        cli("configure terminal")

        for line in config_lines:
            if line:
                log_message(f"Executing: {line}")
                try:
                    output = cli(line)
                    if output:
                        log_message(f"Output: {output}")
                except Exception as e:
                    log_message(f"Error on '{line}': {str(e)}")

        cli("end")
        cli("copy running-config startup-config")

        log_message("Fallback configuration method completed")
        return True

    except Exception as e:
        log_message(f"Fallback method failed: {str(e)}")
        return False


def configure_iosxe_device():
    """
    Configure Cisco Catalyst (IOS-XE) device via ZTP
    """
    log_message("Starting IOS-XE ZTP Configuration")

    try:
        # Import IOS-XE specific modules
        import cli

        # Build configuration as a single block (maintains config mode context)
        iosxe_config = """
hostname IOSXE-SWITCH-SETBY-ZTP
!
!
username admin privilege 15 secret Cisco123
enable secret Cisco123
!
vlan 10
 name DATA_VLAN
vlan 20
 name VOICE_VLAN
!
interface GigabitEthernet1/0/1
 description UPLINK
 no switchport
 ip address 10.0.0.2 255.255.255.0
 no shutdown
!
interface Vlan1
 description MANAGEMENT
 ip address dhcp
 no shutdown
!
ip ssh version 2
!
line vty 0 15
 transport input all
 login local
 exec-timeout 30 0
!
end
"""

        log_message("Applying IOS-XE configuration block...")
        try:
            # Use cli.configure() to apply entire config block at once
            output = cli.configure(iosxe_config.strip().split('\n'))
            if output:
                log_message(f"Configuration output: {output}")
        except Exception as e:
            log_message(f"Error applying configuration: {str(e)}")
            # Try alternative method with cli.cli()
            try:
                log_message("Attempting alternative configuration method...")
                output = cli.cli('configure terminal\n' + iosxe_config + '\nend')
                if output:
                    log_message(f"Configuration output: {output}")
            except Exception as e2:
                log_message(f"Alternative method also failed: {str(e2)}")
                return False

        # Generate RSA keys (requires separate execution)
        log_message("Generating RSA keys...")
        try:
            output = cli.execute("crypto key generate rsa modulus 2048")
            log_message(f"RSA key generation: {output}")
        except Exception as e:
            log_message(f"RSA key generation note: {str(e)}")

        # Save configuration
        log_message("Saving configuration...")
        try:
            output = cli.execute("write memory")
            log_message(f"Save output: {output}")
        except Exception as e:
            log_message(f"Error saving configuration: {str(e)}")

        log_message("IOS-XE configuration completed successfully")
        return True

    except Exception as e:
        log_message(f"Error during IOS-XE configuration: {str(e)}")
        return False
def main():
    """
    Main function to orchestrate the unified onboarding process
    """
    log_message("=" * 60)
    log_message("UNIFIED DAY0 ONBOARDING SCRIPT")
    log_message("=" * 60)

    # Log environment information
    log_message("Environment Information:")
    if 'POAP_SERIAL' in os.environ:
        log_message(f"  Serial Number: {os.environ['POAP_SERIAL']}")
    if 'POAP_PHASE' in os.environ:
        log_message(f"  POAP Phase: {os.environ['POAP_PHASE']}")
    if 'POAP_INTF' in os.environ:
        log_message(f"  Interface: {os.environ['POAP_INTF']}")

    # Detect device type
    device_type = detect_device_type()
    log_message(f"Detected Device Type: {device_type}")

    if device_type == "NX-OS":
        log_message("This is a Cisco Nexus device - using POAP workflow")
        success = configure_nxos_device()
    elif device_type == "IOS-XE":
        log_message("This is a Cisco Catalyst device - using ZTP workflow")
        success = configure_iosxe_device()
    else:
        log_message("ERROR: Unable to detect device type!")
        log_message(
            "This script supports only Cisco Nexus (NX-OS) "
            "and Catalyst (IOS-XE)"
        )
        sys.exit(1)

    if success:
        log_message("=" * 60)
        log_message("ONBOARDING COMPLETED SUCCESSFULLY")
        log_message("=" * 60)
        sys.exit(0)
    else:
        log_message("=" * 60)
        log_message("ONBOARDING FAILED - Check logs for details")
        log_message("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()

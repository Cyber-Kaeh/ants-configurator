"""Avocor G60 display configuration module"""
import subprocess
import os


def configure(serial: str) -> bool:
    """
    Configure Avocor G60 display defaults.
    
    Args:
        serial: The USB serial number for the display
        
    Returns:
        bool: True if configuration succeeded, False otherwise
    """
    print(f"Configuring Avocor G60 with serial: {serial}")
    
    # Find the USB serial device
    device_path = f"/dev/tty.usbserial-{serial}"
    
    # Check if device exists
    if not os.path.exists(device_path):
        print(f"⚠️  Warning: Serial device not found: {device_path}")
    
    # Define all the defaults to write for G60
    defaults_config = {
        "Name": "Main 4K Avocor",
        "ExpectedPowerON": "Power On",
        "ExpectedSignal": "Signal Present",
        "GetSignal": f"/usr/local/bin/python /Local/scripts/serial/AvocorG60.py {device_path} GetSignalv2",
        "GetPower": f"/usr/local/bin/python /Local/scripts/serial/AvocorG60.py {device_path} GetPower",
        "PowerOn": f"/usr/local/bin/python /Local/scripts/serial/AvocorG60.py {device_path} PowerOn",
        "PowerOff": f"/usr/local/bin/python /Local/scripts/serial/AvocorG60.py {device_path} PowerOff",
        "GetMute": f"/usr/local/bin/python /Local/scripts/serial/AvocorG60.py {device_path} GetMute",
        "GetVolume": f"/usr/local/bin/python /Local/scripts/serial/AvocorG60.py {device_path} GetVolume",
        "HDMI1": f"/usr/local/bin/python /Local/scripts/serial/AvocorG60.py {device_path} HDMI1",
        "HDMI2": f"/usr/local/bin/python /Local/scripts/serial/AvocorG60.py {device_path} HDMI2",
        "HDMI3": f"/usr/local/bin/python /Local/scripts/serial/AvocorG60.py {device_path} HDMI3",
        "HDMI4": f"/usr/local/bin/python /Local/scripts/serial/AvocorG60.py {device_path} HDMI4",
    }
    
    try:
        for key, value in defaults_config.items():
            result = subprocess.run([
                "defaults", "write", "com.t1visions.SerialScripts",
                "Display 1", "-dict-add", key, value
            ], check=True, capture_output=True, text=True)
            print(f"  ✓ Set {key}")
        
        print("✅ Avocor G60 configuration complete!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Configuration failed: {e}")
        if e.stderr:
            print(f"Error details: {e.stderr}")
        return False
import subprocess
import os
from pathlib import Path

def configure(serial: str) -> None:
    """Configure Avocor E50 display defaults."""
    
    # Find the USB serial device
    device = f"/dev/tty.usbserial-{serial}"
    if not os.path.exists(device):
        raise FileNotFoundError(f"Serial device not found: {device}")
    
    # Define all the defaults to write
    defaults_config = {
        "Name": "Main 4K Avocor",
        "ExpectedPowerON": "Power On",
        "GetPower": f"/usr/local/bin/python /Local/scripts/serial/AvocorE50.py {device} GetPower",
        "PowerOn": f"/usr/local/bin/python /Local/scripts/serial/AvocorE50.py {device} PowerOn",
        "PowerOff": f"/usr/local/bin/python /Local/scripts/serial/AvocorE50.py {device} PowerOff",
        "GetButtonLock": f"/usr/local/bin/python /Local/scripts/serial/AvocorE50.py {device} GetButtonLock",
        "ButtonLockOff": f"/usr/local/bin/python /Local/scripts/serial/AvocorE50.py {device} ButtonLockOff",
        "ButtonLockOn": f"/usr/local/bin/python /Local/scripts/serial/AvocorE50.py {device} ButtonLockOn",
        "GetMute": f"/usr/local/bin/python /Local/scripts/serial/AvocorE50.py {device} GetMute",
        "GetVolume": f"/usr/local/bin/python /Local/scripts/serial/AvocorE50.py {device} GetVolume",
        "HDMI1": f"/usr/local/bin/python /Local/scripts/serial/AvocorE50.py {device} HDMI1",
        "HDMI2": f"/usr/local/bin/python /Local/scripts/serial/AvocorE50.py {device} HDMI2",
        "HomeScreen": f"/usr/local/bin/python /Local/scripts/serial/AvocorE50.py {device} HomeScreen",
        "Reset": f"/usr/local/bin/python /Local/scripts/serial/AvocorE50.py {device} Reset"
    }
    
    for key, value in defaults_config.items():
        subprocess.run([
            "defaults", "write", "com.t1visions.SerialScripts",
            "Display 1", "-dict-add", key, value
        ], check=True)
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
        "ExpectedSignal": "Signal Present",
        "BacklightOff": f"/usr/local/bin/python /Local/scripts/serial/AvocorG60.py {device} BacklightOff",
        "BacklightOn": f"/usr/local/bin/python /Local/scripts/serial/AvocorG60.py {device} BacklightOn",
        "GetBacklight": f"/usr/local/bin/python /Local/scripts/serial/AvocorG60.py {device} GetBackLight",
        "GetPower": f"/usr/local/bin/python /Local/scripts/serial/AvocorG60.py {device} GetPower",
        "GetSignal": f"/usr/local/bin/python /Local/scripts/serial/AvocorG60.py {device} GetSignalv2",
        "GetFirmware": f"/usr/local/bin/python /Local/scripts/serial/AvocorG60.py {device} GetFirmware",
        "SetInput": f"/usr/local/bin/python /Local/scripts/serial/AvocorG60.py {device} HDMI2",
        "LockKeys": f"/usr/local/bin/python /Local/scripts/serial/AvocorG60.py {device} LockKeys",
        "UnlockKeys": f"/usr/local/bin/python /Local/scripts/serial/AvocorG60.py {device} UnlockKeys",
    }
    
    for key, value in defaults_config.items():
        subprocess.run([
            "defaults", "write", "com.t1visions.SerialScripts",
            "Display 1", "-dict-add", key, value
        ], check=True)
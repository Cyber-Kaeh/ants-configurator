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
        "BacklightOff": f"/usr/local/bin/python /Local/scripts/serial/AvocorF50.py {device} BacklightOff",
        "BacklightOn": f"/usr/local/bin/python /Local/scripts/serial/AvocorF50.py {device} BacklightOn",
        "GetBacklight": f"/usr/local/bin/python /Local/scripts/serial/AvocorF50.py {device} GetBacklight",
        "GetSignal": f"/usr/local/bin/python /Local/scripts/serial/AvocorF50.py {device} GetSignal",
        "GetFirmware": f"/usr/local/bin/python /Local/scripts/serial/AvocorF50.py {device} GetFirmware",
    }
    
    for key, value in defaults_config.items():
        subprocess.run([
            "defaults", "write", "com.t1visions.SerialScripts",
            "Display 1", "-dict-add", key, value
        ], check=True)
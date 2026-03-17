"""Integral crontab entry generator"""


def generate_crontab_entries(serial: str) -> dict:
    """
    Generate crontab entries for Integral display monitoring.
    
    Args:
        serial: The USB serial number for the Integral device
        
    Returns:
        dict: Dictionary of crontab entry types and their commands
    """
    entries = {
        "standard_mirror": {
            "description": "Standard Mirror EDID - Verifies i/o resolutions of Integral",
            "command": f"@reboot /bin/sleep 95; python /Local/scripts/integralStatus.py --serial /dev/tty.usbserial-{serial} --rx0 \"4K60 444\" --tx0 \"4K60 444\" --input \"bot\" --fix --notify --reboot"
        },
        "dock": {
            "description": "Dock - Verifies i/o resolutions of Dock Integral",
            "command": f"@reboot /bin/sleep 95; python /Local/scripts/integralStatus.py --serial /dev/tty.usbserial-{serial} --rx0 \"1080P60 444\" --input \"bot\" --fix --notify --reboot"
        },
        "matrix_mode": {
            "description": "Matrix Mode - Verifies i/o resolutions of Dual Integral",
            "command": f"@reboot /bin/sleep 95; python /Local/scripts/integralStatus.py --serial /dev/tty.usbserial-{serial} --rx0 \"4K60 444\" --rx1 \"4K60 444\" --input \"thru\" --notify --reboot"
        }
    }
    return entries


def print_crontab_entries(serial: str = "xxx"):
    """
    Print formatted crontab entries for copy/paste.
    
    Args:
        serial: The USB serial number (defaults to 'xxx' as placeholder)
    """
    entries = generate_crontab_entries(serial)
    
    print("Standard Mirror EDID")
    print(" ")
    print(f"# {entries['standard_mirror']['description']}")
    print(entries['standard_mirror']['command'])
    print(" ")
    print(" ")
    
    print("Dock")
    print(" ")
    print(f"# {entries['dock']['description']}")
    print(entries['dock']['command'])
    print(" ")
    print(" ")
    
    print("Matrix Mode")
    print(" ")
    print(f"# {entries['matrix_mode']['description']}")
    print(entries['matrix_mode']['command'])


if __name__ == "__main__":
    # When run as a script, print with default serial
    print_crontab_entries()
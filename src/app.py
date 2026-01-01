from menu import Menu
import sys
import subprocess
import os
import re
import json
from ascii_art import ASCII_ART
from models import DisplayConfig, DisplaySerialConfig, DockConfig, IntegralConfig, VCConfig

SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../scripts"))
LOCAL_SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "/Local/scripts"))
LOCAL_SERIAL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "/Local/scripts/serial"))

class AppState:
    def __init__(self):
        self.display_config = DisplayConfig()
        self.display_serial_config = DisplaySerialConfig()
        self.dock_config = DockConfig()
        self.integral_config = IntegralConfig()
        self.vc_config = VCConfig()
        # ...other state...

# class AppState:
#     def __init__(self):
#         self.screen_count = None
#         self.screen_size = None
#         self.screen_placement = None
#         self.screen_height = None
#         self.dock_names = None
#         self.integrals = {}
#         self.display_serial = None

#     @property
#     def screen_count(self):
#         return self._screen_count
    
#     @screen_count.setter
#     def screen_count(self, count: int):
#         if count is not None and count <= 0:
#             raise ValueError("Screen count must be positive")
#         self._screen_count = count

#     @property
#     def screen_size(self):
#         return self._screen_size
    
#     @screen_size.setter
#     def screen_size(self, size: str):
#         if size is not None and size.strip() == "":
#             raise ValueError("Screen size cannot be empty")
#         self._screen_size = size
    
#     @property
#     def screen_placement(self):
#         return self._screen_placement
    
#     @screen_placement.setter
#     def screen_placement(self, placement: int):
#         if placement is not None and placement < 0:
#             raise ValueError("Screen placement must be non-negative")
#         self._screen_placement = placement

#     @property
#     def screen_height(self):
#         return self._screen_height

#     @screen_height.setter
#     def screen_height(self, height: int):
#         if height is not None and height < 0:
#             raise ValueError("Screen height must be non-negative")
#         self._screen_height = height

#     @property
#     def dock_names(self):
#         return self._dock_names
    
#     @dock_names.setter
#     def dock_names(self, names: str):
#         if names is not None and names.strip() == "":
#             raise ValueError("No Dock names set")
#         self._dock_names = names

#     @property
#     def integrals(self):
#         return self._integrals

#     @integrals.setter
#     def integrals(self, value):
#         if not isinstance(value, dict):
#             raise ValueError("Integrals must be a dictionary")
#         self._integrals = value

#     @property
#     def display_serial(self):
#         return self._display_serial
    
#     @display_serial.setter
#     def display_serial(self, id: str):
#         if id is not None and id.strip() == "":
#             raise ValueError("No display serial ID set")
#         self._display_serial = id


class MenuStack:
    def __init__(self):
        self.stack = []

    def push(self, menu):
        self.stack.append(menu)
        menu.run()

    def back(self):
        if len(self.stack) > 1:
            self.stack.pop()
            self.stack[-1].run()


def exit_app():
    sys.exit(0)

def build_app():
    state = AppState()
    nav = MenuStack()

    def write_state():
        with open("app_state.json", "w") as f:
            json.dump(state.__dict__, f)

    def load_last_configs():
        try:
            with open("app_state.json", "r") as f:
                data = json.load(f)
                state.__dict__.update(data)
                print("Last configurations loaded.")
        except FileNotFoundError:
            print("No saved configurations found.")
        except json.JSONDecodeError:
            print("Error decoding saved configurations.")

    def calculate_frame():
        try:
            res = state.screen_size
            count = state.screen_count
            if res is None or count is None:
                print("Screen size or count not set.")
                return
            width, height = map(int, res.split('x'))
            total_width = width * count
            state.screen_height = height
            state.screen_placement = total_width
            # Should probably move this to its own function.
            subprocess.run([os.path.join(SCRIPTS_DIR, "set_frame.sh"), str(state.screen_placement)])
            print(f"Calculated frame size: {total_width}x{height}")
        except Exception as e:
            print(f"Error calculating frame: {e}")

    def set_custom_res():
        try:
            res = input("Enter custom resolution (e.g., 2560x1440): ")
            state.screen_size = res
        except ValueError as e:
            print(f"Invalid input: {e}")

    def display_title():
        return (
            f"Display Configuration\n"
            f"Screen Count: {state.screen_count}\n"
            f"Screen Size: {state.screen_size}"
        )

    def set_screen_count():
        try:
            count = int(input("Enter number of displays: "))
            state.screen_count = count
        except ValueError as e:
            print(f"Invalid input: {e}")

    def set_screen_size(option):
        state.screen_size = option
        print(f"Screen size set to {option}")
        nav.back()

    def set_dock_names():
        try:
            names = input("Enter dock names: ")
            state.dock_names = names
            print("Dock names set.")
        except ValueError as e:
            print(f"Invalid input: {e}")

    def initialize_dock():
        if state.screen_placement is None or state.dock_names is None:
            print("Screen placement and/or dock names not set.")
            return
        subprocess.run([os.path.join(SCRIPTS_DIR, "initialize_dock.sh"), str(state.screen_placement), state.dock_names])

    def select_integral():
        if not state.integrals:
            print("Error: No Integral serial ID set. Run '1) Find Integral Serial #' first.")
            return None
        elif len(state.integrals) == 1:
            key = next(iter(state.integrals))
            print(f"Only one Integral found: Serial ID: {state.integrals[key]['serial']}")
            return key
        else:
            print("Multiple Integrals detected. Please select which one to reboot:")
            for key, integral in state.integrals.items():
                print(f"{key}) Serial: {integral['serial']}, Firmware: {integral['firmware']}")
            choice = input("Enter the number of the Integral: ")
            if choice in state.integrals:
                return choice
            else:
                print("Invalid selection.")

    def set_4k_mirror():
        selected_key = select_integral()
        if selected_key:
            serial = state.integrals[selected_key]['serial']
            print(f"Setting 4K mirror for Serial ID: {serial}")
            subprocess.run([os.path.join(SCRIPTS_DIR, "set_4k_mirror.sh"), serial])

    def reboot_integral():
        selected_key = select_integral()
        if selected_key:
            serial = state.integrals[selected_key]['serial']
            print(f"Rebooting Integral with Serial ID: {serial}")
            script_path = os.path.join(LOCAL_SERIAL_DIR, "integralSerial.py")
            result = subprocess.run(
                [sys.executable, script_path, f"/dev/tty.usbserial-{serial}", "reboot"],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                print("Reboot command sent successfully.")
            else:
                print(f"Error: Reboot command failed with return code {result.returncode}")
                print("Error Output:")
                print(result.stderr)
                
    def interrogate_integral():
        selected_key = select_integral()
        if selected_key:
            serial = state.integrals[selected_key]['serial']
            print(f"Interrogating Integral with Serial ID: {serial}")
            script_path = os.path.join(SCRIPTS_DIR, "integralStatus.py")
            result = subprocess.run(
                [sys.executable, script_path, "--serial", f"/dev/tty.usbserial-{serial}", "--interrogate"],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                print("Interrogate Output:")
                print(result.stdout)
            else:
                print(f"Error: Interrogate failed with return code {result.returncode}")
                print("Error Output:")
                print(result.stderr)
            return

    def get_integral_serial_id():
        result = subprocess.run(['ls /dev/tty.usb*'], shell=True, capture_output=True, text=True)
        output = result.stdout

        # Find all matches
        matches = re.findall(r'/dev/tty\.usbserial-([A-Za-z0-9]+)', output)
        print("Serial Matches: ",matches)

        integrals = {}
        for idx, serial in enumerate(matches, 1):
            script_path = os.path.join(SCRIPTS_DIR, "integralSerial.py")
            serial_result = subprocess.run(
                [sys.executable, script_path, f"/dev/tty.usbserial-{serial}", "getVersion"],
                capture_output=True, text=True)
            # read output of getVersion command and search for "HdFury"
            get_version_output = serial_result.stdout
            if "HdFury" in get_version_output:
                version_match = re.search(r"ver FW: ([\d.]+)", get_version_output)
                firmware = version_match.group(1) if version_match else None
                integrals[str(idx)] = {"serial": serial, "firmware": firmware}
                print(f"Integral {idx}: serial={serial}, firmware={firmware}")
            else:
                print(f"No Integral found for serial: {serial}")
        
        state.integrals = integrals
        if not integrals:
            print("No serial USB found.")

    def get_display_serial_id(choice):
        result = subprocess.run(['ls /dev/tty.usb*'], shell=True, capture_output=True, text=True)
        output = result.stdout
        matches = re.findall(r'/dev/tty\.usbserial-([A-Za-z0-9]+)', output)
        if not matches:
            print(f"No matching serial found for {choice}")
            return

        for serial in matches:
            script_path = os.path.join(LOCAL_SERIAL_DIR, f"{choice}.py")
            serial_result = subprocess.run(
                [sys.executable, script_path, f"/dev/tty.usbserial-{serial}", "GetPower"],
                capture_output=True, text=True
            )
            get_power_output = serial_result.stdout
            if "Display is ON" in get_power_output:
                state.display_serial = serial
                print(f"Display Serial ID set to: {serial}")
            else:
                print(f"No display found for serial: {serial}")

    def run_betterdisplays_sh():
        print("\nIf you want to add a license for BetterDisplays,\n"
            "please copy the command from library page and run\n"
            "it in terminal.\n\n" \
            "https://sites.google.com/a/t1v.com/process-docs/technical-knowledge-database/virtual-fitheadless-better-display-setup\n")
        input("Press [Return] when ready to continue...\n")
        subprocess.run([os.path.join(SCRIPTS_DIR, "tester.sh")])

    def run_software_vc_sh(choice):
        if state.screen_placement and state.screen_height is None:
            print("Error: Screen placement not set.\n" \
            "Please set screen in Display menu first.")
            return
        screen_placement = str(state.screen_placement)
        screen_height = str(state.screen_height)

        subprocess.run([os.path.join(SCRIPTS_DIR, "software_vc.sh"), choice, screen_placement, screen_height])


    # Initialize menus and sub-menus
    main_menu = Menu("Main Menu", {}, startup_art=ASCII_ART)
    display_config_menu = Menu("Display Configuration", {})
    resolution_menu = Menu("Resolution Menu", {})
    displays_menu = Menu("Displays Menu", {})
    display_serial_menu = Menu("Display Serial Commands", {})
    find_display_serial_menu = Menu("Select Display", {})
    integral_menu = Menu("Integral Menu", {})
    touch_menu = Menu("Touch Menu", {})
    uppd_menu = Menu("UPPD Menu", {})
    hid_menu = Menu("HID Menu", {})
    software_vc_menu = Menu("Software VC Menu", {})
    dock_menu = Menu("Dock Menu", {})

    # Define menu commands in dictionaries
    dock_menu.commands.update({
        "1": ("Set Names Array", lambda: set_dock_names()),
        "2": ("Initialize Dock", lambda: initialize_dock()),
        "t": ("Toggle TTMenu", lambda: subprocess.run([os.path.join(SCRIPTS_DIR, "toggle_ttmenu.sh")])),
        "b": ("Back", nav.back),
        "qq": ("Quit", exit_app),
    })

    software_vc_menu.commands.update({
        "1": ("Set up BetterDisplays", lambda: run_betterdisplays_sh()),
        "2": ("Enable Zoom", lambda: run_software_vc_sh("zoom")),
        "3": ("Enable Teams", lambda: run_software_vc_sh("teams")),
        "4": ("Enable both", lambda: run_software_vc_sh("both")),
        "t": ("Toggle TTMenu", lambda: subprocess.run([os.path.join(SCRIPTS_DIR, "toggle_ttmenu.sh")])),
        "b": ("Back", nav.back),
        "qq": ("Quit", exit_app),
    })

    uppd_menu.commands.update({
        "1": ("Set Defaults", lambda: subprocess.run([os.path.join(SCRIPTS_DIR, "tester.sh")])),
        "2": ("Avocor E Defaults", print("Setting Avocor E defaults...")),
        "3": ("Avocor F Defaults", print("Setting Avocor F defaults...")),
        "t": ("Toggle TTMenu", lambda: subprocess.run([os.path.join(SCRIPTS_DIR, "toggle_ttmenu.sh")])),
        "b": ("Back", nav.back),
        "qq": ("Quit", exit_app),
    })

    hid_menu.commands.update({
        "1": ("Set Defaults", lambda: subprocess.run([os.path.join(SCRIPTS_DIR, "tester.sh")])),
        "t": ("Toggle TTMenu", lambda: subprocess.run([os.path.join(SCRIPTS_DIR, "toggle_ttmenu.sh")])),
        "b": ("Back", nav.back),
        "qq": ("Quit", exit_app),
    })

    touch_menu.commands.update({
        "1": ("UPPD", lambda: nav.push(uppd_menu)),
        "2": ("HID", lambda: nav.push(hid_menu)),
        "t": ("Toggle TTMenu", lambda: subprocess.run([os.path.join(SCRIPTS_DIR, "toggle_ttmenu.sh")])),
        "b": ("Back", nav.back),
        "qq": ("Quit", exit_app),
    })

    integral_menu.commands.update({
        "1": ("Find Integral Serial #", lambda: get_integral_serial_id()),
        "2": ("Interrogate Integral", lambda: interrogate_integral()),
        "3": ("Reboot Integral", lambda: reboot_integral()),
        "4": ("Set 4K Mirror", lambda: set_4k_mirror()),
        "5": ("Example crontabs", lambda: subprocess.run([
            os.path.join(SCRIPTS_DIR, "integral_crontabs.sh"),
            state.integrals[next(iter(state.integrals))]['serial'] if state.integrals else 'XXXXXXXX'
        ])),
        "b": ("Back", nav.back),
        "ss": ("Save Configurations", write_state),
        "qq": ("Quit", exit_app),
    })

    display_serial_menu.commands.update({
        "1": ("Find USB Serial #", lambda: nav.push(find_display_serial_menu)),
        "2": ("Set Defaults", lambda: subprocess.run([os.path.join(SCRIPTS_DIR, "tester.sh")])),
        "3": ("Test Power On", lambda: subprocess.run([os.path.join(SCRIPTS_DIR, "tester.sh")])),
        "b": ("Back", nav.back),
        "qq": ("Quit", exit_app),
    })

    find_display_serial_menu.commands.update({
        "1": ("Avocor E50", lambda: get_display_serial_id("AvocorE50")),
        "2": ("Avocor F50", lambda: get_display_serial_id("AvocorF50")),
        "3": ("AvocorG60", lambda: get_display_serial_id("AvocorG60")),
        "4": ("AvocorH20", lambda: get_display_serial_id("AvocorH20")),
        "b": ("Back", nav.back),
        "qq": ("Quit", exit_app),
    })

    resolution_menu.commands.update({
        "1": ("Set resolution to 3840x2160", lambda: set_screen_size("3840x2160")),
        "2": ("Set resolution to 5120x2880", lambda: set_screen_size("5120x2880")),
        "3": ("Set resolution to 1920x1080", lambda: set_screen_size("1920x1080")),
        "4": ("Set custom resolution", set_custom_res),
        "t": ("Toggle TTMenu", lambda: subprocess.run([os.path.join(SCRIPTS_DIR, "toggle_ttmenu.sh")])),
        "b": ("Back", nav.back),
        "qq": ("Quit", exit_app),
    })

    display_config_menu.commands.update({
        "1": ("Set screen count", set_screen_count),
        "2": ("Set screen size", lambda: nav.push(resolution_menu)),
        "3": ("Show current", lambda: print(f"Screen Count: {state.screen_count}, Screen Size: {state.screen_size}")),
        "4": ("Set frame", lambda: calculate_frame()),
        "t": ("Toggle TTMenu", lambda: subprocess.run([os.path.join(SCRIPTS_DIR, "toggle_ttmenu.sh")])),
        "b": ("Back", nav.back),
        "qq": ("Quit", exit_app),
    })

    displays_menu.commands.update({
        "1": ("Displays Configuration", lambda: nav.push(display_config_menu)),
        "2": ("Serial Commands Menu", lambda: nav.push(display_serial_menu)),
        "t": ("Toggle TTMenu", lambda: subprocess.run([os.path.join(SCRIPTS_DIR, "toggle_ttmenu.sh")])),
        "b": ("Back", nav.back),
        "qq": ("Quit", exit_app),
    })

    main_menu.commands.update({
        "1": ("Displays Menu", lambda: nav.push(displays_menu)),
        "2": ("Integral Menu", lambda: nav.push(integral_menu)),
        "3": ("Touch Menu", lambda: nav.push(touch_menu)),
        "4": ("Software VC Menu", lambda: nav.push(software_vc_menu)),
        "5": ("Dock Menu", lambda: nav.push(dock_menu)),
        "6": ("Other Defaults", lambda: nav.push(other_defaults_menu)),
        "t": ("Toggle TTMenu", lambda: subprocess.run([os.path.join(SCRIPTS_DIR, "toggle_ttmenu.sh")])),
        "ss": ("Save Configurations", write_state),
        "b4": ("Load Last Configs", load_last_configs),
        "qq": ("Quit", exit_app),
    })

    
    return nav, main_menu

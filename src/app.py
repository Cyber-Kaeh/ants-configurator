from menu import Menu
import sys
import subprocess
import os
import re
import json
from ascii_art import ASCII_ART

SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../scripts"))
LOCAL_SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "/Local/scripts"))

class AppState:
    def __init__(self):
        self.screen_count = None
        self.screen_size = None
        self.screen_placement = None
        self.dock_names = None
        self.integral_serial = None
        self.display_serial = None

    @property
    def screen_count(self):
        return self._screen_count
    
    @screen_count.setter
    def screen_count(self, count: int):
        if count is not None and count <= 0:
            raise ValueError("Screen count must be positive")
        self._screen_count = count

    @property
    def screen_size(self):
        return self._screen_size
    
    @screen_size.setter
    def screen_size(self, size: str):
        if size is not None and size.strip() == "":
            raise ValueError("Screen size cannot be empty")
        self._screen_size = size
    
    @property
    def screen_placement(self):
        return self._screen_placement
    
    @screen_placement.setter
    def screen_placement(self, placement: int):
        if placement is not None and placement < 0:
            raise ValueError("Screen placement must be non-negative")
        self._screen_placement = placement

    @property
    def dock_names(self):
        return self._dock_names
    
    @dock_names.setter
    def dock_names(self, names: str):
        if names is not None and names.strip() == "":
            raise ValueError("No Dock names set")
        self._dock_names = names

    @property
    def integral_serial(self):
        return self._integral_serial
    
    @integral_serial.setter
    def integral_serial(self, id: str):
        if id is not None and id.strip() == "":
            raise ValueError("No integral serial ID set")
        self._integral_serial = id

    @property
    def display_serial(self):
        return self._display_serial
    
    @display_serial.setter
    def display_serial(self, id: str):
        if id is not None and id.strip() == "":
            raise ValueError("No display serial ID set")
        self._display_serial = id


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

    def calculate_frame():
        try:
            res = state.screen_size
            count = state.screen_count
            if res is None or count is None:
                print("Screen size or count not set.")
                return
            width, height = map(int, res.split('x'))
            total_width = width * count
            state.screen_placement = total_width
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

    def interrogate_integral():
        if state.integral_serial is None:
            print("Error: Integral serial ID not set. Run '1) Find Integral Serial #' first.")
            return

        try:
            script_path = os.path.join(LOCAL_SCRIPTS_DIR, "integralStatus.py")
            print(f"serial ID: {state.integral_serial}")
            result = subprocess.run(
                [sys.executable, script_path, "--serial", f"/dev/tty.usbserial-{state.integral_serial}", "--interrogate"],
                capture_output=True, text=True
            )
            print(f'result: {result}')
            if result.returncode == 0:
                print("Interrogate Output:")
                print(result.stdout)
            else:
                print(f"Error: Interrogation failed with return code {result.returncode}")
                print("Error Output:")
                print(result.stderr)
        except FileNotFoundError:
            print(f"Error: Script not found at {script_path}. Please check the path.")
        except Exception as e:
            print(f"Error during interrogation: {e}")

    def get_integral_serial_id():
        result = subprocess.run(['ls /dev/tty.usb*'], shell=True, capture_output=True, text=True)
        output = result.stdout

        # Find all matches
        matches = re.findall(r'/dev/tty\.usbserial-([A-Za-z0-9]+)', output)
        print("Matches: ",matches)

        # if more than one match, try to reboot integral on each
        if len(matches) > 1:
            for serial in matches:
                print(f"Rebooting Integral with serial: {serial}")
                serial_result = subprocess.run(
                    [sys.executable, f"/Local/scripts/serial/integralSerial.py", f"/dev/tty.usbserial-{serial}", "reboot"],
                    capture_output=True, text=True)
                # read output of reboot command and search for "reboot on"
                reboot_output = serial_result.stdout
                if "reboot on" in reboot_output:
                    print(f"Reboot successful for serial: {serial}")
                    state.integral_serial = serial
                    break
                else:
                    print(f"Reboot failed for serial: {serial}")
        elif len(matches) == 1:
            serial = matches[0]
            # save serial to state
            state.integral_serial = serial
        elif len(matches) > 2:
            print("More than 2 USB serials found. Manual configuration needed.")
        else:
            print("No serial USB found.")
            

    # Initialize menus and sub-menus
    main_menu = Menu("Main Menu", {}, startup_art=ASCII_ART)
    display_config_menu = Menu("Display Configuration", {})
    resolution_menu = Menu("Resolution Menu", {})
    displays_menu = Menu("Displays Menu", {})
    display_serial_menu = Menu("Display Serial Commands", {})
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
        "1": ("Enable Zoom", lambda: print("Zoom enabled.")),
        "2": ("Enable Teams", lambda: print("Teams enabled.")),
        "3": ("Enable both", lambda: print("Zoom and Teams enabled.")),
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
        "2": ("Set crontab", lambda: subprocess.run([os.path.join(SCRIPTS_DIR, "tester.sh")])),
        "3": ("Interrogate Integral", lambda: interrogate_integral()),
        "4": ("Reboot Integral", lambda: reboot_integral),
        "5": ("Set 4K Mirror", lambda: set_4k_mirror),
        "b": ("Back", nav.back),
        "qq": ("Quit", exit_app),
        "11": ("Test reading output", lambda: test_reading_output())
    })

    display_serial_menu.commands.update({
        "1": ("Find USB Serial #", lambda: subprocess.run([os.path.join(SCRIPTS_DIR, "tester.sh")])),
        "2": ("Set Defaults", lambda: subprocess.run([os.path.join(SCRIPTS_DIR, "tester.sh")])),
        "3": ("Test Power On", lambda: subprocess.run([os.path.join(SCRIPTS_DIR, "tester.sh")])),
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
        "t": ("Toggle TTMenu", lambda: subprocess.run([os.path.join(SCRIPTS_DIR, "toggle_ttmenu.sh")])),
        "b": ("Back", nav.back),
        "qq": ("Quit", exit_app),
    })

    displays_menu.commands.update({
        # "1": ("Set frame", lambda: subprocess.run([os.path.join(SCRIPTS_DIR, "tester.sh")])),
        "1": ("Set frame", lambda: calculate_frame()),
        "2": ("Serial Commands Menu", lambda: nav.push(display_serial_menu)),
        "t": ("Toggle TTMenu", lambda: subprocess.run([os.path.join(SCRIPTS_DIR, "toggle_ttmenu.sh")])),
        "b": ("Back", nav.back),
        "qq": ("Quit", exit_app),
    })

    main_menu.commands.update({
        "1": ("Display Configuration", lambda: nav.push(display_config_menu)),
        "2": ("Displays Menu", lambda: nav.push(displays_menu)),
        "3": ("Integral Menu", lambda: nav.push(integral_menu)),
        "4": ("Touch Menu", lambda: nav.push(touch_menu)),
        "5": ("Software VC Menu", lambda: nav.push(software_vc_menu)),
        "6": ("Dock Menu", lambda: nav.push(dock_menu)),
        "7": ("Other Defaults", lambda: nav.push(other_defaults_menu)),
        "t": ("Toggle TTMenu", lambda: subprocess.run([os.path.join(SCRIPTS_DIR, "toggle_ttmenu.sh")])),
        "ss": ("Save Configurations", write_state),
        "qq": ("Quit", exit_app),
    })

    
    return nav, main_menu

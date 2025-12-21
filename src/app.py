from menu import Menu
import sys
import subprocess
import os
from ascii_art import ASCII_ART

SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../scripts"))

class AppState:
    def __init__(self):
        self.screen_count = None
        self.screen_size = None
        self.screen_placement = None
        self.dock_names = None

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


    # Initialize menus and sub-menus
    main_menu = Menu("Main Menu", {}, startup_art=ASCII_ART)
    display_config_menu = Menu("Display Configuration", {})
    resolution_menu = Menu("Resolution Menu", {})
    displays_menu = Menu("Displays Menu", {})
    touch_menu = Menu("Touch Menu", {})
    software_vc_menu = Menu("Software VC Menu", {})
    dock_menu = Menu("Dock Menu", {})

    # Define menu commands in dictionaries
    dock_menu.commands.update({
        "1": ("Set Names Array", lambda: set_dock_names()),
        "2": ("Initialize Dock", lambda: initialize_dock()),
        "b": ("Back", nav.back),
        "qq": ("Quit", exit_app),
    })

    software_vc_menu.commands.update({
        "1": ("Enable Zoom", lambda: print("Zoom enabled.")),
        "2": ("Enable Teams", lambda: print("Teams enabled.")),
        "3": ("Enable both", lambda: print("Zoom and Teams enabled.")),
        "b": ("Back", nav.back),
        "qq": ("Quit", exit_app),
    })

    touch_menu.commands.update({
        "1": ("UPPD", lambda: nav.push(uppd_menu)),
        "2": ("HID", lambda: nav.push(hid_menu)),
        "b": ("Back", nav.back),
        "qq": ("Quit", exit_app),
    })

    resolution_menu.commands.update({
        "1": ("Set resolution to 3840x2160", lambda: set_screen_size("3840x2160")),
        "2": ("Set resolution to 5120x2880", lambda: set_screen_size("5120x2880")),
        "3": ("Set resolution to 1920x1080", lambda: set_screen_size("1920x1080")),
        "4": ("Set custom resolution", set_custom_res),
        "b": ("Back", nav.back),
        "qq": ("Quit", exit_app),
    })

    display_config_menu.commands.update({
        "1": ("Set screen count", set_screen_count),
        "2": ("Set screen size", lambda: nav.push(resolution_menu)),
        "3": ("Show current", lambda: print(f"Screen Count: {state.screen_count}, Screen Size: {state.screen_size}")),
        "b": ("Back", nav.back),
        "qq": ("Quit", exit_app),
    })

    displays_menu.commands.update({
        # "1": ("Set frame", lambda: subprocess.run([os.path.join(SCRIPTS_DIR, "tester.sh")])),
        "1": ("Set frame", lambda: calculate_frame()),
        "b": ("Back", nav.back),
        "qq": ("Quit", exit_app),
    })

    main_menu.commands.update({
        "1": ("Display Configuration", lambda: nav.push(display_config_menu)),
        "2": ("Displays Menu", lambda: nav.push(displays_menu)),
        "3": ("Touch Menu", lambda: nav.push(touch_menu)),
        "4": ("Software VC Menu", lambda: nav.push(software_vc_menu)),
        "5": ("Dock Menu", lambda: nav.push(dock_menu)),
        "qq": ("Quit", exit_app),
    })

    
    return nav, main_menu

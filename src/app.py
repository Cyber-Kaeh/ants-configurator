from menu import Menu
import sys
import subprocess
import os

SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../scripts"))

class AppState:
    def __init__(self):
        self.screen_count = None
        self.screen_size = None

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

    main_menu = Menu("Main Menu", {})
    display_config_menu = Menu("Display Configuration", {})
    resolution_menu = Menu("Resolution Menu", {})
    displays_menu = Menu("Displays Menu", {})
    touch_menu = Menu("Touch Menu", {})
    software_vc_menu = Menu("Software VC Menu", {})

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
        "1": ("Set frame", lambda: subprocess.run([os.path.join(SCRIPTS_DIR, "tester.sh")])),
        "b": ("Back", nav.back),
        "qq": ("Quit", exit_app),
    })

    main_menu.commands.update({
        "1": ("Display Configuration", lambda: nav.push(display_config_menu)),
        "2": ("Displays Menu", lambda: nav.push(displays_menu)),
        "3": ("Touch Menu", lambda: nav.push(touch_menu)),
        "4": ("Software VC Menu", lambda: nav.push(software_vc_menu)),
        "5": ("Initialize Dock", lambda: print("Dock initialized.")),
        "qq": ("Quit", exit_app),
    })

    
    return nav, main_menu

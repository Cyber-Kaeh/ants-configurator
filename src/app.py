from menu import Menu
import sys
import subprocess
import os
import re
from ascii_art import ASCII_ART
from models import DisplayConfig, DockConfig, IntegralConfig, VCConfig
from actions import SaveStateAction, LoadStateAction, DeleteConfigAction, ToggleTTMenuAction, WriteDefaultsAction, RunIntegralSerialAction, RunScriptAction, RunCommandAction, AddCrontabEntryAction, ClearConfigAction

SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../scripts"))
LOCAL_SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "/Local/scripts"))
LOCAL_SERIAL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "/Local/scripts/serial"))
T1VAPPS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "/Users/t1user/T1VApps"))

class AppState:
    def __init__(self):
        self.display_config = DisplayConfig()
        self.dock_config = DockConfig()
        self.integral_config = IntegralConfig()
        self.vc_config = VCConfig()


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

    def home(self):
        if not self.stack:
            return
        while len(self.stack) > 1:
            self.stack.pop()
        self.stack[0].run()


def exit_app():
    sys.exit(0)

def build_app():
    state = AppState()
    nav = MenuStack()
    try:
        LoadStateAction(state).execute()
    except Exception as e:
        print(f"Error loading state: {e}")

    def calculate_frame():
        try:
            res = state.display_config.size
            count = state.display_config.count
            if res is None or count is None:
                print("Screen size or count not set.")
                return
            width, height = map(int, res.split('x'))
            total_width = width * count
            state.display_config.height = height
            state.display_config.placement = total_width
            SaveStateAction(state).execute()
            print(f"Calculated frame size: {total_width}x{height}")
        except Exception as e:
            print(f"Error calculating frame: {e}")

    def set_frame():
        calculate_frame()
        if state.display_config.placement:
            frame_string = f"{{{{0, 0}}, {{{state.display_config.placement}, {state.display_config.height}}}}}"
            WriteDefaultsAction("TTMenu", "frame", frame_string, value_type="-string").execute()
            WriteDefaultsAction("MultiTouchCalibrate", "frame", frame_string, value_type="-string").execute()
            SaveStateAction(state).execute()

    def set_custom_res():
        try:
            res = input("Enter custom resolution (e.g., 3840x2160): ")
            state.display_config.size = res
            SaveStateAction(state).execute()
        except ValueError as e:
            print(f"Invalid input: {e}")

    def set_screen_count():
        try:
            count = int(input("Enter number of displays: "))
            state.display_config.count = count
            SaveStateAction(state).execute()
        except ValueError as e:
            print(f"Invalid input: {e}")
        
        if state.display_config.count > 1:
            WriteDefaultsAction("TTMenu", "thinkHubMediumLineDrawWidth", "10").execute()
            WriteDefaultsAction("TTMenu", "thinkHubThickLineDrawWidth", "20").execute()
            state.vc_config.multi_display = True

    def set_screen_size(option):
        state.display_config.size = option
        SaveStateAction(state).execute()
        print(f"Screen size set to {option}")
        nav.back()

    def set_frameScaling(option, include_pan_gesture=False):
        if include_pan_gesture:
            WriteDefaultsAction("TTMenu", "panGestureFactor", "2").execute()
            
        WriteDefaultsAction("TTMenu", "frameScaling", option).execute()
        nav.back()

    def set_touch_display_resolution(option):
        if option == "custom":
            try:
                value = input("Enter custom touchDisplayResolution value: ")
                WriteDefaultsAction("TTMenu", "touchDisplayResolution", value).execute()
                print(f"touchDisplayResolution set to {value}")
            except ValueError as e:
                print(f"Invalid input: {e}")
        else:
            WriteDefaultsAction("TTMenu", "touchDisplayResolution", option).execute()
            print(f"touchDisplayResolution set to {option}")
        nav.back()

    def set_uppd_defaults():
        WriteDefaultsAction("TTMenu", "MTManagerSearchPriority", "UPDD").execute()
        WriteDefaultsAction("TTMenu", "thinkHubEnableRemoteKeyboardAction", "1").execute()
        command = ["/usr/local/bin/upddutils", "nodevice", "set", "minimum_notify_level", "2"]
        RunCommandAction(command, success_message="UPDD minimum notify level set.").execute()
        command = ["/usr/local/bin/upddprocesses", "stop", "-c"]
        RunCommandAction(command, success_message="UPDD processes stopped.").execute()
        crontab_label = "# Disable UPDD Commander so that touch events pass straight to TTMenu"
        crontab_entry = "@reboot /bin/sleep 80; /usr/local/bin/upddprocesses stop -c"
        AddCrontabEntryAction(crontab_label).execute()
        AddCrontabEntryAction(crontab_entry).execute()

    def get_confirmed_input(prompt, common_list):
        while True:
            val = input(prompt)
            if val.lower() == 'done' or val in common_list:
                return val
            
            confirm = input(f"Warning: '{val}' is not a common name. Continue anyway? (y/N): ")
            if confirm.lower() in ['y', 'yes']:
                return val
            print("Entry cancelled. Try again.")

    def configure_docks():
        common_names = ["Dock1", "Dock2", "Dock3", "Dock4", "Dock", "MTR"]
        common_res = ["1280x720","1920x1080", "3840x2160"]
        while True:
            dock_name = get_confirmed_input(
                "Enter dock name (or 'done' if finished): ", common_names)
            
            if dock_name.lower() == 'done':
                break

            while True:
                res = input("Enter resolution (e.g., 1920x1080): ")
                if res.lower() == 'done':
                    break
                if not re.match(r"^\d+x\d+$", res):
                    print(f"Invalid format: '{res}'. Use widthxheight (e.g., 1920x1080). Please try again.")
                    continue
                if not res in common_res:
                    confirm = input(f"Warning: {res} is not a common resolution. Continue anyway? (y/N): ")
                    if confirm.lower() not in ['y', 'yes']:
                        continue

                state.dock_config.add_dock(dock_name, res)
                print(f"Added {dock_name} with resolution: {res}")
                break

        SaveStateAction(state).execute()

    def initialize_dock():
        if state.display_config.placement is None or not state.dock_config.names:
            print("Screen placement and/or dock names not set.")
            return

        coordinates = []
        current_x = state.display_config.placement

        for i in range(state.dock_config.count):
            dock_width, dock_height = map(int, state.dock_config.size[i].split('x'))
            coord_string = f"'{{{{{current_x}, 0}}, {{{dock_width}, {dock_height}}}}}'"
            coordinates.append(coord_string)
            current_x += dock_width
        state.dock_config.total_width = current_x
        SaveStateAction(state).execute()

        WriteDefaultsAction("TTMenu", "thinkHubEnableDock", "1").execute()
        WriteDefaultsAction("TTMenu", "multiViewScreenLabels", state.dock_config.names, value_type="-array").execute()
        WriteDefaultsAction("TTMenu", "multiViewScreenCoordinates", coordinates, value_type="-array").execute()
        WriteDefaultsAction("TTMenu", "disableHideInfoPanelOnCast", "1").execute()
        WriteDefaultsAction("TTMenu", "disableHideInfoPanelOnHideTray", "1").execute()
        WriteDefaultsAction("TTMenu", "thinkHubDockShowCanvasOnUndock", "1").execute()


    def select_integral():
        if not state.integral_config.integrals:
            print("Error: No Integral serial ID set. Run '1) Find Integral Serial #' first.")
            return None
        elif len(state.integral_config.integrals) == 1:
            key = next(iter(state.integral_config.integrals))
            print(f"Only one Integral found: Serial ID: {state.integral_config.integrals[key]['serial']}")
            return key
        else:
            print("Multiple Integrals detected. Please select which one to reboot:")
            for key, integral in state.integral_config.integrals.items():
                print(f"{key}) Serial: {integral['serial']}, Firmware: {integral['firmware']}")
            choice = input("Enter the number of the Integral: ")
            if choice in state.integral_config.integrals:
                return choice
            else:
                print("Invalid selection.")

    def custom_integral_command():
        selected_key = select_integral()
        print("Enter commad to run, or [help] for list of commands")
        choice = input("> ")
        if selected_key:
            serial = state.integral_config.integrals[selected_key]['serial']
            if choice == "help":
                RunIntegralSerialAction(serial, "help").execute()
            else:
                RunIntegralSerialAction(serial, choice).execute()

    def set_4k_mirror():
        selected_key = select_integral()
        if selected_key:
            serial = state.integral_config.integrals[selected_key]['serial']
            print(f"Setting 4K mirror for Serial ID: {serial}")
            RunIntegralSerialAction(serial, "setScalingNone").execute()
            RunIntegralSerialAction(serial, "reboot").execute()

    def reboot_integral():
        selected_key = select_integral()
        if selected_key:
            serial = state.integral_config.integrals[selected_key]['serial']
            print(f"Rebooting Integral with Serial ID: {serial}")
            RunIntegralSerialAction(serial, "reboot").execute()
        else:
            print("No Integral selected.")

                
    def interrogate_integral():
        selected_key = select_integral()
        if selected_key:
            serial = state.integral_config.integrals[selected_key]['serial']
            print(f"Interrogating Integral with Serial ID: {serial}")
            print("Be patient... this can take a minute...")
            script_path = os.path.join(LOCAL_SCRIPTS_DIR, "integralStatus.py")
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
                SaveStateAction(state).execute()
            else:
                print(f"No Integral found for serial: {serial}")
        
        state.integral_config.integrals = integrals
        if not integrals:
            print("No serial USB found.")
        # Was getting double saves. trying to fix
        # SaveStateAction(state).execute()

    def set_display_serial_crontab():
        label_entry = "#Checks display(s) signal status"
        crontab_entry = "@reboot /bin/sleep 200; /usr/local/bin/python /Local/scripts/DisplayMegaScript.py --fix --notify --reboot"
        AddCrontabEntryAction(label_entry).execute()
        AddCrontabEntryAction(crontab_entry).execute()

    def set_display_serial_defaults(model):
        if not state.display_config.serial:
            print("No display serial found, run 1) Find USB Serial #.")
            return
        serial = state.display_config.serial
        state.display_config.model = model
        SaveStateAction(state).execute()
        RunScriptAction(SCRIPTS_DIR, f"{model}.sh", serial).execute()

        displays_list = ["AvocorH20", "AvocorF50", "AvocorG60"]
        if model in displays_list:
            print("Adding crontab for displayMegaScript.py")
            set_display_serial_crontab()
        nav.back()

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
                state.display_config.serial = serial
                print(f"Display Serial ID set to: {serial}")
                SaveStateAction(state).execute()
                nav.back()
            else:
                print(f"No display found for serial: {serial}")

    def run_betterdisplays_sh():
        print("\nIf you want to add a license for BetterDisplays,\n"
            "please copy the command from library page and run\n"
            "it in terminal.\n\n" \
            "https://sites.google.com/a/t1v.com/process-docs/technical-knowledge-database/virtual-fitheadless-better-display-setup\n")
        continue_resp = input("Type:\n"
                              "[Q]uit to stop and enter license\n"
                              "[B]ack to return to previous menu\n"
                              "Any other key to continue...\n> ")
        if continue_resp.lower() == "q" or continue_resp.lower() == "quit":
            exit_app()
        elif continue_resp.lower() == "b" or continue_resp.lower() == "back":
            return

        resp = input("Is TTMenu toggled down? (y/N): ")
        if resp.lower() in ["n", "no"]:
            ToggleTTMenuAction().execute()

        print("Beginning BetterDisplays setup, this may take a few moments...")
        placement = state.display_config.placement
        screens = state.display_config.count

        # Ensure placement and screens are strings for subprocess
        script_path = os.path.join(SCRIPTS_DIR, "better_displays.sh")
        result = subprocess.run(
            [script_path, str(placement), str(screens)],
            capture_output=True, text=True
        )

        if result.returncode == 0:
            print("BetterDisplays setup completed successfully.")
            print(result.stdout)
        else:
            print("Error during BetterDisplays setup:")
            print(result.stderr)

    def initialize_software_vc(choice):
        if state.display_config.placement is None or state.display_config.height is None:
            print("Error: Screen placement not set.\n" \
            "Please set screen in Display menu first.")
            return
        if not state.dock_config.enabled:
            resp = input("Docks should be set up before VC. Continue anyway? (y/N): ")
            if resp.lower() not in ["y", "yes"]:
                return
 
        display_width = state.display_config.placement
        height = state.display_config.height - 720
        dock_width = state.dock_config.total_width
        placement = display_width + dock_width
        multi_string = f"{{{{{placement}, {height}}}}}, {{{{1280, 720}}}}"

        if state.display_config.count == 1:
            WriteDefaultsAction("TTMenu", "screenUpdateOnAllChanges", "1").execute()
            WriteDefaultsAction("TTMenu", "desktopMoveAllWindows", "1").execute()
        else:
            WriteDefaultsAction("TTMenu", "desktopMoveAllWindows", "1").execute()
            WriteDefaultsAction("TTMenu", "thinkHubDesktopThinkHubScreenIndex", "0").execute()
            WriteDefaultsAction("TTMenu", "thinkHubDesktopScreenRect", multi_string, value_type="-string").execute()

        if choice == "zoom" or choice == "both":
            WriteDefaultsAction("TTMenu", "ThinkHubZoom", "1").execute()
        if choice == "teams" or choice == "both":
            WriteDefaultsAction("TTMenu", "ThinkHubTeams", "1").execute()
            WriteDefaultsAction("automate", "VCCaptureRect", f"{placement},0,1280,720", value_type="-string").execute()
        SaveStateAction(state).execute()

    def set_magewell_defaults():
        WriteDefaultsAction("TTMenu", "deviceSettings", "/Users/t1user/Documents/deviceSettings.plist").execute()
        WriteDefaultsAction("TTMenu", "captureSessionDefaultAudioVolume", "0.75").execute()
        WriteDefaultsAction("TTMenu", "thinkHubEnableTouchBack", "1").execute()

    def set_max_browsers(count):
        WriteDefaultsAction("TTMenu", "webViewMaxClients", count).execute()
        nav.back()

    def enable_api_server():
        RunCommandAction(["cp", "/Local/scripts/externalCommand/com.t1v.externalCommandTelnetServer3.plist", "/Users/t1user/Library/LaunchAgents/"]).execute()
        RunCommandAction(["launchctl", "load", "/Library/LaunchAgents/com.t1v.externalCommandTelnetServer3.plist"]).execute()

    def enable_multisite_smb():
        room = input("Enter customer name for Multisite Room: ")
        WriteDefaultsAction("TTMenu", "thinkHubMultiSite", "1").execute()
        WriteDefaultsAction("TTMenu", "thinkHubMultiSiteRoom", room).execute()

    def enable_multisite_enterprise():
        WriteDefaultsAction("TTMenu", "thinkHubMultiSite", "1").execute()
        resp = input("Do you want to set the IP for the Multisite Relay? (y/N): ")
        if resp.lower() in ["y", "yes"]:
            ip_address = input("Enter the IP address for the Multisite Relay: ")
            WriteDefaultsAction("TTMenu", "netMessengerHostName", ip_address).execute()
            WriteDefaultsAction("TTMenu", "janusAddress", f"ws://{ip_address}:8188").execute()

    # Initialize menus and sub-menus
    main_menu = Menu("Main Menu", {}, startup_art=ASCII_ART)
    display_config_menu = Menu("Display Configuration", {})
    resolution_menu = Menu("Resolution Menu", {})
    displays_menu = Menu("Displays Menu", {})
    touchDisplay_menu = Menu("Touch Display Resolution", {})
    frameScaling_menu = Menu("Frame Scaling Menu", {})
    display_serial_menu = Menu("Display Serial Commands", {})
    display_serial_defaults_menu = Menu("Display Serial Defaults", {})
    find_display_serial_menu = Menu("Select Display", {})
    integral_menu = Menu("Integral Menu", {})
    touch_menu = Menu("Touch Menu", {})
    uppd_menu = Menu("UPPD Menu", {})
    pq_menu = Menu("HID Menu", {})
    software_vc_menu = Menu("Software VC Menu", {})
    dock_menu = Menu("Dock Menu", {})
    other_defaults_menu = Menu("Other Misc. Defaults", {})
    max_browsers_menu = Menu("Max Browsers Menu", {})
    multisite_menu = Menu("Multisite Menu", {})
    clear_config_menu = Menu("Clear Configurations", {})

    # Define menu commands in dictionaries
    multisite_menu.commands.update({
        "1": ("Enable Multisite Enterprise", lambda: enable_multisite_enterprise()),
        "2": ("Enable Multisite SMB", lambda: enable_multisite_smb()),
        "b": ("Back", nav.back),
        "h": ("Home", nav.home),
        "qq": ("Quit", exit_app),
    })

    clear_config_menu.commands.update({
        "1": ("Clear Display Config", lambda: ClearConfigAction(state, "display").execute()),
        "2": ("Clear Dock Config", lambda: ClearConfigAction(state, "dock").execute()),
        "3": ("Clear Integral Config", lambda: ClearConfigAction(state, "integral").execute()),
        "4": ("Clear Software VC Config", lambda: ClearConfigAction(state, "vc").execute()),
        "b": ("Back", nav.back),
        "h": ("Home", nav.home),
    })

    max_browsers_menu.commands.update({
        "1": ("CollaboratOR Lite - 4", lambda: set_max_browsers("4")),
        "2": ("CX-02 - 5", lambda: set_max_browsers("5")),
        "3": ("CX-06/07 - 10", lambda: set_max_browsers("10")),
        "b": ("Back", nav.back),
        "h": ("Home", nav.home),
        "qq": ("Quit", exit_app),
    })

    other_defaults_menu.commands.update({
        "1": ("Magewell Defaults", lambda: set_magewell_defaults()),
        "2": ("Set Max Browsers", lambda: nav.push(max_browsers_menu)),
        "3": ("Set External Headphones", lambda: RunScriptAction(LOCAL_SCRIPTS_DIR, "AudioSwitcher", "-s", "External Headphones").execute()),
        "4": ("Enable API Control", lambda: enable_api_server()),
        "5": ("Enable Multisite", lambda: nav.push(multisite_menu)),
        # "6": ("Enable Kiosk Mode", lambda: WriteDefaultsAction("TTMenu", "KioskMode", "0").execute()),
        "6": ("Enable Kiosk Mode", lambda: RunCommandAction("defaults", "delete", "com.t1visions.TTMenu", "DisableKiosk").execute()),
        "t": ("Toggle TTMenu", lambda: ToggleTTMenuAction().execute()),        
        "b": ("Back", nav.back),
        "qq": ("Quit", exit_app),
    })

    dock_menu.commands.update({
        "1": ("Configure Dock", lambda: configure_docks()),
        "2": ("Initialize Dock", lambda: initialize_dock()),
        "t": ("Toggle TTMenu", lambda: ToggleTTMenuAction().execute()),
        "b": ("Back", nav.back),
        "qq": ("Quit", exit_app),
    })

    software_vc_menu.commands.update({
        "1": ("Set up BetterDisplays", lambda: run_betterdisplays_sh()),
        "2": ("Enable Zoom", lambda: initialize_software_vc("zoom")),
        "3": ("Enable Teams", lambda: initialize_software_vc("teams")),
        "4": ("Enable both", lambda: initialize_software_vc("both")),
        "t": ("Toggle TTMenu", lambda: ToggleTTMenuAction().execute()),
        "b": ("Back", nav.back),
        "qq": ("Quit", exit_app),
    })

    uppd_menu.commands.update({
        "1": ("Set Defaults", lambda: set_uppd_defaults()),
        "t": ("Toggle TTMenu", lambda: ToggleTTMenuAction().execute()),
        "h": ("Home", nav.home),
        "b": ("Back", nav.back),
        "qq": ("Quit", exit_app),
    })

    pq_menu.commands.update({
        "1": ("Set Defaults", lambda: subprocess.run([os.path.join(SCRIPTS_DIR, "tester.sh")])),
        "t": ("Toggle TTMenu", lambda: ToggleTTMenuAction().execute()),
        "b": ("Back", nav.back),
        "qq": ("Quit", exit_app),
    })

    touch_menu.commands.update({
        "1": ("UPPD", lambda: nav.push(uppd_menu)),
        "2": ("PQ", lambda: nav.push(pq_menu)),
        "t": ("Toggle TTMenu", lambda: ToggleTTMenuAction().execute()),
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
            state.integral_config.integrals[next(iter(state.integral_config.integrals))]['serial'] if state.integral_config.integrals else 'XXXXXXXX'
        ])),
        "6": ("Custom Command", lambda: custom_integral_command()),
        "b": ("Back", nav.back),
        "qq": ("Quit", exit_app),
    })

    display_serial_menu.commands.update({
        "1": ("Find USB Serial #", lambda: nav.push(find_display_serial_menu)),
        "2": ("Set Defaults", lambda: nav.push(display_serial_defaults_menu)),
        "3": ("Set crontab", lambda: set_display_serial_crontab()),
        "4": ("Test Power On", lambda: subprocess.run([os.path.join(SCRIPTS_DIR, "tester.sh")])),
        "b": ("Back", nav.back),
        "h": ("Home", nav.home),
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

    display_serial_defaults_menu.commands.update({
        "1": ("Avocor E50", lambda: set_display_serial_defaults("AvocorE50")),
        "2": ("Avocor F50", lambda: set_display_serial_defaults("AvocorF50")),
        "3": ("AvocorG60", lambda: set_display_serial_defaults("AvocorG60")),
        "4": ("AvocorH20", lambda: set_display_serial_defaults("AvocorH20")),
        "b": ("Back", nav.back),
        "qq": ("Quit", exit_app),
    })

    frameScaling_menu.commands.update({
        "1": ("4k 55in-65in", lambda: set_frameScaling("0.6")),
        "2": ("4k 75in", lambda: set_frameScaling("0.65")),
        "3": ("4k 84in-98in", lambda: set_frameScaling("0.5", True)),
        "4": ("5k 21:9", lambda: set_frameScaling("0.5", True)),
        "5": ("1080p 55in", lambda: set_frameScaling("1")),
        "6": ("1080p 80in", lambda: set_frameScaling("0.7")),
        "7": ("4x2 LCD Video Wall", lambda: set_frameScaling("0.7", True)),
        "8": ("4x2 LED Video Wall", lambda: set_frameScaling("0.75", True)),
        "9": ("Default - 0.6", lambda: set_frameScaling("0.6")),
        "10": ("Default LCD/LED - 0.7", lambda: set_frameScaling("0.7")),
        "b": ("Back", nav.back),
        "h": ("Home", nav.home),
        "qq": ("Quit", exit_app),
    })

    touchDisplay_menu.commands.update({
        "1": ("4k 55in-65in", lambda: set_touch_display_resolution("70")),
        "2": ("4k 75in-98in", lambda: set_touch_display_resolution("52")),
        "3": ("5k 21:9", lambda: set_touch_display_resolution("24")),
        "4": ("1080p 55in", lambda: set_touch_display_resolution("40")),
        "5": ("1080p 80in", lambda: set_touch_display_resolution("28")),
        "6": ("4x2 LCD Video Wall", lambda: set_touch_display_resolution("40")),
        "7": ("4x2 LED Video Wall", lambda: set_touch_display_resolution("52")),
        "8": ("Default - 70", lambda: set_touch_display_resolution("70")),
        "9": ("Default LCD/LED - 40", lambda: set_touch_display_resolution("40")),
        "10": ("Custom Resolution", lambda: set_touch_display_resolution("custom")),
        "b": ("Back", nav.back),
        "h": ("Home", nav.home),
        "qq": ("Quit", exit_app),
    })

    resolution_menu.commands.update({
        "1": ("Set resolution to 3840x2160", lambda: set_screen_size("3840x2160")),
        "2": ("Set resolution to 5120x2880", lambda: set_screen_size("5120x2880")),
        "3": ("Set resolution to 1920x1080", lambda: set_screen_size("1920x1080")),
        "4": ("Set custom resolution", set_custom_res),
        "t": ("Toggle TTMenu", lambda: ToggleTTMenuAction().execute()),
        "b": ("Back", nav.back),
        "qq": ("Quit", exit_app),
    })

    display_config_menu.commands.update({
        "1": ("Set screen count", set_screen_count),
        "2": ("Set screen size", lambda: nav.push(resolution_menu)),
        "3": ("Show current", lambda: print(f"Screen Count: {state.display_config.count}, Screen Size: {state.display_config.size}")),
        "4": ("Set frame", set_frame),
        "5": ("Set touchDisplayResolution", lambda: nav.push(touchDisplay_menu)),
        "6": ("Set frameScaling", lambda: nav.push(frameScaling_menu)),
        "t": ("Toggle TTMenu", lambda: ToggleTTMenuAction().execute()),
        "b": ("Back", nav.back),
        "h": ("Home", nav.home),
        "qq": ("Quit", exit_app),
    })

    displays_menu.commands.update({
        "1": ("Displays Configuration", lambda: nav.push(display_config_menu)),
        "2": ("Serial Commands Menu", lambda: nav.push(display_serial_menu)),
        "3": ("SPDisplays", lambda: RunCommandAction(["/usr/sbin/system_profiler", "SPDisplaysDataType"]).execute()),
        "4": ("Run screensave", lambda: RunCommandAction([os.path.join(T1VAPPS_DIR, "screenArrange/screenArrange"), "save"]).execute()),
        "t": ("Toggle TTMenu", lambda: ToggleTTMenuAction().execute()),
        "b": ("Back", nav.back),
        "qq": ("Quit", exit_app),
    })

    main_menu.commands.update({
        "1": ("Displays Menu", lambda: nav.push(displays_menu)),
        "2": ("Integral Menu", lambda: nav.push(integral_menu)),
        "3": ("Dock Menu", lambda: nav.push(dock_menu)),
        "4": ("Touch Menu", lambda: nav.push(touch_menu)),
        "5": ("Software VC Menu", lambda: nav.push(software_vc_menu)),
        "6": ("Other Defaults", lambda: nav.push(other_defaults_menu)),
        "t": ("Toggle TTMenu", lambda: ToggleTTMenuAction().execute()),
        "pf": ("Disable Firewall", lambda: subprocess.run(["sudo", "/sbin/pfctl", "-d"])),
        "b4": ("Load Last Configs", lambda: LoadStateAction(state).execute()),
        "vs": ("View Current Configurations", lambda: subprocess.run(["cat", "app_state.json"])),
        "cc": ("Clear Configurations", lambda: nav.push(clear_config_menu)),
        "dd": ("Delete Configurations", lambda: DeleteConfigAction().execute()),
        "qq": ("Quit", exit_app),
    })

    
    return nav, main_menu

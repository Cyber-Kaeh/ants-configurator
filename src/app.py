from src.menu import Menu, MenuApp
import sys
import subprocess
import os
import re
import io
import contextlib
import importlib
import threading
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from src.ascii_art import ASCII_ART
from src.models import DisplayConfig, DockConfig, IntegralConfig, VCConfig
from src.actions import SaveStateAction, LoadStateAction, DeleteConfigAction, ToggleTTMenuAction, WriteDefaultsAction, RunIntegralSerialAction, RunCommandAction, AddCrontabEntryAction, ClearConfigAction
from src.scripts import integral_crontabs

SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "scripts"))
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
        self.app: MenuApp | None = None

    def push(self, menu):
        self.stack.append(menu)
        if self.app:
            self.app.current_menu = menu

    def back(self):
        if len(self.stack) > 1:
            self.stack.pop()
            if self.app:
                self.app.current_menu = self.stack[-1]

    def home(self):
        if not self.stack:
            return
        while len(self.stack) > 1:
            self.stack.pop()
        if self.app:
            self.app.current_menu = self.stack[0]


def exit_app():
    sys.exit(0)


def build_app():
    state = AppState()
    nav = MenuStack()
    try:
        LoadStateAction(state).execute()
    except Exception as e:
        print(f"Error loading state: {e}")

    def to_panel(fn):
        """Captures all print() output from fn and sends it to the output panel."""
        def wrapper(*args, **kwargs):
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                result = fn(*args, **kwargs)
            output = buf.getvalue()
            if output and nav.app:
                for line in output.splitlines():
                    nav.app.add_output(line)
            return result
        return wrapper

    def run_streaming(cmd, on_done=None):
        """Run cmd in a background thread, streaming each output line to the panel in real time."""
        def _thread():
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
            )
            for raw_line in proc.stdout:
                line = raw_line.rstrip('\n')
                if nav.app:
                    nav.app.add_output(line)
            proc.wait()
            if on_done and nav.app:
                on_done(proc.returncode)
        threading.Thread(target=_thread, daemon=True).start()

    def calculate_frame():
        try:
            res = state.display_config.size
            count = state.display_config.count
            if res is None or count is None:
                nav.app.set_message("Screen size or count not set.")
                return
            width, height = map(int, res.split('x'))
            total_width = width * count
            state.display_config.height = height
            state.display_config.placement = total_width
            SaveStateAction(state).execute()
            nav.app.set_message(f"Calculated frame size: {total_width}x{height}")
        except Exception as e:
            print(f"Error calculating frame: {e}")

    @to_panel
    def set_frame():
        calculate_frame()
        if state.display_config.placement:
            frame_string = f"{{{{0, 0}}, {{{state.display_config.placement}, {state.display_config.height}}}}}"
            WriteDefaultsAction("TTMenu", "frame", frame_string, value_type="-string").execute()
            WriteDefaultsAction("MultiTouchCalibrate", "frame", frame_string, value_type="-string").execute()
            SaveStateAction(state).execute()

    @to_panel
    def set_custom_res():
        res_completer = WordCompleter(["1280x720", "1920x1080", "3840x2160", "5120x2160"], ignore_case=True)
        def _on_input(value):
            if value is None:
                return
            state.display_config.size = value
            to_panel(lambda: SaveStateAction(state).execute())()
        if nav.app:
            nav.app.request_input("Enter custom resolution (e.g., 3840x2160):", _on_input, completer=res_completer)

    @to_panel
    def set_screen_count():
        def _on_input(value):
            if value is None:
                return
            try:
                count = int(value)
            except ValueError:
                return
            state.display_config.count = count
            def _writes():
                print(f"Screen count set to {count}")
                SaveStateAction(state).execute()
                if count > 1:
                    WriteDefaultsAction("TTMenu", "thinkHubMediumLineDrawWidth", "10").execute()
                    WriteDefaultsAction("TTMenu", "thinkHubThickLineDrawWidth", "20").execute()
                    state.vc_config.multi_display = True
            to_panel(_writes)()
        if nav.app:
            nav.app.request_input("Enter number of displays:", _on_input)

    @to_panel
    def set_screen_size(option):
        state.display_config.size = option
        SaveStateAction(state).execute()
        print(f"Screen size set to {option}")
        nav.back()

    @to_panel
    def set_frameScaling(option, include_pan_gesture=False):
        if include_pan_gesture:
            WriteDefaultsAction("TTMenu", "panGestureFactor", "2").execute()
        WriteDefaultsAction("TTMenu", "frameScaling", option).execute()
        nav.back()
        nav.app.set_message(f"Frame scaling set to {option}")

    @to_panel
    def set_touch_display_resolution(option):
        if option == "custom":
            def _on_input(value):
                if value is None:
                    return
                to_panel(lambda: WriteDefaultsAction("TTMenu", "touchDisplayResolution", value).execute())()
                nav.back()
                nav.app.set_message(f"Touch display resolution set to {value}")
            if nav.app:
                custom_res =nav.app.request_input("Enter custom touchDisplayResolution value:", _on_input)
                to_panel(f"Touch display resolution set to {custom_res}")
        else:
            to_panel(lambda: WriteDefaultsAction("TTMenu", "touchDisplayResolution", option).execute())()
            nav.back()
            nav.app.set_message(f"Touch display resolution set to {option}")

    @to_panel
    def set_uppd_defaults():
        WriteDefaultsAction("TTMenu", "MTManagerSearchPriority", "UPDD").execute()
        WriteDefaultsAction("TTMenu", "thinkHubEnableRemoteKeyboardAction", "1").execute()
        command = ["/usr/local/bin/upddutils", "nodevice", "set", "minimum_notify_level", "2"]
        RunCommandAction(command, success_message="UPDD minimum notify level set.").execute()
        command = ["/usr/local/bin/upddprocesses", "stop", "-c"]
        RunCommandAction(command, success_message="UPDD processes stopped.").execute()
        AddCrontabEntryAction(
            "@reboot /bin/sleep 80; /usr/local/bin/upddprocesses stop -c",
            comment="Disable UPDD Commander so that touch events pass straight to TTMenu",
        ).execute()

    def configure_docks():
        common_names = ["Dock1", "Dock2", "Dock3", "Dock4", "Dock", "MTR"]
        common_res = ["1280x720", "1920x1080", "3840x2160"]
        dock_completer = WordCompleter(common_names, ignore_case=True)
        dock_res_completer = WordCompleter(common_res, ignore_case=True)

        def ask_dock_name():
            def _on_dock(dock_name):
                if dock_name is None or dock_name.lower() == 'done':
                    to_panel(lambda: SaveStateAction(state).execute())()
                    return
                if dock_name not in common_names:
                    def _on_confirm(resp):
                        if resp is None or resp.lower() not in ('y', 'yes'):
                            nav.app.add_output("Entry cancelled. Try again.")
                            ask_dock_name()
                            return
                        ask_res(dock_name)
                    nav.app.request_input(f"'{dock_name}' is not a common name. Continue? (y/N):", _on_confirm)
                else:
                    ask_res(dock_name)
            nav.app.request_input("Enter dock name (or 'done' if finished):", _on_dock, completer=dock_completer)

        def ask_res(dock_name):
            def _on_res(res):
                if res is None or res.lower() == 'done':
                    ask_dock_name()
                    return
                if not re.match(r"^\d+x\d+$", res):
                    nav.app.add_output(f"Invalid format: '{res}'. Use widthxheight (e.g., 1920x1080).")
                    ask_res(dock_name)
                    return
                if res not in common_res:
                    def _on_confirm(resp):
                        if resp is None or resp.lower() not in ('y', 'yes'):
                            ask_res(dock_name)
                            return
                        state.dock_config.add_dock(dock_name, res)
                        nav.app.add_output(f"Added {dock_name} with resolution: {res}")
                        ask_dock_name()
                    nav.app.request_input(f"'{res}' is not a common resolution. Continue? (y/N):", _on_confirm)
                else:
                    state.dock_config.add_dock(dock_name, res)
                    nav.app.add_output(f"Added {dock_name} with resolution: {res}")
                    ask_dock_name()
            nav.app.request_input(f"Enter resolution for {dock_name} (e.g., 1920x1080, or 'done'):", _on_res, completer=dock_res_completer)

        ask_dock_name()

    @to_panel
    def initialize_dock():
        if state.display_config.placement is None or not state.dock_config.names:
            nav.app.set_message("Screen placement and/or dock names not set.")
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

    def select_integral(callback):
        if not state.integral_config.integrals:
            nav.app.set_message("Error: No Integral serial ID set. Run '> Find Integral Serial #' first.")
            return
        if len(state.integral_config.integrals) == 1:
            key = next(iter(state.integral_config.integrals))
            nav.app.add_output(f"Using Integral: Serial ID {state.integral_config.integrals[key]['serial']}")
            callback(key)
        else:
            nav.app.add_output("Multiple Integrals detected. Select which one to use:")
            for key, integral in state.integral_config.integrals.items():
                nav.app.add_output(f"  {key}) Serial: {integral['serial']}, Firmware: {integral['firmware']}")
            def _on_choice(choice):
                if choice is None:
                    return
                if choice in state.integral_config.integrals:
                    callback(choice)
                else:
                    nav.app.add_output("Invalid selection.")
            nav.app.request_input("Enter the number of the Integral:", _on_choice)

    def set_integral_serial_crontab():
        def _on_selected(key):
            serial = state.integral_config.integrals[key]['serial']
            entries = integral_crontabs.generate_crontab_entries(serial)

            integral_crontab_type_menu = Menu("Select Crontab Type", {})

            def make_action(entry_key):
                def _action():
                    entry = entries[entry_key]
                    def _run():
                        AddCrontabEntryAction(entry['command'], comment=entry['description']).execute()
                    to_panel(_run)()
                    nav.back()
                    nav.app.set_message("Crontab entry added successfully.")
                return _action

            integral_crontab_type_menu.commands.update({
                "1": (entries['standard_mirror']['description'], make_action('standard_mirror')),
                "2": (entries['dock']['description'], make_action('dock')),
                "3": (entries['matrix_mode']['description'], make_action('matrix_mode')),
            })
            nav.push(integral_crontab_type_menu)

        select_integral(_on_selected)



    def custom_integral_command():
        def _on_selected(key):
            nav.app.add_output("Enter command to run, or 'help' for list of commands")
            def _on_command(cmd):
                if cmd is None:
                    return
                serial = state.integral_config.integrals[key]['serial']
                to_panel(lambda: RunIntegralSerialAction(serial, cmd).execute())()
            nav.app.request_input(">", _on_command)
        select_integral(_on_selected)

    def set_4k_mirror():
        def _on_selected(key):
            serial = state.integral_config.integrals[key]['serial']
            nav.app.add_output(f"Setting 4K mirror for Serial ID: {serial}")
            nav.app.start_spinner("Setting 4K mirror...")
            def _run():
                to_panel(lambda: RunIntegralSerialAction(serial, "setScalingNone").execute())()
                to_panel(lambda: RunIntegralSerialAction(serial, "reboot").execute())()
                nav.app.stop_spinner("4K mirror set.")
            threading.Thread(target=_run, daemon=True).start()
        select_integral(_on_selected)

    def reboot_integral():
        def _on_selected(key):
            serial = state.integral_config.integrals[key]['serial']
            nav.app.add_output(f"Rebooting Integral with Serial ID: {serial}")
            nav.app.start_spinner("Rebooting Integral...")
            def _run():
                to_panel(lambda: RunIntegralSerialAction(serial, "reboot").execute())()
                nav.app.stop_spinner("Reboot command sent.")
            threading.Thread(target=_run, daemon=True).start()
        select_integral(_on_selected)

    def interrogate_integral():
        def _on_selected(key):
            serial = state.integral_config.integrals[key]['serial']
            nav.app.add_output(f"Interrogating Integral with Serial ID: {serial}")
            nav.app.add_output("Starting interrogation (be patient, ~1 minute)...")
            nav.app.start_spinner("Interrogating Integral...")
            script_path = os.path.join(LOCAL_SCRIPTS_DIR, "integralStatus.py")
            def _on_done(rc):
                nav.app.stop_spinner(
                    "Interrogate complete." if rc == 0 else f"Interrogate failed (exit code {rc})."
                )
            run_streaming(
                [sys.executable, script_path, "--serial", f"/dev/tty.usbserial-{serial}", "--interrogate"],
                on_done=_on_done,
            )
        select_integral(_on_selected)

    def set_integral_serial_crontab():
        def _on_selected(key):
            serial = state.integral_config.integrals[key]['serial']
            entries = integral_crontabs.generate_crontab_entries(serial)

            integral_crontab_type_menu = Menu("Select Crontab Type", {})

            def make_action(entry_key):
                def _action():
                    entry = entries[entry_key]
                    def _run():
                        AddCrontabEntryAction(entry['command'], comment=entry['description']).execute()
                    to_panel(_run)()
                    nav.back()
                    nav.app.set_message("Crontab entry added successfully.")
                return _action

            integral_crontab_type_menu.commands.update({
                "1": (entries['standard_mirror']['description'], make_action('standard_mirror')),
                "2": (entries['dock']['description'], make_action('dock')),
                "3": (entries['matrix_mode']['description'], make_action('matrix_mode')),
            })
            nav.push(integral_crontab_type_menu)

        select_integral(_on_selected)

    def get_integral_serial_id():
        def _run():
            nav.app.start_spinner("Scanning for Integral serial devices...")
            result = subprocess.run(['ls /dev/tty.usb*'], shell=True, capture_output=True, text=True)
            matches = re.findall(r'/dev/tty\.usbserial-([A-Za-z0-9]+)', result.stdout)
            if not matches:
                nav.app.stop_spinner()
                nav.app.set_message("No serial USB found.")
                return
            nav.app.add_output(f"Found {len(matches)} serial device(s): {', '.join(matches)}")
            integrals = {}
            for idx, serial in enumerate(matches, 1):
                nav.app.add_output(f"Checking serial {serial}...")
                script_path = os.path.join(LOCAL_SERIAL_DIR, "integralSerial.py")
                serial_result = subprocess.run(
                    [sys.executable, script_path, f"/dev/tty.usbserial-{serial}", "getVersion"],
                    capture_output=True, text=True)
                get_version_output = serial_result.stdout
                if "HdFury" in get_version_output:
                    version_match = re.search(r"ver FW: ([\d.]+)", get_version_output)
                    firmware = version_match.group(1) if version_match else None
                    integrals[str(idx)] = {"serial": serial, "firmware": firmware}
                    nav.app.add_output(f"Integral {idx}: serial={serial}, firmware={firmware}")
                    SaveStateAction(state).execute()
                else:
                    nav.app.add_output(f"Serial {serial}: not an Integral (no HdFury response)")
            state.integral_config.integrals = integrals
            if not integrals:
                nav.app.stop_spinner("No Integrals found.")
            else:
                nav.app.stop_spinner(f"Done. Found {len(integrals)} Integral(s).")
        threading.Thread(target=_run, daemon=True).start()

    @to_panel
    def set_display_serial_crontab():
        AddCrontabEntryAction(
            "@reboot /bin/sleep 200; /usr/local/bin/python /Local/scripts/DisplayMegaScript.py --fix --notify --reboot",
            comment="Checks display(s) signal status",
        ).execute()

    @to_panel
    def set_display_serial_defaults(model):
        if not state.display_config.serial:
            nav.app.set_message("No display serial found, run > Find USB Serial #.")
            return
        serial = state.display_config.serial
        device_path = f"/dev/tty.usbserial-{serial}"
        if not os.path.exists(device_path):
            nav.app.set_message(f"Serial device not connected: {device_path}")
            print(f"❌ Aborted: Serial device not found: {device_path}")
            print("Run '> Find USB Serial #' to update the serial ID.")
            return
        state.display_config.model = model
        SaveStateAction(state).execute()
        module = importlib.import_module(f"src.scripts.{model}")
        module.configure(serial)
        displays_list = ["AvocorH20", "AvocorF50", "AvocorG60"]
        if model in displays_list:
            print("Adding crontab for displayMegaScript.py")
            set_display_serial_crontab()
        nav.back()

    def get_display_serial_id(choice):
        def _run():
            nav.app.start_spinner(f"Scanning for {choice} display serial...")
            result = subprocess.run(['ls /dev/tty.usb*'], shell=True, capture_output=True, text=True)
            matches = re.findall(r'/dev/tty\.usbserial-([A-Za-z0-9]+)', result.stdout)
            if not matches:
                nav.app.stop_spinner(f"No matching serial found for {choice}")
                return
            found = False

            for serial in matches:
                nav.app.add_output(f"Checking serial {serial}...")
                script_path = os.path.join(LOCAL_SERIAL_DIR, f"{choice}.py")
                serial_result = subprocess.run(
                    [sys.executable, script_path, f"/dev/tty.usbserial-{serial}", "GetPower"],
                    capture_output=True, text=True
                )
                if "Display is ON" in serial_result.stdout:
                    state.display_config.serial = serial
                    nav.app.add_output(f"Display Serial ID found: {serial}")
                    SaveStateAction(state).execute()
                    nav.app.set_message(f"Display Serial ID set to: {serial}")
                    found = True
                    break
                else:
                    nav.app.add_output(f"No display found for serial: {serial}")

            if nav.app:
                if found:
                    nav.app.stop_spinner(f"Display Serial ID set to: {state.display_config.serial}")
                    nav.app._loop.call_soon_threadsafe(nav.back)
                    nav.app.set_message(f"Display Serial ID set to: {state.display_config.serial}")
                else:
                    nav.app.stop_spinner(f"Could not find a display for {choice}")

        threading.Thread(target=_run, daemon=True).start()

    def run_betterdisplays_sh():
        nav.app.add_output("If you want to add a license for BetterDisplays,")
        nav.app.add_output("copy the command from the library page and run it in terminal.")
        nav.app.add_output("https://sites.google.com/a/t1v.com/process-docs/technical-knowledge-database/virtual-fitheadless-better-display-setup")
        def _on_continue(resp):
            if resp is None or resp.lower() in ("q", "quit"):
                exit_app()
                return
            if resp.lower() in ("b", "back"):
                return
            def _on_toggled(resp2):
                if resp2 is not None and resp2.lower() in ("n", "no"):
                    to_panel(lambda: ToggleTTMenuAction().execute())()
                nav.app.add_output("Beginning BetterDisplays setup, this may take a few moments...")
                def _run():
                    script_path = os.path.join(SCRIPTS_DIR, "better_displays.sh")
                    result = subprocess.run(
                        [script_path, str(state.display_config.placement), str(state.display_config.count)],
                        capture_output=True, text=True
                    )
                    if result.returncode == 0:
                        print("BetterDisplays setup completed successfully.")
                        print(result.stdout)
                    else:
                        print("Error during BetterDisplays setup:")
                        print(result.stderr)
                to_panel(_run)()
            nav.app.request_input("Is TTMenu toggled down? (y/N):", _on_toggled)
        nav.app.request_input("[Q]uit / [B]ack / any key to continue:", _on_continue)

    def initialize_software_vc(choice):
        if state.display_config.placement is None or state.display_config.height is None:
            nav.app.add_output("Error: Screen placement not set. Please set screen in Display menu first.")
            return

        def _do_vc():
            display_width = state.display_config.placement
            height = state.display_config.height - 720
            dock_width = state.dock_config.total_width
            placement = display_width + dock_width
            multi_string = f"{{{{{placement}, {height}}}}}, {{{{1280, 720}}}}"
            def _run():
                if state.display_config.count == 1:
                    WriteDefaultsAction("TTMenu", "screenUpdateOnAllChanges", "1").execute()
                    WriteDefaultsAction("TTMenu", "desktopMoveAllWindows", "1").execute()
                else:
                    WriteDefaultsAction("TTMenu", "desktopMoveAllWindows", "1").execute()
                    WriteDefaultsAction("TTMenu", "thinkHubDesktopThinkHubScreenIndex", "0").execute()
                    WriteDefaultsAction("TTMenu", "thinkHubDesktopScreenRect", multi_string, value_type="-string").execute()
                if choice in ("zoom", "both"):
                    WriteDefaultsAction("TTMenu", "ThinkHubZoom", "1").execute()
                if choice in ("teams", "both"):
                    WriteDefaultsAction("TTMenu", "ThinkHubTeams", "1").execute()
                    WriteDefaultsAction("automate", "VCCaptureRect", f"{placement},0,1280,720", value_type="-string").execute()
                SaveStateAction(state).execute()
            to_panel(_run)()

        if not state.dock_config.enabled:
            def _on_confirm(resp):
                if resp is None or resp.lower() not in ("y", "yes"):
                    return
                _do_vc()
            nav.app.request_input("Docks should be set up before VC. Continue anyway? (y/N):", _on_confirm)
        else:
            _do_vc()

    @to_panel
    def set_magewell_defaults():
        WriteDefaultsAction("TTMenu", "deviceSettings", "/Users/t1user/Documents/deviceSettings.plist").execute()
        WriteDefaultsAction("TTMenu", "captureSessionDefaultAudioVolume", "0.75").execute()
        WriteDefaultsAction("TTMenu", "thinkHubEnableTouchBack", "1").execute()

    @to_panel
    def set_max_browsers(count):
        WriteDefaultsAction("TTMenu", "webViewMaxClients", count).execute()
        nav.back()

    @to_panel
    def enable_api_server():
        RunCommandAction(["cp", "/Local/scripts/externalCommand/com.t1v.externalCommandTelnetServer3.plist", "/Users/t1user/Library/LaunchAgents/"]).execute()
        RunCommandAction(["launchctl", "load", "/Library/LaunchAgents/com.t1v.externalCommandTelnetServer3.plist"]).execute()

    def enable_multisite_smb():
        def _on_input(value):
            if value is None:
                return
            def _writes():
                WriteDefaultsAction("TTMenu", "thinkHubMultiSite", "1").execute()
                WriteDefaultsAction("TTMenu", "thinkHubMultiSiteRoom", value).execute()
            to_panel(_writes)()
        if nav.app:
            nav.app.request_input("Enter customer name for Multisite Room:", _on_input)

    def enable_multisite_enterprise():
        to_panel(lambda: WriteDefaultsAction("TTMenu", "thinkHubMultiSite", "1").execute())()
        def _on_ip(ip):
            if ip is None or not ip.strip():
                nav.app.set_message("Multisite enabled. No relay IP set.")
                return
            def _writes():
                WriteDefaultsAction("TTMenu", "netMessengerHostName", ip.strip()).execute()
                WriteDefaultsAction("TTMenu", "janusAddress", f"ws://{ip.strip()}:8188").execute()
            to_panel(_writes)()
            nav.app.set_message("Multisite enterprise configured.")
        if nav.app:
            nav.app.request_input("Enter Multisite Relay IP ([Enter] to skip):", _on_ip)

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

    multisite_menu.commands.update({
        "1": ("Enable Multisite Enterprise", lambda: enable_multisite_enterprise()),
        "2": ("Enable Multisite SMB", lambda: enable_multisite_smb()),
    })

    clear_config_menu.commands.update({
        "1": ("Clear Display Config", to_panel(lambda: ClearConfigAction(state, "display").execute())),
        "2": ("Clear Dock Config", to_panel(lambda: ClearConfigAction(state, "dock").execute())),
        "3": ("Clear Integral Config", to_panel(lambda: ClearConfigAction(state, "integral").execute())),
        "4": ("Clear Software VC Config", to_panel(lambda: ClearConfigAction(state, "vc").execute())),
    })

    max_browsers_menu.commands.update({
        "1": ("CollaboratOR Lite - 4", lambda: set_max_browsers("4")),
        "2": ("CX-02 - 5", lambda: set_max_browsers("5")),
        "3": ("CX-06/07 - 10", lambda: set_max_browsers("10")),
    })

    other_defaults_menu.commands.update({
        "1": ("Magewell Defaults", lambda: set_magewell_defaults()),
        "2": ("Set Max Browsers", lambda: nav.push(max_browsers_menu)),
        "3": ("Set Default Web Browser", to_panel(lambda: WriteDefaultsAction("TTMenu", "webViewDefaultURL", "http://www.bing.com/").execute())),
        "4": ("Set External Headphones", to_panel(lambda: RunCommandAction(
            [os.path.join(LOCAL_SCRIPTS_DIR, "AudioSwitcher"), "-s", "External Headphones"]).execute())),
        "5": ("Enable API Control", lambda: enable_api_server()),
        "6": ("Enable Multisite", lambda: nav.push(multisite_menu)),
        "7": ("Enable Kiosk Mode", to_panel(lambda: RunCommandAction(
            ["defaults", "delete", "com.t1visions.TTMenu", "DisableKiosk"]).execute())),
    })

    dock_menu.commands.update({
        "1": ("Configure Dock", lambda: configure_docks()),
        "2": ("Initialize Dock", lambda: initialize_dock()),
    })

    software_vc_menu.commands.update({
        "1": ("Set up BetterDisplays", lambda: run_betterdisplays_sh()),
        "2": ("Enable Zoom", lambda: initialize_software_vc("zoom")),
        "3": ("Enable Teams", lambda: initialize_software_vc("teams")),
        "4": ("Enable both", lambda: initialize_software_vc("both")),
    })

    uppd_menu.commands.update({
        "1": ("Set Defaults", lambda: set_uppd_defaults()),
    })

    pq_menu.commands.update({
        "1": ("Set Defaults", to_panel(lambda: RunCommandAction(
            [os.path.join(SCRIPTS_DIR, "tester.sh")]).execute())),
    })

    touch_menu.commands.update({
        "1": ("UPPD", lambda: nav.push(uppd_menu)),
        "2": ("PQ", lambda: nav.push(pq_menu)),
    })

    integral_menu.commands.update({
        "1": ("Find Integral Serial #", lambda: get_integral_serial_id()),
        "2": ("Interrogate Integral", lambda: interrogate_integral()),
        "3": ("Reboot Integral", lambda: reboot_integral()),
        "4": ("Set 4K Mirror", lambda: set_4k_mirror()),
        "5": ("Set Integral Crontab", lambda: set_integral_serial_crontab()),
    })

    display_serial_menu.commands.update({
        "1": ("Find USB Serial #", lambda: nav.push(find_display_serial_menu)),
        "2": ("Set Defaults", lambda: nav.push(display_serial_defaults_menu)),
        "3": ("Set crontab", lambda: set_display_serial_crontab()),
        "4": ("Test Power On", to_panel(lambda: RunCommandAction(
            [os.path.join(SCRIPTS_DIR, "tester.sh")]).execute())),
    })

    find_display_serial_menu.commands.update({
        "1": ("Avocor E50", lambda: get_display_serial_id("AvocorE50")),
        "2": ("Avocor F50", lambda: get_display_serial_id("AvocorF50")),
        "3": ("AvocorG60", lambda: get_display_serial_id("AvocorG60")),
        "4": ("AvocorH20", lambda: get_display_serial_id("AvocorH20")),
    })

    display_serial_defaults_menu.commands.update({
        "1": ("Avocor E50", lambda: set_display_serial_defaults("AvocorE50")),
        "2": ("Avocor F50", lambda: set_display_serial_defaults("AvocorF50")),
        "3": ("AvocorG60", lambda: set_display_serial_defaults("AvocorG60")),
        "4": ("AvocorH20", lambda: set_display_serial_defaults("AvocorH20")),
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
    })

    resolution_menu.commands.update({
        "1": ("Set resolution to 3840x2160", lambda: set_screen_size("3840x2160")),
        "2": ("Set resolution to 5120x2160", lambda: set_screen_size("5120x2160")),
        "3": ("Set resolution to 1920x1080", lambda: set_screen_size("1920x1080")),
        "4": ("Set custom resolution", set_custom_res),
    })

    display_config_menu.commands.update({
        "1": ("Set screen count", set_screen_count),
        "2": ("Set screen size", lambda: nav.push(resolution_menu)),
        "3": ("Show current", to_panel(lambda: print(
            f"Screen Count: {state.display_config.count}, Screen Size: {state.display_config.size}"))),
        "4": ("Set frame", set_frame),
        "5": ("Set touchDisplayResolution", lambda: nav.push(touchDisplay_menu)),
        "6": ("Set frameScaling", lambda: nav.push(frameScaling_menu)),
    })

    displays_menu.commands.update({
        "1": ("Displays Configuration", lambda: nav.push(display_config_menu)),
        "2": ("Serial Commands Menu", lambda: nav.push(display_serial_menu)),
        "3": ("SPDisplays", to_panel(lambda: RunCommandAction(
            ["/usr/sbin/system_profiler", "SPDisplaysDataType"]).execute())),
        "4": ("Run screensave", to_panel(lambda: RunCommandAction(
            [os.path.join(T1VAPPS_DIR, "screenArrange/screenArrange"), "save"]).execute())),
    })

    main_menu.commands.update({
        "1": ("Displays Menu", lambda: nav.push(displays_menu)),
        "2": ("Integral Menu", lambda: nav.push(integral_menu)),
        "3": ("Dock Menu", lambda: nav.push(dock_menu)),
        "4": ("Touch Menu", lambda: nav.push(touch_menu)),
        "5": ("Software VC Menu", lambda: nav.push(software_vc_menu)),
        "6": ("Other Defaults", lambda: nav.push(other_defaults_menu)),
        "pf": ("Disable Firewall", to_panel(lambda: RunCommandAction(
            ["sudo", "/sbin/pfctl", "-d"], success_message="Firewall disabled.").execute())),
        #"b4": ("Load Last Configs", to_panel(lambda: LoadStateAction(state).execute())),
        #"vs": ("View Current Configurations", to_panel(lambda: RunCommandAction(
        #    ["cat", "app_state.json"]).execute())),
        "cc": ("Clear Configurations", lambda: nav.push(clear_config_menu)),
        #"dd": ("Delete Configurations", to_panel(lambda: DeleteConfigAction().execute())),
    })

    # Build global key bindings
    kb = KeyBindings()

    @kb.add('b')
    def _back(_event):
        nav.back()

    @kb.add('h')
    def _home(_event):
        nav.home()

    @kb.add('q', 'q')
    def _quit(_event):
        exit_app()

    @kb.add('t')
    def _toggle(_event):
        to_panel(lambda: ToggleTTMenuAction().execute())()

    app = MenuApp(
        extra_bindings=kb,
        toolbar_actions=[
            ("b",  "back",   nav.back),
            ("h",  "home",   nav.home),
            ("t",  "toggle", lambda: to_panel(lambda: ToggleTTMenuAction().execute())()),
            ("qq", "quit",   exit_app),
        ],
    )
    nav.app = app

    return app, nav, main_menu